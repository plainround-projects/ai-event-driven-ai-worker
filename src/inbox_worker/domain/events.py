"""The inbox event: its envelope, and the checks that decide an event can never be processed."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass

from inbox_worker.domain.errors import PermanentEventError

MAX_EMAIL_BYTES = 100_000
POISON_MARKER = (
    "POISON-SCHEMA"  # an email containing this makes the fake model answer with something that is not a ticket
)


@dataclass(frozen=True, slots=True)
class EmailEvent:
    """An "email received" event: a unique id and the email text."""

    event_id: str
    body: str


def parse_event(payload: str) -> EmailEvent:
    """Decode a delivery's payload. Raises `PermanentEventError` for a body that is not an event, is not valid text, or
    is too large: none of those will be different on the next attempt, so they go to the dead-letter table."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        raise PermanentEventError("malformed_event", f"the event is not valid JSON: {error.msg}") from None
    if not isinstance(data, dict) or not isinstance(data.get("event_id"), str) or not data["event_id"].strip():
        raise PermanentEventError("malformed_event", "the event needs a non-empty string event_id")
    if "body_b64" in data:
        try:
            raw = base64.b64decode(str(data["body_b64"]), validate=True)
        except (binascii.Error, ValueError):
            raise PermanentEventError("malformed_event", "body_b64 is not valid base64") from None
        try:
            body = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise PermanentEventError(
                "bad_encoding", f"the email is not valid UTF-8: {error.reason} at byte {error.start}"
            ) from None
    else:
        found = data.get("body")
        if not isinstance(found, str) or not found.strip():
            raise PermanentEventError("malformed_event", "the event needs a non-empty string body")
        body = found
    size = len(body.encode("utf-8"))
    if size > MAX_EMAIL_BYTES:
        raise PermanentEventError("event_too_large", f"the email is {size} bytes; the limit is {MAX_EMAIL_BYTES}")
    return EmailEvent(data["event_id"].strip(), body)


def event_id_of(payload: str) -> str:
    """The event id a receiver files a payload under; a payload that is not an event gets a stable placeholder so it can
    still be queued, parked and shown to a person."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = None
    if isinstance(data, dict) and isinstance(data.get("event_id"), str) and data["event_id"].strip():
        return str(data["event_id"]).strip()
    return "unparsed-" + hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]
