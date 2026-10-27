"""Configuration from the environment, validated once at startup (twelve-factor). Secrets only from here."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from inbox_worker.infrastructure.environment import (
    ConfigurationError,
    read_choice,
    read_float,
    read_int,
    read_optional,
    read_text,
)


@dataclass(frozen=True, slots=True)
class Settings:
    """Everything the programs read from the environment."""

    log_level: str
    root: Path
    database_url: str
    webhook_secret: bytes
    model_adapter: str
    model_id: str
    anthropic_api_key: str | None
    cassette: Path
    fake_delay_seconds: float
    fake_error_rate: float
    fake_max_rps: float
    concurrency: int
    lease_seconds: float
    max_attempts: int
    backoff_base_seconds: float
    backoff_cap_seconds: float
    event_deadline_seconds: float
    host: str
    port: int
    max_webhook_bytes: int

    @classmethod
    def from_environ(cls, environ: Mapping[str, str]) -> Settings:
        """Read and validate; raises `ConfigurationError` naming the first bad variable."""
        secret = read_text(environ, "WEBHOOK_SECRET", "unset-secret-for-tests-only-0000")
        if len(secret) < 16:
            raise ConfigurationError("WEBHOOK_SECRET must be at least 16 characters")
        user, database = read_text(environ, "POSTGRES_USER", "inbox"), read_text(environ, "POSTGRES_DB", "inbox")
        password, port = (
            read_text(environ, "POSTGRES_PASSWORD", "inbox-local-only"),
            read_int(environ, "POSTGRES_PORT", 5434),
        )
        return cls(
            log_level=read_choice(environ, "LOG_LEVEL", "INFO", frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})),
            root=Path(read_text(environ, "PROJECT_ROOT", ".")),
            database_url=read_text(
                environ, "DATABASE_URL", f"postgresql://{user}:{password}@localhost:{port}/{database}"
            ),
            webhook_secret=secret.encode(),
            model_adapter=read_choice(environ, "MODEL_ADAPTER", "fake", frozenset({"fake", "recorded", "claude"})),
            model_id=read_text(environ, "MODEL_ID", "claude-haiku-5-5"),
            anthropic_api_key=read_optional(environ, "ANTHROPIC_API_KEY"),
            cassette=Path(read_text(environ, "CASSETTE", "tests/fixtures/cassettes/smoke-v1.json")),
            fake_delay_seconds=read_float(environ, "FAKE_MODEL_DELAY_SECONDS", 0.0),
            fake_error_rate=read_float(environ, "FAKE_MODEL_ERROR_RATE", 0.0),
            fake_max_rps=read_float(environ, "FAKE_MODEL_MAX_RPS", 0.0),
            concurrency=read_int(environ, "CONCURRENCY", 5),
            lease_seconds=read_float(environ, "LEASE_SECONDS", 30.0, 0.1),
            max_attempts=read_int(environ, "MAX_ATTEMPTS", 5),
            backoff_base_seconds=read_float(environ, "BACKOFF_BASE_SECONDS", 0.5),
            backoff_cap_seconds=read_float(environ, "BACKOFF_CAP_SECONDS", 30.0),
            event_deadline_seconds=read_float(environ, "EVENT_DEADLINE_SECONDS", 300.0, 1.0),
            host=read_text(environ, "HOST", "127.0.0.1"),
            port=read_int(environ, "WEBHOOK_PORT", 8090),
            max_webhook_bytes=read_int(environ, "MAX_WEBHOOK_BYTES", 1_000_000),
        )
