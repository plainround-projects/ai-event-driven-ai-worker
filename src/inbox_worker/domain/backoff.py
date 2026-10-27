"""Backoff with full jitter, capped."""

from __future__ import annotations

import random


def backoff_delay(attempt: int, base_seconds: float, cap_seconds: float, rng: random.Random) -> float:
    """A random delay in [0, min(cap, base * 2**(attempt - 1))]. Full jitter spreads retries of many failing events
    over time; a fixed exponential schedule would have them all retry at the same moments and synchronize into bursts."""
    return rng.uniform(0, min(cap_seconds, base_seconds * 2 ** (attempt - 1)))
