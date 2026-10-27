"""Handle one delivery: decode, skip a duplicate, run the model outside any transaction, apply the effects once."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from inbox_worker.application.extraction import TicketExtractor
from inbox_worker.application.ports import Clock, Delivery, DeliveryQueue, EffectsStore
from inbox_worker.domain.backoff import backoff_delay
from inbox_worker.domain.errors import ModelCallError, PermanentEventError, RetryableModelError
from inbox_worker.domain.events import parse_event

PROCESSED = "processed"
DUPLICATE = "duplicate"
RETRY = "retry"
DEAD = "dead_lettered"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """How a failing event is retried before it is parked."""

    max_attempts: int = 5
    base_seconds: float = 0.5
    cap_seconds: float = 30.0
    event_deadline_seconds: float = 300.0


class EventHandler:
    """Applies each event's effects once, however often the queue delivers it.

    `crash_at` is called with a point name ("after_model", "after_commit"); the crash tests make it kill the process.
    """

    def __init__(
        self,
        queue: DeliveryQueue,
        effects: EffectsStore,
        extractor: TicketExtractor,
        clock: Clock,
        policy: RetryPolicy | None = None,
        *,
        rng: random.Random | None = None,
        crash_at: Callable[[str], None] = lambda point: None,
    ) -> None:
        self._queue = queue
        self._effects = effects
        self._extractor = extractor
        self._clock = clock
        self._policy = policy or RetryPolicy()
        self._rng = rng or random.Random()
        self._crash_at = crash_at

    def handle(self, delivery: Delivery) -> str:
        """Process one delivery to a final outcome, acknowledging it unless the process dies first."""
        try:
            event = parse_event(delivery.payload)
            if self._effects.is_processed(event.event_id):
                self._queue.ack(delivery.delivery_id)
                return DUPLICATE
            if (self._clock.now() - delivery.received_at).total_seconds() > self._policy.event_deadline_seconds:
                raise PermanentEventError("deadline_exceeded", "the event waited longer than its deadline")
            extraction = self._extractor.extract(event.body)
            self._crash_at("after_model")
            applied = self._effects.apply(event.event_id, extraction.ticket)
            self._crash_at("after_commit")
            self._queue.ack(delivery.delivery_id)
            return PROCESSED if applied else DUPLICATE
        except PermanentEventError as error:
            self._queue.dead_letter(delivery, error.reason, str(error))
            return DEAD
        except (RetryableModelError, ModelCallError) as error:
            return self._retry_or_park(delivery, error)

    def _retry_or_park(self, delivery: Delivery, error: RetryableModelError | ModelCallError) -> str:
        if isinstance(error, ModelCallError):
            self._queue.dead_letter(delivery, "permanent_error", f"{type(error).__name__}: {error}")
            return DEAD
        if delivery.attempts >= self._policy.max_attempts:
            self._queue.dead_letter(delivery, "attempts_exhausted", f"{type(error).__name__}: {error}")
            return DEAD
        delay = backoff_delay(delivery.attempts, self._policy.base_seconds, self._policy.cap_seconds, self._rng)
        self._queue.retry(delivery.delivery_id, delay, f"{type(error).__name__}: {error}")
        return RETRY
