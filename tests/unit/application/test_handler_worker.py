import json
import random

import pytest

from inbox_worker.application.extraction import TicketExtractor
from inbox_worker.application.generate_events import generate_events
from inbox_worker.application.handler import DEAD, DUPLICATE, PROCESSED, RETRY, EventHandler, RetryPolicy
from inbox_worker.application.outbox import DuplicateSendError, OutboxRelay
from inbox_worker.application.worker import Worker
from inbox_worker.domain.errors import ModelCallError, RetryableModelError
from tests.unit.application.fakes import VALID, FixedClock, MemoryEffects, MemoryQueue, ScriptedModel, delivery


def _recorder(into: list[float]):
    def wait(seconds: float) -> bool:
        into.append(seconds)
        return False

    return wait


def _handler(model, queue=None, effects=None, clock=None, policy=None, crash=None):
    queue = queue if queue is not None else MemoryQueue()
    handler = EventHandler(
        queue,
        effects if effects is not None else MemoryEffects(),
        TicketExtractor(model),
        clock or FixedClock(),
        policy or RetryPolicy(),
        rng=random.Random(1),
        crash_at=crash or (lambda point: None),
    )
    return handler, queue


def test_a_new_event_is_extracted_applied_once_and_acknowledged():
    effects = MemoryEffects()
    queue = MemoryQueue()
    queue.put("e-1", "x")
    handler, _ = _handler(ScriptedModel(VALID), queue, effects)
    assert handler.handle(delivery()) == PROCESSED
    assert effects.processed["e-1"].intent == "cancel" and queue.acked == [1]


def test_a_delivery_of_an_event_that_was_already_applied_skips_the_model_and_is_acknowledged():
    effects = MemoryEffects()
    model = ScriptedModel(VALID)
    handler, queue = _handler(model, effects=effects)
    queue.put("e-1", "x")
    handler.handle(delivery())
    queue.put("e-1", "x")
    assert handler.handle(delivery(delivery_id=2)) == DUPLICATE
    assert len(model.calls) == 1 and len(effects.processed) == 1


def test_a_twin_delivery_that_commits_first_makes_this_one_a_duplicate():
    class RacingEffects(MemoryEffects):
        def is_processed(self, event_id: str) -> bool:
            return False

    effects = RacingEffects()
    handler, _ = _handler(ScriptedModel(VALID, VALID), effects=effects)
    assert handler.handle(delivery()) == PROCESSED
    assert handler.handle(delivery(delivery_id=2)) == DUPLICATE
    assert len(effects.processed) == 1


def test_the_model_runs_before_the_effects_and_the_crash_points_are_reported_in_order():
    points: list[str] = []
    handler, _ = _handler(ScriptedModel(VALID), crash=lambda point: points.append(point))
    handler.handle(delivery())
    assert points == ["after_model", "after_commit"]


def test_a_crash_after_the_model_call_leaves_nothing_behind_and_a_crash_after_the_commit_leaves_one_ticket():
    class CrashError(Exception):
        pass

    def die_at(target):
        def hook(point):
            if point == target:
                raise CrashError

        return hook

    effects, queue = MemoryEffects(), MemoryQueue()
    queue.put("e-1", "x")
    handler, _ = _handler(ScriptedModel(VALID), queue, effects, crash=die_at("after_model"))
    with pytest.raises(CrashError):
        handler.handle(delivery())
    assert effects.processed == {} and queue.acked == []
    survivor, _ = _handler(ScriptedModel(VALID), queue, effects, crash=die_at("after_commit"))
    with pytest.raises(CrashError):
        survivor.handle(delivery())
    assert list(effects.processed) == ["e-1"] and queue.acked == []
    again, _ = _handler(ScriptedModel(), queue, effects)
    assert again.handle(delivery()) == DUPLICATE and queue.acked == [1] and len(effects.processed) == 1


@pytest.mark.parametrize(
    ("payload", "reason"),
    [("{broken", "malformed_event"), (json.dumps({"event_id": "e-1", "body": "x" * 100_001}), "event_too_large")],
)
def test_a_poison_event_is_dead_lettered_at_once_with_its_reason_and_the_model_is_never_called(payload, reason):
    model = ScriptedModel()
    handler, queue = _handler(model)
    queue.put("e-1", payload)
    bad = delivery()
    bad = type(bad)(bad.delivery_id, bad.event_id, payload, bad.received_at, 1)
    assert handler.handle(bad) == DEAD
    assert queue.dead[0][1] == reason and model.calls == []


def test_a_schema_failure_after_one_repair_is_dead_lettered_after_exactly_one_attempt():
    handler, queue = _handler(ScriptedModel("nope", "still nope"))
    queue.put("e-1", "x")
    assert handler.handle(delivery(attempts=1)) == DEAD
    assert queue.dead[0][1] == "permanent_error" and "after one repair" in queue.dead[0][2] and queue.retries == []


def test_a_retryable_error_is_retried_with_a_jittered_delay_that_grows_until_the_attempts_run_out():
    queue = MemoryQueue()
    queue.put("e-1", "x")
    delays = []
    for attempt in range(1, 5):
        handler, _ = _handler(
            ScriptedModel(RetryableModelError("429")),
            queue,
            policy=RetryPolicy(max_attempts=5, base_seconds=1.0, cap_seconds=10.0),
        )
        assert handler.handle(delivery(attempts=attempt)) == RETRY
        delays.append(queue.retries[-1][1])
    assert all(0 <= delay <= min(10.0, 2 ** (attempt)) for attempt, delay in enumerate(delays))
    handler, _ = _handler(ScriptedModel(RetryableModelError("429")), queue, policy=RetryPolicy(max_attempts=5))
    assert handler.handle(delivery(attempts=5)) == DEAD and queue.dead[-1][1] == "attempts_exhausted"


def test_an_error_a_retry_cannot_fix_is_parked_without_retrying():
    handler, queue = _handler(ScriptedModel(ModelCallError("401")))
    assert handler.handle(delivery()) == DEAD and queue.dead[0][1] == "permanent_error" and queue.retries == []


def test_an_event_that_waited_longer_than_its_deadline_is_parked_before_the_model_is_called():
    clock = FixedClock()
    clock.advance(600)
    model = ScriptedModel()
    handler, queue = _handler(model, clock=clock, policy=RetryPolicy(event_deadline_seconds=300))
    assert handler.handle(delivery()) == DEAD and queue.dead[0][1] == "deadline_exceeded" and model.calls == []


def test_extraction_repairs_once_and_a_repair_that_works_counts_two_calls():
    from inbox_worker.application.extraction import TicketExtractor as Extractor

    model = ScriptedModel("{intent:", VALID)
    result = Extractor(model).extract("Please cancel order 4417.")
    assert result.calls == 2 and "Your reply was not a valid ticket" in model.calls[1]


def test_the_worker_processes_the_queue_until_idle_and_survives_an_unexpected_failure():
    queue, effects = MemoryQueue(), MemoryEffects()
    for number in range(4):
        queue.put(f"e-{number}", json.dumps({"event_id": f"e-{number}", "body": "Please cancel order 4417."}))
    model = ScriptedModel(*[VALID] * 4)
    handler, _ = _handler(model, queue, effects)
    outcomes = Worker(
        queue, handler, concurrency=2, lease_seconds=5, stop_requested=lambda: False, wait=lambda s: False
    ).run(until_idle=True)
    assert outcomes[PROCESSED] == 4 and len(effects.processed) == 4

    class Broken(MemoryEffects):
        def is_processed(self, event_id: str) -> bool:
            raise RuntimeError("database gone")

    broken_queue = MemoryQueue()
    broken_queue.put("e-1", json.dumps({"event_id": "e-1", "body": "x"}))
    broken, _ = _handler(ScriptedModel(), broken_queue, Broken())
    stops = iter([False, True])
    outcomes = Worker(
        broken_queue, broken, concurrency=1, lease_seconds=5, stop_requested=lambda: next(stops), wait=lambda s: False
    ).run()
    assert outcomes["error"] == 1


def test_the_worker_waits_and_retries_when_the_queue_is_unreachable():
    class Flaky(MemoryQueue):
        failures = 2

        def claim(self, limit, lease_seconds):
            if self.failures:
                self.failures -= 1
                raise ConnectionError("database restarting")
            return super().claim(limit, lease_seconds)

    queue = Flaky()
    queue.put("e-1", json.dumps({"event_id": "e-1", "body": "Please cancel order 4417."}))
    effects = MemoryEffects()
    handler, _ = _handler(ScriptedModel(VALID), queue, effects)
    waits: list[float] = []
    outcomes = Worker(
        queue,
        handler,
        concurrency=1,
        lease_seconds=5,
        stop_requested=lambda: False,
        wait=_recorder(waits),
        idle_poll_seconds=0.5,
    ).run(until_idle=True)
    assert outcomes["queue_error"] == 2 and outcomes[PROCESSED] == 1 and len(effects.processed) == 1
    assert waits == [1.0, 2.0]


def test_a_stop_request_ends_the_loop_after_the_work_in_flight():
    queue = MemoryQueue()
    handler, _ = _handler(ScriptedModel())
    waits: list[float] = []
    outcomes = Worker(
        queue,
        handler,
        concurrency=1,
        lease_seconds=5,
        stop_requested=lambda: len(waits) >= 2,
        wait=_recorder(waits),
    ).run()
    assert outcomes == {} and len(waits) == 2


class _Outbox:
    def __init__(self):
        self.rows = [(1, "e-1", "acknowledge"), (2, "e-2", "acknowledge")]
        self.sent = []

    def unsent(self, limit):
        return [row for row in self.rows if row[0] not in self.sent][:limit]

    def mark_sent(self, outbox_id):
        self.sent.append(outbox_id)


class _Gateway:
    def __init__(self):
        self.mail = []

    def send(self, event_id, kind):
        if event_id in self.mail:
            raise DuplicateSendError(event_id)
        self.mail.append(event_id)


def test_the_outbox_relay_sends_each_acknowledgment_once_and_tolerates_a_send_that_happened_before_a_crash():
    outbox, gateway = _Outbox(), _Gateway()
    gateway.mail.append("e-1")
    assert OutboxRelay(outbox, gateway).run_once() == 2
    assert gateway.mail == ["e-1", "e-2"] and outbox.sent == [1, 2]
    assert OutboxRelay(outbox, gateway).run_once() == 0


def test_the_generated_inbox_has_the_planted_duplicates_and_poison_and_is_the_same_every_time():
    inbox = generate_events()
    assert len({event_id for event_id, _ in inbox.deliveries}) == 1000 and len(inbox.deliveries) == 1020
    assert len(inbox.duplicates) == 20 and len(inbox.poison) == 10
    assert sorted(inbox.poison.values()).count("too_large") == 3
    assert generate_events().deliveries == inbox.deliveries
    seen: dict[str, list[str]] = {}
    for event_id, payload in inbox.deliveries:
        seen.setdefault(event_id, []).append(payload)
    assert {event_id for event_id, payloads in seen.items() if len(payloads) == 2} == set(inbox.duplicates)
    assert all(
        len(payload) > 300_000 for event_id, payload in inbox.deliveries if inbox.poison.get(event_id) == "too_large"
    )
