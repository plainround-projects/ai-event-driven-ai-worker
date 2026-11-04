# ai-event-driven-ai-worker

A worker for the support inbox. Each "email received" event, arriving through a signed webhook or straight from a queue, runs the support-email extractor, writes a ticket row and an acknowledgment to an outbox in one transaction, and a relay sends the acknowledgment through a fake mail sender that records every send. The queue is a PostgreSQL table read with row locks. The worker applies each event's effects once however often the queue delivers it, retries with jittered backoff, parks poison events in a dead-letter table with a reason, survives a kill at any point, and reports its throughput under a burst.

Never used these tools before? [tech/README.md](tech/README.md) teaches each technology in this repository from zero, through its own files, with a ten-minute shortlist.

| | |
| --- | --- |
| **Lesson** | `/prep/ai/project-event-driven-ai-worker`, "An event-driven worker that survives crashes and duplicates" (`data-structure-explainer/src/content/tracks/ai/111-project-event-driven-ai-worker.md` in the Plainround app) |
| **Planned hours** | 10 |
| **Level** | Intermediate |
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md), decisions: [docs/adr](docs/adr) |

**What the offline run is.** No model key was available to the build, so the model is a fake with a configurable delay, error rate and rate limit (`FakeModel`, a token bucket that raises a retryable error over its limit), and the 20-email "real-model smoke run" replays an authored cassette. The queue, the transactions, the retries, the crash recovery and the measurements are real; the model's answers and its limits are not. The Claude adapter, `make record` and the live test exist and have not been run. **All timings were taken on a machine under heavy load (load average 50 to 90, a Docker disk too slow to finish a crash recovery in minutes), so read the properties (nothing lost, nothing doubled) and the ratios, not the absolute numbers.**

## Architecture

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/architecture-dark.svg">
  <img alt="A sender posts a signed event to the Webhook, which verifies the signature and inserts a row in the deliveries table of PostgreSQL. The Worker claims rows for the Handler, which reads and writes the effects store and dead_letters, calls the Extractor and its ChatModel adapters, and acknowledges. The Outbox relay sends through a fake mail sender." src="docs/diagrams/architecture.svg">
</picture>

The queue is a table in the same database as the effects, so one statement can write the mark, the ticket and the outbox row while the model call stays outside it.

## How one run flows

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/diagrams/flow-dark.svg">
  <img alt="One email event through ten rows: verify and enqueue, claim, decode, dedupe, call the model, write the effects in one statement, acknowledge, and relay the mail, with warning rows for a twin delivery and a crash before the acknowledgment." src="docs/diagrams/flow.svg">
</picture>

An event is applied once however often it is delivered, and the amber rows show a twin skipped before the model and a crash absorbed by the processed mark.

## Prerequisites

| Tool | Version | Used for |
| --- | --- | --- |
| Python | 3.12 or 3.13 (tested with 3.13.12; CI uses 3.13) | the webhook, the worker, the measurements |
| GNU Make | 3.81 or newer | every command below |
| Docker | 24 or newer, with Compose | PostgreSQL 16 (`make up`); the image (`make docker-build`; pending capacity: run it, it was not built during this work because Docker's storage failed on the build machine) |
| Python packages | `psycopg` (binary), `psycopg_pool`, `fastapi`, `uvicorn`, `httpx` and `anthropic` 2.3 or newer at run time; pytest, pytest-cov, ruff, mypy, import-linter, pip-audit for development. Hash-pinned in `requirements.lock` and `requirements-dev.lock`; `make` installs them into `.venv/` | everything |
| uv | optional, only for `make lock` | regenerating the lock files |

No cloud account, no API key. PostgreSQL runs in a container on `localhost:5434`; its compose file turns `fsync` off because the database is a local teaching database (do not copy that into a real deployment).

## Setup, run, test, stop

```bash
make up              # .env, .venv from the lock file, PostgreSQL in a container, the schema and seed applied
make run             # queue the 1,000-event inbox, process it, replay it, send acknowledgments, show the counts and the SQL report
make webhook-demo    # a valid, a tampered and a replayed request against the signature check
make bench-webhook   # 500 signed requests through a real HTTP server: p50 and p95, then a tampered and a replayed one
make crash-test      # kill the worker process after the model call and after the commit, restart it, compare event ids
make burst           # 500 events in ten seconds at two concurrency limits against a rate-limited fake model
make smoke           # 20 emails through the recorded model (SMOKE_ADAPTER=claude uses the real one)
make redrive DEAD_ID=3  # put dead letter 3 back on the queue after the cause is fixed
make test            # unit tests with coverage (the domain and application stay at 95% or more)
make test-integration  # the adapters against the running PostgreSQL
make test-e2e        # the lesson's scenarios through the command-line programs
make lint            # ruff check, ruff format check, mypy (strict), import-linter
make audit           # known-vulnerability check of the locked dependencies
make down            # stop and remove the container and its data
```

`make help` lists every target. `make worker` and `make relay` process what is queued and exit. As services, run `.venv/bin/inbox-worker worker` and `.venv/bin/inbox-worker relay` without their one-shot flags: they run until SIGTERM or SIGINT, finishing the work in flight first. `make serve-webhook` starts the HTTP endpoint on `WEBHOOK_PORT` (8090). The webhook secret is a setting; the committed `.env.example` value is a placeholder for local use.

## The data

| Item | What it is |
| --- | --- |
| Generated events | `generate_events()` (seeded) produces 1,000 email events with unique ids, 20 of them delivered twice (2%) and 10 poison (1%): malformed JSON, a 300 KB email, and a body that is not valid UTF-8. `make run` queues 1,020 deliveries. |
| [sql/001_schema.sql](sql/001_schema.sql) | DDL: `deliveries` (the queue; `event_id` is not unique), `processed_events` (the primary key that settles a race), `tickets`, `outbox`, `sent_mail` (unique event id), `dead_letters`. |
| [sql/002_seed.sql](sql/002_seed.sql) | Minimal reference data. |
| [sql/003_queries.sql](sql/003_queries.sql) | Queue depth, processed vs tickets vs outbox vs mails (must be equal), events with two tickets (must be empty), lost events (must be empty), deliveries per event, dead letters by reason, event-to-ticket time. |
| [sql/reset.sql](sql/reset.sql) | Empties every table. |
| [prompts/extract.v1.md](prompts/extract.v1.md) | The extractor's versioned prompt; [prompts/CHANGELOG.md](prompts/CHANGELOG.md). |
| [tests/fixtures/cassettes/smoke-v1.json](tests/fixtures/cassettes/smoke-v1.json) | Twenty replies keyed by a hash of the whole request, authored from the fake model and labeled so in its `provenance` field. |

## Done when: the lesson's checklist and the proof for each line

| # | Done when (from the lesson) | Command | What proves it |
| --- | --- | --- | --- |
| 1 | A tampered body and a replayed old request both get a 401, and the endpoint's p95 stays under 100 ms because the model is nowhere on its path. | `make webhook-demo`, `make bench-webhook` | `tampered body -> 401 signature mismatch` and `replayed old request -> 401 request too old` (two different reasons, constant-time compare, the timestamp is signed with the body). The model is not imported by the webhook module. **The 100 ms bar was not met on this machine**: p95 was 246.5 ms in one run and 146.0 ms in the next (p50 54.5 and 24.4 ms, 500 requests each, load average 40 to 90), so the property that matters, that the model is not on the path, holds, but the number does not. Pending capacity: rerun `make bench-webhook` when `uptime` shows a load under 30 for clean figures. The command exits non-zero when the bar is missed (`WEBHOOK_P95_BUDGET_MS` changes it); the measured cost is one database insert per request, which the load turned into tens of milliseconds. |
| 2 | Replaying all 1,000 events a second time creates no new ticket and no second acknowledgment, checked by the counts in the ticket table and the fake sender. | `make run` | First pass over the 1,020 deliveries: `processed 990, dead_lettered 10, duplicate 20` (the 20 twins delivered inside the first pass are already skipped). The replay pass: `outcomes: duplicate 1010, dead_lettered 10` and no new ticket. Final counts from the SQL report: processed 990, tickets 990, outbox rows 990, mails sent 990, events with two tickets: none, lost events: none. The relay ran once after the replay, so the fake sender holds one send per ticket. Event-to-ticket time is long (median 73 s, p95 113 s) because all 1,020 deliveries were queued at once on a loaded machine and the worker drains them at its own pace. |
| 3 | With the fake model failing 30% of calls with a retryable error, every event still completes, and the retry log shows growing, jittered delays. | `make test-integration`, unit tests | `test_a_rate_limited_event_is_retried_later_and_a_permanent_failure_is_parked_after_one_attempt` (integration) and the handler tests with an injected random generator: delays are `uniform(0, min(cap, base * 2**attempt))`, grow with the attempt number and are capped; a schema failure after one repair is parked after exactly one attempt. The burst run below also completes every event through rate-limit errors. |
| 4 | Every planted poison event lands in the dead-letter queue with a reason a person can act on, none of them holds up the events behind it, and redriving a fixed one processes it exactly once. | `make run`, `make redrive` | `make run` parks 10 poison events with reasons `event_too_large`, `malformed_event`, `bad_encoding` and `permanent_error`, each with the attempt count, last error and a 12-character payload hash, while 990 healthy events finish. Test: `test_a_redriven_dead_letter_is_processed_exactly_once_through_the_normal_path` (the second redrive returns nothing). |
| 5 | After each restart no event is lost and none has two tickets, checked by comparing the event ids sent with the event ids in the ticket table. | `make crash-test` | The child worker process is killed with exit code 137 (`os._exit`, as a SIGKILL would leave it) at a named point, restarted, and the event ids sent are compared with the event ids in the ticket table as two full sets. After the crash at `after_model` (model called, nothing committed): 6 tickets existed at the crash, the restart processed 24 more, `event ids sent: 30; tickets: 30; distinct events with a ticket: 30`, `lost: []; duplicated tickets: 0`. After the crash at `after_commit` (committed, not acknowledged): 7 tickets at the crash, the restart processed 23 and skipped 1 as `duplicate` (the event that had committed before the kill), again 30 of 30, none lost, none doubled. |
| 6 | (load average 40 to 90 during these runs; rerun for clean figures with `make burst`) A table reports throughput, peak queue depth, p95 event-to-ticket time and rate-limit errors for both settings, and the queue drains fully after each burst. | `make burst` | 500 events arrive over ten seconds against a fake model with a 150 ms delay and a limit of 30 calls a second (a token bucket). Measured:

    | Concurrency | Throughput (events/s) | Peak queue depth | p95 event to ticket (s) | Rate-limit errors | Tickets | Dead letters | Drained |
    | --- | --- | --- | --- | --- | --- | --- | --- |
    | 5 | 10.1 | 380 | 38.75 | 0 | 500 | 0 | True |
    | 20 | 22.5 | 117 | 3.85 | 149 | 500 | 0 | True |

    The queue drained fully in both runs and every event got a ticket. At 5 the worker is the bottleneck: the backlog peaks at 380 and the last event waits 39 s, with no rate-limit error. At 20 the throughput more than doubles and p95 falls ten-fold, but the model's limit now shows: 149 calls were refused as rate-limited and retried with backoff, which is the ceiling the lesson says the errors, not the queue depth, reveal. Absolute rates are low because the loaded machine made each database round trip slow. |

Lines that need a live key: none of the six. What a key adds is the real-model smoke run (`make smoke SMOKE_ADAPTER=claude`, 20 emails) and the opt-in live test; neither has been run. The smoke run here replays the authored cassette: `20/20 emails gave a ticket in 20 model calls (adapter: recorded)`, which shows the recorded path works, not that a model reads the emails.

## Stretch goals

| Stretch | Built? |
| --- | --- |
| A broker instead of a table. | No. ARCHITECTURE.md, ADR 0001. |
| Per-tenant fairness in the claim. | No. |
| The Java twin on Spring AI. | No. |

## What is simplified for teaching

- The model is a fake and the smoke run is a replay of an authored cassette (see the top of this file).
- The queue is a table; the `done` rows are never removed. A real system needs a retention job.
- The fake mail sender is a table. A real sender needs the provider's idempotency key.
- Dead letters store the raw payload; a real system would encrypt or redact it.
- After the replay in `make run`, each poison event is parked again (20 dead-letter rows for 10 distinct events) because each delivery of a poison event is parked on its own.
- Timings come from a heavily loaded machine (see the top of this file).
- The database image is PostgreSQL 16. With PostgreSQL 18 the server restarted itself at least three times during this build, each time right after the log line `untracked child process ... exited with exit code 2` (a feature new in 18) while the machine was starved; 16 did not.

## Project structure

```text
src/inbox_worker/
  domain/            signatures, event decoding with reasons, backoff, statistics, the ticket. Standard library only.
  application/       the handler, the worker loop, the extractor, the outbox relay, event generation, ports.
                     Depends on domain.
  infrastructure/    PostgreSQL queue, effects store, outbox and reports; the fake, recorded and Claude models; prompt
                     file, settings, logging. Depends on application and domain.
  interfaces/        the `inbox-worker` command, the webhook app, the burst and crash-test measurements, the wiring.
                     Nothing depends on it.
sql/                 001_schema, 002_seed, 003_queries, reset.
prompts/             extract.v1.md and its CHANGELOG.
scripts/             smoke.py (replay, author or record the 20-email smoke run).
tests/               unit (domain, application, infrastructure, interfaces), integration (PostgreSQL), e2e (the
                     lesson's scenarios), live (opt-in), fixtures (the cassette).
docs/adr/            decision records.
```

The dependency rule (domain depends on nothing; application on domain; infrastructure and interfaces on both; nothing on interfaces) is enforced by `make lint` through import-linter. A second contract keeps vendor SDKs, web frameworks and database drivers out of domain and application.

## Live key

```bash
export ANTHROPIC_API_KEY=...        # your own key; nothing in this repository stores one
make smoke SMOKE_ADAPTER=claude     # 20 emails through the real model
make record                         # the same, written to tests/fixtures/cassettes/live-v1.json
make test-live                      # one real extraction
```

## Pending verification

- pending capacity: run `make docker-build` after Docker Desktop is restarted with free disk (Docker.raw was at its 60 GiB cap on 2026-10-28).
- pending capacity: run `make bench-webhook` after Docker Desktop is restarted with free disk (Docker.raw was at its 60 GiB cap on 2026-10-28). The webhook p95 figures above were taken at a load average of 40 to 90 (146 to 246 ms): rerun for clean figures.
- pending capacity: run `make burst` after Docker Desktop is restarted with free disk (Docker.raw was at its 60 GiB cap on 2026-10-28). The burst figures above were taken at a load average of 40 to 90: rerun for clean figures.

Everything else in the Done-when table was run and passed, from a fresh clone, on 2026-10-27.

## Author and license

Written by Sumit Srivastava. Released under the MIT License, see [LICENSE](LICENSE). Changes are in [CHANGELOG.md](CHANGELOG.md).
