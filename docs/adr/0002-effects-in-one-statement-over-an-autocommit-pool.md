# 2. The effects are one statement, on an autocommit pool

Status: accepted, 2026-10-27

## Context

An event's effects are three rows: the processed mark, the ticket and the outbox row. They must commit together, and a twin delivery must not produce a second set. Database round trips were slow on the test machine (about 180 ms each with explicit transactions).

## Decision

`PostgresEffects.apply` is a single statement with data-modifying CTEs: insert the mark with `ON CONFLICT DO NOTHING RETURNING`, then insert the ticket and the outbox row by selecting from what the first insert returned. One statement is one transaction and one round trip. If a twin committed first, the mark insert returns no row and the other two insert nothing; the statement reports that the event was already done. The connection pool is in autocommit mode, so multi-statement work (dead-lettering, redrive, bulk loading) states its transaction explicitly with `connection.transaction()`. The "was it processed" check is a fresh read every time and is only an optimization; the primary key is the guarantee.

## Alternatives considered

- **A transaction with three inserts:** correct, three more round trips per event.
- **Check then insert without a constraint:** has a gap between the check and the write that two workers can both pass.

## Consequences

- Median handling time per event fell to about 52 ms on the loaded test machine.
- The SQL needs the comment it has; a reader who expects three inserts needs to know why it is one.
- Any new multi-statement write must open a transaction, or it is not atomic. A bug of that kind was found and fixed in `dead_letter` and `redrive` while writing these notes.
