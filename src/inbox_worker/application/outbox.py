"""The outbox relay: send each acknowledgment, tolerate a send that happened before a crash, mark it sent."""

from __future__ import annotations

import contextlib

from inbox_worker.application.ports import MailGateway, OutboxStore


class DuplicateSendError(RuntimeError):
    """The mail gateway has already sent this event's acknowledgment."""


class OutboxRelay:
    """Sends unsent outbox rows. A row whose mail was already sent (the relay died before marking it) is just marked."""

    def __init__(self, outbox: OutboxStore, gateway: MailGateway) -> None:
        self._outbox = outbox
        self._gateway = gateway

    def run_once(self, limit: int = 100) -> int:
        """Send up to `limit` rows; returns how many rows were marked sent."""
        done = 0
        for outbox_id, event_id, kind in self._outbox.unsent(limit):
            with contextlib.suppress(DuplicateSendError):
                self._gateway.send(event_id, kind)
            self._outbox.mark_sent(outbox_id)
            done += 1
        return done
