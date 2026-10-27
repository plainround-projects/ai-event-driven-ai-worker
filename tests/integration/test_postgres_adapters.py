import concurrent.futures
import json
import time

import psycopg
import pytest

from inbox_worker.application.extraction import TicketExtractor
from inbox_worker.application.handler import DEAD, DUPLICATE, PROCESSED, RETRY, EventHandler, RetryPolicy
from inbox_worker.application.outbox import OutboxRelay
from inbox_worker.application.worker import Worker
from inbox_worker.domain.ticket import Ticket
from inbox_worker.infrastructure.clock import SystemClock
from inbox_worker.infrastructure.fake_model import FakeModel
from inbox_worker.infrastructure.postgres import (
    FakeMailSender,
    PostgresEffects,
    PostgresOutbox,
    PostgresQueue,
    PostgresReports,
)

pytestmark = pytest.mark.integration
TICKET = Ticket("cancel", "4417", "neutral", "cancel_order")


def _payload(event_id, body="Please cancel order 4417."):
    return json.dumps({"event_id": event_id, "body": body})


def test_the_schema_has_the_tables_the_lesson_needs_and_rejects_bad_rows(clean):
    with clean.connection() as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            ).fetchall()
        }
        assert {"deliveries", "processed_events", "tickets", "outbox", "sent_mail", "dead_letters"} <= names
        with pytest.raises(psycopg.errors.CheckViolation):
            connection.execute("INSERT INTO deliveries (event_id, payload, status) VALUES ('e', 'p', 'weird')")
        with pytest.raises(psycopg.errors.ForeignKeyViolation):
            connection.execute(
                "INSERT INTO tickets (event_id, intent, sentiment, requested_action) VALUES ('nope', 'cancel', 'neutral', 'none')"
            )


def test_a_claim_hands_each_delivery_to_one_worker_and_an_expired_claim_is_handed_out_again(clean):
    queue = PostgresQueue(clean)
    for number in range(6):
        queue.put(f"e-{number}", _payload(f"e-{number}"))
    first, second = queue.claim(4, 30), queue.claim(4, 30)
    assert len(first) == 4 and len(second) == 2 and not {d.delivery_id for d in first} & {d.delivery_id for d in second}
    assert queue.claim(4, 30) == []
    queue.ack(first[0].delivery_id)
    short = PostgresQueue(clean)
    for delivery in second:
        short.retry(delivery.delivery_id, 0, "x")
    reclaimed = short.claim(10, 0.2)
    assert len(reclaimed) == 2 and all(d.attempts == 2 for d in reclaimed)
    time.sleep(0.4)
    again = short.claim(10, 30)
    assert {d.delivery_id for d in again} >= {d.delivery_id for d in reclaimed}


def test_concurrent_claims_never_return_the_same_delivery_twice(clean):
    queue = PostgresQueue(clean)
    for number in range(60):
        queue.put(f"e-{number}", "{}")
    with concurrent.futures.ThreadPoolExecutor(6) as pool:
        batches = list(pool.map(lambda _: queue.claim(10, 30), range(6)))
    ids = [d.delivery_id for batch in batches for d in batch]
    assert len(ids) == len(set(ids)) == 60


def test_applying_an_event_twice_leaves_one_ticket_one_outbox_row_and_reports_the_twin(clean):
    effects = PostgresEffects(clean)
    assert effects.apply("e-1", TICKET) is True
    assert effects.apply("e-1", TICKET) is False
    assert effects.is_processed("e-1") and not effects.is_processed("e-2")
    counts = PostgresReports(clean).counts()
    assert (counts["processed"], counts["tickets"], counts["outbox"]) == (1, 1, 1)


def test_two_threads_applying_the_same_event_at_once_produce_exactly_one_ticket(clean):
    effects = PostgresEffects(clean)
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda _: effects.apply("e-race", TICKET), range(8)))
    assert results.count(True) == 1 and PostgresReports(clean).counts()["tickets"] == 1


def test_the_full_path_processes_a_replay_with_no_new_ticket_and_no_second_acknowledgment(clean):
    queue, effects = PostgresQueue(clean), PostgresEffects(clean)
    handler = EventHandler(
        queue, effects, TicketExtractor(FakeModel()), SystemClock(), RetryPolicy(base_seconds=0.01, cap_seconds=0.05)
    )
    ids = [f"e-{n:02d}" for n in range(20)]
    for _ in range(2):
        for event_id in ids:
            queue.put(event_id, _payload(event_id))
        outcomes = Worker(
            queue,
            handler,
            concurrency=4,
            lease_seconds=30,
            stop_requested=lambda: False,
            wait=lambda s: False,
            idle_poll_seconds=0.01,
        ).run(until_idle=True)
        OutboxRelay(PostgresOutbox(clean), FakeMailSender(clean)).run_once(100)
        if _ == 0:
            assert outcomes[PROCESSED] == 20
        else:
            assert outcomes[DUPLICATE] == 20 and PROCESSED not in outcomes
    counts = PostgresReports(clean).counts()
    assert (counts["tickets"], counts["outbox"], counts["mails_sent"]) == (20, 20, 20)
    assert sorted(PostgresReports(clean).ticket_event_ids()) == ids


def test_the_mail_sender_refuses_a_second_send_of_one_acknowledgment_and_the_relay_tolerates_it(clean):
    PostgresEffects(clean).apply("e-1", TICKET)
    FakeMailSender(clean).send("e-1", "acknowledge")
    outbox = PostgresOutbox(clean)
    assert OutboxRelay(outbox, FakeMailSender(clean)).run_once() == 1
    assert outbox.unsent(10) == [] and PostgresReports(clean).counts()["mails_sent"] == 1


def test_poison_events_are_parked_with_a_reason_and_do_not_hold_up_the_events_behind_them(clean):
    queue = PostgresQueue(clean)
    queue.put("bad-1", '{"event_id": "bad-1", "body": ')
    queue.put("bad-2", json.dumps({"event_id": "bad-2", "body": "x" * 300_000}))
    for number in range(5):
        queue.put(f"ok-{number}", _payload(f"ok-{number}"))
    handler = EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())
    outcomes = Worker(
        queue,
        handler,
        concurrency=1,
        lease_seconds=30,
        stop_requested=lambda: False,
        wait=lambda s: False,
        idle_poll_seconds=0.01,
    ).run(until_idle=True)
    assert outcomes[DEAD] == 2 and outcomes[PROCESSED] == 5
    reasons = {event: reason for _, event, reason, *_ in PostgresReports(clean).dead_events()}
    assert reasons == {"bad-1": "malformed_event", "bad-2": "event_too_large"}


def test_a_rate_limited_event_is_retried_later_and_a_permanent_failure_is_parked_after_one_attempt(clean):
    queue = PostgresQueue(clean)
    queue.put("slow", _payload("slow"))
    handler = EventHandler(
        queue,
        PostgresEffects(clean),
        TicketExtractor(FakeModel(error_rate=1.0)),
        SystemClock(),
        RetryPolicy(base_seconds=0.01, cap_seconds=0.02),
    )
    delivery = queue.claim(1, 30)[0]
    assert handler.handle(delivery) == RETRY
    with clean.connection() as connection:
        status, available, error = connection.execute(
            "SELECT status, available_at > now() - interval '1 second', last_error FROM deliveries"
        ).fetchone()
    assert status == "queued" and "503" in error and available
    queue.put("poison", _payload("poison", "POISON-SCHEMA cancel order 4417"))
    parked = EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())
    time.sleep(0.1)
    for item in queue.claim(5, 30):
        if item.event_id == "poison":
            assert parked.handle(item) == DEAD
    assert [(row[2], row[3]) for row in PostgresReports(clean).dead_events()] == [("permanent_error", 1)]


def test_a_redriven_dead_letter_is_processed_exactly_once_through_the_normal_path(clean):
    queue = PostgresQueue(clean)
    queue.put("fixme", _payload("fixme", "POISON-SCHEMA cancel order 4417"))
    broken = EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())
    assert broken.handle(queue.claim(1, 30)[0]) == DEAD
    dead_id = PostgresReports(clean).dead_events()[0][0]
    with clean.connection() as connection:
        connection.execute(
            "UPDATE dead_letters SET payload = %s WHERE dead_id = %s",
            (_payload("fixme", "Please cancel order 4417."), dead_id),
        )
    assert queue.redrive(dead_id) is not None and queue.redrive(dead_id) is None
    fixed = EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())
    assert fixed.handle(queue.claim(1, 30)[0]) == PROCESSED
    assert PostgresReports(clean).counts()["tickets"] == 1 and PostgresReports(clean).dead_events() == []
