# PostgreSQL

## What it is

PostgreSQL ("Postgres") is a full database *server*: a program that runs all the time, listens on a network port (here 5434 on your machine, 5432 inside its container), and serves many connections at once. This repository runs it in a Docker container and uses it as the queue and the store for tickets.

## Why this repository uses it

The queue is a table in PostgreSQL. Putting the queue, the processed-event marks, the tickets and the outbox in one database means one transaction can cover the effects, and `FOR UPDATE SKIP LOCKED` lets several workers share the queue safely.

## Where it appears

| File | What it does with PostgreSQL |
| --- | --- |
| `docker-compose.yml` | starts PostgreSQL 16 in a container |
| `sql/*.sql` | the schema and the report queries |
| `src/inbox_worker/infrastructure/postgres.py` | the claim and the effects statements |

## How it works underneath

A client connects with a *connection string* (host, port, user, password, database name) and sends SQL. Each connection is served by its own server process. Postgres keeps old row versions so readers and writers do not block each other (MVCC), and a *transaction* makes a group of statements atomic: all become visible together on `COMMIT`, or none do.

Three features carry this repository:

- `SELECT ... FOR UPDATE SKIP LOCKED` locks the rows it returns and skips rows already locked by another connection. Several workers can ask for work at the same moment and each gets different rows. This is how a table behaves like a queue.
- `INSERT ... ON CONFLICT DO NOTHING` inserts unless a unique value already exists; combined with a primary key, it settles races between two workers.
- A single statement made of *CTEs* (`WITH name AS (...)`) can contain several `INSERT`s that happen together in one transaction.

`fsync` makes the server force each commit to disk. The compose file turns it off for this local teaching database so a restart on a busy machine does not stall; never do that for real data.

## Walkthrough of this repository's use

The claim query, in `PostgresQueue.claim`, is the heart of the queue. It is one SQL statement:

```sql
WITH ready AS (
    SELECT delivery_id FROM deliveries
    WHERE (status = 'queued' AND available_at <= now()) OR (status = 'processing' AND locked_until < now())
    ORDER BY available_at, delivery_id
    LIMIT %s FOR UPDATE SKIP LOCKED)
UPDATE deliveries d SET status = 'processing', attempts = d.attempts + 1,
       locked_until = now() + make_interval(secs => %s)
FROM ready WHERE d.delivery_id = ready.delivery_id
RETURNING d.delivery_id, d.event_id, d.payload, d.received_at, d.attempts
```

- `WITH ready AS (...)` defines a named temporary result, a *common table expression* (CTE): the rows to claim.
- `SELECT delivery_id FROM deliveries WHERE (status = 'queued' AND available_at <= now()) OR (status = 'processing' AND locked_until < now())`: a delivery is ready if it is queued and its retry time has come, **or** it is marked processing but its lease has run out. The second half is the redelivery: if a worker died, its claim expires and the row is claimable again. `now()` is the database server's current time.
- `ORDER BY available_at, delivery_id`: oldest first, for fairness.
- `LIMIT %s`: take at most that many rows (`%s` is a parameter placeholder: the value is sent separately).
- `FOR UPDATE SKIP LOCKED`: lock the chosen rows so no other transaction can change them, and *skip* any row another transaction has already locked, instead of waiting. Two workers asking at the same instant therefore get different rows and never wait for each other.
- `UPDATE deliveries d SET status = 'processing', attempts = d.attempts + 1, locked_until = now() + make_interval(secs => %s)`: mark the claimed rows as being processed, count the attempt, and set the lease end (`make_interval(secs => N)` builds a time span of N seconds).
- `FROM ready WHERE d.delivery_id = ready.delivery_id`: update exactly the rows the CTE chose.
- `RETURNING ...`: give the updated rows back to the program in the same round trip.

Because the select, the lock and the update are one statement, there is no gap in which two workers could claim the same row.

The effects statement, in `PostgresEffects.apply`, writes the processed mark, the ticket and the outbox row in one statement, and therefore one transaction:

```sql
WITH mark AS (
    INSERT INTO processed_events (event_id) VALUES (%(event)s) ON CONFLICT (event_id) DO NOTHING RETURNING event_id),
made AS (
    INSERT INTO tickets (event_id, intent, order_number, sentiment, requested_action)
    SELECT event_id, %(intent)s, %(order)s, %(sentiment)s, %(action)s FROM mark RETURNING 1),
queued AS (
    INSERT INTO outbox (event_id, kind) SELECT event_id, 'acknowledge' FROM mark RETURNING 1)
SELECT (SELECT COUNT(*) FROM mark), (SELECT COUNT(*) FROM made), (SELECT COUNT(*) FROM queued)
```

- `mark`: insert the event id into `processed_events`. The table's primary key makes a second insert of the same id a conflict; `ON CONFLICT (event_id) DO NOTHING` turns a conflict into 'insert nothing', and `RETURNING event_id` gives back the id only if a row was really inserted.
- `made`: insert the ticket **from `mark`**: `SELECT ... FROM mark` produces a row only if `mark` inserted one. So if a twin delivery already committed, `mark` is empty and no ticket is written.
- `queued`: the same for the outbox row (the acknowledgment to send).
- The final `SELECT` counts how many rows each part wrote. The Python code reads the first count: 1 means 'this delivery applied the effects', 0 means 'a twin got there first'.
- `%(event)s` and the other `%(name)s` marks are *named parameters*; psycopg sends the values separately from the SQL.

The effect: the mark, the ticket and the outbox row appear together or not at all, and a race between two deliveries of one event is settled by the primary key, not by a check-then-insert gap.

### The container

`docker-compose.yml` starts `postgres:16` (see `docker-compose.md`). It runs with `fsync=off` and `synchronous_commit=off` because it is a local teaching database: a restart after a crash does not stall on a busy disk. The crash tests kill the *worker* process, never this server. The image is 16, not 18, because 18 restarted itself repeatedly under this machine's load.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make up
```

Starts the container and applies the schema.

```bash
docker compose exec -T postgres psql -U inbox -d inbox -c '\dt'
```

Lists the six tables (needs the container running).

```bash
make queries
```

Runs `sql/003_queries.sql` inside the container.

```bash
make status
```

Prints counts and the dead letters.

## Mistakes people make

- Opening a transaction and then waiting for a slow external call inside it. The model call here happens outside any transaction.
- Forgetting `SKIP LOCKED` in a queue, so workers wait for each other.
- Assuming a delivered message arrives only once. The schema keeps duplicates and a primary key makes the effect once.
- Leaving connections open. The code uses a pool and returns connections.
- Running with `fsync=off` anywhere that matters.

## Check yourself

1. What does `FOR UPDATE SKIP LOCKED` do?
   *Answer:* Locks the selected rows and skips rows another connection has locked.
2. What is a transaction?
   *Answer:* A group of statements that all take effect together or not at all.
3. What does `ON CONFLICT DO NOTHING` do?
   *Answer:* Skips an insert whose unique value already exists.
4. Why is the model call kept outside the transaction?
   *Answer:* A transaction open during a slow call holds a connection and locks for nothing.
5. What port does the container publish?
   *Answer:* 5434 on the host, mapped to 5432 inside.

## Further reading

- [PostgreSQL 16 documentation](https://www.postgresql.org/docs/16/)
- [The locking clause (FOR UPDATE, SKIP LOCKED)](https://www.postgresql.org/docs/16/sql-select.html#SQL-FOR-UPDATE-SHARE)
- [INSERT ... ON CONFLICT](https://www.postgresql.org/docs/16/sql-insert.html)
