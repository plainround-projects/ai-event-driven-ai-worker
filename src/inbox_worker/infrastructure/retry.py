"""Retry with exponential backoff and full jitter for calls that cross the network."""

from __future__ import annotations

import random
import time
from collections.abc import Callable


def retry[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    max_delay_seconds: float = 10.0,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    """Call `operation` up to `attempts` times, backing off after each failure in `retry_on`.

    The pause after attempt n is a random value in [0, min(max_delay, base * 2**(n - 1))] (full jitter),
    so many clients do not retry in step. The last failure is raised.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    jitter = rng or random.Random()
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_on as error:
            if attempt == attempts:
                raise
            if on_retry:
                on_retry(attempt, error)
            sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))))
    raise AssertionError("unreachable")  # pragma: no cover
