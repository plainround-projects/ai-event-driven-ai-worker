# Architecture: an event-driven AI worker

A signed email event arrives through a webhook, waits in a PostgreSQL queue, and a worker runs the extractor model on it, writes a ticket and an acknowledgment to an outbox in one transaction, and a relay sends the acknowledgment through a fake mail sender that records every send. The design answers four questions an interviewer asks of any consumer: what happens on a duplicate, on a crash halfway, on an event that can never succeed, and on a burst that meets the model's rate limit.

## Components and what each owns

| Component | Where | Owns |
| --- | --- | --- |
| Signature check | `domain/signature.py` | HMAC-SHA256 over `timestamp.body`, constant-time compare, a five-minute age limit, two distinct rejection reasons. Pure functions. |
| Event decoding | `domain/events.py` | Turns a payload into an event or raises a permanent error with a reason: `malformed_event`, `event_too_large` (limit 100,000 bytes of email), `bad_encoding`. |
| Backoff | `domain/backoff.py` | Exponential delay with full jitter and a cap. |
| Webhook | `interfaces/webhook.py` | Size-limit, verify, enqueue, answer 202. The model is not imported here, so its latency cannot reach this path. |
| Queue | `infrastructure/postgres.py` (`PostgresQueue`) | The `deliveries` table: claim with `FOR UPDATE SKIP LOCKED`, lease expiry as redelivery, ack, retry with a delay, dead-letter, redrive. |
| Handler | `application/handler.py` | One delivery to a final outcome: decode, skip a duplicate, check the deadline, run the model, apply the effects once, acknowledge. |
| Extractor | `application/extraction.py` | One model call and one repair call; a schema failure after the repair is a permanent error. Prompt text and version come from `prompts/extract.v1.md`. |
| Effects store | `infrastructure/postgres.py` (`PostgresEffects`) | The processed mark, the ticket and the outbox row in one statement. |
| Worker | `application/worker.py` | Claims batches, handles them on a bounded thread pool, finishes work in flight on a stop request, waits and retries when the queue is unreachable. |
| Outbox relay | `application/outbox.py` | Sends unsent acknowledgments, tolerates a send that happened before a crash, marks the row sent. |
| Model adapters | `infrastructure/fake_model.py`, `cassette.py`, `claude_model.py` | A fake with delay, error rate and a token-bucket rate limit; a recorded replay; the Claude adapter. All behind `ChatModel`. |
| Measurements | `interfaces/measure.py` | The burst (two concurrency settings) and the crash test (a real child process killed at a named point). |

## Pattern: layers, with a queue in the database

Domain depends on nothing. Application depends on domain and on the ports it defines (`DeliveryQueue`, `EffectsStore`, `OutboxStore`, `MailGateway`, `ChatModel`, `Clock`). Infrastructure implements the ports. Interfaces wire them. `make lint` enforces this with import-linter, plus a second contract that keeps vendor SDKs, web frameworks and database drivers out of domain and application.

The queue is a table, not a broker. That is the lesson's allowance ("a database table read with row locks is enough"), and it has one real advantage here: the queue, the processed marks, the tickets and the outbox live in one database, so the claim, the effects and the acknowledgment can be reasoned about with ordinary transactions.

## Data flow

Drawn versions of this figure and of the walk-through: [the architecture](docs/diagrams/architecture.svg) and [one run](docs/diagrams/flow.svg).

```text
sender -> webhook ---202---> deliveries (queued)
                                 |  claim: FOR UPDATE SKIP LOCKED, lease 30 s
                                 v
                             worker pool (N threads)
                                 |
        decode -> already processed? -> deadline? -> model call (outside any transaction)
                                 |                         |
                      duplicate: ack            retryable error: retry with jittered delay
                                 |              permanent error: dead_letters (reason, attempts, hash)
                                 v
        ONE statement: processed_events + tickets + outbox
                                 |
                                 v
                         ack the delivery
                                 
outbox --relay--> fake mail sender (sent_mail, unique event id) --> mark sent
```

### One event, step by step

1. The webhook reads the body as a stream and rejects it with 413 as soon as it passes the size limit. It then checks the signature and the age, inserts a `deliveries` row and answers 202. A tampered body and a replayed old request get 401 with different reasons.
2. A worker thread claims the row: status `processing`, attempts plus one, a lease of 30 seconds. If the process dies, the lease expires and the row is claimed again; that is the redelivery.
3. The handler decodes the payload. Malformed JSON, a body over the limit and invalid UTF-8 are permanent: the delivery goes to `dead_letters` at once, with the reason, the attempt count, the last error and a 12-character hash of the payload.
4. The handler reads `processed_events` fresh from the database. A hit means a twin delivery already finished: acknowledge and move on, no model call.
5. The model call runs outside any transaction. A rate limit, a server error or a timeout is retryable: the row is released with `available_at` set to now plus a jittered delay. A schema failure after one repair is permanent, and so is any other model-call failure a retry will not fix: the delivery goes to `dead_letters` with the reason `permanent_error`. A fifth failed attempt or an event older than its deadline is parked too.
6. One SQL statement inserts the processed mark (`ON CONFLICT DO NOTHING`), the ticket and the outbox row. If a twin delivery committed first, the mark insert returns nothing, the other two inserts select from it, and nothing is written.
7. The delivery is acknowledged. A crash between step 6 and this one leaves a committed event and an unacknowledged row; the redelivery finds the mark in step 4.
8. The relay sends each acknowledgment through the mail gateway. The send table has a unique event id, so a send repeated after a crash is refused and the row is just marked sent.

## Decisions and trade-offs

| Decision | Why | Cost |
| --- | --- | --- |
| The queue is a PostgreSQL table with `SKIP LOCKED` | One database to reason about; no broker to run | Throughput is bounded by the database; no fan-out to many consumer groups |
| `event_id` is not unique in `deliveries`; `processed_events` is the guard | Redelivery and webhook retries legitimately repeat an id; the effect must be idempotent, the delivery need not be | Duplicates are stored and read before they are skipped |
| The model call is outside the transaction | A transaction open across a slow call holds a connection and locks for nothing | A crash after the call wastes one call; the retry pays for it again |
| Mark, ticket and outbox in one statement over an autocommit pool | One round trip and one transaction; 52 ms instead of 180 ms per event on the loaded test machine | The statement is longer than three inserts; it needs a comment (ADR 0002) |
| Lease expiry is the only redelivery mechanism | A dead worker needs no coordinator | A slow handler that outlives its lease can be handled twice; the processed mark makes that safe |
| Full jitter backoff | Many failing events must not retry in step against a model that is already struggling | Retry times are random, so tests inject the random generator |
| Dead letter keeps a hash and the payload | A person can act, and can tell two entries are the same payload without opening the email | The payload is stored; a production system would encrypt or redact it |
| Burst limited by a fake model's token bucket, not by a fixed error percentage | A real provider limits the request rate; a fixed percentage hides how concurrency interacts with it | The fake is still a model of a limit, not the limit (see "Limits") |

## Failure modes the lesson teaches, and where the code shows them

| Failure | Where | Evidence |
| --- | --- | --- |
| Replay of a captured request | `domain/signature.py` | `make webhook-demo`, `make bench-webhook`: 401 "request too old" |
| Tampered body | the same | 401 "signature mismatch", a different reason |
| Duplicate delivery | `handler.py`, `PostgresEffects.apply` | `make run`: the replay processes 0 events and counts 1,010 duplicates |
| Race between twins | the primary key on `processed_events` | `tests/integration`: two threads apply one event, one wins |
| Poison event | `domain/events.py`, `dead_letters` | `make run`: 10 dead letters with reasons; none holds up the 990 behind it |
| Retry storm | `domain/backoff.py` | `tests/unit/domain`: delays grow, stay under the cap, differ per call |
| Crash after the model, or after the commit | `handler.py` `crash_at` | `make crash-test`: exit 137 at each point, then no lost and no duplicated event |
| Lost acknowledgment | `outbox.py` | the relay marks a row sent when the mail table already holds the send |
| Database restart | `worker.py`, `cli.py` `_relay` | `test_the_worker_waits_and_retries_when_the_queue_is_unreachable` |
| Rate limit under a burst | `fake_model.py`, `measure.py` | `make burst`: rate-limit errors and queue depth for two concurrency settings |

## Limits of the teaching build against a production one

- The model is a fake in every automated run, so retry behavior is measured against injected errors, not against a provider's real 429s and timeouts. The Claude adapter and the opt-in live test exist; neither has been run (no key was available).
- Mail sending is a table. A real sender needs the provider's idempotency key, not just our unique constraint.
- One database, one region, no partitioning of `deliveries`. A table that keeps `done` rows forever needs a retention job.
- The webhook secret is a setting. Production needs rotation, with two secrets accepted for an overlap.
- Dead letters store the raw payload. Production needs encryption and an access policy.
- Timings in the README were taken on a machine under heavy load; read the ratios and the pass/fail properties, not the absolute numbers.

## How to extend it

- A second event type: a new payload shape in `domain/events.py`, a new extractor port implementation, the same handler.
- A real broker: implement `DeliveryQueue` over the broker client; the handler and the worker do not change, but lease expiry becomes the broker's visibility timeout.
- Per-tenant fairness: add a `tenant` column and claim round-robin; today one noisy sender can fill the queue.
- The Java twin on Spring AI (the lesson asks for both languages) is not built here.
