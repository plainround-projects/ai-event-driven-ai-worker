"""Compose the database, model, handler, worker and relay the settings ask for."""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from inbox_worker.application.extraction import TicketExtractor
from inbox_worker.application.handler import EventHandler, RetryPolicy
from inbox_worker.application.ports import ChatModel
from inbox_worker.infrastructure.cassette import RecordedModel
from inbox_worker.infrastructure.claude_model import ClaudeModel
from inbox_worker.infrastructure.clock import SystemClock
from inbox_worker.infrastructure.fake_model import FakeModel
from inbox_worker.infrastructure.postgres import (
    Database,
    FakeMailSender,
    PostgresEffects,
    PostgresOutbox,
    PostgresQueue,
    PostgresReports,
)
from inbox_worker.infrastructure.prompt_file import read_prompt
from inbox_worker.infrastructure.settings import Settings


@dataclass(frozen=True, slots=True)
class Components:
    """Everything a command needs, built once."""

    settings: Settings
    database: Database
    queue: PostgresQueue
    effects: PostgresEffects
    outbox: PostgresOutbox
    mail: FakeMailSender
    reports: PostgresReports


def build_components(settings: Settings) -> Components:
    """Wire the PostgreSQL adapters over one pool sized for the worker's concurrency."""
    database = Database(settings.database_url, max_connections=settings.concurrency + 6)
    return Components(
        settings,
        database,
        PostgresQueue(database),
        PostgresEffects(database),
        PostgresOutbox(database),
        FakeMailSender(database),
        PostgresReports(database),
    )


def build_model(settings: Settings) -> ChatModel:
    """The fake model (load tests), the recorded adapter (offline smoke run), or Claude."""
    if settings.model_adapter == "claude":
        return ClaudeModel(settings.model_id, settings.anthropic_api_key)
    if settings.model_adapter == "recorded":
        return RecordedModel(settings.root / settings.cassette)
    return FakeModel(
        delay_seconds=settings.fake_delay_seconds, error_rate=settings.fake_error_rate, max_rps=settings.fake_max_rps
    )


def retry_policy(settings: Settings) -> RetryPolicy:
    """The retry settings as a value."""
    return RetryPolicy(
        settings.max_attempts,
        settings.backoff_base_seconds,
        settings.backoff_cap_seconds,
        settings.event_deadline_seconds,
    )


def crash_hook_from_environment() -> Callable[[str], None]:
    """For the crash tests: `CRASH_AT=<point>` and `CRASH_AFTER=<n>` kill the process (exit code 137, as SIGKILL would)
    the n-th time the handler reaches that point. Unset, it does nothing."""
    point, after = os.environ.get("CRASH_AT"), int(os.environ.get("CRASH_AFTER", "1"))
    seen = {"count": 0}

    def hook(reached: str) -> None:
        if point and reached == point:
            seen["count"] += 1
            if seen["count"] >= after:
                os._exit(137)

    return hook


PROMPT_FILE = Path("prompts/extract.v1.md")


def build_extractor(settings: Settings, model: ChatModel) -> TicketExtractor:
    """The extractor over the model, with the prompt text and version read from the versioned prompt file."""
    prompt = read_prompt(settings.root / PROMPT_FILE)
    return TicketExtractor(model, prompt.text, prompt.version)


def build_handler(
    components: Components, model: ChatModel, crash_at: Callable[[str], None] | None = None
) -> EventHandler:
    """The event handler over the components' queue and effects store."""
    settings = components.settings
    return EventHandler(
        components.queue,
        components.effects,
        build_extractor(settings, model),
        SystemClock(),
        retry_policy(settings),
        crash_at=crash_at or (lambda point: None),
    )
