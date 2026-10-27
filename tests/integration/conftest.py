"""A real PostgreSQL (docker compose: make up). The schema is rebuilt from sql/ once per session and emptied per test."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from inbox_worker.infrastructure.postgres import Database, apply_scripts, reset_tables
from inbox_worker.infrastructure.settings import Settings
from tests.conftest import REPO


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Settings from the environment (the .env values `make` exports) with this repository as the root."""
    return Settings.from_environ({**os.environ, "PROJECT_ROOT": str(REPO)})


@pytest.fixture(scope="session")
def database(settings: Settings) -> Iterator[Database]:
    """The pool; skips the whole suite when PostgreSQL is not up."""
    db = Database(settings.database_url, max_connections=16)
    try:
        db.ping()
    except Exception:
        pytest.skip("PostgreSQL is not running; run `make up`")
    apply_scripts(db, REPO / "sql")
    yield db
    db.close()


@pytest.fixture
def clean(database: Database) -> Database:
    """The database with every table emptied."""
    reset_tables(database, REPO / "sql")
    return database
