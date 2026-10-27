"""Named errors of the inbox worker. Retryable and permanent failures are different types so no code has to guess."""

from __future__ import annotations


class PermanentEventError(Exception):
    """An event that can never succeed. `reason` is one of the dead-letter reasons; the message is what a person reads."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class RetryableModelError(RuntimeError):
    """A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection."""


class ModelCallError(RuntimeError):
    """A model call failed in a way a retry will not fix."""


class ReplyInvalidError(ValueError):
    """A model reply is not a valid ticket; the message says why."""


class WebhookRejectedError(Exception):
    """A webhook request failed verification; `reason` is the text of the 401."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason
