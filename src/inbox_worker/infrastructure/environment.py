"""Configuration helpers: read and validate environment variables once at startup (twelve-factor)."""

from __future__ import annotations

from collections.abc import Mapping


class ConfigurationError(ValueError):
    """An environment variable is missing or has an unusable value."""


def read_text(environ: Mapping[str, str], name: str, default: str | None = None) -> str:
    """A non-empty string variable, or `default`."""
    value = environ.get(name, default if default is not None else "").strip()
    if not value:
        raise ConfigurationError(f"{name} must be set and not empty")
    return value


def read_optional(environ: Mapping[str, str], name: str) -> str | None:
    """A string variable that may be absent or empty (for example an API key)."""
    value = environ.get(name, "").strip()
    return value or None


def read_int(environ: Mapping[str, str], name: str, default: int, minimum: int = 1) -> int:
    """An integer variable of at least `minimum`."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError:
        raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from None
    if value < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")
    return value


def read_float(environ: Mapping[str, str], name: str, default: float, minimum: float = 0.0) -> float:
    """A float variable of at least `minimum`."""
    raw = environ.get(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError:
        raise ConfigurationError(f"{name} must be a number, got {raw!r}") from None
    if value < minimum:
        raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")
    return value


def read_choice(environ: Mapping[str, str], name: str, default: str, choices: frozenset[str]) -> str:
    """A string variable restricted to `choices`."""
    value = environ.get(name, default).strip()
    if value not in choices:
        raise ConfigurationError(f"{name} must be one of {sorted(choices)}, got {value!r}")
    return value
