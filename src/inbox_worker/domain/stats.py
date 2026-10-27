"""Small statistics for the burst report."""

from __future__ import annotations

import math
from collections.abc import Sequence


def percentile(values: Sequence[float], fraction: float) -> float:
    """Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values."""
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))]
