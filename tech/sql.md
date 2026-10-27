# SQL

## What it is

SQL (Structured Query Language) is the language for talking to relational databases. A *relational database* stores data in *tables*: grids where each row is one record and each column is one kind of value. SQL lets you create tables, add rows, change or delete them, and ask questions (queries) about them.

## Why this repository uses it

The structure and the questions the lesson asks (is anything lost, is anything doubled, what was parked and why) are SQL files, so the database can be rebuilt from nothing and the checks read as plain queries.

## Where it appears

| File | What it does with SQL |
| --- | --- |
| `sql/001_schema.sql` | six tables and their constraints |
| `sql/002_seed.sql` | nothing to seed (`SELECT 1;`) |
| `sql/003_queries.sql` | the counts and the lost/duplicate checks |
| `sql/reset.sql` | `TRUNCATE ... RESTART IDENTITY` |

## How it works underneath

Statements end with `;`. The main ones:

- `CREATE TABLE name (...)` defines a table and its columns, each with a type and rules (*constraints*). `PRIMARY KEY` identifies a row; `NOT NULL` requires a value; `UNIQUE` forbids repeats; `CHECK (...)` rejects rows that break a condition; `REFERENCES other (column)` is a *foreign key*, which forces the value to exist in another table.
- `INSERT INTO t (columns) VALUES (...)` adds rows. `UPDATE` changes rows. `DELETE FROM t WHERE ...` removes rows.
- `SELECT columns FROM t WHERE condition GROUP BY ... ORDER BY ...` reads rows. `WHERE` filters rows; `GROUP BY` groups them so functions like `COUNT(*)` and `SUM(x)` work per group; `ORDER BY` sorts.
- `CREATE INDEX` builds a sorted structure so lookups by some columns are fast. A *unique index* also forbids repeats; a *partial index* (`WHERE ...`) covers only some rows.
- A *transaction* groups statements so they all happen or none do.

The database engine (here SQLite or PostgreSQL) parses the text, plans how to read the data, and does it. The same statements work in both with small differences, which the files point out.

The SQL files here are numbered: `001_schema.sql` (the structure), `002_seed.sql` (starting data), `003_queries.sql` (the questions the lesson asks), and `reset.sql` (empties the data). `make db` runs the first two in order on an empty database, so the structure is always rebuilt from the files, never edited by hand.

## Walkthrough of this repository's use

### `sql/001_schema.sql`

```sql
-- DDL for the inbox worker (PostgreSQL 16). `make db` applies this file and 002_seed.sql in order.
-- The queue. A webhook retry or a redelivery can put the same event id here twice, so event_id is NOT unique:
-- the guard against applying an event twice is processed_events, below, not this table.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: DDL for the inbox worker (PostgreSQL 16). `make db` applies this file and 002_seed.sql in order. The queue. A webhook retry or a redelivery can put the same event id here twice, so event_id is NOT unique: the guard against applying an event twice is processed_events, below, not this table.

```sql
CREATE TABLE deliveries (
    delivery_id  BIGSERIAL PRIMARY KEY,
    event_id     TEXT NOT NULL,
    payload      TEXT NOT NULL,                       -- the event as received, text
    received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    status       TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'done', 'dead')),
    attempts     INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    available_at TIMESTAMPTZ NOT NULL DEFAULT now(),  -- not before this time (backoff)
    locked_until TIMESTAMPTZ,                         -- a claim lasts this long; after it, another worker may take the row
    last_error   TEXT
);
```

- `CREATE TABLE deliveries (`: creates a table named `deliveries`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `delivery_id  BIGSERIAL PRIMARY KEY,`: A column `delivery_id`, a whole number that PostgreSQL fills in automatically with the next number (1, 2, 3, ...); it is the primary key: the value that identifies a row, unique and never empty.
- `event_id     TEXT NOT NULL,`: A column `event_id`, text (any length of characters); `NOT NULL` means a value is required.
- `payload      TEXT NOT NULL,                       -- the event as received, text`: A column `payload`, text (any length of characters); `NOT NULL` means a value is required. The comment says: the event as received, text
- `received_at  TIMESTAMPTZ NOT NULL DEFAULT now(),`: A column `received_at`, a date and time together with a time zone; `NOT NULL` means a value is required; `DEFAULT now()` is used when an insert gives no value.
- `status       TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'done', 'dead')),`: A column `status`, text (any length of characters); `NOT NULL` means a value is required; `DEFAULT 'queued'` is used when an insert gives no value; `CHECK`: `status` must be one of the listed values: 'queued', 'processing', 'done', 'dead'.
- `attempts     INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),`: A column `attempts`, a whole number; `NOT NULL` means a value is required; `DEFAULT 0` is used when an insert gives no value; `CHECK`: `attempts` must not be negative.
- `available_at TIMESTAMPTZ NOT NULL DEFAULT now(),  -- not before this time (backoff)`: A column `available_at`, a date and time together with a time zone; `NOT NULL` means a value is required; `DEFAULT now()` is used when an insert gives no value. The comment says: not before this time (backoff)
- `locked_until TIMESTAMPTZ,                         -- a claim lasts this long; after it, another worker may take the row`: A column `locked_until`, a date and time together with a time zone. The comment says: a claim lasts this long; after it, another worker may take the row
- `last_error   TEXT`: A column `last_error`, text (any length of characters).
- `);`: ends the column list and the statement.

```sql
-- The claim query reads only rows that are ready.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: The claim query reads only rows that are ready.

```sql
CREATE INDEX deliveries_ready ON deliveries (available_at, delivery_id) WHERE status IN ('queued', 'processing');
```

Creates an index named `deliveries_ready` on table `deliveries` over (available_at, delivery_id). An index is a sorted side-structure the database keeps so it can find rows by these columns without reading the whole table. `WHERE status IN ('queued', 'processing')` makes it a partial index: only rows for which that is true are indexed and (for a unique index) compared.

```sql
CREATE INDEX deliveries_by_event ON deliveries (event_id);
```

Creates an index named `deliveries_by_event` on table `deliveries` over (event_id). An index is a sorted side-structure the database keeps so it can find rows by these columns without reading the whole table.

```sql
-- One row per event whose effects were applied. Its primary key settles a race between two deliveries of one event.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: One row per event whose effects were applied. Its primary key settles a race between two deliveries of one event.

```sql
CREATE TABLE processed_events (
    event_id     TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- `CREATE TABLE processed_events (`: creates a table named `processed_events`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `event_id     TEXT PRIMARY KEY,`: A column `event_id`, text (any length of characters); it is the primary key: the value that identifies a row, unique and never empty.
- `processed_at TIMESTAMPTZ NOT NULL DEFAULT now()`: A column `processed_at`, a date and time together with a time zone; `NOT NULL` means a value is required; `DEFAULT now()` is used when an insert gives no value.
- `);`: ends the column list and the statement.

```sql
CREATE TABLE tickets (
    ticket_id        BIGSERIAL PRIMARY KEY,
    event_id         TEXT NOT NULL UNIQUE REFERENCES processed_events (event_id),
    intent           TEXT NOT NULL,
    order_number     TEXT,
    sentiment        TEXT NOT NULL,
    requested_action TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- `CREATE TABLE tickets (`: creates a table named `tickets`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `ticket_id        BIGSERIAL PRIMARY KEY,`: A column `ticket_id`, a whole number that PostgreSQL fills in automatically with the next number (1, 2, 3, ...); it is the primary key: the value that identifies a row, unique and never empty.
- `event_id         TEXT NOT NULL UNIQUE REFERENCES processed_events (event_id),`: A column `event_id`, text (any length of characters); `NOT NULL` means a value is required; a foreign key: every value must exist in `processed_events.event_id`; `UNIQUE`: no two rows may have the same value.
- `intent           TEXT NOT NULL,`: A column `intent`, text (any length of characters); `NOT NULL` means a value is required.
- `order_number     TEXT,`: A column `order_number`, text (any length of characters).
- `sentiment        TEXT NOT NULL,`: A column `sentiment`, text (any length of characters); `NOT NULL` means a value is required.
- `requested_action TEXT NOT NULL,`: A column `requested_action`, text (any length of characters); `NOT NULL` means a value is required.
- `created_at       TIMESTAMPTZ NOT NULL DEFAULT now()`: A column `created_at`, a date and time together with a time zone; `NOT NULL` means a value is required; `DEFAULT now()` is used when an insert gives no value.
- `);`: ends the column list and the statement.

```sql
-- The acknowledgment to send, written in the same transaction as the ticket; a relay sends it afterwards.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: The acknowledgment to send, written in the same transaction as the ticket; a relay sends it afterwards.

```sql
CREATE TABLE outbox (
    outbox_id  BIGSERIAL PRIMARY KEY,
    event_id   TEXT NOT NULL UNIQUE REFERENCES processed_events (event_id),
    kind       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at    TIMESTAMPTZ
);
```

- `CREATE TABLE outbox (`: creates a table named `outbox`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `outbox_id  BIGSERIAL PRIMARY KEY,`: A column `outbox_id`, a whole number that PostgreSQL fills in automatically with the next number (1, 2, 3, ...); it is the primary key: the value that identifies a row, unique and never empty.
- `event_id   TEXT NOT NULL UNIQUE REFERENCES processed_events (event_id),`: A column `event_id`, text (any length of characters); `NOT NULL` means a value is required; a foreign key: every value must exist in `processed_events.event_id`; `UNIQUE`: no two rows may have the same value.
- `kind       TEXT NOT NULL,`: A column `kind`, text (any length of characters); `NOT NULL` means a value is required.
- `created_at TIMESTAMPTZ NOT NULL DEFAULT now(),`: A column `created_at`, a date and time together with a time zone; `NOT NULL` means a value is required; `DEFAULT now()` is used when an insert gives no value.
- `sent_at    TIMESTAMPTZ`: A column `sent_at`, a date and time together with a time zone.
- `);`: ends the column list and the statement.

```sql
CREATE INDEX outbox_unsent ON outbox (outbox_id) WHERE sent_at IS NULL;
```

Creates an index named `outbox_unsent` on table `outbox` over (outbox_id). An index is a sorted side-structure the database keeps so it can find rows by these columns without reading the whole table. `WHERE sent_at IS NULL` makes it a partial index: only rows for which that is true are indexed and (for a unique index) compared.

```sql
-- The fake mail sender's record of every send. The unique event id means a second send of one acknowledgment fails.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: The fake mail sender's record of every send. The unique event id means a second send of one acknowledgment fails.

```sql
CREATE TABLE sent_mail (
    send_id  BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    kind     TEXT NOT NULL,
    sent_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- `CREATE TABLE sent_mail (`: creates a table named `sent_mail`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `send_id  BIGSERIAL PRIMARY KEY,`: A column `send_id`, a whole number that PostgreSQL fills in automatically with the next number (1, 2, 3, ...); it is the primary key: the value that identifies a row, unique and never empty.
- `event_id TEXT NOT NULL UNIQUE,`: A column `event_id`, text (any length of characters); `NOT NULL` means a value is required; `UNIQUE`: no two rows may have the same value.
- `kind     TEXT NOT NULL,`: A column `kind`, text (any length of characters); `NOT NULL` means a value is required.
- `sent_at  TIMESTAMPTZ NOT NULL DEFAULT now()`: A column `sent_at`, a date and time together with a time zone; `NOT NULL` means a value is required; `DEFAULT now()` is used when an insert gives no value.
- `);`: ends the column list and the statement.

```sql
-- Events that can never succeed, with what a person needs to act: reason, attempts, last error and a payload hash.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Events that can never succeed, with what a person needs to act: reason, attempts, last error and a payload hash.

```sql
CREATE TABLE dead_letters (
    dead_id      BIGSERIAL PRIMARY KEY,
    event_id     TEXT NOT NULL,
    reason       TEXT NOT NULL CHECK (reason IN ('malformed_event', 'event_too_large', 'bad_encoding', 'permanent_error', 'attempts_exhausted', 'deadline_exceeded')),
    attempts     INTEGER NOT NULL,
    last_error   TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    payload      TEXT NOT NULL,
    dead_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    redriven_at  TIMESTAMPTZ
);
```

- `CREATE TABLE dead_letters (`: creates a table named `dead_letters`: a grid in which every row is one record and every column one named kind of value. The columns are listed in the lines below.
- `dead_id      BIGSERIAL PRIMARY KEY,`: A column `dead_id`, a whole number that PostgreSQL fills in automatically with the next number (1, 2, 3, ...); it is the primary key: the value that identifies a row, unique and never empty.
- `event_id     TEXT NOT NULL,`: A column `event_id`, text (any length of characters); `NOT NULL` means a value is required.
- `reason       TEXT NOT NULL CHECK (reason IN ('malformed_event', 'event_too_large', 'bad_encoding', 'permanent_error', 'attempts_exhausted', 'deadline_exceeded')),`: A column `reason`, text (any length of characters); `NOT NULL` means a value is required; `CHECK`: `reason` must be one of the listed values: 'malformed_event', 'event_too_large', 'bad_encoding', 'permanent_error', 'attempts_exhausted', 'deadline_exceeded'.
- `attempts     INTEGER NOT NULL,`: A column `attempts`, a whole number; `NOT NULL` means a value is required.
- `last_error   TEXT NOT NULL,`: A column `last_error`, text (any length of characters); `NOT NULL` means a value is required.
- `payload_hash TEXT NOT NULL,`: A column `payload_hash`, text (any length of characters); `NOT NULL` means a value is required.
- `payload      TEXT NOT NULL,`: A column `payload`, text (any length of characters); `NOT NULL` means a value is required.
- `dead_at      TIMESTAMPTZ NOT NULL DEFAULT now(),`: A column `dead_at`, a date and time together with a time zone; `NOT NULL` means a value is required; `DEFAULT now()` is used when an insert gives no value.
- `redriven_at  TIMESTAMPTZ`: A column `redriven_at`, a date and time together with a time zone.
- `);`: ends the column list and the statement.

```sql
CREATE INDEX dead_letters_open ON dead_letters (dead_id) WHERE redriven_at IS NULL;
```

Creates an index named `dead_letters_open` on table `dead_letters` over (dead_id). An index is a sorted side-structure the database keeps so it can find rows by these columns without reading the whole table. `WHERE redriven_at IS NULL` makes it a partial index: only rows for which that is true are indexed and (for a unique index) compared.

### `sql/002_seed.sql`

```sql
-- DML: nothing to seed. The inbox starts empty; `inbox-worker generate-events` writes the 1,000 sample events and
-- `inbox-worker enqueue` loads them. This file exists so `make db` has the two numbered scripts every repository has.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: DML: nothing to seed. The inbox starts empty; `inbox-worker generate-events` writes the 1,000 sample events and `inbox-worker enqueue` loads them. This file exists so `make db` has the two numbered scripts every repository has.

```sql
SELECT 1;
```

- `SELECT` names the columns or calculations to return: `1`

### `sql/003_queries.sql`

```sql
-- The queries the lesson's steps run. Each statement is preceded by a one-line comment.
-- Queue depth by status
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: The queries the lesson's steps run. Each statement is preceded by a one-line comment. Queue depth by status

```sql
SELECT status, COUNT(*) AS deliveries FROM deliveries GROUP BY status ORDER BY status;
```

- `SELECT` names the columns or calculations to return: `status, COUNT(*) AS deliveries`
- `FROM` names the table (or the subquery) to read from: `deliveries`
- `GROUP BY` makes one output row per distinct combination of these columns, so aggregate functions count or add within each group: `status`
- `ORDER BY` sorts the result (`DESC` means largest first): `status`
- Terms used: `COUNT(*)` counts rows.

```sql
-- Events whose effects were applied, and the tickets and acknowledgments they produced (all three must be equal)
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Events whose effects were applied, and the tickets and acknowledgments they produced (all three must be equal)

```sql
SELECT (SELECT COUNT(*) FROM processed_events) AS processed, (SELECT COUNT(*) FROM tickets) AS tickets, (SELECT COUNT(*) FROM outbox) AS outbox_rows, (SELECT COUNT(*) FROM sent_mail) AS mails_sent;
```

- `SELECT` names the columns or calculations to return: `(SELECT COUNT(*) FROM processed_events) AS processed, (SELECT COUNT(*) FROM tickets) AS tickets, (SELECT COUNT(*) FROM outbox) AS outbox_rows, (SELECT COUNT(*) FROM sent_mail) AS mails_sent`
- Terms used: `COUNT(*)` counts rows.
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT COUNT(*) FROM processed_events`. It means:
  - `SELECT` names the columns or calculations to return: `COUNT(*)`
  - `FROM` names the table (or the subquery) to read from: `processed_events`
  - Terms used: `COUNT(*)` counts rows.
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT COUNT(*) FROM tickets`. It means:
  - `SELECT` names the columns or calculations to return: `COUNT(*)`
  - `FROM` names the table (or the subquery) to read from: `tickets`
  - Terms used: `COUNT(*)` counts rows.
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT COUNT(*) FROM outbox`. It means:
  - `SELECT` names the columns or calculations to return: `COUNT(*)`
  - `FROM` names the table (or the subquery) to read from: `outbox`
  - Terms used: `COUNT(*)` counts rows.
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT COUNT(*) FROM sent_mail`. It means:
  - `SELECT` names the columns or calculations to return: `COUNT(*)`
  - `FROM` names the table (or the subquery) to read from: `sent_mail`
  - Terms used: `COUNT(*)` counts rows.

```sql
-- Events with more than one ticket (must be empty)
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Events with more than one ticket (must be empty)

```sql
SELECT event_id, COUNT(*) AS tickets FROM tickets GROUP BY event_id HAVING COUNT(*) > 1;
```

- `SELECT` names the columns or calculations to return: `event_id, COUNT(*) AS tickets`
- `FROM` names the table (or the subquery) to read from: `tickets`
- `GROUP BY` makes one output row per distinct combination of these columns, so aggregate functions count or add within each group: `event_id`
- `HAVING` keeps only the groups for which this is true: `COUNT(*) > 1`
- Terms used: `COUNT(*)` counts rows; `HAVING` filters groups after they are formed (`WHERE` filters rows before).

```sql
-- Event ids that were delivered but have no ticket and are not dead-lettered (lost events; must be empty at the end of a run)
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Event ids that were delivered but have no ticket and are not dead-lettered (lost events; must be empty at the end of a run)

```sql
SELECT DISTINCT d.event_id FROM deliveries d WHERE NOT EXISTS (SELECT 1 FROM tickets t WHERE t.event_id = d.event_id) AND NOT EXISTS (SELECT 1 FROM dead_letters x WHERE x.event_id = d.event_id) ORDER BY d.event_id;
```

- `SELECT DISTINCT` returns the columns or calculations below, with duplicate rows removed: `d.event_id`
- `FROM` names the table (or the subquery) to read from: `deliveries d`
- `WHERE` keeps only the rows for which this is true: `NOT EXISTS (SELECT 1 FROM tickets t WHERE t.event_id = d.event_id) AND NOT EXISTS (SELECT 1 FROM dead_letters x WHERE x.event_id = d.event_id)`
- `ORDER BY` sorts the result (`DESC` means largest first): `d.event_id`
- Terms used: `NOT EXISTS (subquery)` is true when the subquery finds no row; `DISTINCT` removes duplicate rows.
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT 1 FROM tickets t WHERE t.event_id = d.event_id`. It means:
  - `SELECT` names the columns or calculations to return: `1`
  - `FROM` names the table (or the subquery) to read from: `tickets t`
  - `WHERE` keeps only the rows for which this is true: `t.event_id = d.event_id`
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT 1 FROM dead_letters x WHERE x.event_id = d.event_id`. It means:
  - `SELECT` names the columns or calculations to return: `1`
  - `FROM` names the table (or the subquery) to read from: `dead_letters x`
  - `WHERE` keeps only the rows for which this is true: `x.event_id = d.event_id`

```sql
-- How many events arrived once, twice or more (after the replay every event has at least two deliveries)
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: How many events arrived once, twice or more (after the replay every event has at least two deliveries)

```sql
SELECT deliveries, COUNT(*) AS events FROM (SELECT event_id, COUNT(*) AS deliveries FROM deliveries GROUP BY event_id) per_event GROUP BY deliveries ORDER BY deliveries;
```

- `SELECT` names the columns or calculations to return: `deliveries, COUNT(*) AS events`
- `FROM` names the table (or the subquery) to read from: `(SELECT event_id, COUNT(*) AS deliveries FROM deliveries GROUP BY event_id) per_event`
- `GROUP BY` makes one output row per distinct combination of these columns, so aggregate functions count or add within each group: `deliveries`
- `ORDER BY` sorts the result (`DESC` means largest first): `deliveries`
- Terms used: `COUNT(*)` counts rows.
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT event_id, COUNT(*) AS deliveries FROM deliveries GROUP BY event_id`. It means:
  - `SELECT` names the columns or calculations to return: `event_id, COUNT(*) AS deliveries`
  - `FROM` names the table (or the subquery) to read from: `deliveries`
  - `GROUP BY` makes one output row per distinct combination of these columns, so aggregate functions count or add within each group: `event_id`
  - Terms used: `COUNT(*)` counts rows.

```sql
-- Dead letters by reason
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Dead letters by reason

```sql
SELECT reason, COUNT(*) AS events, MAX(attempts) AS most_attempts FROM dead_letters GROUP BY reason ORDER BY reason;
```

- `SELECT` names the columns or calculations to return: `reason, COUNT(*) AS events, MAX(attempts) AS most_attempts`
- `FROM` names the table (or the subquery) to read from: `dead_letters`
- `GROUP BY` makes one output row per distinct combination of these columns, so aggregate functions count or add within each group: `reason`
- `ORDER BY` sorts the result (`DESC` means largest first): `reason`
- Terms used: `COUNT(*)` counts rows; `MAX(x)` is the largest value.

```sql
-- Event to ticket time: median and 95th percentile in seconds
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Event to ticket time: median and 95th percentile in seconds

```sql
SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM t.created_at - d.received_at)) AS p50_seconds, percentile_cont(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM t.created_at - d.received_at)) AS p95_seconds FROM tickets t JOIN LATERAL (SELECT MIN(received_at) AS received_at FROM deliveries WHERE event_id = t.event_id) d ON true;
```

- `SELECT` names the columns or calculations to return: `percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM t.created_at - d.received_at)) AS p50_seconds, percentile_cont(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM t.created_at - d.received_at)) AS p95_seconds`
- `FROM` names the table (or the subquery) to read from: `tickets t`
- `JOIN LATERAL` adds the result of a subquery that may use columns of the row on its left: `(SELECT MIN(received_at) AS received_at FROM deliveries WHERE event_id = t.event_id) d`
- `ON` is the condition that pairs the rows of the two tables: `true`
- Terms used: `MIN(x)` is the smallest value; `percentile_cont(0.5) WITHIN GROUP (ORDER BY x)` is the median of x (0.95 would be the 95th percentile); `EXTRACT(EPOCH FROM interval)` turns a time difference into seconds; `JOIN` combines rows of two tables where the `ON` condition holds; `JOIN LATERAL` lets the joined subquery use columns of the row on its left.
- A subquery (a query inside parentheses that produces a value or a table for the outer query): `SELECT MIN(received_at) AS received_at FROM deliveries WHERE event_id = t.event_id`. It means:
  - `SELECT` names the columns or calculations to return: `MIN(received_at) AS received_at`
  - `FROM` names the table (or the subquery) to read from: `deliveries`
  - `WHERE` keeps only the rows for which this is true: `event_id = t.event_id`
  - Terms used: `MIN(x)` is the smallest value.

### `sql/reset.sql`

```sql
-- Empty every table and restart the id counters. Run by `make reset` and by the tests.
```

Comment lines (SQL comments start with `--`; the database ignores them). They say: Empty every table and restart the id counters. Run by `make reset` and by the tests.

```sql
TRUNCATE sent_mail, outbox, tickets, processed_events, dead_letters, deliveries RESTART IDENTITY;
```

`TRUNCATE a, b, ...` empties the listed tables in one fast step (PostgreSQL). `RESTART IDENTITY` also resets their automatic id counters to 1.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make db
```

Prints `applied 001_schema.sql, 002_seed.sql`.

```bash
make queries
```

Prints each query's result.

```bash
make reset
```

Prints `tables emptied`.

## Mistakes people make

- Building SQL by joining strings with user input. That allows *SQL injection*. The code passes values as parameters (`?` or `%s`), and the database never treats them as SQL.
- Storing money as floating-point. Amounts here are text or exact decimals and are converted when compared.
- Relying on application code alone to keep data valid. The `CHECK`, `UNIQUE` and foreign-key rules make the database refuse bad rows even if the code has a bug.
- Forgetting an index for a column that is searched often.
- Running `DELETE` without `WHERE` by accident. The only unconditional deletes are in the reset scripts.

## Check yourself

1. What is a primary key?
   *Answer:* The column (or columns) whose value identifies each row; it is unique and never empty.
2. What does a foreign key do?
   *Answer:* Forces a value to exist in another table's column.
3. What does `GROUP BY status` with `COUNT(*)` give?
   *Answer:* One row per distinct status, with the number of rows in each.
4. What is an index for?
   *Answer:* To find rows by some columns quickly without reading the whole table.
5. Why pass values as parameters instead of building SQL text?
   *Answer:* To prevent SQL injection: values are never interpreted as SQL.

## Further reading

- [SQLite SQL language reference](https://www.sqlite.org/lang.html)
- [PostgreSQL 16 SQL commands](https://www.postgresql.org/docs/16/sql-commands.html)
