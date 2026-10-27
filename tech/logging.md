# Logging (Python logging and the logfmt line format)

## What it is

*Logging* means writing short messages about what a program is doing, so you can see afterwards what happened. Python's standard `logging` module gives each message a *level* (DEBUG, INFO, WARNING, ERROR), a *logger name* (which part of the program wrote it) and sends it to a *handler* (here the terminal's standard error). This repository formats each line as `key=value` pairs, a style called logfmt, which is easy to read and to search.

## Why this repository uses it

Operators need to see what the program did without seeing customers' text. One `key=value` line per event, with ids, sizes and timings, answers 'what happened and how long did it take' and can be searched with `grep`.

## Where it appears

| File | What it does with Logging (Python logging and the logfmt line format) |
| --- | --- |
| `src/inbox_worker/infrastructure/logging.py` | the formatter and the set-up function |
| `src/inbox_worker/interfaces/cli.py` | calls `configure_logging` once |

## How it works underneath

A *logger* is obtained by name: `logging.getLogger("package.module")`. Names form a tree separated by dots; a message sent to a child also reaches the parent's handlers. `logger.info("text", extra={"fields": {...}})` creates a *record*. A *formatter* turns a record into text; this repository's `LogfmtFormatter` writes `ts=... level=INFO logger=... msg="..." key=value`. A *handler* delivers the text; `configure_logging(level)` attaches one stream handler to the root logger at the chosen level, so messages below that level are dropped.

Logs never contain secrets or raw customer text in this repository: tests check that a log line carries fields (ids, counts, timings) but not the content of an email.

Because the format is `key=value`, a line can be searched with `grep "status=504"` and parsed by log tools without a special parser.

## Walkthrough of this repository's use

From `src/inbox_worker/infrastructure/logging.py`:

```python
"""Structured logging: one logfmt line per event. Prompt and completion text is never logged at INFO."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, TextIO


def _quote(value: object) -> str:
    text = str(value)
    return json.dumps(text) if not text or any(char in text for char in ' ="\n') else text


class LogfmtFormatter(logging.Formatter):
    """Format a log record as one logfmt line, with the record's extra fields as key=value pairs."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")
        parts = [
            f"ts={timestamp}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f"msg={_quote(record.getMessage())}",
        ]
        parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())
        if record.exc_info:
            parts.append(f"exc={_quote(self.formatException(record.exc_info))}")
        return " ".join(parts)


def fields(**values: Any) -> dict[str, Any]:
    """Use as `logger.info("message", extra=fields(order_id=...))` to attach key=value pairs."""
    return {"fields": values}


def configure_logging(level: str, stream: TextIO | None = None) -> None:
    """Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."""
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(LogfmtFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level)
    for noisy in ("httpx", "httpcore", "anthropic", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(max(logging.getLevelName(level), logging.WARNING))
```

- `"""Structured logging: one logfmt line per event. Prompt and completion text is never logged at INFO."""`: The module docstring (the text in triple quotes at the top). It says what the module is for and promises that prompt and completion text is not logged at INFO level.
- `from __future__ import annotations`: Makes type hints be stored as text and evaluated later. It lets hints refer to things defined further down and costs nothing at run time.
- `import json`: Brings in the standard `json` module; here only to quote text safely.
- `import logging`: Brings in Python's standard logging module.
- `import sys`: Brings in `sys`, which gives access to the standard error stream (`sys.stderr`).
- `from datetime import UTC, datetime`: `datetime` is Python's date-and-time type. `UTC` is the time zone with no offset; using it keeps every timestamp comparable.
- `from typing import Any, TextIO`: `Any` is the type that accepts anything. `TextIO` is the type of an open text stream. Both are only used in hints.
- `def _quote(value: object) -> str:`: A helper function. The leading underscore says it is private to this module. It takes any value and returns text.
- `text = str(value)`: Turns the value into text.
- `return json.dumps(text) if not text or any(char in text for char in ' ="\n') else text`: If the text is empty or contains a space, `=`, a double quote or a newline, wrap it in double quotes with JSON escaping, so `key=value` pairs stay unambiguous; otherwise return it unchanged. `any(char in text for char in ' ="\n')` is a *generator expression*: it checks the characters one at a time and stops at the first one that matches.
- `class LogfmtFormatter(logging.Formatter):`: A class that *inherits* from `logging.Formatter`: it is a Formatter with some behaviour changed. A formatter's job is to turn a log record into text.
- `"""Format a log record as one logfmt line, with the record's extra fields as key=value pairs."""`: The class docstring.
- `def format(self, record: logging.LogRecord) -> str:`: The method the logging system calls for every record. `self` is the formatter object; `record` carries the message, the level, the time and the extra fields. It returns the finished line.
- `timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")`: Turns the record's creation time (seconds since 1970) into a UTC date and time, written in ISO form with milliseconds, for example `2026-10-27T03:57:25.509+00:00`.
- `parts = [`: Starts a list of the first four `key=value` pieces.
- `f"ts={timestamp}",`: An *f-string*: text with `{...}` holes filled by values. This piece is the time.
- `f"level={record.levelname}",`: The level name, such as INFO or WARNING.
- `f"logger={record.name}",`: The name of the logger that wrote the message.
- `f"msg={_quote(record.getMessage())}",`: The message text, quoted if needed.
- `parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())`: Adds one `key=value` piece for every extra field. `getattr(record, "fields", {})` reads the attribute `fields` from the record, or an empty dict if there is none. The expression inside is a *generator expression* that builds one piece per key and value.
- `if record.exc_info:`: If the record came with an exception (a crash being reported), include it.
- `parts.append(f"exc={_quote(self.formatException(record.exc_info))}")`: Adds the exception's text (traceback), quoted, as `exc=...`.
- `return " ".join(parts)`: Joins all pieces with single spaces into one line.
- `def fields(**values: Any) -> dict[str, Any]:`: A function that takes any number of named arguments (`**values` collects them into a dict). It exists so call sites can write `fields(run_id="x", status=200)`.
- `` """Use as `logger.info("message", extra=fields(order_id=...))` to attach key=value pairs.""" ``: The docstring shows the intended use.
- `return {"fields": values}`: Returns the dict `{"fields": {...}}`, which is exactly the shape the logging call's `extra=` argument needs.
- `def configure_logging(level: str, stream: TextIO | None = None) -> None:`: Sets up logging once. `level` is a name such as "INFO"; `stream` is where to write, defaulting to `None`, meaning standard error. `TextIO | None` means 'a stream or nothing'. `-> None` says it returns nothing.
- `` """Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.""" ``: The docstring.
- `handler = logging.StreamHandler(stream or sys.stderr)`: Creates a handler that writes to the chosen stream. `stream or sys.stderr` means: use `stream` if given, else standard error.
- `handler.setFormatter(LogfmtFormatter())`: Tells the handler to use the logfmt formatter above.
- `root = logging.getLogger()`: Gets the *root logger*, the ancestor of every logger, so one handler serves the whole program.
- `root.handlers[:] = [handler]`: Replaces the root logger's handlers with just this one. Assigning to `[:]` changes the list in place. Doing it this way makes the function safe to call twice.
- `root.setLevel(level)`: Drops messages less important than `level`.
- `for noisy in ("httpx", "httpcore", "anthropic", "uvicorn.access"):`: Loops over the names of four libraries that log a lot (`httpx`, `httpcore`, `anthropic`, `uvicorn.access`).
- `logging.getLogger(noisy).setLevel(max(logging.getLevelName(level), logging.WARNING))`: Sets those loggers to at least WARNING, so their routine messages (every request line, for example) do not drown the application's own. `logging.getLevelName(level)` turns the name into its number; `max(...)` picks the higher, that is the stricter, of the two.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
LOG_LEVEL=DEBUG .venv/bin/python -c "from inbox_worker.infrastructure.logging import configure_logging, fields; import logging; configure_logging('INFO'); logging.getLogger('demo').info('hello world', extra=fields(run_id='r 1', n=3))"
```

Prints one line such as `ts=2026-10-27T... level=INFO logger=demo msg="hello world" run_id="r 1" n=3` on standard error.

```bash
grep -rn 'LOGGER = ' src | head -3
```

Shows how modules obtain their logger.

## Mistakes people make

- Using `print` for operational messages; it has no level, no timestamp and cannot be turned down.
- Logging personal data or secrets. The fields are ids, sizes and timings.
- Building the message with an f-string before the level check. The call `logger.info("x %s", y)` defers formatting; the logging here passes fields instead.
- Configuring logging inside library code. Only `main` configures it, once.
- Logging inside tight loops at INFO, which makes real signals hard to see.

## Check yourself

1. What is a log level for?
   *Answer:* To say how important a message is, so output can be filtered (INFO, WARNING, ERROR...).
2. What is a logger name?
   *Answer:* A dotted name that says which part of the program wrote the message.
3. What is logfmt?
   *Answer:* A line format of `key=value` pairs.
4. What does a handler do?
   *Answer:* Delivers formatted records to a place, such as the terminal.
5. Why must logs avoid raw customer text?
   *Answer:* Logs are copied and kept; personal data does not belong there.

## Further reading

- [logging](https://docs.python.org/3.12/library/logging.html)
- [Logging HOWTO](https://docs.python.org/3.12/howto/logging.html)
- [logfmt](https://brandur.org/logfmt)
