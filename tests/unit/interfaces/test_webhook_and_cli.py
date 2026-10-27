import json

import pytest
from fastapi.testclient import TestClient

from inbox_worker.domain.signature import sign
from inbox_worker.interfaces import cli
from inbox_worker.interfaces.webhook import create_app
from tests.unit.application.fakes import MemoryQueue

SECRET = b"unit-test-secret-0123456789"
NOW = 1_800_000_000.0
BODY = json.dumps({"event_id": "e-001", "body": "Please cancel order 4417"})


def _client(queue=None, ready=True, max_bytes=1_000_000):
    queue = queue if queue is not None else MemoryQueue()
    app = create_app(queue, SECRET, max_bytes, lambda: ready, clock=lambda: NOW)
    return TestClient(app), queue


def _headers(body=BODY, at=NOW):
    return {"X-Timestamp": str(at), "X-Signature": sign(SECRET, at, body)}


def test_a_signed_event_is_queued_and_answered_with_202():
    client, queue = _client()
    response = client.post("/webhook/email", content=BODY, headers=_headers())
    assert response.status_code == 202 and response.json() == {"delivery_id": 1}
    assert queue.items[1]["event_id"] == "e-001" and queue.items[1]["payload"] == BODY


def test_a_tampered_body_and_a_replayed_old_request_both_get_401_with_different_reasons():
    client, queue = _client()
    tampered = client.post("/webhook/email", content=BODY.replace("4417", "9999"), headers=_headers())
    replayed = client.post("/webhook/email", content=BODY, headers=_headers(at=NOW - 400))
    assert (tampered.status_code, replayed.status_code) == (401, 401)
    assert "signature mismatch" in tampered.json()["error"] and "too old" in replayed.json()["error"]
    assert client.post("/webhook/email", content=BODY).status_code == 401
    assert queue.items == {}


def test_a_body_over_the_limit_is_refused_with_413_and_a_300_kb_event_under_it_is_queued():
    client, _ = _client(max_bytes=1000)
    assert client.post("/webhook/email", content="x" * 5000, headers=_headers("x" * 5000)).status_code == 413
    client, _ = _client()
    big = json.dumps({"event_id": "e-2", "body": "y" * 300_000})
    assert client.post("/webhook/email", content=big, headers=_headers(big)).status_code == 202


def test_a_payload_that_is_not_json_is_still_queued_under_a_placeholder_id_so_it_can_be_parked():
    client, queue = _client()
    assert client.post("/webhook/email", content="{broken", headers=_headers("{broken")).status_code == 202
    assert queue.items[1]["event_id"].startswith("unparsed-")


def test_health_and_readiness():
    client, _ = _client()
    assert client.get("/healthz").json() == {"status": "ok"} and client.get("/readyz").status_code == 200
    down, _ = _client(ready=False)
    assert down.get("/readyz").status_code == 503


def test_the_webhook_demo_prints_the_three_verdicts(monkeypatch, capsys):
    assert cli.main(["webhook-demo"]) == 0
    out = capsys.readouterr().out
    assert "valid request: (True, 'ok')" in out and "signature mismatch" in out and "request too old" in out


def test_a_bad_environment_stops_with_exit_code_two(monkeypatch, capsys):
    monkeypatch.setenv("WEBHOOK_SECRET", "short")
    assert cli.main(["status"]) == 2
    assert "WEBHOOK_SECRET" in capsys.readouterr().err


@pytest.mark.parametrize("command", ["db", "worker", "burst"])
def test_each_database_command_is_a_known_subcommand(command):
    assert cli._parser().parse_args([command]).command == command
