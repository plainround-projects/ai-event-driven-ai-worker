"""The lesson's Done-when lines through the command-line programs against PostgreSQL (make up first)."""

import os

import pytest

from inbox_worker.application.generate_events import generate_events
from inbox_worker.infrastructure.postgres import Database, apply_scripts
from inbox_worker.infrastructure.settings import Settings
from inbox_worker.interfaces import cli
from inbox_worker.interfaces.wiring import build_components
from tests.conftest import REPO

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def components():
    settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str(REPO), "CONCURRENCY": "8"})
    database = Database(settings.database_url)
    try:
        database.ping()
    except Exception:
        pytest.skip("PostgreSQL is not running; run `make up`")
    apply_scripts(database, REPO / "sql")
    database.close()
    built = build_components(settings)
    yield built
    built.database.close()


def test_step_1_a_tampered_body_and_a_replayed_request_get_401_and_the_endpoint_p95_stays_under_100_ms(
    components, capsys
):
    assert cli.main(["reset"]) == 0
    assert cli.main(["bench-webhook"]) == 0
    out = capsys.readouterr().out
    assert "tampered body -> 401" in out and "replayed old request -> 401" in out and "p95" in out


def test_steps_2_and_4_the_replayed_inbox_creates_no_new_ticket_and_every_poison_event_is_parked_with_a_reason(
    components, capsys
):
    assert cli.main(["reset"]) == 0
    inbox = generate_events()
    healthy = {event_id for event_id, _ in inbox.deliveries} - set(inbox.poison)
    assert cli.main(["enqueue"]) == 0
    assert cli.main(["worker", "--until-idle"]) == 0
    first = components.reports.counts()
    assert first["tickets"] == len(healthy) == 990 and first["dead_letters"] == 10
    assert cli.main(["enqueue"]) == 0
    assert cli.main(["worker", "--until-idle"]) == 0
    assert cli.main(["relay", "--once"]) == 0
    second = components.reports.counts()
    assert (second["tickets"], second["outbox"], second["mails_sent"]) == (990, 990, 990)
    assert second["dead_letters"] == 20
    assert sorted(components.reports.ticket_event_ids()) == sorted(healthy)
    reasons = {reason for _, _, reason, *_ in components.reports.dead_events()}
    assert reasons == {"malformed_event", "event_too_large", "bad_encoding", "permanent_error"}
    capsys.readouterr()
    assert cli.main(["status"]) == 0


def test_step_4_redriving_a_fixed_dead_letter_processes_it_once(components):
    dead = next(row for row in components.reports.dead_events() if row[2] == "event_too_large")
    assert cli.main(["redrive", str(dead[0])]) == 0
    assert cli.main(["redrive", str(dead[0])]) == 1


@pytest.mark.parametrize("point", ["after_model", "after_commit"])
def test_step_5_after_a_real_process_kill_no_event_is_lost_and_none_has_two_tickets(components, point, capsys):
    assert cli.main(["crash-test", "--at", point]) == 0
    out = capsys.readouterr().out
    assert "crash run exit 137" in out and "lost: []; duplicated tickets: 0" in out


def test_step_6_the_burst_reports_two_concurrency_settings_and_the_queue_drains(components, capsys):
    assert (
        cli.main(
            [
                "burst",
                "--events",
                "100",
                "--seconds",
                "3",
                "--concurrency",
                "5",
                "20",
                "--delay",
                "0.1",
                "--max-rps",
                "30",
            ]
        )
        == 0
    )
    rows = [
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("| ") and "---" not in line and "Concurrency" not in line
    ]
    assert len(rows) == 2 and all(row.rstrip().endswith("True |") for row in rows)
