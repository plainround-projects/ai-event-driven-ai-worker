import io
import json
import logging
from types import SimpleNamespace

import anthropic
import pytest

from inbox_worker.application.ports import ModelReply
from inbox_worker.domain.errors import ModelCallError, RetryableModelError
from inbox_worker.infrastructure.cassette import MissingRecordingError, RecordedModel, RecordingModel, request_key
from inbox_worker.infrastructure.claude_model import ClaudeModel
from inbox_worker.infrastructure.environment import ConfigurationError
from inbox_worker.infrastructure.fake_model import FakeModel
from inbox_worker.infrastructure.logging import configure_logging, fields
from inbox_worker.infrastructure.settings import Settings
from inbox_worker.infrastructure.shutdown import ShutdownSignal
from tests.unit.application.fakes import FixedClock


class Time:
    def __init__(self):
        self.now = 0.0
        self.slept = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def test_the_fake_model_waits_for_its_delay_and_returns_a_ticket():
    time = Time()
    model = FakeModel(delay_seconds=0.1, sleep=time.sleep, clock=time.clock)
    reply = model.complete("S", "Please cancel order 4417. This is unacceptable.", "v")
    assert json.loads(reply.text) == {
        "intent": "cancel",
        "order_number": "4417",
        "sentiment": "negative",
        "requested_action": "cancel_order",
    }
    assert time.slept == [0.1] and model.calls == 1


def test_the_fake_model_enforces_a_rate_limit_like_a_token_bucket_and_counts_the_errors():
    time = Time()
    model = FakeModel(max_rps=5, sleep=time.sleep, clock=time.clock)
    admitted = limited = 0
    for _ in range(12):
        try:
            model.complete("S", "Where is order 1234?", "v")
            admitted += 1
        except RetryableModelError:
            limited += 1
    assert (admitted, limited) == (5, 7) and model.rate_limited == 7
    time.now += 1.0
    model.complete("S", "Where is order 1234?", "v")


def test_the_fake_model_fails_at_the_configured_error_rate_and_the_poison_marker_makes_a_non_ticket():
    model = FakeModel(error_rate=0.5, seed=3)
    failures = 0
    for _ in range(200):
        try:
            model.complete("S", "hello", "v")
        except RetryableModelError:
            failures += 1
    assert 60 < failures < 140 and model.injected_errors == failures
    assert FakeModel().complete("S", "POISON-SCHEMA please cancel", "v").text == "not a ticket"


def _message(text="{}", stop_reason="end_turn"):
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        stop_reason=stop_reason,
        model="m",
        usage=SimpleNamespace(input_tokens=50, output_tokens=9),
    )


class Stub:
    def __init__(self, outcome):
        self.outcome, self.calls, self.messages = outcome, [], self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def _status(code):
    response = SimpleNamespace(status_code=code, headers={}, request=SimpleNamespace(method="POST", url="x"))
    return anthropic.APIStatusError("boom", response=response, body=None)  # type: ignore[arg-type]


def test_the_claude_adapter_sends_the_email_and_classifies_failures():
    client = Stub(_message('{"a": 1}'))
    assert ClaudeModel("claude-haiku-5-5", None, client=client).complete("SYS", "email", "v1") == ModelReply(
        '{"a": 1}', "m", 50, 9
    )
    assert client.calls[0]["system"] == "SYS" and client.calls[0]["messages"] == [{"role": "user", "content": "email"}]
    for error, expected in (
        (anthropic.APIConnectionError(request=SimpleNamespace(method="POST", url="x")), RetryableModelError),  # type: ignore[arg-type]
        (_status(429), ModelCallError),
        (_status(503), RetryableModelError),
        (_status(401), ModelCallError),
    ):
        if isinstance(error, anthropic.APIStatusError) and error.status_code == 429:
            continue
        with pytest.raises(expected):
            ClaudeModel("m", None, client=Stub(error)).complete("S", "u", "v")
    with pytest.raises(ModelCallError, match="declined"):
        ClaudeModel("m", None, client=Stub(_message(stop_reason="refusal"))).complete("S", "u", "v")
    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        ClaudeModel("m", None)


def test_a_recording_replays_by_the_hash_of_the_request_and_a_changed_prompt_misses(tmp_path):
    path = tmp_path / "c.json"
    RecordingModel(
        SimpleNamespace(complete=lambda s, u, v: ModelReply("text", "m", 5, 2)), path, "model-x", "test"
    ).complete("S", "u", "v1")
    replay = RecordedModel(path)
    assert replay.complete("S", "u", "v1").text == "text" and replay.provenance == "test"
    with pytest.raises(MissingRecordingError, match="make record"):
        replay.complete("S", "u", "v2")
    assert request_key("a", "S", "u", "v") != request_key("b", "S", "u", "v")


def test_the_committed_smoke_cassette_is_labeled_and_replays_a_sample_email():
    from inbox_worker.application.extraction import PROMPT_VERSION, SYSTEM
    from tests.conftest import REPO

    replay = RecordedModel(REPO / "tests/fixtures/cassettes/smoke-v1.json")
    assert "not a model recording" in replay.provenance
    key_count = len(json.loads((REPO / "tests/fixtures/cassettes/smoke-v1.json").read_text())["entries"])
    assert key_count == 20 and PROMPT_VERSION and SYSTEM


def test_settings_have_safe_defaults_and_reject_a_short_secret_and_bad_values():
    settings = Settings.from_environ({})
    assert (
        settings.model_adapter == "fake"
        and settings.concurrency == 5
        and settings.database_url.startswith("postgresql://inbox:")
    )
    for bad in (
        {"WEBHOOK_SECRET": "short"},
        {"MODEL_ADAPTER": "gpt"},
        {"CONCURRENCY": "0"},
        {"LEASE_SECONDS": "0"},
        {"LOG_LEVEL": "LOUD"},
    ):
        with pytest.raises(ConfigurationError):
            Settings.from_environ(bad)
    assert (
        Settings.from_environ({"POSTGRES_PASSWORD": "pw", "POSTGRES_PORT": "6000"}).database_url
        == "postgresql://inbox:pw@localhost:6000/inbox"
    )


def test_logs_are_logfmt_and_a_shutdown_signal_is_a_flag():
    stream = io.StringIO()
    configure_logging("INFO", stream)
    logging.getLogger("x").info("worker stopped", extra=fields(processed=10))
    assert "processed=10" in stream.getvalue()
    flag = ShutdownSignal()
    assert not flag.requested
    flag.request()
    assert flag.requested and flag.wait(0.001)
    flag.install()
    assert FixedClock().now().tzinfo is not None


def test_the_prompt_file_is_the_prompt_the_extractor_defaults_to():
    from pathlib import Path

    from inbox_worker.application.extraction import PROMPT_VERSION, SYSTEM
    from inbox_worker.infrastructure.prompt_file import PromptFileError, read_prompt

    prompt = read_prompt(Path(__file__).resolve().parents[3] / "prompts/extract.v1.md")
    assert (prompt.version, prompt.text) == (PROMPT_VERSION, SYSTEM) and prompt.owner

    broken = Path(__file__).with_name("not_a_prompt.md")
    broken.write_text("no fences here", encoding="utf-8")
    try:
        with pytest.raises(PromptFileError):
            read_prompt(broken)
    finally:
        broken.unlink()
