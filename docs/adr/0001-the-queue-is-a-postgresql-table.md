# 1. The queue is a PostgreSQL table read with row locks

Status: accepted, 2026-10-27

## Context

The worker needs acknowledgments and redelivery. The lesson allows any queue that has both; "a database table read with row locks is enough".

## Decision

Deliveries are rows in `deliveries`. A worker claims rows with `SELECT ... FOR UPDATE SKIP LOCKED` inside an `UPDATE ... RETURNING`, setting `status = 'processing'`, `attempts + 1` and `locked_until = now() + lease`. A claim whose lease has expired is claimable again; that is the only redelivery mechanism. A retry sets `available_at` to a later time. `event_id` is not unique in this table, because a webhook retry or a second delivery of one event is normal; the guard against applying an event twice is the primary key of `processed_events`.

## Alternatives considered

- **A broker (RabbitMQ, SQS, Kafka):** more realistic fan-out and retention, but one more service to run and a second system to reason about when the effects and the queue must agree.
- **An in-memory queue:** loses events on a crash, which is the property the project exists to test.

## Consequences

- The claim, the effects and the acknowledgment share one database and ordinary transactions.
- Throughput is bounded by the database and the table grows until a retention job removes `done` rows (not built).
- A handler that outlives its lease can run twice; safe because of the processed mark (ADR 0002).
- The image is PostgreSQL 16. 18 restarted itself at least three times under this build machine's load (the log showed `untracked child process ... exited with exit code 2` followed by crash recovery); the schema uses nothing newer than 16, so nothing is lost by the choice.
