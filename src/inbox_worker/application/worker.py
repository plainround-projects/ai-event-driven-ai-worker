"""The worker loop: claim deliveries, handle them on a bounded pool, and stop cleanly when asked."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from inbox_worker.application.handler import EventHandler
from inbox_worker.application.ports import Delivery, DeliveryQueue

LOGGER = logging.getLogger("inbox_worker.worker")
MAX_BACKOFF_SECONDS = 10.0


class Worker:
    """Pulls batches from the queue. A shutdown request finishes the deliveries in flight and then returns."""

    def __init__(
        self,
        queue: DeliveryQueue,
        handler: EventHandler,
        *,
        concurrency: int,
        lease_seconds: float,
        stop_requested: Callable[[], bool],
        wait: Callable[[float], bool],
        idle_poll_seconds: float = 0.2,
    ) -> None:
        self._queue = queue
        self._handler = handler
        self._concurrency = concurrency
        self._lease = lease_seconds
        self._stop = stop_requested
        self._wait = wait
        self._idle = idle_poll_seconds

    def _handle_safely(self, delivery: Delivery) -> str:
        """A failure the handler did not classify is logged and left to the lease: the delivery comes back."""
        try:
            return self._handler.handle(delivery)
        except Exception:
            LOGGER.exception("delivery failed unexpectedly", extra={"fields": {"delivery_id": delivery.delivery_id}})
            return "error"

    def run(self, *, until_idle: bool = False) -> Counter[str]:
        """Process deliveries until a stop is requested (or, with `until_idle`, until the queue is empty)."""
        outcomes: Counter[str] = Counter()
        with ThreadPoolExecutor(max_workers=self._concurrency, thread_name_prefix="handle") as pool:
            failures = 0
            while not self._stop():
                try:
                    batch = self._queue.claim(self._concurrency, self._lease)
                    if not batch and until_idle and self._queue.depth() == 0:
                        break
                except Exception:
                    # The queue is unreachable (database restart, failover). Nothing is lost: claimed rows come
                    # back when their lease expires. Wait with a growing pause and try again.
                    failures += 1
                    LOGGER.exception("queue unavailable", extra={"fields": {"consecutive_failures": failures}})
                    outcomes["queue_error"] += 1
                    self._wait(min(self._idle * 2**failures, MAX_BACKOFF_SECONDS))
                    continue
                failures = 0
                if not batch:
                    self._wait(self._idle)
                    continue
                for outcome in pool.map(self._handle_safely, batch):
                    outcomes[outcome] += 1
        LOGGER.info("worker stopped", extra={"fields": dict(outcomes)})
        return outcomes
