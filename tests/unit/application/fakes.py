"""In-memory stand-ins for the ports, shared by the application tests."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from inbox_worker.application.ports import Delivery, ModelReply
from inbox_worker.domain.ticket import Ticket

START = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)
VALID = '{"intent": "cancel", "order_number": "4417", "sentiment": "neutral", "requested_action": "cancel_order"}'


class FixedClock:
    """A clock the test moves by hand."""

    def __init__(self) -> None:
        self.current = START

    def now(self) -> datetime:
        return self.current

    def advance(self, seconds: float) -> None:
        self.current += timedelta(seconds=seconds)


@dataclass
class MemoryQueue:
    """The queue in memory: deliveries by id with a status, and the calls the handler made."""

    items: dict[int, dict[str, Any]] = field(default_factory=dict)
    retries: list[tuple[int, float, str]] = field(default_factory=list)
    dead: list[tuple[int, str, str]] = field(default_factory=list)
    acked: list[int] = field(default_factory=list)

    def put(self, event_id: str, payload: str) -> int:
        delivery_id = len(self.items) + 1
        self.items[delivery_id] = {"event_id": event_id, "payload": payload, "status": "queued", "attempts": 0}
        return delivery_id

    def claim(self, limit: int, lease_seconds: float) -> Sequence[Delivery]:
        claimed: list[Delivery] = []
        for delivery_id, item in self.items.items():
            if item["status"] == "queued" and len(claimed) < limit:
                item["status"] = "processing"
                item["attempts"] += 1
                claimed.append(Delivery(delivery_id, item["event_id"], item["payload"], START, item["attempts"]))
        return claimed

    def ack(self, delivery_id: int) -> None:
        self.items.setdefault(delivery_id, {})["status"] = "done"
        self.acked.append(delivery_id)

    def retry(self, delivery_id: int, delay_seconds: float, error: str) -> None:
        self.items.setdefault(delivery_id, {})["status"] = "queued"
        self.retries.append((delivery_id, delay_seconds, error))

    def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:
        self.items.setdefault(delivery.delivery_id, {})["status"] = "dead"
        self.dead.append((delivery.delivery_id, reason, error))

    def depth(self) -> int:
        return sum(item.get("status") in ("queued", "processing") for item in self.items.values())


@dataclass
class MemoryEffects:
    """The effects store in memory; `apply` returns False for an event that already has a mark."""

    processed: dict[str, Ticket] = field(default_factory=dict)

    def is_processed(self, event_id: str) -> bool:
        return event_id in self.processed

    def apply(self, event_id: str, ticket: Ticket) -> bool:
        if event_id in self.processed:
            return False
        self.processed[event_id] = ticket
        return True


class ScriptedModel:
    """Replies from a queue of texts or exceptions; an unscripted call fails the test."""

    def __init__(self, *script: str | Exception | Callable[[str], str]) -> None:
        self._script = list(script)
        self.calls: list[str] = []

    def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
        self.calls.append(user)
        if not self._script:
            raise AssertionError(f"unexpected extra call #{len(self.calls)}")
        item = self._script.pop(0)
        if isinstance(item, Exception):
            raise item
        return ModelReply(item(user) if callable(item) else item, "scripted", 10, 5)


def delivery(
    event_id: str = "e-1", body: str = "Please cancel order 4417.", attempts: int = 1, delivery_id: int = 1
) -> Delivery:
    import json

    return Delivery(delivery_id, event_id, json.dumps({"event_id": event_id, "body": body}), START, attempts)
