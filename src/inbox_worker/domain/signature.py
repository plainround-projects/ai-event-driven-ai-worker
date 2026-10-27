"""Webhook signatures: HMAC-SHA256 over the timestamp and the body together, with a maximum age."""

from __future__ import annotations

import hashlib
import hmac

MAX_AGE_SECONDS = 300
TAMPERED = "signature mismatch (tampered or wrong secret)"
TOO_OLD = "request too old (replay rejected)"
BAD_TIMESTAMP = "timestamp is not a number"


def sign(secret: bytes, timestamp: float, body: str) -> str:
    """The signature a sender attaches. Signing the timestamp too is what stops a captured request being replayed later."""
    return hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashlib.sha256).hexdigest()


def verify(secret: bytes, timestamp: str, body: str, signature: str, now: float) -> tuple[bool, str]:
    """(ok, reason). Age is checked first and cheaply; the comparison is constant-time."""
    try:
        sent_at = float(timestamp)
    except ValueError:
        return False, BAD_TIMESTAMP
    if abs(now - sent_at) > MAX_AGE_SECONDS:
        return False, TOO_OLD
    if not hmac.compare_digest(sign(secret, sent_at, body), signature):
        return False, TAMPERED
    return True, "ok"
