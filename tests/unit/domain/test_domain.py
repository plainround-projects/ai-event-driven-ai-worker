import base64
import json
import random

import pytest

from inbox_worker.domain.backoff import backoff_delay
from inbox_worker.domain.errors import PermanentEventError, ReplyInvalidError
from inbox_worker.domain.events import MAX_EMAIL_BYTES, event_id_of, parse_event
from inbox_worker.domain.signature import BAD_TIMESTAMP, MAX_AGE_SECONDS, TAMPERED, TOO_OLD, sign, verify
from inbox_worker.domain.stats import percentile
from inbox_worker.domain.ticket import Ticket

SECRET = b"unit-test-secret-0123456789"
BODY = '{"event_id": "e-001", "body": "Please cancel order 4417"}'
NOW = 1_800_000_000.0


def test_a_valid_request_passes_a_tampered_body_fails_on_signature_and_an_old_one_fails_on_age():
    signature = sign(SECRET, NOW, BODY)
    assert verify(SECRET, str(NOW), BODY, signature, NOW) == (True, "ok")
    assert verify(SECRET, str(NOW), BODY.replace("4417", "9999"), signature, NOW) == (False, TAMPERED)
    old = NOW - 400
    assert verify(SECRET, str(old), BODY, sign(SECRET, old, BODY), NOW) == (False, TOO_OLD)
    assert verify(SECRET, "yesterday", BODY, signature, NOW) == (False, BAD_TIMESTAMP)
    assert verify(b"another-secret-0123456789", str(NOW), BODY, signature, NOW)[1] == TAMPERED


def test_the_timestamp_is_part_of_what_is_signed_so_a_captured_body_cannot_be_replayed_with_a_new_time():
    signature = sign(SECRET, NOW, BODY)
    assert verify(SECRET, str(NOW + 10), BODY, signature, NOW + 10) == (False, TAMPERED)
    assert verify(SECRET, str(NOW - MAX_AGE_SECONDS), BODY, sign(SECRET, NOW - MAX_AGE_SECONDS, BODY), NOW)[0]


def test_a_valid_event_is_parsed_from_text_or_from_base64():
    assert parse_event(BODY).body == "Please cancel order 4417"
    encoded = base64.b64encode("Please cancel order 4417 ünï".encode()).decode()
    assert parse_event(json.dumps({"event_id": " e-2 ", "body_b64": encoded})).event_id == "e-2"


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        ('{"event_id": "e-1", "body": ', "malformed_event"),
        ("[1, 2]", "malformed_event"),
        ('{"event_id": "", "body": "x"}', "malformed_event"),
        ('{"event_id": "e-1"}', "malformed_event"),
        ('{"event_id": "e-1", "body_b64": "!!not base64!!"}', "malformed_event"),
        (json.dumps({"event_id": "e-1", "body_b64": base64.b64encode(b"ok \xff\xfe").decode()}), "bad_encoding"),
        (json.dumps({"event_id": "e-1", "body": "x" * (MAX_EMAIL_BYTES + 1)}), "event_too_large"),
    ],
)
def test_an_event_that_can_never_succeed_is_permanent_with_a_reason_a_person_can_act_on(payload, reason):
    with pytest.raises(PermanentEventError) as caught:
        parse_event(payload)
    assert caught.value.reason == reason and str(caught.value)


def test_an_unparsable_payload_is_filed_under_a_stable_placeholder_id():
    assert event_id_of(BODY) == "e-001"
    placeholder = event_id_of("{broken")
    assert placeholder.startswith("unparsed-") and placeholder == event_id_of("{broken")


def test_backoff_uses_full_jitter_and_is_capped():
    rng = random.Random(1)
    delays = [backoff_delay(attempt, 1.0, 8.0, rng) for attempt in (1, 2, 3, 4, 5, 6) for _ in range(200)]
    assert all(0 <= delay <= 8.0 for delay in delays)
    firsts = [backoff_delay(1, 1.0, 8.0, rng) for _ in range(200)]
    assert max(firsts) <= 1.0 and len({round(d, 3) for d in firsts}) > 50
    assert max(backoff_delay(6, 1.0, 8.0, rng) for _ in range(500)) > 4.0


def test_percentile_is_nearest_rank_and_safe_on_nothing():
    assert percentile([], 0.95) == 0.0 and percentile([5.0], 0.95) == 5.0
    assert percentile([float(n) for n in range(1, 101)], 0.95) == 95.0 and percentile([3.0, 1.0, 2.0], 0.5) == 2.0


def test_a_ticket_is_checked_field_by_field():
    good = {"intent": "cancel", "order_number": None, "sentiment": "neutral", "requested_action": "none"}
    assert Ticket.from_dict(good).intent == "cancel"
    for bad in (
        {**good, "intent": "buy"},
        {**good, "order_number": "12"},
        {**good, "sentiment": "angry"},
        {**good, "requested_action": "x"},
    ):
        with pytest.raises(ReplyInvalidError):
            Ticket.from_dict(bad)
