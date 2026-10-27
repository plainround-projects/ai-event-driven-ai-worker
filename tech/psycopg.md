# psycopg 3 and psycopg_pool

## What it is

`psycopg` (version 3) is the Python driver for PostgreSQL: the library that opens a connection, sends SQL, and returns rows. `psycopg_pool` adds a *connection pool*: a small set of connections kept open and lent out, because opening a connection for every query is slow.

## Why this repository uses it

The queue, the effects and the outbox all live in PostgreSQL, so the worker needs a driver and a pool. psycopg 3 is the current Python driver; the pool keeps connections open and lends them out, so each queue operation is one round trip.

## Where it appears

| File | What it does with psycopg 3 and psycopg_pool |
| --- | --- |
| `src/inbox_worker/infrastructure/postgres.py` | `Database` (the pool), the queue, the effects store, the outbox, the reports |
| `tests/integration/` | tests the adapters against a real PostgreSQL |
| `pyproject.toml` | pins `psycopg[binary,pool]>=3.2,<4` |

## How it works underneath

`ConnectionPool(url, min_size=1, max_size=16, kwargs={"autocommit": True})` opens connections on demand. `with pool.connection() as connection:` borrows one and returns it afterwards. `connection.execute(sql, params)` runs a statement; `%s` marks a parameter, and values are sent separately from the SQL. In *autocommit* mode each statement is its own transaction, one network round trip; to group several statements the code writes `with connection.transaction():`. `.fetchone()` and `.fetchall()` read rows.

A connection that the server closed (a restart) is discarded by the pool and replaced, but a statement in flight fails with `OperationalError`; the worker loop treats that as 'try again later'.

## Walkthrough of this repository's use

From `src/inbox_worker/infrastructure/postgres.py`:

```python
class Database:
    """A small connection pool over one database URL."""
```

- `class Database:`: The object that owns the connection pool.
- `"""A small connection pool over one database URL."""`: The docstring.

```python
    def __init__(self, url: str, max_connections: int = 16) -> None:
        self._pool = ConnectionPool(url, min_size=1, max_size=max_connections, open=True, kwargs={"autocommit": True})
```

- `def __init__(self, url: str, max_connections: int = 16) -> None:`: Takes the database URL and the largest number of connections.
- `self._pool = ConnectionPool(url, min_size=1, max_size=max_connections, open=True, kwargs={"autocommit": True})`: Creates the pool: at least one connection, at most 16, opened now. `kwargs` are passed to each connection: `autocommit=True` makes every statement its own transaction and its own round trip.

```python
    def connection(self) -> psycopg.Connection:
        """Borrow a connection (autocommit: one statement is one transaction and one round trip). Wrap several
        statements that must happen together in `with connection.transaction():`."""
        return self._pool.connection()  # type: ignore[return-value]
```

- `def connection(self) -> psycopg.Connection:`: Hands out a connection. Used as `with database.connection() as connection:`, which returns it to the pool at the end of the block.
- `"""Borrow a connection (autocommit: one statement is one transaction and one round trip). Wrap several`: The docstring begins: statements that must happen together go in `with connection.transaction():`.
- `` statements that must happen together in `with connection.transaction():`.""" ``: (The docstring continues.)
- `return self._pool.connection()  # type: ignore[return-value]`: Another line of the function (a statement or a continuation of the one above).

```python
    def close(self) -> None:
        """Close the pool."""
        self._pool.close()
```

- `def close(self) -> None:`: Closes the pool at shutdown.
- `"""Close the pool."""`: The docstring.
- `self._pool.close()`: Closes every connection.

```python
    def ping(self) -> bool:
        """True when a trivial query works."""
        with self.connection() as connection:
            return connection.execute("SELECT 1").fetchone() == (1,)
```

- `def ping(self) -> bool:`: A health check.
- `"""True when a trivial query works."""`: The docstring.
- `with self.connection() as connection:`: Borrows a connection for the block.
- `return connection.execute("SELECT 1").fetchone() == (1,)`: Runs `SELECT 1` and checks that the one row is `(1,)`: the database answered.

Two other places need an explicit transaction, because the pool is in *autocommit* mode (each statement is its own transaction). `dead_letter` inserts into `dead_letters` and updates `deliveries`; `redrive` reads a dead letter `FOR UPDATE`, inserts a new delivery and marks the dead letter redriven. Both are wrapped in `with connection.transaction():` so their statements are atomic. A version of the code that forgot this was found and fixed during the work: without the wrapper a crash between the statements could leave a delivery that was parked in `dead_letters` but still marked `processing`.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/python -c "import psycopg; print(psycopg.__version__)"
```

Prints `3.3.6`.

```bash
make test-integration
```

Runs the adapters against the running database.

```bash
make status
```

Prints the counts of deliveries, tickets, outbox rows and dead letters.

## Mistakes people make

- Forgetting that autocommit makes a multi-statement write non-atomic unless wrapped in `connection.transaction()`. A bug of this kind was found and fixed in the dead-letter and redrive code.
- Building SQL with f-strings.
- Holding a pooled connection during slow work.
- Not closing the pool at shutdown.
- Assuming `psycopg` 2 habits apply; version 3 differs.

## Check yourself

1. What is a connection pool?
   *Answer:* A set of open connections lent out and returned, to avoid reconnecting for every query.
2. What does `%s` mean in the SQL?
   *Answer:* A parameter placeholder; the value is sent separately.
3. What does autocommit do?
   *Answer:* Makes every statement its own transaction.
4. How do you group several statements atomically?
   *Answer:* Wrap them in `with connection.transaction():`.
5. What happens to a statement in flight when the server restarts?
   *Answer:* It fails with `OperationalError`.

## Further reading

- [psycopg 3 documentation (pinned version 3.3.6)](https://www.psycopg.org/psycopg3/docs/)
- [Connection pools](https://www.psycopg.org/psycopg3/docs/advanced/pool.html)
- [Transactions](https://www.psycopg.org/psycopg3/docs/basic/transactions.html)
