"""A fake model for load tests: a configurable delay, an error rate and a rate limit. It is not a model.

It extracts a ticket with keyword rules, so a run has real tickets to count. The rate limit is a token bucket in requests
per second; a call over it raises the same error a provider's 429 would, and the call is counted.
"""

from __future__ import annotations

import json
import math
import random
import re
import threading
import time
from collections.abc import Callable

from inbox_worker.application.ports import ModelReply
from inbox_worker.domain.errors import RetryableModelError
from inbox_worker.domain.events import POISON_MARKER

_ORDER = re.compile(r"(?<!\d)\d{4}(?!\d)")


class FakeModel:
    """Thread-safe; counts calls, rate-limit errors and injected errors."""

    name = "fake-model"

    def __init__(
        self,
        *,
        delay_seconds: float = 0.0,
        error_rate: float = 0.0,
        max_rps: float = 0.0,
        seed: int = 1,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._delay = delay_seconds
        self._error_rate = error_rate
        self._max_rps = max_rps
        self._rng = random.Random(seed)
        self._sleep = sleep
        self._clock = clock
        self._lock = threading.Lock()
        self._tokens = max_rps
        self._refilled = clock()
        self.calls = 0
        self.rate_limited = 0
        self.injected_errors = 0

    def _admit(self) -> None:
        with self._lock:
            self.calls += 1
            if self._max_rps > 0:
                now = self._clock()
                self._tokens = min(self._max_rps, self._tokens + (now - self._refilled) * self._max_rps)
                self._refilled = now
                if self._tokens < 1:
                    self.rate_limited += 1
                    raise RetryableModelError("rate limited (429)")
                self._tokens -= 1
            if self._error_rate > 0 and self._rng.random() < self._error_rate:
                self.injected_errors += 1
                raise RetryableModelError("server error (503)")

    def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
        """Wait for the delay, then answer; raises `RetryableModelError` over the rate limit or on an injected error."""
        self._admit()
        if self._delay:
            self._sleep(self._delay)
        text = "not a ticket" if POISON_MARKER in user else self._ticket(user)
        return ModelReply(text, self.name, math.ceil((len(system) + len(user)) / 4), math.ceil(len(text) / 4))

    @staticmethod
    def _ticket(email: str) -> str:
        lowered = email.lower()
        if "cancel" in lowered:
            intent, action = "cancel", "cancel_order"
        elif "refund" in lowered or "money back" in lowered:
            intent, action = "refund", "issue_refund"
        elif "where" in lowered or "tracking" in lowered:
            intent, action = "order_status", "send_tracking"
        else:
            intent, action = "other", "none"
        found = _ORDER.search(email)
        sentiment = (
            "negative" if any(word in lowered for word in ("furious", "unacceptable", "terrible")) else "neutral"
        )
        return json.dumps(
            {
                "intent": intent,
                "order_number": found.group(0) if found else None,
                "sentiment": sentiment,
                "requested_action": action,
            }
        )
