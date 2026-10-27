"""The boundaries the worker talks through: the queue, the effects store, the model, the mail gateway."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from inbox_worker.domain.ticket import Ticket


@dataclass(frozen=True, slots=True)
class Delivery:
    """One queue message: a delivery of an event. The same event can arrive in more than one delivery."""

    delivery_id: int
    event_id: str
    payload: str
    received_at: datetime
    attempts: int


class DeliveryQueue(Protocol):
    """A queue with acknowledgments and redelivery, in a database table read with row locks."""

    def put(self, event_id: str, payload: str) -> int:
        """Add a delivery; returns its id."""
        ...

    def claim(self, limit: int, lease_seconds: float) -> Sequence[Delivery]:
        """Take up to `limit` ready deliveries for `lease_seconds`. A claim that is never acknowledged expires, and the
        delivery is handed out again (this is the redelivery after a crash)."""
        ...

    def ack(self, delivery_id: int) -> None:
        """The delivery is finished."""
        ...

    def retry(self, delivery_id: int, delay_seconds: float, error: str) -> None:
        """Make the delivery available again after `delay_seconds`, remembering the error."""
        ...

    def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:
        """Move the delivery to the dead-letter table with a reason, the attempt count, the last error and a payload hash."""
        ...

    def depth(self) -> int:
        """Deliveries waiting or in flight."""
        ...


class EffectsStore(Protocol):
    """Where an event's effects land: the processed mark, the ticket and the outbox row."""

    def is_processed(self, event_id: str) -> bool:
        """True when this event's effects were already applied."""
        ...

    def apply(self, event_id: str, ticket: Ticket) -> bool:
        """Write the processed mark, the ticket and the outbox row in one transaction. Returns False when a twin
        delivery committed first (the primary key on the mark settles the race); nothing is written then."""
        ...


class MailGateway(Protocol):
    """Sends an acknowledgment. The fake implementation records every send."""

    def send(self, event_id: str, kind: str) -> None:
        """Send one acknowledgment; sending the same event's twice must fail or be refused."""
        ...


class OutboxStore(Protocol):
    """The acknowledgments waiting to be sent."""

    def unsent(self, limit: int) -> Sequence[tuple[int, str, str]]:
        """(outbox id, event id, kind) of unsent rows, oldest first."""
        ...

    def mark_sent(self, outbox_id: int) -> None:
        """Record that the row was sent."""
        ...


@dataclass(frozen=True, slots=True)
class ModelReply:
    """The model's text and what the call used."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int


class ChatModel(Protocol):
    """A text model. Raises `RetryableModelError` for failures worth retrying and `ModelCallError` for the rest."""

    def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
        """Answer one request."""
        ...


class Clock(Protocol):
    """The current time, injected so tests are deterministic."""

    def now(self) -> datetime:
        """Now, timezone-aware."""
        ...
