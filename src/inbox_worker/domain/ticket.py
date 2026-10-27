"""The ticket the extractor produces."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from inbox_worker.domain.errors import ReplyInvalidError

INTENTS = ("cancel", "refund", "order_status", "other")
SENTIMENTS = ("positive", "neutral", "negative")
ACTIONS = ("cancel_order", "issue_refund", "send_tracking", "none")


@dataclass(frozen=True, slots=True)
class Ticket:
    """What the customer wants, about which order, in what mood, and the action it asks for."""

    intent: str
    order_number: str | None
    sentiment: str
    requested_action: str

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Ticket:
        """Build a ticket from a decoded reply, checking every field."""
        order = data.get("order_number")
        valid = (
            data.get("intent") in INTENTS
            and data.get("sentiment") in SENTIMENTS
            and data.get("requested_action") in ACTIONS
            and (order is None or (isinstance(order, str) and len(order) == 4 and order.isdigit()))
        )
        if not valid:
            raise ReplyInvalidError("the reply does not match the ticket schema")
        return cls(data["intent"], order, data["sentiment"], data["requested_action"])
