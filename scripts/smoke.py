"""Run 20 sample emails through the extractor with the chosen model: the real-model smoke run of the lesson.

python scripts/smoke.py             # MODEL_ADAPTER=recorded (default) replays tests/fixtures/cassettes/smoke-v1.json
python scripts/smoke.py --author    # write that cassette from the fake model (not a model recording)
python scripts/smoke.py --record    # MODEL_ADAPTER=claude: call the real model and write live-v1.json (needs a key)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from inbox_worker.application.extraction import PROMPT_VERSION, SYSTEM
from inbox_worker.application.generate_events import generate_events
from inbox_worker.domain.errors import ModelCallError, PermanentEventError, RetryableModelError
from inbox_worker.infrastructure.cassette import RecordingModel, request_key
from inbox_worker.infrastructure.claude_model import ClaudeModel
from inbox_worker.infrastructure.fake_model import FakeModel
from inbox_worker.infrastructure.settings import Settings
from inbox_worker.interfaces.wiring import build_extractor, build_model

ROOT = Path(__file__).resolve().parents[1]
CASSETTE = ROOT / "tests/fixtures/cassettes/smoke-v1.json"


def emails() -> list[str]:
    """The first 20 healthy sample emails."""
    inbox = generate_events(200, poison_rate=0.0, duplicate_rate=0.0)
    return [json.loads(payload)["body"] for _, payload in inbox.deliveries[:20]]


def author() -> None:
    """Write the cassette from the fake model."""
    fake = FakeModel()
    entries = {}
    for email in emails():
        reply = fake.complete(SYSTEM, email, PROMPT_VERSION)
        entries[request_key("authored-fake-model", SYSTEM, email, PROMPT_VERSION)] = {
            "text": reply.text,
            "input_tokens": reply.input_tokens,
            "output_tokens": reply.output_tokens,
        }
    document = {
        "provenance": "authored by scripts/smoke.py --author from the fake model; not a model recording. Replace with `make record`.",
        "model": "authored-fake-model",
        "entries": entries,
    }
    CASSETTE.parent.mkdir(parents=True, exist_ok=True)
    CASSETTE.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(entries)} replies to {CASSETTE.relative_to(ROOT)}")


def run(record: bool) -> int:
    """Extract all 20 emails and print the tickets and the totals."""
    settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str(ROOT)})
    model = build_model(settings)
    if record:
        model = RecordingModel(
            ClaudeModel(settings.model_id, settings.anthropic_api_key),
            ROOT / "tests/fixtures/cassettes/live-v1.json",
            settings.model_id,
            f"recorded from {settings.model_id}",
        )
    extractor = build_extractor(settings, model)
    done = calls = 0
    for email in emails():
        try:
            result = extractor.extract(email)
        except (PermanentEventError, RetryableModelError, ModelCallError) as error:
            print(f"FAILED {email[:50]!r}: {error}")
            continue
        done += 1
        calls += result.calls
        print(
            f"{result.ticket.intent:12} {result.ticket.order_number} {result.ticket.sentiment:8} {result.ticket.requested_action}"
        )
    print(f"{done}/20 emails gave a ticket in {calls} model calls (adapter: {settings.model_adapter})")
    return 0 if done == 20 else 1


if __name__ == "__main__":
    if "--author" in sys.argv:
        author()
        sys.exit(0)
    sys.exit(run("--record" in sys.argv))
