"""The Module 2 extractor as a step: an email in, a ticket out, one bounded repair, errors classified."""

from __future__ import annotations

import json
from dataclasses import dataclass

from inbox_worker.application.ports import ChatModel
from inbox_worker.domain.errors import PermanentEventError, ReplyInvalidError
from inbox_worker.domain.ticket import Ticket

PROMPT_VERSION = "extract.v1"
SYSTEM = (
    "Extract intent (cancel, refund, order_status or other), order_number (four digits or null), sentiment "
    "(positive, neutral or negative) and requested_action (cancel_order, issue_refund, send_tracking or none) "
    "from this support email. Reply with one JSON object only."
)


@dataclass(frozen=True, slots=True)
class Extraction:
    """A ticket and the model calls it took."""

    ticket: Ticket
    calls: int


def _parse(text: str) -> Ticket:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ReplyInvalidError(f"not valid JSON: {error.msg}") from None
    if not isinstance(data, dict):
        raise ReplyInvalidError("not a JSON object")
    return Ticket.from_dict(data)


class TicketExtractor:
    """Model-backed extraction. A schema failure that survives one repair is permanent; model errors keep their type."""

    def __init__(self, model: ChatModel, system: str = SYSTEM, version: str = PROMPT_VERSION) -> None:
        self._model = model
        self._system = system
        self._version = version

    def extract(self, email: str) -> Extraction:
        """One call, and one repair call when the reply is not a valid ticket."""
        first = self._model.complete(self._system, email, self._version)
        try:
            return Extraction(_parse(first.text), 1)
        except ReplyInvalidError as reason:
            second = self._model.complete(
                self._system,
                f"{email}\n\nYour reply was not a valid ticket ({reason}). Return only the JSON.",
                self._version,
            )
            try:
                return Extraction(_parse(second.text), 2)
            except ReplyInvalidError as final:
                raise PermanentEventError(
                    "permanent_error", f"schema validation failed after one repair: {final}"
                ) from None
