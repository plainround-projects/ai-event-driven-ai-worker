"""PostgreSQL adapters: the queue (rows claimed with SKIP LOCKED), the effects store, the outbox and the report queries."""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg import errors
from psycopg_pool import ConnectionPool

from inbox_worker.application.outbox import DuplicateSendError
from inbox_worker.application.ports import Delivery
from inbox_worker.domain.ticket import Ticket

SCRIPTS = ("001_schema.sql", "002_seed.sql")


class Database:
    """A small connection pool over one database URL."""

    def __init__(self, url: str, max_connections: int = 16) -> None:
        self._pool = ConnectionPool(url, min_size=1, max_size=max_connections, open=True, kwargs={"autocommit": True})

    def connection(self) -> psycopg.Connection:
        """Borrow a connection (autocommit: one statement is one transaction and one round trip). Wrap several
        statements that must happen together in `with connection.transaction():`."""
        return self._pool.connection()  # type: ignore[return-value]

    def close(self) -> None:
        """Close the pool."""
        self._pool.close()

    def ping(self) -> bool:
        """True when a trivial query works."""
        with self.connection() as connection:
            return connection.execute("SELECT 1").fetchone() == (1,)


def apply_scripts(database: Database, sql_dir: Path) -> list[str]:
    """Drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran."""
    ran = []
    with database.connection() as connection:
        connection.execute("DROP SCHEMA public CASCADE")
        connection.execute("CREATE SCHEMA public")
        for name in SCRIPTS:
            connection.execute((sql_dir / name).read_text(encoding="utf-8"))
            ran.append(name)
    return ran


def reset_tables(database: Database, sql_dir: Path) -> None:
    """Empty every table (sql/reset.sql)."""
    with database.connection() as connection:
        connection.execute((sql_dir / "reset.sql").read_text(encoding="utf-8"))


class PostgresQueue:
    """The delivery queue."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def put(self, event_id: str, payload: str) -> int:
        """Insert one delivery."""
        with self._database.connection() as connection:
            row = connection.execute(
                "INSERT INTO deliveries (event_id, payload) VALUES (%s, %s) RETURNING delivery_id", (event_id, payload)
            ).fetchone()
        return int(row[0]) if row else 0

    def put_many(self, items: Sequence[tuple[str, str]]) -> None:
        """Insert many deliveries in one transaction (loading the sample events)."""
        with self._database.connection() as connection, connection.transaction(), connection.cursor() as cursor:
            cursor.executemany("INSERT INTO deliveries (event_id, payload) VALUES (%s, %s)", list(items))

    def claim(self, limit: int, lease_seconds: float) -> Sequence[Delivery]:
        """Claim ready deliveries; an expired claim is handed out again."""
        with self._database.connection() as connection:
            rows = connection.execute(
                """
                WITH ready AS (
                    SELECT delivery_id FROM deliveries
                    WHERE (status = 'queued' AND available_at <= now()) OR (status = 'processing' AND locked_until < now())
                    ORDER BY available_at, delivery_id
                    LIMIT %s FOR UPDATE SKIP LOCKED)
                UPDATE deliveries d SET status = 'processing', attempts = d.attempts + 1,
                       locked_until = now() + make_interval(secs => %s)
                FROM ready WHERE d.delivery_id = ready.delivery_id
                RETURNING d.delivery_id, d.event_id, d.payload, d.received_at, d.attempts
                """,
                (limit, lease_seconds),
            ).fetchall()
        return [Delivery(*row) for row in rows]

    def ack(self, delivery_id: int) -> None:
        """Finish a delivery."""
        with self._database.connection() as connection:
            connection.execute(
                "UPDATE deliveries SET status = 'done', locked_until = NULL WHERE delivery_id = %s", (delivery_id,)
            )

    def retry(self, delivery_id: int, delay_seconds: float, error: str) -> None:
        """Release the claim and make the delivery available after a delay."""
        with self._database.connection() as connection:
            connection.execute(
                "UPDATE deliveries SET status = 'queued', locked_until = NULL, last_error = %s, "
                "available_at = now() + make_interval(secs => %s) WHERE delivery_id = %s",
                (error, delay_seconds, delivery_id),
            )

    def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:
        """Park the delivery with what a person needs to act; both writes are one transaction."""
        digest = hashlib.sha256(delivery.payload.encode("utf-8", "replace")).hexdigest()[:12]
        with self._database.connection() as connection, connection.transaction():
            connection.execute(
                "INSERT INTO dead_letters (event_id, reason, attempts, last_error, payload_hash, payload) VALUES (%s, %s, %s, %s, %s, %s)",
                (delivery.event_id, reason, delivery.attempts, error, digest, delivery.payload),
            )
            connection.execute(
                "UPDATE deliveries SET status = 'dead', locked_until = NULL, last_error = %s WHERE delivery_id = %s",
                (error, delivery.delivery_id),
            )

    def depth(self) -> int:
        """Deliveries that are queued or in flight."""
        with self._database.connection() as connection:
            row = connection.execute(
                "SELECT COUNT(*) FROM deliveries WHERE status IN ('queued', 'processing')"
            ).fetchone()
        return int(row[0]) if row else 0

    def redrive(self, dead_id: int) -> int | None:
        """Put a dead letter's payload back on the queue as a new delivery and mark it redriven; None if unknown or done."""
        with self._database.connection() as connection, connection.transaction():
            row = connection.execute(
                "SELECT event_id, payload FROM dead_letters WHERE dead_id = %s AND redriven_at IS NULL FOR UPDATE",
                (dead_id,),
            ).fetchone()
            if row is None:
                return None
            new = connection.execute(
                "INSERT INTO deliveries (event_id, payload) VALUES (%s, %s) RETURNING delivery_id", row
            ).fetchone()
            connection.execute("UPDATE dead_letters SET redriven_at = now() WHERE dead_id = %s", (dead_id,))
        return int(new[0]) if new else None


class PostgresEffects:
    """The processed mark, the ticket and the outbox row."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def is_processed(self, event_id: str) -> bool:
        """True when the event's effects were applied (read fresh from the database every time)."""
        with self._database.connection() as connection:
            return (
                connection.execute("SELECT 1 FROM processed_events WHERE event_id = %s", (event_id,)).fetchone()
                is not None
            )

    def apply(self, event_id: str, ticket: Ticket) -> bool:
        """Write the mark, the ticket and the outbox row in ONE statement (so one transaction and one round trip). The
        primary key on the mark settles a race: a twin delivery that commits first leaves this statement inserting nothing."""
        with self._database.connection() as connection:
            row = connection.execute(
                """
                WITH mark AS (
                    INSERT INTO processed_events (event_id) VALUES (%(event)s) ON CONFLICT (event_id) DO NOTHING RETURNING event_id),
                made AS (
                    INSERT INTO tickets (event_id, intent, order_number, sentiment, requested_action)
                    SELECT event_id, %(intent)s, %(order)s, %(sentiment)s, %(action)s FROM mark RETURNING 1),
                queued AS (
                    INSERT INTO outbox (event_id, kind) SELECT event_id, 'acknowledge' FROM mark RETURNING 1)
                SELECT (SELECT COUNT(*) FROM mark), (SELECT COUNT(*) FROM made), (SELECT COUNT(*) FROM queued)
                """,
                {
                    "event": event_id,
                    "intent": ticket.intent,
                    "order": ticket.order_number,
                    "sentiment": ticket.sentiment,
                    "action": ticket.requested_action,
                },
            ).fetchone()
        return bool(row and row[0] == 1)


class PostgresOutbox:
    """The unsent acknowledgments."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def unsent(self, limit: int) -> Sequence[tuple[int, str, str]]:
        """Oldest unsent rows."""
        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT outbox_id, event_id, kind FROM outbox WHERE sent_at IS NULL ORDER BY outbox_id LIMIT %s",
                (limit,),
            ).fetchall()
        return [(int(a), b, c) for a, b, c in rows]

    def mark_sent(self, outbox_id: int) -> None:
        """Record that the row was sent."""
        with self._database.connection() as connection:
            connection.execute("UPDATE outbox SET sent_at = now() WHERE outbox_id = %s", (outbox_id,))


class FakeMailSender:
    """Records every send in `sent_mail`; the unique event id refuses a second send of one acknowledgment."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def send(self, event_id: str, kind: str) -> None:
        """Record one send."""
        try:
            with self._database.connection() as connection:
                connection.execute("INSERT INTO sent_mail (event_id, kind) VALUES (%s, %s)", (event_id, kind))
        except errors.UniqueViolation:
            raise DuplicateSendError(event_id) from None


class PostgresReports:
    """Read-only queries for the reports and the verification steps."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def _one(self, sql: str) -> int:
        with self._database.connection() as connection:
            row = connection.execute(sql).fetchone()
        return int(row[0]) if row else 0

    def counts(self) -> dict[str, int]:
        """Rows in the tables that matter."""
        return {
            "deliveries": self._one("SELECT COUNT(*) FROM deliveries"),
            "processed": self._one("SELECT COUNT(*) FROM processed_events"),
            "tickets": self._one("SELECT COUNT(*) FROM tickets"),
            "outbox": self._one("SELECT COUNT(*) FROM outbox"),
            "mails_sent": self._one("SELECT COUNT(*) FROM sent_mail"),
            "dead_letters": self._one("SELECT COUNT(*) FROM dead_letters"),
        }

    def ticket_event_ids(self) -> list[str]:
        """Event id of every ticket (duplicates would show up twice)."""
        with self._database.connection() as connection:
            return [row[0] for row in connection.execute("SELECT event_id FROM tickets ORDER BY ticket_id").fetchall()]

    def dead_events(self) -> list[tuple[int, str, str, int, str, str]]:
        """(dead id, event id, reason, attempts, last error, payload hash) of open dead letters."""
        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT dead_id, event_id, reason, attempts, last_error, payload_hash FROM dead_letters WHERE redriven_at IS NULL ORDER BY dead_id"
            ).fetchall()
        return [(int(r[0]), r[1], r[2], int(r[3]), r[4], r[5]) for r in rows]

    def event_to_ticket_seconds(self) -> list[float]:
        """Seconds from the first delivery of each ticketed event to its ticket."""
        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT EXTRACT(EPOCH FROM t.created_at - d.first_seen) FROM tickets t JOIN "
                "(SELECT event_id, MIN(received_at) AS first_seen FROM deliveries GROUP BY event_id) d USING (event_id)"
            ).fetchall()
        return [float(row[0]) for row in rows]

    def now(self) -> datetime:
        """The database's clock."""
        with self._database.connection() as connection:
            row = connection.execute("SELECT now()").fetchone()
        return row[0] if row else datetime.min
