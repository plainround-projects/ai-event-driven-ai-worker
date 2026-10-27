"""The system clock."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Now, in UTC."""

    def now(self) -> datetime:
        """The current time, timezone-aware."""
        return datetime.now(UTC)
