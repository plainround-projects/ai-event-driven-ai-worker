-- DDL for the inbox worker (PostgreSQL 16). `make db` applies this file and 002_seed.sql in order.

-- The queue. A webhook retry or a redelivery can put the same event id here twice, so event_id is NOT unique:
-- the guard against applying an event twice is processed_events, below, not this table.
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
-- The claim query reads only rows that are ready.
CREATE INDEX deliveries_ready ON deliveries (available_at, delivery_id) WHERE status IN ('queued', 'processing');
CREATE INDEX deliveries_by_event ON deliveries (event_id);

-- One row per event whose effects were applied. Its primary key settles a race between two deliveries of one event.
CREATE TABLE processed_events (
    event_id     TEXT PRIMARY KEY,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tickets (
    ticket_id        BIGSERIAL PRIMARY KEY,
    event_id         TEXT NOT NULL UNIQUE REFERENCES processed_events (event_id),
    intent           TEXT NOT NULL,
    order_number     TEXT,
    sentiment        TEXT NOT NULL,
    requested_action TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- The acknowledgment to send, written in the same transaction as the ticket; a relay sends it afterwards.
CREATE TABLE outbox (
    outbox_id  BIGSERIAL PRIMARY KEY,
    event_id   TEXT NOT NULL UNIQUE REFERENCES processed_events (event_id),
    kind       TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at    TIMESTAMPTZ
);
CREATE INDEX outbox_unsent ON outbox (outbox_id) WHERE sent_at IS NULL;

-- The fake mail sender's record of every send. The unique event id means a second send of one acknowledgment fails.
CREATE TABLE sent_mail (
    send_id  BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    kind     TEXT NOT NULL,
    sent_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Events that can never succeed, with what a person needs to act: reason, attempts, last error and a payload hash.
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
CREATE INDEX dead_letters_open ON dead_letters (dead_id) WHERE redriven_at IS NULL;
