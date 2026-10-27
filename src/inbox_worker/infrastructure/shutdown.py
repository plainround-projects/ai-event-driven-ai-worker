"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""

from __future__ import annotations

import signal
import threading
from types import FrameType


class ShutdownSignal:
    """A flag that SIGINT and SIGTERM set, which work loops check between units of work."""

    def __init__(self) -> None:
        self._requested = threading.Event()

    def install(self) -> None:
        """Route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close."""
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, self._handle)

    def _handle(self, _number: int, _frame: FrameType | None) -> None:
        self.request()

    def request(self) -> None:
        """Ask the loops to stop after the unit of work in flight."""
        self._requested.set()

    @property
    def requested(self) -> bool:
        """True once a stop was requested."""
        return self._requested.is_set()

    def wait(self, seconds: float) -> bool:
        """Sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested."""
        return self._requested.wait(seconds)
