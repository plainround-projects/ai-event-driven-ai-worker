# pytest

## What it is

`pytest` is the most used Python test runner. A *test* is a small function that runs a piece of the program and checks the result with `assert`. `pytest` finds the tests, runs them, and tells you which passed and which failed and why.

## Why this repository uses it

The tests are the evidence for every claim in the README. They run offline against fakes, so they pass on any machine without a key. There are 7 test files; the Done-when lines of the lesson each have a test or a command.

## Where it appears

| File | What it does with pytest |
| --- | --- |
| `tests/` | the tests |
| `pyproject.toml` (`[tool.pytest.ini_options]`) | paths, options, markers |
| `Makefile` (`test`...) | the commands |

## How it works underneath

`pytest` looks in the folders named in `testpaths` for files called `test_*.py`, imports them, and treats every function called `test_*` as a test. A plain `assert x == y` is enough: `pytest` rewrites the assertion when the file is imported so that a failure prints the two values and where they differ.

A *fixture* is a function marked `@pytest.fixture` that prepares something a test needs (a database, a temporary folder). A test asks for it by naming it as a parameter, and `pytest` supplies it. `@pytest.mark.parametrize` runs one test with several inputs. A *marker* such as `@pytest.mark.live` labels a test so you can select or skip groups with `-m`. With `--strict-markers` a marker that is not registered in `pyproject.toml` is an error.

`pytest.raises(SomeError)` checks that code fails the way it should. `capsys` captures what a program prints so a test can check it. `monkeypatch` changes an environment variable or function for one test and undoes it afterwards. A test passes if it finishes without an exception; it fails on an exception or a failed `assert`.

## Walkthrough of this repository's use

### Where the tests live

| Folder | Test files | Examples |
| --- | --- | --- |
| `tests/unit/` | 4 | test_handler_worker.py, test_domain.py, test_adapters.py, test_webhook_and_cli.py |
| `tests/integration/` | 1 | test_postgres_adapters.py |
| `tests/e2e/` | 1 | test_done_when.py |
| `tests/live/` | 1 | test_claude_live.py |

### The settings

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers"
markers = [
    "live: calls the real model; needs ANTHROPIC_API_KEY and RUN_LIVE=1 (make test-live)",
    "integration: needs PostgreSQL from docker-compose.yml (make up)",
    "e2e: runs the lesson scenarios against PostgreSQL (make test-e2e)",
]
```

- `[tool.pytest.ini_options]`: Settings for `pytest`, the test runner.
- `testpaths = ["tests"]`: Look for tests in the `tests` folder when `pytest` runs with no arguments.
- `addopts = "-ra --strict-markers"`: Options added to every run. `-ra` prints a short reason for every test that did not simply pass. `--strict-markers` makes an unknown marker name an error, so a typo cannot silently skip a test.
- `markers = [`: The list of marker names the tests may use. A marker is a label attached to a test with `@pytest.mark.name`.
- `"live: calls the real model; needs ANTHROPIC_API_KEY and RUN_LIVE=1 (make test-live)",`: Registers the marker `live`. Its description says: calls the real model; needs ANTHROPIC_API_KEY and RUN_LIVE=1 (make test-live)
- `"integration: needs PostgreSQL from docker-compose.yml (make up)",`: Registers the marker `integration`. Its description says: needs PostgreSQL from docker-compose.yml (make up)
- `"e2e: runs the lesson scenarios against PostgreSQL (make test-e2e)",`: Registers the marker `e2e`. Its description says: runs the lesson scenarios against PostgreSQL (make test-e2e)

### The commands

```make
test: install ## unit tests (no services) with coverage; domain and application stay at 95% or more
	$(PY) -m pytest tests/unit --cov=$(PKG) --cov-report=term
	$(PY) -m coverage report --include='src/$(PKG)/domain/*,src/$(PKG)/application/*' --fail-under=95
```

- `test: install ## unit tests (no services) with coverage; domain and application stay at 95% or more`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(PY) -m pytest tests/unit --cov=$(PKG) --cov-report=term`: Run the tests with pytest, using the virtual environment's Python (`-m` runs a module). The options: `tests/unit --cov=$(PKG) --cov-report=term`.
- `$(PY) -m coverage report --include='src/$(PKG)/domain/*,src/$(PKG)/application/*' --fail-under=95`: Print the coverage of the domain and application layers only (`--include`) and exit with an error if it is below 95 percent.

```make
test-integration: install ## the adapters against the running PostgreSQL (make up first)
	$(PY) -m pytest tests/integration -m integration
```

- `test-integration: install ## the adapters against the running PostgreSQL (make up first)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(PY) -m pytest tests/integration -m integration`: Run the tests with pytest, using the virtual environment's Python (`-m` runs a module). The options: `tests/integration -m integration`.

```make
test-e2e: install ## the lesson's scenarios through the command-line programs (make up first)
	$(PY) -m pytest tests/e2e -m e2e
```

- `test-e2e: install ## the lesson's scenarios through the command-line programs (make up first)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(PY) -m pytest tests/e2e -m e2e`: Run the tests with pytest, using the virtual environment's Python (`-m` runs a module). The options: `tests/e2e -m e2e`.

```make
test-live: install ## the opt-in test that calls the real model (needs ANTHROPIC_API_KEY)
	RUN_LIVE=1 $(PY) -m pytest tests/live -m live
```

- `test-live: install ## the opt-in test that calls the real model (needs ANTHROPIC_API_KEY)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `RUN_LIVE=1 $(PY) -m pytest tests/live -m live`: Put `RUN_LIVE=1` in the environment of this one command, then run only tests marked `live`. The live test refuses to run unless this variable is set.

### A test, line by line

From `tests/unit/application/test_handler_worker.py`:

```python
def test_the_worker_waits_and_retries_when_the_queue_is_unreachable():
    class Flaky(MemoryQueue):
        failures = 2
```

- `def test_the_worker_waits_and_retries_when_the_queue_is_unreachable():`: A test: the name starts with `test_`, so pytest runs it, and the name says what it checks. The parameters are *fixtures* that pytest supplies by name.
- `class Flaky(MemoryQueue):`: A step of the test (the statement continues or calls the code under test).
- `failures = 2`: Prepares `failures` as `2`.

```python
        def claim(self, limit, lease_seconds):
            if self.failures:
                self.failures -= 1
                raise ConnectionError("database restarting")
            return super().claim(limit, lease_seconds)
```

- `def claim(self, limit, lease_seconds):`: A step of the test (the statement continues or calls the code under test).
- `if self.failures:`: A step of the test (the statement continues or calls the code under test).
- `self.failures -= 1`: A step of the test (the statement continues or calls the code under test).
- `raise ConnectionError("database restarting")`: A step of the test (the statement continues or calls the code under test).
- `return super().claim(limit, lease_seconds)`: Gives back `super().claim(limit, lease_seconds)`.

```python
    queue = Flaky()
    queue.put("e-1", json.dumps({"event_id": "e-1", "body": "Please cancel order 4417."}))
    effects = MemoryEffects()
    handler, _ = _handler(ScriptedModel(VALID), queue, effects)
```

- `queue = Flaky()`: Prepares `queue` as `Flaky()`.
- `queue.put("e-1", json.dumps({"event_id": "e-1", "body": "Please cancel order 4417."}))`: A step of the test (the statement continues or calls the code under test).
- `effects = MemoryEffects()`: Prepares `effects` as `MemoryEffects()`.
- `handler, _ = _handler(ScriptedModel(VALID), queue, effects)`: A step of the test (the statement continues or calls the code under test).



<!-- fullwalk -->
### Every test file, statement by statement

This part quotes every file under `tests/`, in the order git lists them, and says in plain words what each statement does. A test is a small program that runs a piece of the repository with chosen inputs and checks the result with `assert`.

#### `tests/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/conftest.py`

```python
"""Shared paths."""
```

- The docstring (documentation kept with the code) says: *Shared paths.*

> **A Python file is a module.** When another file writes `import` or `from ... import`, Python runs this file once and hands over the names it defines. A docstring is a string that sits first in a module, class or function; Python keeps it as the documentation of that thing.

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
```

- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `REPO = Path(__file__).resolve().parents[1]`: stores the item `Path(__file__).resolve().parents[1]` in `REPO`.

> **`import` and `from ... import`.** `import x` makes the module `x` available under that name. `from x import y` fetches only the name `y` from `x` so it can be used without the prefix. `as` renames what you import. Imports at the top mean: this file needs those things from elsewhere.

> **A name is a label for a value.** `x = 5` makes the name `x` point to the value 5. Names are not boxes with a fixed type; Python looks at the value at run time. A name written in CAPITALS by habit marks a constant: nobody should change it.

> **Indexing and slicing.** `items[0]` is the first item; `items[-1]` the last; `items[a:b]` is a new list from position `a` up to but not including `b`; `d['key']` looks a key up in a dict (and raises `KeyError` if it is missing).

#### `tests/e2e/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/e2e/test_done_when.py`

```python
"""The lesson's Done-when lines through the command-line programs against PostgreSQL (make up first)."""
```

- The docstring (documentation kept with the code) says: *The lesson's Done-when lines through the command-line programs against PostgreSQL (make up first).*

```python
import os

import pytest

from inbox_worker.application.generate_events import generate_events
from inbox_worker.infrastructure.postgres import Database, apply_scripts
from inbox_worker.infrastructure.settings import Settings
from inbox_worker.interfaces import cli
```

- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import pytest`: makes the module `pytest` available (the test framework).
- `from inbox_worker.application.generate_events import ...`: takes names from `inbox_worker.application.generate_events`, this repository's own code. (`generate_events`: `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable.)
- `from inbox_worker.infrastructure.postgres import ...`: takes names from `inbox_worker.infrastructure.postgres`, this repository's own code. (`Database`: A small connection pool over one database URL.) (`apply_scripts`: Drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran.)
- `from inbox_worker.infrastructure.settings import ...`: takes names from `inbox_worker.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from inbox_worker.interfaces import ...`: takes names from `inbox_worker.interfaces`, this repository's own code. (`cli`: a name defined in this repository.)

```python
from inbox_worker.interfaces.wiring import build_components
from tests.conftest import REPO

pytestmark = pytest.mark.e2e
```

- `from inbox_worker.interfaces.wiring import ...`: takes names from `inbox_worker.interfaces.wiring`, this repository's own code. (`build_components`: Wire the PostgreSQL adapters over one pool sized for the worker's concurrency.)
- `from tests.conftest import ...`: takes names from `tests.conftest`, this repository's own code. (`REPO`: a name defined in this repository.)
- `pytestmark = pytest.mark.e2e`: stores `pytest.mark.e2e` in `pytestmark`.

```python
@pytest.fixture(scope="module")
def components():
```

- Defines the function `components`.
- `@pytest.fixture(scope="module")`: marks the function as a pytest fixture.

> **A function.** `def name(parameters):` defines a reusable block of code. The indented lines below it are the body; they run each time the function is called. `return` ends the call and hands a value back. A function that reaches its end without `return` hands back `None`, Python's 'nothing'.

> **Decorators.** A line `@something` above a function or class passes the definition through `something`, and the name then refers to what comes back.

> **A fixture** is a function marked `@pytest.fixture` that prepares something a test needs (a temporary folder, a database, a client). A test asks for it by naming it as a parameter.

```python
settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str(REPO), "CONCURRENCY": "8"})
database = Database(settings.database_url)
```

- `settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str...`: stores the result of calling `Settings.from_environ({**os.environ, "PROJECT_ROOT": str(REPO), "CONCURRENCY": "8"})`, which is this repository's own `from_environ` (in `src/inbox_worker/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable in `settings`.
- `database = Database(settings.database_url)`: stores the result of calling `Database(settings.database_url)`, which is this repository's own `Database` (in `src/inbox_worker/infrastructure/postgres.py`): a small connection pool over one database URL in `database`.

> **`yield`.** A function with `yield` is a generator: calling it does not run the body at once; each time the caller asks for the next value, the body runs up to the next `yield`, gives that value out, and waits.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

> **`try` / `except` / `finally`.** Code in `try` runs; if it raises an error of the kind named in `except`, that block runs instead of the program stopping. `else` runs only if there was no error. `finally` always runs last. `raise` makes an error on purpose; `raise ... from other` records the earlier error as its cause.

```python
database.ping()
```

- `database.ping()`: calling `database.ping()`, which is this repository's own `ping` (in `src/inbox_worker/infrastructure/postgres.py`): true when a trivial query works.

```python
except Exception:
```

- If an error of kind `Exception` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
pytest.skip("PostgreSQL is not running; run `make up`")
```

- ``pytest.skip("PostgreSQL is not running; run `make up`")``: calling ``pytest.skip("PostgreSQL is not running; run `make up`")``.

```python
apply_scripts(database, REPO / "sql")
database.close()
built = build_components(settings)
yield built
built.database.close()
```

- `apply_scripts(database, REPO / "sql")`: calling `apply_scripts(database, REPO / "sql")`, which is this repository's own `apply_scripts` (in `src/inbox_worker/infrastructure/postgres.py`): drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran.
- `database.close()`: calling `database.close()`, which closes `database`.
- `built = build_components(settings)`: stores the result of calling `build_components(settings)`, which is this repository's own `build_components` (in `src/inbox_worker/interfaces/wiring.py`): wire the PostgreSQL adapters over one pool sized for the worker's concurrency in `built`.
- `yield built`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `built.database.close()`: calling `built.database.close()`, which closes `built.database`.

```python
def test_step_1_a_tampered_body_and_a_replayed_request_get_401_and_the_endpoint_p95_stays_under_100_ms(
    components, capsys
):
```

- Defines the test `test_step_1_a_tampered_body_and_a_replayed_request_get_401_and_the_endpoint_p95_stays_under_100_ms`.
- Parameters:
  - `components`: a fixture (defined in `tests/e2e/test_done_when.py`).
  - `capsys`: a fixture; captures what the code prints.

> **A pytest test.** pytest finds every function whose name starts with `test_` in a file whose name starts with `test_`, calls it, and counts it as passed if it returns without an error. The parameters of a test are *fixtures*: pytest looks each name up and passes in the value the fixture makes.

> **Parameters.** A parameter with `= value` is optional: if the caller gives nothing, the default is used. A bare `*` in the list means everything after it must be passed by name (`f(x=1)`). `*args` collects extra positional arguments in a tuple and `**kwargs` collects extra named ones in a dict. `->` followed by a type says what the function gives back.

```python
assert cli.main(["reset"]) == 0
assert cli.main(["bench-webhook"]) == 0
out = capsys.readouterr().out
assert "tampered body -> 401" in out and "replayed old request -> 401" in out and "p95" in out
```

- `assert cli.main(["reset"]) == 0`: checks that `cli.main(["reset"])` equals `0`. A false check stops the test as failed.
- `assert cli.main(["bench-webhook"]) == 0`: checks that `cli.main(["bench-webhook"])` equals `0`. A false check stops the test as failed.
- `out = capsys.readouterr().out`: stores `capsys.readouterr().out` in `out`.
- `assert "tampered body -> 401" in out and "replayed old request -> 4...`: checks that `"tampered body -> 401"` is among `out` and `"replayed old request -> 401"` is among `out` and `"p95"` is among `out`. A false check stops the test as failed.

> **`assert`.** `assert condition` does nothing when the condition is true and stops with an `AssertionError` when it is false. In a test file, a failing assert is how a test fails. `pytest` rewrites assert lines so its failure message shows the values involved.

> **Operators.** `//` divides and rounds down; `%` is the remainder; `**` is the power; `a and b` / `a or b` / `not a` combine conditions and stop at the first answer that decides the result; `x in items` asks whether `x` is among them; `x is None` asks whether it is exactly `None`.

```python
def test_steps_2_and_4_the_replayed_inbox_creates_no_new_ticket_and_every_poison_event_is_parked_with_a_reason(
    components, capsys
):
```

- Defines the test `test_steps_2_and_4_the_replayed_inbox_creates_no_new_ticket_and_every_poison_event_is_parked_with_a_reason`.
- Parameters:
  - `components`: a fixture (defined in `tests/e2e/test_done_when.py`).
  - `capsys`: a fixture; captures what the code prints.

```python
assert cli.main(["reset"]) == 0
inbox = generate_events()
healthy = {event_id for event_id, _ in inbox.deliveries} - set(inbox.poison)
assert cli.main(["enqueue"]) == 0
assert cli.main(["worker", "--until-idle"]) == 0
first = components.reports.counts()
```

- `assert cli.main(["reset"]) == 0`: checks that `cli.main(["reset"])` equals `0`. A false check stops the test as failed.
- `inbox = generate_events()`: stores the result of calling `generate_events()`, which is this repository's own `generate_events` (in `src/inbox_worker/application/generate_events.py`): `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable in `inbox`.
- `healthy = {event_id for event_id, _ in inbox.deliveries} - set(inbo...`: stores `{event_id for event_id, _ in inbox.deliveries} - set(inbox.poison)`, which subtracts `{event_id for event_id, _ in inbox.deliveries}` and `set(inbox.poison)` in `healthy`.
- `assert cli.main(["enqueue"]) == 0`: checks that `cli.main(["enqueue"])` equals `0`. A false check stops the test as failed.
- `assert cli.main(["worker", "--until-idle"]) == 0`: checks that `cli.main(["worker", "--until-idle"])` equals `0`. A false check stops the test as failed.
- `first = components.reports.counts()`: stores the result of calling `components.reports.counts()`, which is this repository's own `counts` (in `src/inbox_worker/infrastructure/postgres.py`): rows in the tables that matter in `first`.

```python
assert first["tickets"] == len(healthy) == 990 and first["dead_letters"] == 10
assert cli.main(["enqueue"]) == 0
assert cli.main(["worker", "--until-idle"]) == 0
assert cli.main(["relay", "--once"]) == 0
second = components.reports.counts()
assert (second["tickets"], second["outbox"], second["mails_sent"]) == (990, 990, 990)
```

- `assert first["tickets"] == len(healthy) == 990 and first["dead_lett...`: checks that `first["tickets"]` equals `len(healthy)` and `len(healthy)` equals `990` and `first["dead_letters"]` equals `10`. A false check stops the test as failed.
- `assert cli.main(["enqueue"]) == 0`: checks that `cli.main(["enqueue"])` equals `0`. A false check stops the test as failed.
- `assert cli.main(["worker", "--until-idle"]) == 0`: checks that `cli.main(["worker", "--until-idle"])` equals `0`. A false check stops the test as failed.
- `assert cli.main(["relay", "--once"]) == 0`: checks that `cli.main(["relay", "--once"])` equals `0`. A false check stops the test as failed.
- `second = components.reports.counts()`: stores the result of calling `components.reports.counts()`, which is this repository's own `counts` (in `src/inbox_worker/infrastructure/postgres.py`): rows in the tables that matter in `second`.
- `assert (second["tickets"], second["outbox"], second["mails_sent"]) ...`: checks that `(second["tickets"], second["outbox"], second["mails_sent"])` equals `(990, 990, 990)`. A false check stops the test as failed.

```python
assert second["dead_letters"] == 20
assert sorted(components.reports.ticket_event_ids()) == sorted(healthy)
reasons = {reason for _, _, reason, *_ in components.reports.dead_events()}
assert reasons == {"malformed_event", "event_too_large", "bad_encoding", "permanent_error"}
capsys.readouterr()
assert cli.main(["status"]) == 0
```

- `assert second["dead_letters"] == 20`: checks that `second["dead_letters"]` equals `20`. A false check stops the test as failed.
- `assert sorted(components.reports.ticket_event_ids()) == sorted(heal...`: checks that `sorted(components.reports.ticket_event_ids())` equals `sorted(healthy)`. A false check stops the test as failed.
- `reasons = {reason for _, _, reason, *_ in components.reports.dead_e...`: stores a set built by running `reason` for each `_, _, reason, *_` in `components.reports.dead_events()` in `reasons`.
- `assert reasons == {"malformed_event", "event_too_large", "bad_encod...`: checks that `reasons` equals `{"malformed_event", "event_too_large", "bad_encoding", "permanent_error"}`. A false check stops the test as failed.
- `capsys.readouterr()`: calling `capsys.readouterr()`, which reads what was printed so far.
- `assert cli.main(["status"]) == 0`: checks that `cli.main(["status"])` equals `0`. A false check stops the test as failed.

> **Comprehensions.** `[f(x) for x in items if test(x)]` builds a new list: run `f` on every item that passes the test. With `{k: v for ...}` it builds a dict, with `{x for ...}` a set. With round brackets it is a generator expression: the values are produced one at a time, only when something asks for the next one.

```python
def test_step_4_redriving_a_fixed_dead_letter_processes_it_once(components):
```

- Defines the test `test_step_4_redriving_a_fixed_dead_letter_processes_it_once`.
- Parameters:
  - `components`: a fixture (defined in `tests/e2e/test_done_when.py`).

```python
dead = next(row for row in components.reports.dead_events() if row[2] == "event_too_large")
assert cli.main(["redrive", str(dead[0])]) == 0
assert cli.main(["redrive", str(dead[0])]) == 1
```

- `dead = next(row for row in components.reports.dead_events() if row[...`: stores the result of calling `next(row for row in components.reports.dead_events() if row[2] == "event_too_large")`, which takes the next item from `(row for row in components.reports.dead_events() if row[2] == "event_too_large")` in `dead`.
- `assert cli.main(["redrive", str(dead[0])]) == 0`: checks that `cli.main(["redrive", str(dead[0])])` equals `0`. A false check stops the test as failed.
- `assert cli.main(["redrive", str(dead[0])]) == 1`: checks that `cli.main(["redrive", str(dead[0])])` equals `1`. A false check stops the test as failed.

```python
@pytest.mark.parametrize("point", ["after_model", "after_commit"])
def test_step_5_after_a_real_process_kill_no_event_is_lost_and_none_has_two_tickets(components, point, capsys):
```

- Defines the test `test_step_5_after_a_real_process_kill_no_event_is_lost_and_none_has_two_tickets`.
- `@pytest.mark.parametrize("point", ["after_model", "after_commit"])`: runs the test once per listed set of values.
- Parameters:
  - `components`: a fixture (defined in `tests/e2e/test_done_when.py`).
  - `point`.
  - `capsys`: a fixture; captures what the code prints.

> **`@pytest.mark.parametrize`.** Runs one test function many times, once per set of values listed, so each case is its own test.

```python
assert cli.main(["crash-test", "--at", point]) == 0
out = capsys.readouterr().out
assert "crash run exit 137" in out and "lost: []; duplicated tickets: 0" in out
```

- `assert cli.main(["crash-test", "--at", point]) == 0`: checks that `cli.main(["crash-test", "--at", point])` equals `0`. A false check stops the test as failed.
- `out = capsys.readouterr().out`: stores `capsys.readouterr().out` in `out`.
- `assert "crash run exit 137" in out and "lost: []; duplicated ticket...`: checks that `"crash run exit 137"` is among `out` and `"lost: []; duplicated tickets: 0"` is among `out`. A false check stops the test as failed.

```python
def test_step_6_the_burst_reports_two_concurrency_settings_and_the_queue_drains(components, capsys):
```

- Defines the test `test_step_6_the_burst_reports_two_concurrency_settings_and_the_queue_drains`.
- Parameters:
  - `components`: a fixture (defined in `tests/e2e/test_done_when.py`).
  - `capsys`: a fixture; captures what the code prints.

```python
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
```

- `assert ( cli.main( [ "burst", "--events", "100", "--seconds", "3", ...`: checks that `cli.main( [ "burst", "--events", "100", "--seconds", "3", "--concurrency", "5", "20", "...` equals `0`. A false check stops the test as failed.

```python
rows = [
    line
    for line in capsys.readouterr().out.splitlines()
    if line.startswith("| ") and "---" not in line and "Concurrency" not in line
]
assert len(rows) == 2 and all(row.rstrip().endswith("True |") for row in rows)
```

- `rows = [ line for line in capsys.readouterr().out.splitlines() if l...`: stores a list built by running `line` for each `line` in `capsys.readouterr().out.splitlines()` keeping only those where `line.startswith("| ")` is true (the call asks whether `line` begins with `"| "`) and `"---"` is not among `line` and `"Concurrency"` is not among `line` in `rows`.
- `assert len(rows) == 2 and all(row.rstrip().endswith("True |") for r...`: checks that `len(rows)` equals `2` and `all(row.rstrip().endswith("True |") for row in rows)` is true (the call is true if every item of `(row.rstrip().endswith("True |") for row in rows)` is true). A false check stops the test as failed.

#### `tests/integration/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/integration/conftest.py`

```python
"""A real PostgreSQL (docker compose: make up). The schema is rebuilt from sql/ once per session and emptied per test."""
```

- The docstring (documentation kept with the code) says: *A real PostgreSQL (docker compose: make up). The schema is rebuilt from sql/ once per session and emptied per test.*

```python
from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from inbox_worker.infrastructure.postgres import Database, apply_scripts, reset_tables
from inbox_worker.infrastructure.settings import Settings
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Iterator`: the type hint for something you can loop over once.)
- `import pytest`: makes the module `pytest` available (the test framework).
- `from inbox_worker.infrastructure.postgres import ...`: takes names from `inbox_worker.infrastructure.postgres`, this repository's own code. (`Database`: A small connection pool over one database URL.) (`apply_scripts`: Drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran.) (`reset_tables`: Empty every table (sql/reset.sql).)
- `from inbox_worker.infrastructure.settings import ...`: takes names from `inbox_worker.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)

> **`from __future__ import annotations`.** The type hints written after a colon or an arrow are saved as text and only looked at by type checkers, so a hint may name a class that is defined later in the file.

```python
from tests.conftest import REPO
```

- `from tests.conftest import ...`: takes names from `tests.conftest`, this repository's own code. (`REPO`: a name defined in this repository.)

```python
@pytest.fixture(scope="session")
def settings() -> Settings:
```

- Defines the function `settings`.
- `@pytest.fixture(scope="session")`: marks the function as a pytest fixture.
- Gives back a value of type `Settings`.

```python
"""Settings from the environment (the .env values `make` exports) with this repository as the root."""
```

- The docstring (documentation kept with the code) says: *Settings from the environment (the .env values `make` exports) with this repository as the root.*

```python
return Settings.from_environ({**os.environ, "PROJECT_ROOT": str(REPO)})
```

- `return Settings.from_environ({**os.environ, "PROJECT_ROOT": str(REP...`: ends the function and gives back the result of calling `Settings.from_environ({**os.environ, "PROJECT_ROOT": str(REPO)})`, which is this repository's own `from_environ` (in `src/inbox_worker/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable.

```python
@pytest.fixture(scope="session")
def database(settings: Settings) -> Iterator[Database]:
```

- Defines the function `database`.
- `@pytest.fixture(scope="session")`: marks the function as a pytest fixture.
- Parameters:
  - `settings`, type `Settings`.
- Gives back a value of type `Iterator[Database]`.

```python
"""The pool; skips the whole suite when PostgreSQL is not up."""
```

- The docstring (documentation kept with the code) says: *The pool; skips the whole suite when PostgreSQL is not up.*

```python
db = Database(settings.database_url, max_connections=16)
```

- `db = Database(settings.database_url, max_connections=16)`: stores the result of calling `Database(settings.database_url, max_connections=16)`, which is this repository's own `Database` (in `src/inbox_worker/infrastructure/postgres.py`): a small connection pool over one database URL in `db`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
db.ping()
```

- `db.ping()`: calling `db.ping()`, which is this repository's own `ping` (in `src/inbox_worker/infrastructure/postgres.py`): true when a trivial query works.

```python
except Exception:
```

- If an error of kind `Exception` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
pytest.skip("PostgreSQL is not running; run `make up`")
```

- ``pytest.skip("PostgreSQL is not running; run `make up`")``: calling ``pytest.skip("PostgreSQL is not running; run `make up`")``.

```python
apply_scripts(db, REPO / "sql")
yield db
db.close()
```

- `apply_scripts(db, REPO / "sql")`: calling `apply_scripts(db, REPO / "sql")`, which is this repository's own `apply_scripts` (in `src/inbox_worker/infrastructure/postgres.py`): drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran.
- `yield db`: hands a value to whoever is looping over this generator, then waits to be asked for the next.
- `db.close()`: calling `db.close()`, which closes `db`.

```python
@pytest.fixture
def clean(database: Database) -> Database:
```

- Defines the function `clean`.
- `@pytest.fixture`: marks the function as a pytest fixture.
- Parameters:
  - `database`, type `Database`.
- Gives back a value of type `Database`.

```python
"""The database with every table emptied."""
```

- The docstring (documentation kept with the code) says: *The database with every table emptied.*

```python
reset_tables(database, REPO / "sql")
return database
```

- `reset_tables(database, REPO / "sql")`: calling `reset_tables(database, REPO / "sql")`, which is this repository's own `reset_tables` (in `src/inbox_worker/infrastructure/postgres.py`): empty every table (sql/reset.sql).
- `return database`: ends the function and gives back the value of `database`.

#### `tests/integration/test_postgres_adapters.py`

- This file has no docstring at the top.

```python
import concurrent.futures
import json
import time

import psycopg
import pytest

from inbox_worker.application.extraction import TicketExtractor
```

- `import concurrent.futures`: makes the module `concurrent.futures` available (the standard library's package for running work on several threads or processes).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import time`: makes the module `time` available (clocks and sleeping).
- `import psycopg`: makes the module `psycopg` available (the PostgreSQL driver).
- `import pytest`: makes the module `pytest` available (the test framework).
- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`TicketExtractor`: Model-backed extraction.)

```python
from inbox_worker.application.handler import DEAD, DUPLICATE, PROCESSED, RETRY, EventHandler, RetryPolicy
from inbox_worker.application.outbox import OutboxRelay
from inbox_worker.application.worker import Worker
from inbox_worker.domain.ticket import Ticket
from inbox_worker.infrastructure.clock import SystemClock
from inbox_worker.infrastructure.fake_model import FakeModel
```

- `from inbox_worker.application.handler import ...`: takes names from `inbox_worker.application.handler`, this repository's own code. (`DEAD`: a name defined in this repository.) (`DUPLICATE`: a name defined in this repository.) (`PROCESSED`: a name defined in this repository.) (`RETRY`: a name defined in this repository.) (`EventHandler`: Applies each event's effects once, however often the queue delivers it.) (`RetryPolicy`: How a failing event is retried before it is parked.)
- `from inbox_worker.application.outbox import ...`: takes names from `inbox_worker.application.outbox`, this repository's own code. (`OutboxRelay`: Sends unsent outbox rows.)
- `from inbox_worker.application.worker import ...`: takes names from `inbox_worker.application.worker`, this repository's own code. (`Worker`: Pulls batches from the queue.)
- `from inbox_worker.domain.ticket import ...`: takes names from `inbox_worker.domain.ticket`, this repository's own code. (`Ticket`: What the customer wants, about which order, in what mood, and the action it asks for.)
- `from inbox_worker.infrastructure.clock import ...`: takes names from `inbox_worker.infrastructure.clock`, this repository's own code. (`SystemClock`: Now, in UTC.)
- `from inbox_worker.infrastructure.fake_model import ...`: takes names from `inbox_worker.infrastructure.fake_model`, this repository's own code. (`FakeModel`: Thread-safe; counts calls, rate-limit errors and injected errors.)

```python
from inbox_worker.infrastructure.postgres import (
    FakeMailSender,
    PostgresEffects,
    PostgresOutbox,
    PostgresQueue,
    PostgresReports,
)
```

- `from inbox_worker.infrastructure.postgres import ...`: takes names from `inbox_worker.infrastructure.postgres`, this repository's own code. (`FakeMailSender`: Records every send in `sent_mail`; the unique event id refuses a second send of one acknowledgment.) (`PostgresEffects`: The processed mark, the ticket and the outbox row.) (`PostgresOutbox`: The unsent acknowledgments.) (`PostgresQueue`: The delivery queue.) (`PostgresReports`: Read-only queries for the reports and the verification steps.)

```python
pytestmark = pytest.mark.integration
TICKET = Ticket("cancel", "4417", "neutral", "cancel_order")
```

- `pytestmark = pytest.mark.integration`: stores `pytest.mark.integration` in `pytestmark`.
- `TICKET = Ticket("cancel", "4417", "neutral", "cancel_order")`: stores the result of calling `Ticket("cancel", "4417", "neutral", "cancel_order")`, which is this repository's own `Ticket` (in `src/inbox_worker/domain/ticket.py`): what the customer wants, about which order, in what mood, and the action it asks for in `TICKET`.

```python
def _payload(event_id, body="Please cancel order 4417."):
```

- Defines the function `_payload`.
- Parameters:
  - `event_id`.
  - `body`, optional (default `"Please cancel order 4417."`).

```python
return json.dumps({"event_id": event_id, "body": body})
```

- `return json.dumps({"event_id": event_id, "body": body})`: ends the function and gives back the result of calling `json.dumps({"event_id": event_id, "body": body})`, which turns `{"event_id": event_id, "body": body}` into JSON text.

```python
def test_the_schema_has_the_tables_the_lesson_needs_and_rejects_bad_rows(clean):
```

- Defines the test `test_the_schema_has_the_tables_the_lesson_needs_and_rejects_bad_rows`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
with clean.connection() as connection:
```

- `clean.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

> **`with`.** `with thing as name:` uses a resource for the indented lines and then cleans it up, even if an error happens: a file is closed, a lock is released, a database transaction is committed or rolled back.

```python
names = {
    row[0]
    for row in connection.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    ).fetchall()
}
assert {"deliveries", "processed_events", "tickets", "outbox", "sent_mail", "dead_letters"} <= names
```

- `names = { row[0] for row in connection.execute( "SELECT table_name ...`: stores a set built by running `row[0]` for each `row` in `connection.execute( "SELECT table_name FROM information_schema.tables WHERE table_schem...` in `names`.
- `assert {"deliveries", "processed_events", "tickets", "outbox", "sen...`: checks that `{"deliveries", "processed_events", "tickets", "outbox", "sent_mail", "dead_letters"}` is less than or equal to `names`. A false check stops the test as failed.

```python
with pytest.raises(psycopg.errors.CheckViolation):
```

- `pytest.raises(psycopg.errors.CheckViolation)`: the test passes only if the indented lines raise `psycopg.errors.CheckViolation`; it fails if nothing is raised.

> **`pytest.raises(E)`.** A `with` block that passes only if the code inside raises an error of kind `E`; it fails if nothing is raised.

```python
connection.execute("INSERT INTO deliveries (event_id, payload, status) VALUES ('e', 'p', 'weird')")
```

- `connection.execute("INSERT INTO deliveries (event_id, payload, stat...`: calling `connection.execute("INSERT INTO deliveries (event_id, payload, status) VALUES ('e', 'p'...`, which sends the SQL statement `"INSERT INTO deliveries (event_id, payload, status) VALUES ('e', 'p', 'weird')"` to the database.

```python
with pytest.raises(psycopg.errors.ForeignKeyViolation):
```

- `pytest.raises(psycopg.errors.ForeignKeyViolation)`: the test passes only if the indented lines raise `psycopg.errors.ForeignKeyViolation`; it fails if nothing is raised.

```python
connection.execute(
    "INSERT INTO tickets (event_id, intent, sentiment, requested_action) VALUES ('nope', 'cancel', 'neutral', 'none')"
)
```

- `connection.execute( "INSERT INTO tickets (event_id, intent, sentime...`: calling `connection.execute( "INSERT INTO tickets (event_id, intent, sentiment, requested_action...`, which sends the SQL statement `"INSERT INTO tickets (event_id, intent, sentiment, requested_action) VALUES ('nope', 'c...` to the database.

```python
def test_a_claim_hands_each_delivery_to_one_worker_and_an_expired_claim_is_handed_out_again(clean):
```

- Defines the test `test_a_claim_hands_each_delivery_to_one_worker_and_an_expired_claim_is_handed_out_again`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
queue = PostgresQueue(clean)
```

- `queue = PostgresQueue(clean)`: stores the result of calling `PostgresQueue(clean)`, which is this repository's own `PostgresQueue` (in `src/inbox_worker/infrastructure/postgres.py`): the delivery queue in `queue`.

```python
for number in range(6):
```

- Repeats the indented lines once for each item of `range(6)`, naming the current item `number`.

> **`for`.** `for item in things:` runs the indented lines once per item, giving the name `item` the next value each time. `break` leaves the loop early; `continue` jumps to the next item.

```python
queue.put(f"e-{number}", _payload(f"e-{number}"))
```

- `queue.put(f"e-{number}", _payload(f"e-{number}"))`: calling `queue.put(f"e-{number}", _payload(f"e-{number}"))`.

```python
first, second = queue.claim(4, 30), queue.claim(4, 30)
assert len(first) == 4 and len(second) == 2 and not {d.delivery_id for d in first} & {d.delivery_id for d in second}
assert queue.claim(4, 30) == []
queue.ack(first[0].delivery_id)
short = PostgresQueue(clean)
```

- `first, second = queue.claim(4, 30), queue.claim(4, 30)`: unpacks a tuple of 2 items into the names `first`, `second`, one item each.
- `assert len(first) == 4 and len(second) == 2 and not {d.delivery_id ...`: checks that `len(first)` equals `4` and `len(second)` equals `2` and it is not the case that `{d.delivery_id for d in first} & {d.delivery_id for d in second}` is true. A false check stops the test as failed.
- `assert queue.claim(4, 30) == []`: checks that `queue.claim(4, 30)` equals `[]`. A false check stops the test as failed.
- `queue.ack(first[0].delivery_id)`: calling `queue.ack(first[0].delivery_id)`.
- `short = PostgresQueue(clean)`: stores the result of calling `PostgresQueue(clean)`, which is this repository's own `PostgresQueue` (in `src/inbox_worker/infrastructure/postgres.py`): the delivery queue in `short`.

> **Tuples and unpacking.** `(a, b)` is a fixed-length group. `x, y = pair` unpacks the two items into two names at once.

```python
for delivery in second:
```

- Repeats the indented lines once for each item of `second`, naming the current item `delivery`.

```python
short.retry(delivery.delivery_id, 0, "x")
```

- `short.retry(delivery.delivery_id, 0, "x")`: calling `short.retry(delivery.delivery_id, 0, "x")`.

```python
reclaimed = short.claim(10, 0.2)
assert len(reclaimed) == 2 and all(d.attempts == 2 for d in reclaimed)
time.sleep(0.4)
again = short.claim(10, 30)
assert {d.delivery_id for d in again} >= {d.delivery_id for d in reclaimed}
```

- `reclaimed = short.claim(10, 0.2)`: stores the result of calling `short.claim(10, 0.2)` in `reclaimed`.
- `assert len(reclaimed) == 2 and all(d.attempts == 2 for d in reclaimed)`: checks that `len(reclaimed)` equals `2` and `all(d.attempts == 2 for d in reclaimed)` is true (the call is true if every item of `(d.attempts == 2 for d in reclaimed)` is true). A false check stops the test as failed.
- `time.sleep(0.4)`: calling `time.sleep(0.4)`, which waits `0.4` seconds.
- `again = short.claim(10, 30)`: stores the result of calling `short.claim(10, 30)` in `again`.
- `assert {d.delivery_id for d in again} >= {d.delivery_id for d in re...`: checks that `{d.delivery_id for d in again}` is greater than or equal to `{d.delivery_id for d in reclaimed}`. A false check stops the test as failed.

```python
def test_concurrent_claims_never_return_the_same_delivery_twice(clean):
```

- Defines the test `test_concurrent_claims_never_return_the_same_delivery_twice`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
queue = PostgresQueue(clean)
```

- `queue = PostgresQueue(clean)`: stores the result of calling `PostgresQueue(clean)`, which is this repository's own `PostgresQueue` (in `src/inbox_worker/infrastructure/postgres.py`): the delivery queue in `queue`.

```python
for number in range(60):
```

- Repeats the indented lines once for each item of `range(60)`, naming the current item `number`.

```python
queue.put(f"e-{number}", "{}")
```

- `queue.put(f"e-{number}", "{}")`: calling `queue.put(f"e-{number}", "{}")`.

```python
with concurrent.futures.ThreadPoolExecutor(6) as pool:
```

- Opens `concurrent.futures.ThreadPoolExecutor(6)` as `pool` for the indented lines, and cleans it up when they end (even after an error).

```python
batches = list(pool.map(lambda _: queue.claim(10, 30), range(6)))
```

- `batches = list(pool.map(lambda _: queue.claim(10, 30), range(6)))`: stores the result of calling `list(pool.map(lambda _: queue.claim(10, 30), range(6)))`, which builds a new list from `pool.map(lambda _: queue.claim(10, 30), range(6))` in `batches`.

```python
ids = [d.delivery_id for batch in batches for d in batch]
assert len(ids) == len(set(ids)) == 60
```

- `ids = [d.delivery_id for batch in batches for d in batch]`: stores a list built by running `d.delivery_id` for each `batch` in `batches` in `ids`.
- `assert len(ids) == len(set(ids)) == 60`: checks that `len(ids)` equals `len(set(ids))` and `len(set(ids))` equals `60`. A false check stops the test as failed.

```python
def test_applying_an_event_twice_leaves_one_ticket_one_outbox_row_and_reports_the_twin(clean):
```

- Defines the test `test_applying_an_event_twice_leaves_one_ticket_one_outbox_row_and_reports_the_twin`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
effects = PostgresEffects(clean)
assert effects.apply("e-1", TICKET) is True
assert effects.apply("e-1", TICKET) is False
assert effects.is_processed("e-1") and not effects.is_processed("e-2")
counts = PostgresReports(clean).counts()
assert (counts["processed"], counts["tickets"], counts["outbox"]) == (1, 1, 1)
```

- `effects = PostgresEffects(clean)`: stores the result of calling `PostgresEffects(clean)`, which is this repository's own `PostgresEffects` (in `src/inbox_worker/infrastructure/postgres.py`): the processed mark, the ticket and the outbox row in `effects`.
- `assert effects.apply("e-1", TICKET) is True`: checks that `effects.apply("e-1", TICKET)` is exactly `True`. A false check stops the test as failed.
- `assert effects.apply("e-1", TICKET) is False`: checks that `effects.apply("e-1", TICKET)` is exactly `False`. A false check stops the test as failed.
- `assert effects.is_processed("e-1") and not effects.is_processed("e-2")`: checks that `effects.is_processed("e-1")` is true and it is not the case that `effects.is_processed("e-2")` is true. A false check stops the test as failed.
- `counts = PostgresReports(clean).counts()`: stores the result of calling `PostgresReports(clean).counts()`, which is this repository's own `counts` (in `src/inbox_worker/infrastructure/postgres.py`): rows in the tables that matter in `counts`.
- `assert (counts["processed"], counts["tickets"], counts["outbox"]) =...`: checks that `(counts["processed"], counts["tickets"], counts["outbox"])` equals `(1, 1, 1)`. A false check stops the test as failed.

```python
def test_two_threads_applying_the_same_event_at_once_produce_exactly_one_ticket(clean):
```

- Defines the test `test_two_threads_applying_the_same_event_at_once_produce_exactly_one_ticket`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
effects = PostgresEffects(clean)
```

- `effects = PostgresEffects(clean)`: stores the result of calling `PostgresEffects(clean)`, which is this repository's own `PostgresEffects` (in `src/inbox_worker/infrastructure/postgres.py`): the processed mark, the ticket and the outbox row in `effects`.

```python
with concurrent.futures.ThreadPoolExecutor(8) as pool:
```

- Opens `concurrent.futures.ThreadPoolExecutor(8)` as `pool` for the indented lines, and cleans it up when they end (even after an error).

```python
results = list(pool.map(lambda _: effects.apply("e-race", TICKET), range(8)))
```

- `results = list(pool.map(lambda _: effects.apply("e-race", TICKET), ...`: stores the result of calling `list(pool.map(lambda _: effects.apply("e-race", TICKET), range(8)))`, which builds a new list from `pool.map(lambda _: effects.apply("e-race", TICKET), range(8))` in `results`.

```python
assert results.count(True) == 1 and PostgresReports(clean).counts()["tickets"] == 1
```

- `assert results.count(True) == 1 and PostgresReports(clean).counts()...`: checks that `results.count(True)` equals `1` and `PostgresReports(clean).counts()["tickets"]` equals `1`. A false check stops the test as failed.

```python
def test_the_full_path_processes_a_replay_with_no_new_ticket_and_no_second_acknowledgment(clean):
```

- Defines the test `test_the_full_path_processes_a_replay_with_no_new_ticket_and_no_second_acknowledgment`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
queue, effects = PostgresQueue(clean), PostgresEffects(clean)
handler = EventHandler(
    queue, effects, TicketExtractor(FakeModel()), SystemClock(), RetryPolicy(base_seconds=0.01, cap_seconds=0.05)
)
ids = [f"e-{n:02d}" for n in range(20)]
```

- `queue, effects = PostgresQueue(clean), PostgresEffects(clean)`: unpacks a tuple of 2 items into the names `queue`, `effects`, one item each.
- `handler = EventHandler( queue, effects, TicketExtractor(FakeModel()...`: stores the result of calling `EventHandler( queue, effects, TicketExtractor(FakeModel()), SystemClock(), RetryPolicy(...`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it in `handler`.
- `ids = [f"e-{n:02d}" for n in range(20)]`: stores a list built by running `f"e-{n:02d}"` for each `n` in `range(20)` in `ids`.

```python
for _ in range(2):
```

- Repeats the indented lines once for each item of `range(2)`, naming the current item `_`.

```python
for event_id in ids:
```

- Repeats the indented lines once for each item of `ids`, naming the current item `event_id`.

```python
queue.put(event_id, _payload(event_id))
```

- `queue.put(event_id, _payload(event_id))`: calling `queue.put(event_id, _payload(event_id))`.

```python
outcomes = Worker(
    queue,
    handler,
    concurrency=4,
    lease_seconds=30,
    stop_requested=lambda: False,
    wait=lambda s: False,
    idle_poll_seconds=0.01,
).run(until_idle=True)
```

- `outcomes = Worker( queue, handler, concurrency=4, lease_seconds=30,...`: stores the result of calling `Worker( queue, handler, concurrency=4, lease_seconds=30, stop_requested=lambda: False, ...`, which runs a program or a coroutine The named values are `until_idle`. in `outcomes`.

```python
OutboxRelay(PostgresOutbox(clean), FakeMailSender(clean)).run_once(100)
```

- `OutboxRelay(PostgresOutbox(clean), FakeMailSender(clean)).run_once(...`: calling `OutboxRelay(PostgresOutbox(clean), FakeMailSender(clean)).run_once(100)`, which is this repository's own `run_once` (in `src/inbox_worker/application/outbox.py`): send up to `limit` rows; returns how many rows were marked sent.

```python
if _ == 0:
```

- Checks whether `_` equals `0`. If so, the indented lines run.

> **`if`.** `if condition:` runs the indented lines only when the condition is true. `elif` adds another condition to try, `else` runs when none held. 'Truthy' values count as true; 'falsy' ones are `False`, `None`, zero and anything empty (`''`, `[]`, `{}`).

```python
assert outcomes[PROCESSED] == 20
```

- `assert outcomes[PROCESSED] == 20`: checks that `outcomes[PROCESSED]` equals `20`. A false check stops the test as failed.

```python
else:
```

- Runs when none of the conditions above held.

```python
assert outcomes[DUPLICATE] == 20 and PROCESSED not in outcomes
```

- `assert outcomes[DUPLICATE] == 20 and PROCESSED not in outcomes`: checks that `outcomes[DUPLICATE]` equals `20` and `PROCESSED` is not among `outcomes`. A false check stops the test as failed.

```python
counts = PostgresReports(clean).counts()
assert (counts["tickets"], counts["outbox"], counts["mails_sent"]) == (20, 20, 20)
assert sorted(PostgresReports(clean).ticket_event_ids()) == ids
```

- `counts = PostgresReports(clean).counts()`: stores the result of calling `PostgresReports(clean).counts()`, which is this repository's own `counts` (in `src/inbox_worker/infrastructure/postgres.py`): rows in the tables that matter in `counts`.
- `assert (counts["tickets"], counts["outbox"], counts["mails_sent"]) ...`: checks that `(counts["tickets"], counts["outbox"], counts["mails_sent"])` equals `(20, 20, 20)`. A false check stops the test as failed.
- `assert sorted(PostgresReports(clean).ticket_event_ids()) == ids`: checks that `sorted(PostgresReports(clean).ticket_event_ids())` equals `ids`. A false check stops the test as failed.

```python
def test_the_mail_sender_refuses_a_second_send_of_one_acknowledgment_and_the_relay_tolerates_it(clean):
```

- Defines the test `test_the_mail_sender_refuses_a_second_send_of_one_acknowledgment_and_the_relay_tolerates_it`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
PostgresEffects(clean).apply("e-1", TICKET)
FakeMailSender(clean).send("e-1", "acknowledge")
outbox = PostgresOutbox(clean)
assert OutboxRelay(outbox, FakeMailSender(clean)).run_once() == 1
assert outbox.unsent(10) == [] and PostgresReports(clean).counts()["mails_sent"] == 1
```

- `PostgresEffects(clean).apply("e-1", TICKET)`: calling `PostgresEffects(clean).apply("e-1", TICKET)`.
- `FakeMailSender(clean).send("e-1", "acknowledge")`: calling `FakeMailSender(clean).send("e-1", "acknowledge")`.
- `outbox = PostgresOutbox(clean)`: stores the result of calling `PostgresOutbox(clean)`, which is this repository's own `PostgresOutbox` (in `src/inbox_worker/infrastructure/postgres.py`): the unsent acknowledgments in `outbox`.
- `assert OutboxRelay(outbox, FakeMailSender(clean)).run_once() == 1`: checks that `OutboxRelay(outbox, FakeMailSender(clean)).run_once()` equals `1`. A false check stops the test as failed.
- `assert outbox.unsent(10) == [] and PostgresReports(clean).counts()[...`: checks that `outbox.unsent(10)` equals `[]` and `PostgresReports(clean).counts()["mails_sent"]` equals `1`. A false check stops the test as failed.

```python
def test_poison_events_are_parked_with_a_reason_and_do_not_hold_up_the_events_behind_them(clean):
```

- Defines the test `test_poison_events_are_parked_with_a_reason_and_do_not_hold_up_the_events_behind_them`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
queue = PostgresQueue(clean)
queue.put("bad-1", '{"event_id": "bad-1", "body": ')
queue.put("bad-2", json.dumps({"event_id": "bad-2", "body": "x" * 300_000}))
```

- `queue = PostgresQueue(clean)`: stores the result of calling `PostgresQueue(clean)`, which is this repository's own `PostgresQueue` (in `src/inbox_worker/infrastructure/postgres.py`): the delivery queue in `queue`.
- `queue.put("bad-1", '{"event_id": "bad-1", "body": ')`: calling `queue.put("bad-1", '{"event_id": "bad-1", "body": ')`.
- `queue.put("bad-2", json.dumps({"event_id": "bad-2", "body": "x" * 3...`: calling `queue.put("bad-2", json.dumps({"event_id": "bad-2", "body": "x" * 300_000}))`.

```python
for number in range(5):
```

- Repeats the indented lines once for each item of `range(5)`, naming the current item `number`.

```python
queue.put(f"ok-{number}", _payload(f"ok-{number}"))
```

- `queue.put(f"ok-{number}", _payload(f"ok-{number}"))`: calling `queue.put(f"ok-{number}", _payload(f"ok-{number}"))`.

```python
handler = EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())
outcomes = Worker(
    queue,
    handler,
    concurrency=1,
    lease_seconds=30,
    stop_requested=lambda: False,
    wait=lambda s: False,
    idle_poll_seconds=0.01,
).run(until_idle=True)
```

- `handler = EventHandler(queue, PostgresEffects(clean), TicketExtract...`: stores the result of calling `EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it in `handler`.
- `outcomes = Worker( queue, handler, concurrency=1, lease_seconds=30,...`: stores the result of calling `Worker( queue, handler, concurrency=1, lease_seconds=30, stop_requested=lambda: False, ...`, which runs a program or a coroutine The named values are `until_idle`. in `outcomes`.

```python
assert outcomes[DEAD] == 2 and outcomes[PROCESSED] == 5
reasons = {event: reason for _, event, reason, *_ in PostgresReports(clean).dead_events()}
assert reasons == {"bad-1": "malformed_event", "bad-2": "event_too_large"}
```

- `assert outcomes[DEAD] == 2 and outcomes[PROCESSED] == 5`: checks that `outcomes[DEAD]` equals `2` and `outcomes[PROCESSED]` equals `5`. A false check stops the test as failed.
- `reasons = {event: reason for _, event, reason, *_ in PostgresReport...`: stores a dict built by running `event` for each `_, event, reason, *_` in `PostgresReports(clean).dead_events()` in `reasons`.
- `assert reasons == {"bad-1": "malformed_event", "bad-2": "event_too_...`: checks that `reasons` equals `{"bad-1": "malformed_event", "bad-2": "event_too_large"}`. A false check stops the test as failed.

```python
def test_a_rate_limited_event_is_retried_later_and_a_permanent_failure_is_parked_after_one_attempt(clean):
```

- Defines the test `test_a_rate_limited_event_is_retried_later_and_a_permanent_failure_is_parked_after_one_attempt`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
queue = PostgresQueue(clean)
queue.put("slow", _payload("slow"))
handler = EventHandler(
    queue,
    PostgresEffects(clean),
    TicketExtractor(FakeModel(error_rate=1.0)),
    SystemClock(),
    RetryPolicy(base_seconds=0.01, cap_seconds=0.02),
)
```

- `queue = PostgresQueue(clean)`: stores the result of calling `PostgresQueue(clean)`, which is this repository's own `PostgresQueue` (in `src/inbox_worker/infrastructure/postgres.py`): the delivery queue in `queue`.
- `queue.put("slow", _payload("slow"))`: calling `queue.put("slow", _payload("slow"))`.
- `handler = EventHandler( queue, PostgresEffects(clean), TicketExtrac...`: stores the result of calling `EventHandler( queue, PostgresEffects(clean), TicketExtractor(FakeModel(error_rate=1.0))...`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it in `handler`.

```python
delivery = queue.claim(1, 30)[0]
assert handler.handle(delivery) == RETRY
```

- `delivery = queue.claim(1, 30)[0]`: stores the item `queue.claim(1, 30)[0]` in `delivery`.
- `assert handler.handle(delivery) == RETRY`: checks that `handler.handle(delivery)` equals `RETRY`. A false check stops the test as failed.

```python
with clean.connection() as connection:
```

- `clean.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
status, available, error = connection.execute(
    "SELECT status, available_at > now() - interval '1 second', last_error FROM deliveries"
).fetchone()
```

- `status, available, error = connection.execute( "SELECT status, avai...`: unpacks the result of calling `connection.execute( "SELECT status, available_at > now() - interval '1 second', last_er...`, which takes the next row of the result into the names `status`, `available`, `error`, one item each.

```python
assert status == "queued" and "503" in error and available
queue.put("poison", _payload("poison", "POISON-SCHEMA cancel order 4417"))
parked = EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())
time.sleep(0.1)
```

- `assert status == "queued" and "503" in error and available`: checks that `status` equals `"queued"` and `"503"` is among `error` and `available` is truthy (not `None`, `False`, zero or empty). A false check stops the test as failed.
- `queue.put("poison", _payload("poison", "POISON-SCHEMA cancel order ...`: calling `queue.put("poison", _payload("poison", "POISON-SCHEMA cancel order 4417"))`.
- `parked = EventHandler(queue, PostgresEffects(clean), TicketExtracto...`: stores the result of calling `EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it in `parked`.
- `time.sleep(0.1)`: calling `time.sleep(0.1)`, which waits `0.1` seconds.

```python
for item in queue.claim(5, 30):
```

- Repeats the indented lines once for each item of `queue.claim(5, 30)`, naming the current item `item`.

```python
if item.event_id == "poison":
```

- Checks whether `item.event_id` equals `"poison"`. If so, the indented lines run.

```python
assert parked.handle(item) == DEAD
```

- `assert parked.handle(item) == DEAD`: checks that `parked.handle(item)` equals `DEAD`. A false check stops the test as failed.

```python
assert [(row[2], row[3]) for row in PostgresReports(clean).dead_events()] == [("permanent_error", 1)]
```

- `assert [(row[2], row[3]) for row in PostgresReports(clean).dead_eve...`: checks that `[(row[2], row[3]) for row in PostgresReports(clean).dead_events()]` equals `[("permanent_error", 1)]`. A false check stops the test as failed.

```python
def test_a_redriven_dead_letter_is_processed_exactly_once_through_the_normal_path(clean):
```

- Defines the test `test_a_redriven_dead_letter_is_processed_exactly_once_through_the_normal_path`.
- Parameters:
  - `clean`: a fixture (The database with every table emptied).

```python
queue = PostgresQueue(clean)
queue.put("fixme", _payload("fixme", "POISON-SCHEMA cancel order 4417"))
broken = EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())
assert broken.handle(queue.claim(1, 30)[0]) == DEAD
dead_id = PostgresReports(clean).dead_events()[0][0]
```

- `queue = PostgresQueue(clean)`: stores the result of calling `PostgresQueue(clean)`, which is this repository's own `PostgresQueue` (in `src/inbox_worker/infrastructure/postgres.py`): the delivery queue in `queue`.
- `queue.put("fixme", _payload("fixme", "POISON-SCHEMA cancel order 44...`: calling `queue.put("fixme", _payload("fixme", "POISON-SCHEMA cancel order 4417"))`.
- `broken = EventHandler(queue, PostgresEffects(clean), TicketExtracto...`: stores the result of calling `EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it in `broken`.
- `assert broken.handle(queue.claim(1, 30)[0]) == DEAD`: checks that `broken.handle(queue.claim(1, 30)[0])` equals `DEAD`. A false check stops the test as failed.
- `dead_id = PostgresReports(clean).dead_events()[0][0]`: stores the item `PostgresReports(clean).dead_events()[0][0]` in `dead_id`.

```python
with clean.connection() as connection:
```

- `clean.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
connection.execute(
    "UPDATE dead_letters SET payload = %s WHERE dead_id = %s",
    (_payload("fixme", "Please cancel order 4417."), dead_id),
)
```

- `connection.execute( "UPDATE dead_letters SET payload = %s WHERE dea...`: calling `connection.execute( "UPDATE dead_letters SET payload = %s WHERE dead_id = %s", (_payloa...`, which sends the SQL statement `"UPDATE dead_letters SET payload = %s WHERE dead_id = %s"` to the database.

```python
assert queue.redrive(dead_id) is not None and queue.redrive(dead_id) is None
fixed = EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())
assert fixed.handle(queue.claim(1, 30)[0]) == PROCESSED
assert PostgresReports(clean).counts()["tickets"] == 1 and PostgresReports(clean).dead_events() == []
```

- `assert queue.redrive(dead_id) is not None and queue.redrive(dead_id...`: checks that `queue.redrive(dead_id)` is something (not `None`) and `queue.redrive(dead_id)` is nothing (`None`). A false check stops the test as failed.
- `fixed = EventHandler(queue, PostgresEffects(clean), TicketExtractor...`: stores the result of calling `EventHandler(queue, PostgresEffects(clean), TicketExtractor(FakeModel()), SystemClock())`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it in `fixed`.
- `assert fixed.handle(queue.claim(1, 30)[0]) == PROCESSED`: checks that `fixed.handle(queue.claim(1, 30)[0])` equals `PROCESSED`. A false check stops the test as failed.
- `assert PostgresReports(clean).counts()["tickets"] == 1 and Postgres...`: checks that `PostgresReports(clean).counts()["tickets"]` equals `1` and `PostgresReports(clean).dead_events()` equals `[]`. A false check stops the test as failed.

#### `tests/live/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/live/test_claude_live.py`

```python
"""Opt-in: calls the real model with one email. Run with `make test-live` (RUN_LIVE=1 and ANTHROPIC_API_KEY set)."""
```

- The docstring (documentation kept with the code) says: *Opt-in: calls the real model with one email. Run with `make test-live` (RUN_LIVE=1 and ANTHROPIC_API_KEY set).*

```python
import os
from pathlib import Path

import pytest

from inbox_worker.infrastructure.claude_model import ClaudeModel
from inbox_worker.infrastructure.prompt_file import read_prompt

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("RUN_LIVE") != "1" or not os.environ.get("ANTHROPIC_API_KEY"),
        reason="set RUN_LIVE=1 and ANTHROPIC_API_KEY to call the real model",
    ),
]
```

- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `import pytest`: makes the module `pytest` available (the test framework).
- `from inbox_worker.infrastructure.claude_model import ...`: takes names from `inbox_worker.infrastructure.claude_model`, this repository's own code. (`ClaudeModel`: One Messages API call per request.)
- `from inbox_worker.infrastructure.prompt_file import ...`: takes names from `inbox_worker.infrastructure.prompt_file`, this repository's own code. (`read_prompt`: Read `---`, header lines, `---`, then the prompt text; both fences are required.)
- `pytestmark = [ pytest.mark.live, pytest.mark.skipif( os.environ.get...`: stores a new list holding 2 items in `pytestmark`.

```python
def test_the_real_model_extracts_a_valid_ticket_from_a_cancel_email():
```

- Defines the test `test_the_real_model_extracts_a_valid_ticket_from_a_cancel_email`.

```python
from inbox_worker.application.extraction import TicketExtractor

prompt = read_prompt(Path(__file__).resolve().parents[2] / "prompts/extract.v1.md")
model = ClaudeModel(os.environ.get("MODEL_ID", "claude-haiku-5-5"), os.environ["ANTHROPIC_API_KEY"])
result = TicketExtractor(model, prompt.text, prompt.version).extract(
    "Hi, please cancel order 4417, it was a mistake."
)
assert result.ticket.intent == "cancel" and result.ticket.order_number == "4417" and result.calls <= 2
```

- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`TicketExtractor`: Model-backed extraction.)
- `prompt = read_prompt(Path(__file__).resolve().parents[2] / "prompts...`: stores the result of calling `read_prompt(Path(__file__).resolve().parents[2] / "prompts/extract.v1.md")`, which is this repository's own `read_prompt` (in `src/inbox_worker/infrastructure/prompt_file.py`): read `---`, header lines, `---`, then the prompt text; both fences are required in `prompt`.
- `model = ClaudeModel(os.environ.get("MODEL_ID", "claude-haiku-5-5"),...`: stores the result of calling `ClaudeModel(os.environ.get("MODEL_ID", "claude-haiku-5-5"), os.environ["ANTHROPIC_API_K...`, which is this repository's own `ClaudeModel` (in `src/inbox_worker/infrastructure/claude_model.py`): one Messages API call per request in `model`.
- `result = TicketExtractor(model, prompt.text, prompt.version).extrac...`: stores the result of calling `TicketExtractor(model, prompt.text, prompt.version).extract( "Hi, please cancel order 4...`, which is this repository's own `extract` (in `src/inbox_worker/application/extraction.py`): one call, and one repair call when the reply is not a valid ticket in `result`.
- `assert result.ticket.intent == "cancel" and result.ticket.order_num...`: checks that `result.ticket.intent` equals `"cancel"` and `result.ticket.order_number` equals `"4417"` and `result.calls` is less than or equal to `2`. A false check stops the test as failed.

#### `tests/unit/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/unit/application/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/unit/application/fakes.py`

```python
"""In-memory stand-ins for the ports, shared by the application tests."""
```

- The docstring (documentation kept with the code) says: *In-memory stand-ins for the ports, shared by the application tests.*

```python
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from inbox_worker.application.ports import Delivery, ModelReply
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Callable`: the type hint for a function value.) (`Sequence`: the type hint for an ordered, indexable collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.) (`field`: describes one dataclass field in more detail (its default, or how to build the default).)
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`UTC`: the UTC time zone.) (`datetime`: the date-and-time type.) (`timedelta`: a span of time.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.)
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`Delivery`: One queue message: a delivery of an event.) (`ModelReply`: The model's text and what the call used.)

```python
from inbox_worker.domain.ticket import Ticket

START = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)
VALID = '{"intent": "cancel", "order_number": "4417", "sentiment": "neutral", "requested_action": "cancel_order"}'
```

- `from inbox_worker.domain.ticket import ...`: takes names from `inbox_worker.domain.ticket`, this repository's own code. (`Ticket`: What the customer wants, about which order, in what mood, and the action it asks for.)
- `START = datetime(2026, 10, 27, 9, 0, tzinfo=UTC)`: stores the result of calling `datetime(2026, 10, 27, 9, 0, tzinfo=UTC)` The named values are `tzinfo`. in `START`.
- `VALID = '{"intent": "cancel", "order_number": "4417", "sentiment": ...`: stores the text `'{"intent": "cancel", "order_number": "4417", "sentiment": "neutral", "requested_action...` in `VALID`.

```python
class FixedClock:
```

- Defines the class `FixedClock`.

> **A class.** `class Name:` defines a new kind of object. The functions inside it are methods; the first parameter, called `self` by habit, is the object the method was called on. `__init__` runs when an object is made. `Name(...)` makes an object (an instance) of the class. A class listed in brackets after the name is a base class: the new class inherits its methods.

```python
"""A clock the test moves by hand."""
```

- The docstring (documentation kept with the code) says: *A clock the test moves by hand.*

```python
def __init__(self) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
self.current = START
```

- `self.current = START`: stores the value of `START` in `self.current`.

```python
def now(self) -> datetime:
```

- Defines the method `now`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `datetime`.

```python
return self.current
```

- `return self.current`: ends the function and gives back `self.current`.

```python
def advance(self, seconds: float) -> None:
```

- Defines the method `advance`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `seconds`, type `float`.
- Gives back a value of type `None`.

```python
self.current += timedelta(seconds=seconds)
```

- `self.current += timedelta(seconds=seconds)`: adds `timedelta(seconds=seconds)` to `self.current` and keeps the result there.

```python
@dataclass
class MemoryQueue:
```

- Defines the class `MemoryQueue`.
- `@dataclass`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields.

> **`@dataclass`.** A decorator is a line starting with `@` that wraps the definition below it. `@dataclass` reads the annotated fields in the class body and writes `__init__`, `__repr__` and `__eq__` for the class. `frozen=True` makes the objects read-only after creation, so an accidental change raises an error. `slots=True` stores attributes more compactly.

```python
"""The queue in memory: deliveries by id with a status, and the calls the handler made."""
```

- The docstring (documentation kept with the code) says: *The queue in memory: deliveries by id with a status, and the calls the handler made.*

```python
items: dict[int, dict[str, Any]] = field(default_factory=dict)
retries: list[tuple[int, float, str]] = field(default_factory=list)
dead: list[tuple[int, str, str]] = field(default_factory=list)
acked: list[int] = field(default_factory=list)
```

- `items: dict[int, dict[str, Any]] = field(default_factory=dict)`: a field named `items` of type `dict[int, dict[str, Any]]`, default `field(default_factory=dict)`.
- `retries: list[tuple[int, float, str]] = field(default_factory=list)`: a field named `retries` of type `list[tuple[int, float, str]]`, default `field(default_factory=list)`.
- `dead: list[tuple[int, str, str]] = field(default_factory=list)`: a field named `dead` of type `list[tuple[int, str, str]]`, default `field(default_factory=list)`.
- `acked: list[int] = field(default_factory=list)`: a field named `acked` of type `list[int]`, default `field(default_factory=list)`.

```python
def put(self, event_id: str, payload: str) -> int:
```

- Defines the method `put`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
  - `payload`, type `str`.
- Gives back a value of type `int`.

```python
delivery_id = len(self.items) + 1
self.items[delivery_id] = {"event_id": event_id, "payload": payload, "status": "queued", "attempts": 0}
return delivery_id
```

- `delivery_id = len(self.items) + 1`: stores `len(self.items) + 1`, which adds `len(self.items)` and `1` in `delivery_id`.
- `self.items[delivery_id] = {"event_id": event_id, "payload": payload...`: stores a new dict with 4 entries in the slot `self.items[delivery_id]`.
- `return delivery_id`: ends the function and gives back the value of `delivery_id`.

```python
def claim(self, limit: int, lease_seconds: float) -> Sequence[Delivery]:
```

- Defines the method `claim`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`.
  - `lease_seconds`, type `float`.
- Gives back a value of type `Sequence[Delivery]`.

```python
claimed: list[Delivery] = []
```

- `claimed: list[Delivery] = []`: stores a new list (empty) in `claimed`, whose type is declared as `list[Delivery]`.

> **A type hint.** `x: int = 5` stores 5 in `x` and records that `x` is meant to hold an `int`. Python itself does not enforce the hint; the type checker `mypy` reads it before the program runs and complains if the code disagrees.

```python
for delivery_id, item in self.items.items():
```

- Repeats the indented lines once for each item of `self.items.items()`, naming the current item the names `delivery_id`, `item`.

```python
if item["status"] == "queued" and len(claimed) < limit:
```

- Checks whether `item["status"]` equals `"queued"` and `len(claimed)` is less than `limit`. If so, the indented lines run.

```python
item["status"] = "processing"
item["attempts"] += 1
claimed.append(Delivery(delivery_id, item["event_id"], item["payload"], START, item["attempts"]))
```

- `item["status"] = "processing"`: stores the text `'processing'` in the slot `item["status"]`.
- `item["attempts"] += 1`: adds `1` to `item["attempts"]` and keeps the result there.
- `claimed.append(Delivery(delivery_id, item["event_id"], item["payloa...`: calling `claimed.append(Delivery(delivery_id, item["event_id"], item["payload"], START, item["at...`, which adds `Delivery(delivery_id, item["event_id"], item["payload"], START, item["attempts"])` to the end of `claimed`.

```python
return claimed
```

- `return claimed`: ends the function and gives back the value of `claimed`.

```python
def ack(self, delivery_id: int) -> None:
```

- Defines the method `ack`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery_id`, type `int`.
- Gives back a value of type `None`.

```python
self.items.setdefault(delivery_id, {})["status"] = "done"
self.acked.append(delivery_id)
```

- `self.items.setdefault(delivery_id, {})["status"] = "done"`: stores the text `'done'` in the slot `self.items.setdefault(delivery_id, {})["status"]`.
- `self.acked.append(delivery_id)`: calling `self.acked.append(delivery_id)`, which adds `delivery_id` to the end of `self.acked`.

```python
def retry(self, delivery_id: int, delay_seconds: float, error: str) -> None:
```

- Defines the method `retry`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery_id`, type `int`.
  - `delay_seconds`, type `float`.
  - `error`, type `str`.
- Gives back a value of type `None`.

```python
self.items.setdefault(delivery_id, {})["status"] = "queued"
self.retries.append((delivery_id, delay_seconds, error))
```

- `self.items.setdefault(delivery_id, {})["status"] = "queued"`: stores the text `'queued'` in the slot `self.items.setdefault(delivery_id, {})["status"]`.
- `self.retries.append((delivery_id, delay_seconds, error))`: calling `self.retries.append((delivery_id, delay_seconds, error))`, which adds `(delivery_id, delay_seconds, error)` to the end of `self.retries`.

```python
def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:
```

- Defines the method `dead_letter`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery`, type `Delivery`.
  - `reason`, type `str`.
  - `error`, type `str`.
- Gives back a value of type `None`.

```python
self.items.setdefault(delivery.delivery_id, {})["status"] = "dead"
self.dead.append((delivery.delivery_id, reason, error))
```

- `self.items.setdefault(delivery.delivery_id, {})["status"] = "dead"`: stores the text `'dead'` in the slot `self.items.setdefault(delivery.delivery_id, {})["status"]`.
- `self.dead.append((delivery.delivery_id, reason, error))`: calling `self.dead.append((delivery.delivery_id, reason, error))`, which adds `(delivery.delivery_id, reason, error)` to the end of `self.dead`.

```python
def depth(self) -> int:
```

- Defines the method `depth`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `int`.

```python
return sum(item.get("status") in ("queued", "processing") for item in self.items.values())
```

- `return sum(item.get("status") in ("queued", "processing") for item ...`: ends the function and gives back the result of calling `sum(item.get("status") in ("queued", "processing") for item in self.items.values())`, which adds up the numbers in `(item.get("status") in ("queued", "processing") for item in self.items.values())`.

```python
@dataclass
class MemoryEffects:
```

- Defines the class `MemoryEffects`.
- `@dataclass`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields.

```python
"""The effects store in memory; `apply` returns False for an event that already has a mark."""
```

- The docstring (documentation kept with the code) says: *The effects store in memory; `apply` returns False for an event that already has a mark.*

```python
processed: dict[str, Ticket] = field(default_factory=dict)
```

- `processed: dict[str, Ticket] = field(default_factory=dict)`: a field named `processed` of type `dict[str, Ticket]`, default `field(default_factory=dict)`.

```python
def is_processed(self, event_id: str) -> bool:
```

- Defines the method `is_processed`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
- Gives back a value of type `bool`.

```python
return event_id in self.processed
```

- `return event_id in self.processed`: ends the function and gives back whether `event_id` is among `self.processed`.

```python
def apply(self, event_id: str, ticket: Ticket) -> bool:
```

- Defines the method `apply`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
  - `ticket`, type `Ticket`.
- Gives back a value of type `bool`.

```python
if event_id in self.processed:
```

- Checks whether `event_id` is among `self.processed`. If so, the indented lines run.

```python
return False
```

- `return False`: ends the function and gives back `False`.

```python
self.processed[event_id] = ticket
return True
```

- `self.processed[event_id] = ticket`: stores the value of `ticket` in the slot `self.processed[event_id]`.
- `return True`: ends the function and gives back `True`.

```python
class ScriptedModel:
```

- Defines the class `ScriptedModel`.

```python
"""Replies from a queue of texts or exceptions; an unscripted call fails the test."""
```

- The docstring (documentation kept with the code) says: *Replies from a queue of texts or exceptions; an unscripted call fails the test.*

```python
def __init__(self, *script: str | Exception | Callable[[str], str]) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `*script`: collects extra positional arguments in a tuple.
- Gives back a value of type `None`.

```python
self._script = list(script)
self.calls: list[str] = []
```

- `self._script = list(script)`: stores the result of calling `list(script)`, which builds a new list from `script` in `self._script`.
- `self.calls: list[str] = []`: stores a new list (empty) in `self.calls`, whose type is declared as `list[str]`.

```python
def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
```

- Defines the method `complete`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `system`, type `str`.
  - `user`, type `str`.
  - `prompt_version`, type `str`.
- Gives back a value of type `ModelReply`.

```python
self.calls.append(user)
```

- `self.calls.append(user)`: calling `self.calls.append(user)`, which adds `user` to the end of `self.calls`.

```python
if not self._script:
```

- Checks whether it is not the case that `self._script` is truthy. If so, the indented lines run.

```python
raise AssertionError(f"unexpected extra call #{len(self.calls)}")
```

- `raise AssertionError(f"unexpected extra call #{len(self.calls)}")`: stops with an error of kind `AssertionError` with the message `f"unexpected extra call #{len(self.calls)}"`. Whoever called this code must handle it or the program stops.

```python
item = self._script.pop(0)
```

- `item = self._script.pop(0)`: stores the result of calling `self._script.pop(0)`, which removes and returns an item of `self._script` in `item`.

```python
if isinstance(item, Exception):
```

- Checks whether `isinstance(item, Exception)` is true (the call asks whether `item` is a `Exception`). If so, the indented lines run.

```python
raise item
```

- `raise item`: raises the error `item`.

```python
return ModelReply(item(user) if callable(item) else item, "scripted", 10, 5)
```

- `return ModelReply(item(user) if callable(item) else item, "scripted...`: ends the function and gives back the result of calling `ModelReply(item(user) if callable(item) else item, "scripted", 10, 5)`, which is this repository's own `ModelReply` (in `src/inbox_worker/application/ports.py`): the model's text and what the call used.

```python
def delivery(
    event_id: str = "e-1", body: str = "Please cancel order 4417.", attempts: int = 1, delivery_id: int = 1
) -> Delivery:
```

- Defines the function `delivery`.
- Parameters:
  - `event_id`, type `str`, optional (default `"e-1"`).
  - `body`, type `str`, optional (default `"Please cancel order 4417."`).
  - `attempts`, type `int`, optional (default `1`).
  - `delivery_id`, type `int`, optional (default `1`).
- Gives back a value of type `Delivery`.

```python
import json

return Delivery(delivery_id, event_id, json.dumps({"event_id": event_id, "body": body}), START, attempts)
```

- `import json`: makes the module `json` available (reads and writes JSON text).
- `return Delivery(delivery_id, event_id, json.dumps({"event_id": even...`: ends the function and gives back the result of calling `Delivery(delivery_id, event_id, json.dumps({"event_id": event_id, "body": body}), START...`, which is this repository's own `Delivery` (in `src/inbox_worker/application/ports.py`): one queue message: a delivery of an event.

#### `tests/unit/application/test_handler_worker.py`

- This file has no docstring at the top.

```python
import json
import random

import pytest

from inbox_worker.application.extraction import TicketExtractor
from inbox_worker.application.generate_events import generate_events
from inbox_worker.application.handler import DEAD, DUPLICATE, PROCESSED, RETRY, EventHandler, RetryPolicy
```

- `import json`: makes the module `json` available (reads and writes JSON text).
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `import pytest`: makes the module `pytest` available (the test framework).
- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`TicketExtractor`: Model-backed extraction.)
- `from inbox_worker.application.generate_events import ...`: takes names from `inbox_worker.application.generate_events`, this repository's own code. (`generate_events`: `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable.)
- `from inbox_worker.application.handler import ...`: takes names from `inbox_worker.application.handler`, this repository's own code. (`DEAD`: a name defined in this repository.) (`DUPLICATE`: a name defined in this repository.) (`PROCESSED`: a name defined in this repository.) (`RETRY`: a name defined in this repository.) (`EventHandler`: Applies each event's effects once, however often the queue delivers it.) (`RetryPolicy`: How a failing event is retried before it is parked.)

```python
from inbox_worker.application.outbox import DuplicateSendError, OutboxRelay
from inbox_worker.application.worker import Worker
from inbox_worker.domain.errors import ModelCallError, RetryableModelError
from tests.unit.application.fakes import VALID, FixedClock, MemoryEffects, MemoryQueue, ScriptedModel, delivery
```

- `from inbox_worker.application.outbox import ...`: takes names from `inbox_worker.application.outbox`, this repository's own code. (`DuplicateSendError`: The mail gateway has already sent this event's acknowledgment.) (`OutboxRelay`: Sends unsent outbox rows.)
- `from inbox_worker.application.worker import ...`: takes names from `inbox_worker.application.worker`, this repository's own code. (`Worker`: Pulls batches from the queue.)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`ModelCallError`: A model call failed in a way a retry will not fix.) (`RetryableModelError`: A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection.)
- `from tests.unit.application.fakes import ...`: takes names from `tests.unit.application.fakes`, this repository's own code. (`VALID`: a name defined in this repository.) (`FixedClock`: A clock the test moves by hand.) (`MemoryEffects`: The effects store in memory; `apply` returns False for an event that already has a mark.) (`MemoryQueue`: The queue in memory: deliveries by id with a status, and the calls the handler made.) (`ScriptedModel`: Replies from a queue of texts or exceptions; an unscripted call fails the test.) (`delivery`: a name defined in this repository.)

```python
def _recorder(into: list[float]):
```

- Defines the function `_recorder`.
- Parameters:
  - `into`, type `list[float]`.

```python
def wait(seconds: float) -> bool:
```

- Defines the function `wait`.
- Parameters:
  - `seconds`, type `float`.
- Gives back a value of type `bool`.

```python
into.append(seconds)
return False
```

- `into.append(seconds)`: calling `into.append(seconds)`, which adds `seconds` to the end of `into`.
- `return False`: ends the function and gives back `False`.

```python
return wait
```

- `return wait`: ends the function and gives back the value of `wait`.

```python
def _handler(model, queue=None, effects=None, clock=None, policy=None, crash=None):
```

- Defines the function `_handler`.
- Parameters:
  - `model`.
  - `queue`, optional (default `None`).
  - `effects`, optional (default `None`).
  - `clock`, optional (default `None`).
  - `policy`, optional (default `None`).
  - `crash`, optional (default `None`).

```python
queue = queue if queue is not None else MemoryQueue()
handler = EventHandler(
    queue,
    effects if effects is not None else MemoryEffects(),
    TicketExtractor(model),
    clock or FixedClock(),
    policy or RetryPolicy(),
    rng=random.Random(1),
    crash_at=crash or (lambda point: None),
)
```

- `queue = queue if queue is not None else MemoryQueue()`: stores `queue` when `queue` is something (not `None`), otherwise `MemoryQueue()` in `queue`.
- `handler = EventHandler( queue, effects if effects is not None else ...`: stores the result of calling `EventHandler( queue, effects if effects is not None else MemoryEffects(), TicketExtract...`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it in `handler`.

> **`a if cond else b`.** An expression that gives `a` when the condition holds and `b` otherwise.

```python
return handler, queue
```

- `return handler, queue`: ends the function and gives back a tuple of 2 items.

```python
def test_a_new_event_is_extracted_applied_once_and_acknowledged():
```

- Defines the test `test_a_new_event_is_extracted_applied_once_and_acknowledged`.

```python
effects = MemoryEffects()
queue = MemoryQueue()
queue.put("e-1", "x")
handler, _ = _handler(ScriptedModel(VALID), queue, effects)
assert handler.handle(delivery()) == PROCESSED
assert effects.processed["e-1"].intent == "cancel" and queue.acked == [1]
```

- `effects = MemoryEffects()`: stores the result of calling `MemoryEffects()`, which is this repository's own `MemoryEffects` (in `tests/unit/application/fakes.py`): the effects store in memory; `apply` returns False for an event that already has a mark in `effects`.
- `queue = MemoryQueue()`: stores the result of calling `MemoryQueue()`, which is this repository's own `MemoryQueue` (in `tests/unit/application/fakes.py`): the queue in memory: deliveries by id with a status, and the calls the handler made in `queue`.
- `queue.put("e-1", "x")`: calling `queue.put("e-1", "x")`.
- `handler, _ = _handler(ScriptedModel(VALID), queue, effects)`: unpacks the result of calling `_handler(ScriptedModel(VALID), queue, effects)` into the names `handler`, `_`, one item each.
- `assert handler.handle(delivery()) == PROCESSED`: checks that `handler.handle(delivery())` equals `PROCESSED`. A false check stops the test as failed.
- `assert effects.processed["e-1"].intent == "cancel" and queue.acked ...`: checks that `effects.processed["e-1"].intent` equals `"cancel"` and `queue.acked` equals `[1]`. A false check stops the test as failed.

```python
def test_a_delivery_of_an_event_that_was_already_applied_skips_the_model_and_is_acknowledged():
```

- Defines the test `test_a_delivery_of_an_event_that_was_already_applied_skips_the_model_and_is_acknowledged`.

```python
effects = MemoryEffects()
model = ScriptedModel(VALID)
handler, queue = _handler(model, effects=effects)
queue.put("e-1", "x")
handler.handle(delivery())
queue.put("e-1", "x")
```

- `effects = MemoryEffects()`: stores the result of calling `MemoryEffects()`, which is this repository's own `MemoryEffects` (in `tests/unit/application/fakes.py`): the effects store in memory; `apply` returns False for an event that already has a mark in `effects`.
- `model = ScriptedModel(VALID)`: stores the result of calling `ScriptedModel(VALID)`, which is this repository's own `ScriptedModel` (in `tests/unit/application/fakes.py`): replies from a queue of texts or exceptions; an unscripted call fails the test in `model`.
- `handler, queue = _handler(model, effects=effects)`: unpacks the result of calling `_handler(model, effects=effects)` The named values are `effects`. into the names `handler`, `queue`, one item each.
- `queue.put("e-1", "x")`: calling `queue.put("e-1", "x")`.
- `handler.handle(delivery())`: calling `handler.handle(delivery())`, which is this repository's own `handle` (in `src/inbox_worker/application/handler.py`): process one delivery to a final outcome, acknowledging it unless the process dies first.
- `queue.put("e-1", "x")`: calling `queue.put("e-1", "x")`.

```python
assert handler.handle(delivery(delivery_id=2)) == DUPLICATE
assert len(model.calls) == 1 and len(effects.processed) == 1
```

- `assert handler.handle(delivery(delivery_id=2)) == DUPLICATE`: checks that `handler.handle(delivery(delivery_id=2))` equals `DUPLICATE`. A false check stops the test as failed.
- `assert len(model.calls) == 1 and len(effects.processed) == 1`: checks that `len(model.calls)` equals `1` and `len(effects.processed)` equals `1`. A false check stops the test as failed.

```python
def test_a_twin_delivery_that_commits_first_makes_this_one_a_duplicate():
```

- Defines the test `test_a_twin_delivery_that_commits_first_makes_this_one_a_duplicate`.

```python
class RacingEffects(MemoryEffects):
```

- Defines the class `RacingEffects`.
- It extends `MemoryEffects` (it starts with all of that class's methods and may add or replace some).

```python
def is_processed(self, event_id: str) -> bool:
```

- Defines the method `is_processed`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
- Gives back a value of type `bool`.

```python
return False
```

- `return False`: ends the function and gives back `False`.

```python
effects = RacingEffects()
handler, _ = _handler(ScriptedModel(VALID, VALID), effects=effects)
assert handler.handle(delivery()) == PROCESSED
assert handler.handle(delivery(delivery_id=2)) == DUPLICATE
assert len(effects.processed) == 1
```

- `effects = RacingEffects()`: stores the result of calling `RacingEffects()`, which makes a `RacingEffects` object in `effects`.
- `handler, _ = _handler(ScriptedModel(VALID, VALID), effects=effects)`: unpacks the result of calling `_handler(ScriptedModel(VALID, VALID), effects=effects)` The named values are `effects`. into the names `handler`, `_`, one item each.
- `assert handler.handle(delivery()) == PROCESSED`: checks that `handler.handle(delivery())` equals `PROCESSED`. A false check stops the test as failed.
- `assert handler.handle(delivery(delivery_id=2)) == DUPLICATE`: checks that `handler.handle(delivery(delivery_id=2))` equals `DUPLICATE`. A false check stops the test as failed.
- `assert len(effects.processed) == 1`: checks that `len(effects.processed)` equals `1`. A false check stops the test as failed.

```python
def test_the_model_runs_before_the_effects_and_the_crash_points_are_reported_in_order():
```

- Defines the test `test_the_model_runs_before_the_effects_and_the_crash_points_are_reported_in_order`.

```python
points: list[str] = []
handler, _ = _handler(ScriptedModel(VALID), crash=lambda point: points.append(point))
handler.handle(delivery())
assert points == ["after_model", "after_commit"]
```

- `points: list[str] = []`: stores a new list (empty) in `points`, whose type is declared as `list[str]`.
- `handler, _ = _handler(ScriptedModel(VALID), crash=lambda point: poi...`: unpacks the result of calling `_handler(ScriptedModel(VALID), crash=lambda point: points.append(point))` The named values are `crash`. into the names `handler`, `_`, one item each.
- `handler.handle(delivery())`: calling `handler.handle(delivery())`, which is this repository's own `handle` (in `src/inbox_worker/application/handler.py`): process one delivery to a final outcome, acknowledging it unless the process dies first.
- `assert points == ["after_model", "after_commit"]`: checks that `points` equals `["after_model", "after_commit"]`. A false check stops the test as failed.

```python
def test_a_crash_after_the_model_call_leaves_nothing_behind_and_a_crash_after_the_commit_leaves_one_ticket():
```

- Defines the test `test_a_crash_after_the_model_call_leaves_nothing_behind_and_a_crash_after_the_commit_leaves_one_ticket`.

```python
class CrashError(Exception):
```

- Defines the class `CrashError`.
- It extends `Exception`: it is a kind of error that can be raised and caught.

```python
pass
```

- `pass`: does nothing; it fills a place where a statement is required.

```python
def die_at(target):
```

- Defines the function `die_at`.
- Parameters:
  - `target`.

```python
def hook(point):
```

- Defines the function `hook`.
- Parameters:
  - `point`.

```python
if point == target:
```

- Checks whether `point` equals `target`. If so, the indented lines run.

```python
raise CrashError
```

- `raise CrashError`: raises the error `CrashError`.

```python
return hook
```

- `return hook`: ends the function and gives back the value of `hook`.

```python
effects, queue = MemoryEffects(), MemoryQueue()
queue.put("e-1", "x")
handler, _ = _handler(ScriptedModel(VALID), queue, effects, crash=die_at("after_model"))
```

- `effects, queue = MemoryEffects(), MemoryQueue()`: unpacks a tuple of 2 items into the names `effects`, `queue`, one item each.
- `queue.put("e-1", "x")`: calling `queue.put("e-1", "x")`.
- `handler, _ = _handler(ScriptedModel(VALID), queue, effects, crash=d...`: unpacks the result of calling `_handler(ScriptedModel(VALID), queue, effects, crash=die_at("after_model"))` The named values are `crash`. into the names `handler`, `_`, one item each.

```python
with pytest.raises(CrashError):
```

- `pytest.raises(CrashError)`: the test passes only if the indented lines raise `CrashError`; it fails if nothing is raised.

```python
handler.handle(delivery())
```

- `handler.handle(delivery())`: calling `handler.handle(delivery())`, which is this repository's own `handle` (in `src/inbox_worker/application/handler.py`): process one delivery to a final outcome, acknowledging it unless the process dies first.

```python
assert effects.processed == {} and queue.acked == []
survivor, _ = _handler(ScriptedModel(VALID), queue, effects, crash=die_at("after_commit"))
```

- `assert effects.processed == {} and queue.acked == []`: checks that `effects.processed` equals `{}` and `queue.acked` equals `[]`. A false check stops the test as failed.
- `survivor, _ = _handler(ScriptedModel(VALID), queue, effects, crash=...`: unpacks the result of calling `_handler(ScriptedModel(VALID), queue, effects, crash=die_at("after_commit"))` The named values are `crash`. into the names `survivor`, `_`, one item each.

```python
with pytest.raises(CrashError):
```

- `pytest.raises(CrashError)`: the test passes only if the indented lines raise `CrashError`; it fails if nothing is raised.

```python
survivor.handle(delivery())
```

- `survivor.handle(delivery())`: calling `survivor.handle(delivery())`, which is this repository's own `handle` (in `src/inbox_worker/application/handler.py`): process one delivery to a final outcome, acknowledging it unless the process dies first.

```python
assert list(effects.processed) == ["e-1"] and queue.acked == []
again, _ = _handler(ScriptedModel(), queue, effects)
assert again.handle(delivery()) == DUPLICATE and queue.acked == [1] and len(effects.processed) == 1
```

- `assert list(effects.processed) == ["e-1"] and queue.acked == []`: checks that `list(effects.processed)` equals `["e-1"]` and `queue.acked` equals `[]`. A false check stops the test as failed.
- `again, _ = _handler(ScriptedModel(), queue, effects)`: unpacks the result of calling `_handler(ScriptedModel(), queue, effects)` into the names `again`, `_`, one item each.
- `assert again.handle(delivery()) == DUPLICATE and queue.acked == [1]...`: checks that `again.handle(delivery())` equals `DUPLICATE` and `queue.acked` equals `[1]` and `len(effects.processed)` equals `1`. A false check stops the test as failed.

```python
@pytest.mark.parametrize(
    ("payload", "reason"),
    [("{broken", "malformed_event"), (json.dumps({"event_id": "e-1", "body": "x" * 100_001}), "event_too_large")],
)
def test_a_poison_event_is_dead_lettered_at_once_with_its_reason_and_the_model_is_never_called(payload, reason):
```

- Defines the test `test_a_poison_event_is_dead_lettered_at_once_with_its_reason_and_the_model_is_never_called`.
- `@pytest.mark.parametrize( ("payload", "reason"), [("{broken", "malformed_event...`: runs the test once per listed set of values.
- Parameters:
  - `payload`.
  - `reason`.

```python
model = ScriptedModel()
handler, queue = _handler(model)
queue.put("e-1", payload)
bad = delivery()
bad = type(bad)(bad.delivery_id, bad.event_id, payload, bad.received_at, 1)
assert handler.handle(bad) == DEAD
```

- `model = ScriptedModel()`: stores the result of calling `ScriptedModel()`, which is this repository's own `ScriptedModel` (in `tests/unit/application/fakes.py`): replies from a queue of texts or exceptions; an unscripted call fails the test in `model`.
- `handler, queue = _handler(model)`: unpacks the result of calling `_handler(model)` into the names `handler`, `queue`, one item each.
- `queue.put("e-1", payload)`: calling `queue.put("e-1", payload)`.
- `bad = delivery()`: stores the result of calling `delivery()` in `bad`.
- `bad = type(bad)(bad.delivery_id, bad.event_id, payload, bad.receive...`: stores the result of calling `type(bad)(bad.delivery_id, bad.event_id, payload, bad.received_at, 1)` in `bad`.
- `assert handler.handle(bad) == DEAD`: checks that `handler.handle(bad)` equals `DEAD`. A false check stops the test as failed.

```python
assert queue.dead[0][1] == reason and model.calls == []
```

- `assert queue.dead[0][1] == reason and model.calls == []`: checks that `queue.dead[0][1]` equals `reason` and `model.calls` equals `[]`. A false check stops the test as failed.

```python
def test_a_schema_failure_after_one_repair_is_dead_lettered_after_exactly_one_attempt():
```

- Defines the test `test_a_schema_failure_after_one_repair_is_dead_lettered_after_exactly_one_attempt`.

```python
handler, queue = _handler(ScriptedModel("nope", "still nope"))
queue.put("e-1", "x")
assert handler.handle(delivery(attempts=1)) == DEAD
assert queue.dead[0][1] == "permanent_error" and "after one repair" in queue.dead[0][2] and queue.retries == []
```

- `handler, queue = _handler(ScriptedModel("nope", "still nope"))`: unpacks the result of calling `_handler(ScriptedModel("nope", "still nope"))` into the names `handler`, `queue`, one item each.
- `queue.put("e-1", "x")`: calling `queue.put("e-1", "x")`.
- `assert handler.handle(delivery(attempts=1)) == DEAD`: checks that `handler.handle(delivery(attempts=1))` equals `DEAD`. A false check stops the test as failed.
- `assert queue.dead[0][1] == "permanent_error" and "after one repair"...`: checks that `queue.dead[0][1]` equals `"permanent_error"` and `"after one repair"` is among `queue.dead[0][2]` and `queue.retries` equals `[]`. A false check stops the test as failed.

```python
def test_a_retryable_error_is_retried_with_a_jittered_delay_that_grows_until_the_attempts_run_out():
```

- Defines the test `test_a_retryable_error_is_retried_with_a_jittered_delay_that_grows_until_the_attempts_run_out`.

```python
queue = MemoryQueue()
queue.put("e-1", "x")
delays = []
```

- `queue = MemoryQueue()`: stores the result of calling `MemoryQueue()`, which is this repository's own `MemoryQueue` (in `tests/unit/application/fakes.py`): the queue in memory: deliveries by id with a status, and the calls the handler made in `queue`.
- `queue.put("e-1", "x")`: calling `queue.put("e-1", "x")`.
- `delays = []`: stores a new list (empty) in `delays`.

```python
for attempt in range(1, 5):
```

- Repeats the indented lines once for each item of `range(1, 5)`, naming the current item `attempt`.

```python
handler, _ = _handler(
    ScriptedModel(RetryableModelError("429")),
    queue,
    policy=RetryPolicy(max_attempts=5, base_seconds=1.0, cap_seconds=10.0),
)
assert handler.handle(delivery(attempts=attempt)) == RETRY
delays.append(queue.retries[-1][1])
```

- `handler, _ = _handler( ScriptedModel(RetryableModelError("429")), q...`: unpacks the result of calling `_handler( ScriptedModel(RetryableModelError("429")), queue, policy=RetryPolicy(max_atte...` The named values are `policy`. into the names `handler`, `_`, one item each.
- `assert handler.handle(delivery(attempts=attempt)) == RETRY`: checks that `handler.handle(delivery(attempts=attempt))` equals `RETRY`. A false check stops the test as failed.
- `delays.append(queue.retries[-1][1])`: calling `delays.append(queue.retries[-1][1])`, which adds `queue.retries[-1][1]` to the end of `delays`.

```python
assert all(0 <= delay <= min(10.0, 2 ** (attempt)) for attempt, delay in enumerate(delays))
handler, _ = _handler(ScriptedModel(RetryableModelError("429")), queue, policy=RetryPolicy(max_attempts=5))
assert handler.handle(delivery(attempts=5)) == DEAD and queue.dead[-1][1] == "attempts_exhausted"
```

- `assert all(0 <= delay <= min(10.0, 2 ** (attempt)) for attempt, del...`: checks that `all(0 <= delay <= min(10.0, 2 ** (attempt)) for attempt, delay in enumerate(delays))` is true (the call is true if every item of `(0 <= delay <= min(10.0, 2 ** (attempt)) for attempt, delay in enumerate(delays))` is true). A false check stops the test as failed.
- `handler, _ = _handler(ScriptedModel(RetryableModelError("429")), qu...`: unpacks the result of calling `_handler(ScriptedModel(RetryableModelError("429")), queue, policy=RetryPolicy(max_attem...` The named values are `policy`. into the names `handler`, `_`, one item each.
- `assert handler.handle(delivery(attempts=5)) == DEAD and queue.dead[...`: checks that `handler.handle(delivery(attempts=5))` equals `DEAD` and `queue.dead[-1][1]` equals `"attempts_exhausted"`. A false check stops the test as failed.

```python
def test_an_error_a_retry_cannot_fix_is_parked_without_retrying():
```

- Defines the test `test_an_error_a_retry_cannot_fix_is_parked_without_retrying`.

```python
handler, queue = _handler(ScriptedModel(ModelCallError("401")))
assert handler.handle(delivery()) == DEAD and queue.dead[0][1] == "permanent_error" and queue.retries == []
```

- `handler, queue = _handler(ScriptedModel(ModelCallError("401")))`: unpacks the result of calling `_handler(ScriptedModel(ModelCallError("401")))` into the names `handler`, `queue`, one item each.
- `assert handler.handle(delivery()) == DEAD and queue.dead[0][1] == "...`: checks that `handler.handle(delivery())` equals `DEAD` and `queue.dead[0][1]` equals `"permanent_error"` and `queue.retries` equals `[]`. A false check stops the test as failed.

```python
def test_an_event_that_waited_longer_than_its_deadline_is_parked_before_the_model_is_called():
```

- Defines the test `test_an_event_that_waited_longer_than_its_deadline_is_parked_before_the_model_is_called`.

```python
clock = FixedClock()
clock.advance(600)
model = ScriptedModel()
handler, queue = _handler(model, clock=clock, policy=RetryPolicy(event_deadline_seconds=300))
assert handler.handle(delivery()) == DEAD and queue.dead[0][1] == "deadline_exceeded" and model.calls == []
```

- `clock = FixedClock()`: stores the result of calling `FixedClock()`, which is this repository's own `FixedClock` (in `tests/unit/application/fakes.py`): a clock the test moves by hand in `clock`.
- `clock.advance(600)`: calling `clock.advance(600)`.
- `model = ScriptedModel()`: stores the result of calling `ScriptedModel()`, which is this repository's own `ScriptedModel` (in `tests/unit/application/fakes.py`): replies from a queue of texts or exceptions; an unscripted call fails the test in `model`.
- `handler, queue = _handler(model, clock=clock, policy=RetryPolicy(ev...`: unpacks the result of calling `_handler(model, clock=clock, policy=RetryPolicy(event_deadline_seconds=300))` The named values are `clock`, `policy`. into the names `handler`, `queue`, one item each.
- `assert handler.handle(delivery()) == DEAD and queue.dead[0][1] == "...`: checks that `handler.handle(delivery())` equals `DEAD` and `queue.dead[0][1]` equals `"deadline_exceeded"` and `model.calls` equals `[]`. A false check stops the test as failed.

```python
def test_extraction_repairs_once_and_a_repair_that_works_counts_two_calls():
```

- Defines the test `test_extraction_repairs_once_and_a_repair_that_works_counts_two_calls`.

```python
from inbox_worker.application.extraction import TicketExtractor as Extractor

model = ScriptedModel("{intent:", VALID)
result = Extractor(model).extract("Please cancel order 4417.")
assert result.calls == 2 and "Your reply was not a valid ticket" in model.calls[1]
```

- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`TicketExtractor as Extractor`: Model-backed extraction.)
- `model = ScriptedModel("{intent:", VALID)`: stores the result of calling `ScriptedModel("{intent:", VALID)`, which is this repository's own `ScriptedModel` (in `tests/unit/application/fakes.py`): replies from a queue of texts or exceptions; an unscripted call fails the test in `model`.
- `result = Extractor(model).extract("Please cancel order 4417.")`: stores the result of calling `Extractor(model).extract("Please cancel order 4417.")`, which is this repository's own `extract` (in `src/inbox_worker/application/extraction.py`): one call, and one repair call when the reply is not a valid ticket in `result`.
- `assert result.calls == 2 and "Your reply was not a valid ticket" in...`: checks that `result.calls` equals `2` and `"Your reply was not a valid ticket"` is among `model.calls[1]`. A false check stops the test as failed.

```python
def test_the_worker_processes_the_queue_until_idle_and_survives_an_unexpected_failure():
```

- Defines the test `test_the_worker_processes_the_queue_until_idle_and_survives_an_unexpected_failure`.

```python
queue, effects = MemoryQueue(), MemoryEffects()
```

- `queue, effects = MemoryQueue(), MemoryEffects()`: unpacks a tuple of 2 items into the names `queue`, `effects`, one item each.

```python
for number in range(4):
```

- Repeats the indented lines once for each item of `range(4)`, naming the current item `number`.

```python
queue.put(f"e-{number}", json.dumps({"event_id": f"e-{number}", "body": "Please cancel order 4417."}))
```

- `queue.put(f"e-{number}", json.dumps({"event_id": f"e-{number}", "bo...`: calling `queue.put(f"e-{number}", json.dumps({"event_id": f"e-{number}", "body": "Please cancel ...`.

```python
model = ScriptedModel(*[VALID] * 4)
handler, _ = _handler(model, queue, effects)
outcomes = Worker(
    queue, handler, concurrency=2, lease_seconds=5, stop_requested=lambda: False, wait=lambda s: False
).run(until_idle=True)
assert outcomes[PROCESSED] == 4 and len(effects.processed) == 4
```

- `model = ScriptedModel(*[VALID] * 4)`: stores the result of calling `ScriptedModel(*[VALID] * 4)`, which is this repository's own `ScriptedModel` (in `tests/unit/application/fakes.py`): replies from a queue of texts or exceptions; an unscripted call fails the test in `model`.
- `handler, _ = _handler(model, queue, effects)`: unpacks the result of calling `_handler(model, queue, effects)` into the names `handler`, `_`, one item each.
- `outcomes = Worker( queue, handler, concurrency=2, lease_seconds=5, ...`: stores the result of calling `Worker( queue, handler, concurrency=2, lease_seconds=5, stop_requested=lambda: False, w...`, which runs a program or a coroutine The named values are `until_idle`. in `outcomes`.
- `assert outcomes[PROCESSED] == 4 and len(effects.processed) == 4`: checks that `outcomes[PROCESSED]` equals `4` and `len(effects.processed)` equals `4`. A false check stops the test as failed.

> **`*` and `**` in a call.** `f(*items)` passes the items of a list as separate arguments; `f(**mapping)` passes the entries of a dict as named arguments. In an unpacking `a, *rest = items`, the star collects the leftovers.

```python
class Broken(MemoryEffects):
```

- Defines the class `Broken`.
- It extends `MemoryEffects` (it starts with all of that class's methods and may add or replace some).

```python
def is_processed(self, event_id: str) -> bool:
```

- Defines the method `is_processed`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
- Gives back a value of type `bool`.

```python
raise RuntimeError("database gone")
```

- `raise RuntimeError("database gone")`: stops with an error of kind `RuntimeError` with the message `"database gone"`. Whoever called this code must handle it or the program stops.

```python
broken_queue = MemoryQueue()
broken_queue.put("e-1", json.dumps({"event_id": "e-1", "body": "x"}))
broken, _ = _handler(ScriptedModel(), broken_queue, Broken())
stops = iter([False, True])
outcomes = Worker(
    broken_queue, broken, concurrency=1, lease_seconds=5, stop_requested=lambda: next(stops), wait=lambda s: False
).run()
assert outcomes["error"] == 1
```

- `broken_queue = MemoryQueue()`: stores the result of calling `MemoryQueue()`, which is this repository's own `MemoryQueue` (in `tests/unit/application/fakes.py`): the queue in memory: deliveries by id with a status, and the calls the handler made in `broken_queue`.
- `broken_queue.put("e-1", json.dumps({"event_id": "e-1", "body": "x"}))`: calling `broken_queue.put("e-1", json.dumps({"event_id": "e-1", "body": "x"}))`.
- `broken, _ = _handler(ScriptedModel(), broken_queue, Broken())`: unpacks the result of calling `_handler(ScriptedModel(), broken_queue, Broken())` into the names `broken`, `_`, one item each.
- `stops = iter([False, True])`: stores the result of calling `iter([False, True])`, which gets an iterator over `[False, True]` in `stops`.
- `outcomes = Worker( broken_queue, broken, concurrency=1, lease_secon...`: stores the result of calling `Worker( broken_queue, broken, concurrency=1, lease_seconds=5, stop_requested=lambda: ne...`, which runs a program or a coroutine in `outcomes`.
- `assert outcomes["error"] == 1`: checks that `outcomes["error"]` equals `1`. A false check stops the test as failed.

```python
def test_the_worker_waits_and_retries_when_the_queue_is_unreachable():
```

- Defines the test `test_the_worker_waits_and_retries_when_the_queue_is_unreachable`.

```python
class Flaky(MemoryQueue):
```

- Defines the class `Flaky`.
- It extends `MemoryQueue` (it starts with all of that class's methods and may add or replace some).

```python
failures = 2
```

- `failures = 2`: a class-level value `failures` shared by all objects of the class: the number `2`.

```python
def claim(self, limit, lease_seconds):
```

- Defines the method `claim`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`.
  - `lease_seconds`.

```python
if self.failures:
```

- Checks whether `self.failures` is truthy. If so, the indented lines run.

```python
self.failures -= 1
raise ConnectionError("database restarting")
```

- `self.failures -= 1`: subtracts `1` from `self.failures` and keeps the result there.
- `raise ConnectionError("database restarting")`: stops with an error of kind `ConnectionError` with the message `"database restarting"`. Whoever called this code must handle it or the program stops.

```python
return super().claim(limit, lease_seconds)
```

- `return super().claim(limit, lease_seconds)`: ends the function and gives back the result of calling `super().claim(limit, lease_seconds)`.

```python
queue = Flaky()
queue.put("e-1", json.dumps({"event_id": "e-1", "body": "Please cancel order 4417."}))
effects = MemoryEffects()
handler, _ = _handler(ScriptedModel(VALID), queue, effects)
waits: list[float] = []
outcomes = Worker(
    queue,
    handler,
    concurrency=1,
    lease_seconds=5,
    stop_requested=lambda: False,
    wait=_recorder(waits),
    idle_poll_seconds=0.5,
).run(until_idle=True)
```

- `queue = Flaky()`: stores the result of calling `Flaky()`, which makes a `Flaky` object in `queue`.
- `queue.put("e-1", json.dumps({"event_id": "e-1", "body": "Please can...`: calling `queue.put("e-1", json.dumps({"event_id": "e-1", "body": "Please cancel order 4417."}))`.
- `effects = MemoryEffects()`: stores the result of calling `MemoryEffects()`, which is this repository's own `MemoryEffects` (in `tests/unit/application/fakes.py`): the effects store in memory; `apply` returns False for an event that already has a mark in `effects`.
- `handler, _ = _handler(ScriptedModel(VALID), queue, effects)`: unpacks the result of calling `_handler(ScriptedModel(VALID), queue, effects)` into the names `handler`, `_`, one item each.
- `waits: list[float] = []`: stores a new list (empty) in `waits`, whose type is declared as `list[float]`.
- `outcomes = Worker( queue, handler, concurrency=1, lease_seconds=5, ...`: stores the result of calling `Worker( queue, handler, concurrency=1, lease_seconds=5, stop_requested=lambda: False, w...`, which runs a program or a coroutine The named values are `until_idle`. in `outcomes`.

```python
assert outcomes["queue_error"] == 2 and outcomes[PROCESSED] == 1 and len(effects.processed) == 1
assert waits == [1.0, 2.0]
```

- `assert outcomes["queue_error"] == 2 and outcomes[PROCESSED] == 1 an...`: checks that `outcomes["queue_error"]` equals `2` and `outcomes[PROCESSED]` equals `1` and `len(effects.processed)` equals `1`. A false check stops the test as failed.
- `assert waits == [1.0, 2.0]`: checks that `waits` equals `[1.0, 2.0]`. A false check stops the test as failed.

```python
def test_a_stop_request_ends_the_loop_after_the_work_in_flight():
```

- Defines the test `test_a_stop_request_ends_the_loop_after_the_work_in_flight`.

```python
queue = MemoryQueue()
handler, _ = _handler(ScriptedModel())
waits: list[float] = []
outcomes = Worker(
    queue,
    handler,
    concurrency=1,
    lease_seconds=5,
    stop_requested=lambda: len(waits) >= 2,
    wait=_recorder(waits),
).run()
```

- `queue = MemoryQueue()`: stores the result of calling `MemoryQueue()`, which is this repository's own `MemoryQueue` (in `tests/unit/application/fakes.py`): the queue in memory: deliveries by id with a status, and the calls the handler made in `queue`.
- `handler, _ = _handler(ScriptedModel())`: unpacks the result of calling `_handler(ScriptedModel())` into the names `handler`, `_`, one item each.
- `waits: list[float] = []`: stores a new list (empty) in `waits`, whose type is declared as `list[float]`.
- `outcomes = Worker( queue, handler, concurrency=1, lease_seconds=5, ...`: stores the result of calling `Worker( queue, handler, concurrency=1, lease_seconds=5, stop_requested=lambda: len(wait...`, which runs a program or a coroutine in `outcomes`.

```python
assert outcomes == {} and len(waits) == 2
```

- `assert outcomes == {} and len(waits) == 2`: checks that `outcomes` equals `{}` and `len(waits)` equals `2`. A false check stops the test as failed.

```python
class _Outbox:
```

- Defines the class `_Outbox`.

```python
def __init__(self):
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.

```python
self.rows = [(1, "e-1", "acknowledge"), (2, "e-2", "acknowledge")]
self.sent = []
```

- `self.rows = [(1, "e-1", "acknowledge"), (2, "e-2", "acknowledge")]`: stores a new list holding 2 items in `self.rows`.
- `self.sent = []`: stores a new list (empty) in `self.sent`.

```python
def unsent(self, limit):
```

- Defines the method `unsent`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`.

```python
return [row for row in self.rows if row[0] not in self.sent][:limit]
```

- `return [row for row in self.rows if row[0] not in self.sent][:limit]`: ends the function and gives back the item `[row for row in self.rows if row[0] not in self.sent][:limit]`.

```python
def mark_sent(self, outbox_id):
```

- Defines the method `mark_sent`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `outbox_id`.

```python
self.sent.append(outbox_id)
```

- `self.sent.append(outbox_id)`: calling `self.sent.append(outbox_id)`, which adds `outbox_id` to the end of `self.sent`.

```python
class _Gateway:
```

- Defines the class `_Gateway`.

```python
def __init__(self):
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.

```python
self.mail = []
```

- `self.mail = []`: stores a new list (empty) in `self.mail`.

```python
def send(self, event_id, kind):
```

- Defines the method `send`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`.
  - `kind`.

```python
if event_id in self.mail:
```

- Checks whether `event_id` is among `self.mail`. If so, the indented lines run.

```python
raise DuplicateSendError(event_id)
```

- `raise DuplicateSendError(event_id)`: stops with an error of kind `DuplicateSendError` with the message `event_id`. Whoever called this code must handle it or the program stops.

```python
self.mail.append(event_id)
```

- `self.mail.append(event_id)`: calling `self.mail.append(event_id)`, which adds `event_id` to the end of `self.mail`.

```python
def test_the_outbox_relay_sends_each_acknowledgment_once_and_tolerates_a_send_that_happened_before_a_crash():
```

- Defines the test `test_the_outbox_relay_sends_each_acknowledgment_once_and_tolerates_a_send_that_happened_before_a_crash`.

```python
outbox, gateway = _Outbox(), _Gateway()
gateway.mail.append("e-1")
assert OutboxRelay(outbox, gateway).run_once() == 2
assert gateway.mail == ["e-1", "e-2"] and outbox.sent == [1, 2]
assert OutboxRelay(outbox, gateway).run_once() == 0
```

- `outbox, gateway = _Outbox(), _Gateway()`: unpacks a tuple of 2 items into the names `outbox`, `gateway`, one item each.
- `gateway.mail.append("e-1")`: calling `gateway.mail.append("e-1")`, which adds `"e-1"` to the end of `gateway.mail`.
- `assert OutboxRelay(outbox, gateway).run_once() == 2`: checks that `OutboxRelay(outbox, gateway).run_once()` equals `2`. A false check stops the test as failed.
- `assert gateway.mail == ["e-1", "e-2"] and outbox.sent == [1, 2]`: checks that `gateway.mail` equals `["e-1", "e-2"]` and `outbox.sent` equals `[1, 2]`. A false check stops the test as failed.
- `assert OutboxRelay(outbox, gateway).run_once() == 0`: checks that `OutboxRelay(outbox, gateway).run_once()` equals `0`. A false check stops the test as failed.

```python
def test_the_generated_inbox_has_the_planted_duplicates_and_poison_and_is_the_same_every_time():
```

- Defines the test `test_the_generated_inbox_has_the_planted_duplicates_and_poison_and_is_the_same_every_time`.

```python
inbox = generate_events()
assert len({event_id for event_id, _ in inbox.deliveries}) == 1000 and len(inbox.deliveries) == 1020
assert len(inbox.duplicates) == 20 and len(inbox.poison) == 10
assert sorted(inbox.poison.values()).count("too_large") == 3
assert generate_events().deliveries == inbox.deliveries
seen: dict[str, list[str]] = {}
```

- `inbox = generate_events()`: stores the result of calling `generate_events()`, which is this repository's own `generate_events` (in `src/inbox_worker/application/generate_events.py`): `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable in `inbox`.
- `assert len({event_id for event_id, _ in inbox.deliveries}) == 1000 ...`: checks that `len({event_id for event_id, _ in inbox.deliveries})` equals `1000` and `len(inbox.deliveries)` equals `1020`. A false check stops the test as failed.
- `assert len(inbox.duplicates) == 20 and len(inbox.poison) == 10`: checks that `len(inbox.duplicates)` equals `20` and `len(inbox.poison)` equals `10`. A false check stops the test as failed.
- `assert sorted(inbox.poison.values()).count("too_large") == 3`: checks that `sorted(inbox.poison.values()).count("too_large")` equals `3`. A false check stops the test as failed.
- `assert generate_events().deliveries == inbox.deliveries`: checks that `generate_events().deliveries` equals `inbox.deliveries`. A false check stops the test as failed.
- `seen: dict[str, list[str]] = {}`: stores a new dict (empty) in `seen`, whose type is declared as `dict[str, list[str]]`.

```python
for event_id, payload in inbox.deliveries:
```

- Repeats the indented lines once for each item of `inbox.deliveries`, naming the current item the names `event_id`, `payload`.

```python
seen.setdefault(event_id, []).append(payload)
```

- `seen.setdefault(event_id, []).append(payload)`: calling `seen.setdefault(event_id, []).append(payload)`, which adds `payload` to the end of `seen.setdefault(event_id, [])`.

```python
assert {event_id for event_id, payloads in seen.items() if len(payloads) == 2} == set(inbox.duplicates)
assert all(
    len(payload) > 300_000 for event_id, payload in inbox.deliveries if inbox.poison.get(event_id) == "too_large"
)
```

- `assert {event_id for event_id, payloads in seen.items() if len(payl...`: checks that `{event_id for event_id, payloads in seen.items() if len(payloads) == 2}` equals `set(inbox.duplicates)`. A false check stops the test as failed.
- `assert all( len(payload) > 300_000 for event_id, payload in inbox.d...`: checks that `all( len(payload) > 300_000 for event_id, payload in inbox.deliveries if inbox.poison.g...` is true (the call is true if every item of `( len(payload) > 300_000 for event_id, payload in inbox.deliveries if inbox.poison.get(...` is true). A false check stops the test as failed.

#### `tests/unit/domain/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/unit/domain/test_domain.py`

- This file has no docstring at the top.

```python
import base64
import json
import random

import pytest

from inbox_worker.domain.backoff import backoff_delay
from inbox_worker.domain.errors import PermanentEventError, ReplyInvalidError
```

- `import base64`: makes the module `base64` available (encodes bytes as text made of 64 safe characters and decodes them back).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `import pytest`: makes the module `pytest` available (the test framework).
- `from inbox_worker.domain.backoff import ...`: takes names from `inbox_worker.domain.backoff`, this repository's own code. (`backoff_delay`: A random delay in [0, min(cap, base * 2**(attempt - 1))].)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`PermanentEventError`: An event that can never succeed.) (`ReplyInvalidError`: A model reply is not a valid ticket; the message says why.)

```python
from inbox_worker.domain.events import MAX_EMAIL_BYTES, event_id_of, parse_event
from inbox_worker.domain.signature import BAD_TIMESTAMP, MAX_AGE_SECONDS, TAMPERED, TOO_OLD, sign, verify
from inbox_worker.domain.stats import percentile
from inbox_worker.domain.ticket import Ticket

SECRET = b"unit-test-secret-0123456789"
BODY = '{"event_id": "e-001", "body": "Please cancel order 4417"}'
```

- `from inbox_worker.domain.events import ...`: takes names from `inbox_worker.domain.events`, this repository's own code. (`MAX_EMAIL_BYTES`: a name defined in this repository.) (`event_id_of`: The event id a receiver files a payload under; a payload that is not an event gets a stable placeholder so it can still be queued, parked....) (`parse_event`: Decode a delivery's payload.)
- `from inbox_worker.domain.signature import ...`: takes names from `inbox_worker.domain.signature`, this repository's own code. (`BAD_TIMESTAMP`: a name defined in this repository.) (`MAX_AGE_SECONDS`: a name defined in this repository.) (`TAMPERED`: a name defined in this repository.) (`TOO_OLD`: a name defined in this repository.) (`sign`: The signature a sender attaches.) (`verify`: (ok, reason).)
- `from inbox_worker.domain.stats import ...`: takes names from `inbox_worker.domain.stats`, this repository's own code. (`percentile`: Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values.)
- `from inbox_worker.domain.ticket import ...`: takes names from `inbox_worker.domain.ticket`, this repository's own code. (`Ticket`: What the customer wants, about which order, in what mood, and the action it asks for.)
- `SECRET = b"unit-test-secret-0123456789"`: stores the bytes `b'unit-test-secret-0123456789'` in `SECRET`.
- `BODY = '{"event_id": "e-001", "body": "Please cancel order 4417"}'`: stores the text `'{"event_id": "e-001", "body": "Please cancel order 4417"}'` in `BODY`.

```python
NOW = 1_800_000_000.0
```

- `NOW = 1_800_000_000.0`: stores the number `1800000000.0` in `NOW`.

```python
def test_a_valid_request_passes_a_tampered_body_fails_on_signature_and_an_old_one_fails_on_age():
```

- Defines the test `test_a_valid_request_passes_a_tampered_body_fails_on_signature_and_an_old_one_fails_on_age`.

```python
signature = sign(SECRET, NOW, BODY)
assert verify(SECRET, str(NOW), BODY, signature, NOW) == (True, "ok")
assert verify(SECRET, str(NOW), BODY.replace("4417", "9999"), signature, NOW) == (False, TAMPERED)
old = NOW - 400
assert verify(SECRET, str(old), BODY, sign(SECRET, old, BODY), NOW) == (False, TOO_OLD)
assert verify(SECRET, "yesterday", BODY, signature, NOW) == (False, BAD_TIMESTAMP)
```

- `signature = sign(SECRET, NOW, BODY)`: stores the result of calling `sign(SECRET, NOW, BODY)`, which is this repository's own `sign` (in `src/inbox_worker/domain/signature.py`): the signature a sender attaches in `signature`.
- `assert verify(SECRET, str(NOW), BODY, signature, NOW) == (True, "ok")`: checks that `verify(SECRET, str(NOW), BODY, signature, NOW)` equals `(True, "ok")`. A false check stops the test as failed.
- `assert verify(SECRET, str(NOW), BODY.replace("4417", "9999"), signa...`: checks that `verify(SECRET, str(NOW), BODY.replace("4417", "9999"), signature, NOW)` equals `(False, TAMPERED)`. A false check stops the test as failed.
- `old = NOW - 400`: stores `NOW - 400`, which subtracts `NOW` and `400` in `old`.
- `assert verify(SECRET, str(old), BODY, sign(SECRET, old, BODY), NOW)...`: checks that `verify(SECRET, str(old), BODY, sign(SECRET, old, BODY), NOW)` equals `(False, TOO_OLD)`. A false check stops the test as failed.
- `assert verify(SECRET, "yesterday", BODY, signature, NOW) == (False,...`: checks that `verify(SECRET, "yesterday", BODY, signature, NOW)` equals `(False, BAD_TIMESTAMP)`. A false check stops the test as failed.

```python
assert verify(b"another-secret-0123456789", str(NOW), BODY, signature, NOW)[1] == TAMPERED
```

- `assert verify(b"another-secret-0123456789", str(NOW), BODY, signatu...`: checks that `verify(b"another-secret-0123456789", str(NOW), BODY, signature, NOW)[1]` equals `TAMPERED`. A false check stops the test as failed.

```python
def test_the_timestamp_is_part_of_what_is_signed_so_a_captured_body_cannot_be_replayed_with_a_new_time():
```

- Defines the test `test_the_timestamp_is_part_of_what_is_signed_so_a_captured_body_cannot_be_replayed_with_a_new_time`.

```python
signature = sign(SECRET, NOW, BODY)
assert verify(SECRET, str(NOW + 10), BODY, signature, NOW + 10) == (False, TAMPERED)
assert verify(SECRET, str(NOW - MAX_AGE_SECONDS), BODY, sign(SECRET, NOW - MAX_AGE_SECONDS, BODY), NOW)[0]
```

- `signature = sign(SECRET, NOW, BODY)`: stores the result of calling `sign(SECRET, NOW, BODY)`, which is this repository's own `sign` (in `src/inbox_worker/domain/signature.py`): the signature a sender attaches in `signature`.
- `assert verify(SECRET, str(NOW + 10), BODY, signature, NOW + 10) == ...`: checks that `verify(SECRET, str(NOW + 10), BODY, signature, NOW + 10)` equals `(False, TAMPERED)`. A false check stops the test as failed.
- `assert verify(SECRET, str(NOW - MAX_AGE_SECONDS), BODY, sign(SECRET...`: checks that `verify(SECRET, str(NOW - MAX_AGE_SECONDS), BODY, sign(SECRET, NOW - MAX_AGE_SECONDS, BO...` is true. A false check stops the test as failed.

```python
def test_a_valid_event_is_parsed_from_text_or_from_base64():
```

- Defines the test `test_a_valid_event_is_parsed_from_text_or_from_base64`.

```python
assert parse_event(BODY).body == "Please cancel order 4417"
encoded = base64.b64encode("Please cancel order 4417 ünï".encode()).decode()
assert parse_event(json.dumps({"event_id": " e-2 ", "body_b64": encoded})).event_id == "e-2"
```

- `assert parse_event(BODY).body == "Please cancel order 4417"`: checks that `parse_event(BODY).body` equals `"Please cancel order 4417"`. A false check stops the test as failed.
- `encoded = base64.b64encode("Please cancel order 4417 ünï".encode())...`: stores the result of calling `base64.b64encode("Please cancel order 4417 ünï".encode()).decode()`, which turns the bytes `base64.b64encode("Please cancel order 4417 ünï".encode())` into text in `encoded`.
- `assert parse_event(json.dumps({"event_id": " e-2 ", "body_b64": enc...`: checks that `parse_event(json.dumps({"event_id": " e-2 ", "body_b64": encoded})).event_id` equals `"e-2"`. A false check stops the test as failed.

```python
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
```

- Defines the test `test_an_event_that_can_never_succeed_is_permanent_with_a_reason_a_person_can_act_on`.
- `@pytest.mark.parametrize( ("payload", "reason"), [ ('{"event_id": "e-1", "body...`: runs the test once per listed set of values.
- Parameters:
  - `payload`.
  - `reason`.

```python
with pytest.raises(PermanentEventError) as caught:
```

- `pytest.raises(PermanentEventError)`: the test passes only if the indented lines raise `PermanentEventError`; it fails if nothing is raised.

```python
parse_event(payload)
```

- `parse_event(payload)`: calling `parse_event(payload)`, which is this repository's own `parse_event` (in `src/inbox_worker/domain/events.py`): decode a delivery's payload.

```python
assert caught.value.reason == reason and str(caught.value)
```

- `assert caught.value.reason == reason and str(caught.value)`: checks that `caught.value.reason` equals `reason` and `str(caught.value)` is true (the call turns `caught.value` into text). A false check stops the test as failed.

```python
def test_an_unparsable_payload_is_filed_under_a_stable_placeholder_id():
```

- Defines the test `test_an_unparsable_payload_is_filed_under_a_stable_placeholder_id`.

```python
assert event_id_of(BODY) == "e-001"
placeholder = event_id_of("{broken")
assert placeholder.startswith("unparsed-") and placeholder == event_id_of("{broken")
```

- `assert event_id_of(BODY) == "e-001"`: checks that `event_id_of(BODY)` equals `"e-001"`. A false check stops the test as failed.
- `placeholder = event_id_of("{broken")`: stores the result of calling `event_id_of("{broken")`, which is this repository's own `event_id_of` (in `src/inbox_worker/domain/events.py`): the event id a receiver files a payload under; a payload that is not an event gets a stable placeholder so it can still be queued, parked... in `placeholder`.
- `assert placeholder.startswith("unparsed-") and placeholder == event...`: checks that `placeholder.startswith("unparsed-")` is true (the call asks whether `placeholder` begins with `"unparsed-"`) and `placeholder` equals `event_id_of("{broken")`. A false check stops the test as failed.

```python
def test_backoff_uses_full_jitter_and_is_capped():
```

- Defines the test `test_backoff_uses_full_jitter_and_is_capped`.

```python
rng = random.Random(1)
delays = [backoff_delay(attempt, 1.0, 8.0, rng) for attempt in (1, 2, 3, 4, 5, 6) for _ in range(200)]
assert all(0 <= delay <= 8.0 for delay in delays)
firsts = [backoff_delay(1, 1.0, 8.0, rng) for _ in range(200)]
assert max(firsts) <= 1.0 and len({round(d, 3) for d in firsts}) > 50
assert max(backoff_delay(6, 1.0, 8.0, rng) for _ in range(500)) > 4.0
```

- `rng = random.Random(1)`: stores the result of calling `random.Random(1)`, which makes a random number generator; the same seed gives the same sequence in `rng`.
- `delays = [backoff_delay(attempt, 1.0, 8.0, rng) for attempt in (1, ...`: stores a list built by running `backoff_delay(attempt, 1.0, 8.0, rng)` for each `attempt` in `(1, 2, 3, 4, 5, 6)` in `delays`.
- `assert all(0 <= delay <= 8.0 for delay in delays)`: checks that `all(0 <= delay <= 8.0 for delay in delays)` is true (the call is true if every item of `(0 <= delay <= 8.0 for delay in delays)` is true). A false check stops the test as failed.
- `firsts = [backoff_delay(1, 1.0, 8.0, rng) for _ in range(200)]`: stores a list built by running `backoff_delay(1, 1.0, 8.0, rng)` for each `_` in `range(200)` in `firsts`.
- `assert max(firsts) <= 1.0 and len({round(d, 3) for d in firsts}) > 50`: checks that `max(firsts)` is less than or equal to `1.0` and `len({round(d, 3) for d in firsts})` is greater than `50`. A false check stops the test as failed.
- `assert max(backoff_delay(6, 1.0, 8.0, rng) for _ in range(500)) > 4.0`: checks that `max(backoff_delay(6, 1.0, 8.0, rng) for _ in range(500))` is greater than `4.0`. A false check stops the test as failed.

```python
def test_percentile_is_nearest_rank_and_safe_on_nothing():
```

- Defines the test `test_percentile_is_nearest_rank_and_safe_on_nothing`.

```python
assert percentile([], 0.95) == 0.0 and percentile([5.0], 0.95) == 5.0
assert percentile([float(n) for n in range(1, 101)], 0.95) == 95.0 and percentile([3.0, 1.0, 2.0], 0.5) == 2.0
```

- `assert percentile([], 0.95) == 0.0 and percentile([5.0], 0.95) == 5.0`: checks that `percentile([], 0.95)` equals `0.0` and `percentile([5.0], 0.95)` equals `5.0`. A false check stops the test as failed.
- `assert percentile([float(n) for n in range(1, 101)], 0.95) == 95.0 ...`: checks that `percentile([float(n) for n in range(1, 101)], 0.95)` equals `95.0` and `percentile([3.0, 1.0, 2.0], 0.5)` equals `2.0`. A false check stops the test as failed.

```python
def test_a_ticket_is_checked_field_by_field():
```

- Defines the test `test_a_ticket_is_checked_field_by_field`.

```python
good = {"intent": "cancel", "order_number": None, "sentiment": "neutral", "requested_action": "none"}
assert Ticket.from_dict(good).intent == "cancel"
```

- `good = {"intent": "cancel", "order_number": None, "sentiment": "neu...`: stores a new dict with 4 entries in `good`.
- `assert Ticket.from_dict(good).intent == "cancel"`: checks that `Ticket.from_dict(good).intent` equals `"cancel"`. A false check stops the test as failed.

```python
for bad in (
    {**good, "intent": "buy"},
    {**good, "order_number": "12"},
    {**good, "sentiment": "angry"},
    {**good, "requested_action": "x"},
):
```

- Repeats the indented lines once for each item of `( {**good, "intent": "buy"}, {**good, "order_number": "12"}, {**good, "sentiment": "ang...`, naming the current item `bad`.

```python
with pytest.raises(ReplyInvalidError):
```

- `pytest.raises(ReplyInvalidError)`: the test passes only if the indented lines raise `ReplyInvalidError`; it fails if nothing is raised.

```python
Ticket.from_dict(bad)
```

- `Ticket.from_dict(bad)`: calling `Ticket.from_dict(bad)`, which is this repository's own `from_dict` (in `src/inbox_worker/domain/ticket.py`): build a ticket from a decoded reply, checking every field.

#### `tests/unit/infrastructure/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/unit/infrastructure/test_adapters.py`

- This file has no docstring at the top.

```python
import io
import json
import logging
from types import SimpleNamespace

import anthropic
import pytest
```

- `import io`: makes the module `io` available (in-memory byte and text streams).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import logging`: makes the module `logging` available (the standard library's logging system).
- `from types import ...`: takes names from `types` (names for built-in types such as a module or a function). (`SimpleNamespace`: a name provided by that module.)
- `import anthropic`: makes the module `anthropic` available (Anthropic's official Python library for calling Claude).
- `import pytest`: makes the module `pytest` available (the test framework).

```python
from inbox_worker.application.ports import ModelReply
from inbox_worker.domain.errors import ModelCallError, RetryableModelError
from inbox_worker.infrastructure.cassette import MissingRecordingError, RecordedModel, RecordingModel, request_key
from inbox_worker.infrastructure.claude_model import ClaudeModel
from inbox_worker.infrastructure.environment import ConfigurationError
from inbox_worker.infrastructure.fake_model import FakeModel
```

- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`ModelReply`: The model's text and what the call used.)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`ModelCallError`: A model call failed in a way a retry will not fix.) (`RetryableModelError`: A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection.)
- `from inbox_worker.infrastructure.cassette import ...`: takes names from `inbox_worker.infrastructure.cassette`, this repository's own code. (`MissingRecordingError`: No recording matches this request; the message says how to re-record.) (`RecordedModel`: Replays replies from a cassette file; a request with no recording fails loudly.) (`RecordingModel`: Wraps a real model and writes every reply to a cassette, keyed like `RecordedModel` expects.) (`request_key`: Hash of everything that decides the reply.)
- `from inbox_worker.infrastructure.claude_model import ...`: takes names from `inbox_worker.infrastructure.claude_model`, this repository's own code. (`ClaudeModel`: One Messages API call per request.)
- `from inbox_worker.infrastructure.environment import ...`: takes names from `inbox_worker.infrastructure.environment`, this repository's own code. (`ConfigurationError`: An environment variable is missing or has an unusable value.)
- `from inbox_worker.infrastructure.fake_model import ...`: takes names from `inbox_worker.infrastructure.fake_model`, this repository's own code. (`FakeModel`: Thread-safe; counts calls, rate-limit errors and injected errors.)

```python
from inbox_worker.infrastructure.logging import configure_logging, fields
from inbox_worker.infrastructure.settings import Settings
from inbox_worker.infrastructure.shutdown import ShutdownSignal
from tests.unit.application.fakes import FixedClock
```

- `from inbox_worker.infrastructure.logging import ...`: takes names from `inbox_worker.infrastructure.logging`, this repository's own code. (`configure_logging`: Send every log record to `stream` (stderr by default) as logfmt.) (`fields`: Use as `logger.info("message", extra=fields(order_id=...))` to attach key=value pairs.)
- `from inbox_worker.infrastructure.settings import ...`: takes names from `inbox_worker.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from inbox_worker.infrastructure.shutdown import ...`: takes names from `inbox_worker.infrastructure.shutdown`, this repository's own code. (`ShutdownSignal`: A flag that SIGINT and SIGTERM set, which work loops check between units of work.)
- `from tests.unit.application.fakes import ...`: takes names from `tests.unit.application.fakes`, this repository's own code. (`FixedClock`: A clock the test moves by hand.)

```python
class Time:
```

- Defines the class `Time`.

```python
def __init__(self):
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.

```python
self.now = 0.0
self.slept = []
```

- `self.now = 0.0`: stores the number `0.0` in `self.now`.
- `self.slept = []`: stores a new list (empty) in `self.slept`.

```python
def clock(self):
```

- Defines the method `clock`.
- Parameters:
  - `self`: the object (or class) the method was called on.

```python
return self.now
```

- `return self.now`: ends the function and gives back `self.now`.

```python
def sleep(self, seconds):
```

- Defines the method `sleep`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `seconds`.

```python
self.slept.append(seconds)
self.now += seconds
```

- `self.slept.append(seconds)`: calling `self.slept.append(seconds)`, which adds `seconds` to the end of `self.slept`.
- `self.now += seconds`: adds `seconds` to `self.now` and keeps the result there.

```python
def test_the_fake_model_waits_for_its_delay_and_returns_a_ticket():
```

- Defines the test `test_the_fake_model_waits_for_its_delay_and_returns_a_ticket`.

```python
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
```

- `time = Time()`: stores the result of calling `Time()`, which makes a `Time` object in `time`.
- `model = FakeModel(delay_seconds=0.1, sleep=time.sleep, clock=time.c...`: stores the result of calling `FakeModel(delay_seconds=0.1, sleep=time.sleep, clock=time.clock)`, which is this repository's own `FakeModel` (in `src/inbox_worker/infrastructure/fake_model.py`): thread-safe; counts calls, rate-limit errors and injected errors in `model`.
- `reply = model.complete("S", "Please cancel order 4417. This is unac...`: stores the result of calling `model.complete("S", "Please cancel order 4417. This is unacceptable.", "v")` in `reply`.
- `assert json.loads(reply.text) == { "intent": "cancel", "order_numbe...`: checks that `json.loads(reply.text)` equals `{ "intent": "cancel", "order_number": "4417", "sentiment": "negative", "requested_actio...`. A false check stops the test as failed.
- `assert time.slept == [0.1] and model.calls == 1`: checks that `time.slept` equals `[0.1]` and `model.calls` equals `1`. A false check stops the test as failed.

```python
def test_the_fake_model_enforces_a_rate_limit_like_a_token_bucket_and_counts_the_errors():
```

- Defines the test `test_the_fake_model_enforces_a_rate_limit_like_a_token_bucket_and_counts_the_errors`.

```python
time = Time()
model = FakeModel(max_rps=5, sleep=time.sleep, clock=time.clock)
admitted = limited = 0
```

- `time = Time()`: stores the result of calling `Time()`, which makes a `Time` object in `time`.
- `model = FakeModel(max_rps=5, sleep=time.sleep, clock=time.clock)`: stores the result of calling `FakeModel(max_rps=5, sleep=time.sleep, clock=time.clock)`, which is this repository's own `FakeModel` (in `src/inbox_worker/infrastructure/fake_model.py`): thread-safe; counts calls, rate-limit errors and injected errors in `model`.
- `admitted = limited = 0`: stores the number `0` in `admitted`, `limited`.

```python
for _ in range(12):
```

- Repeats the indented lines once for each item of `range(12)`, naming the current item `_`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
model.complete("S", "Where is order 1234?", "v")
admitted += 1
```

- `model.complete("S", "Where is order 1234?", "v")`: calling `model.complete("S", "Where is order 1234?", "v")`.
- `admitted += 1`: adds `1` to `admitted` and keeps the result there.

```python
except RetryableModelError:
```

- If an error of kind `RetryableModelError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
limited += 1
```

- `limited += 1`: adds `1` to `limited` and keeps the result there.

```python
assert (admitted, limited) == (5, 7) and model.rate_limited == 7
time.now += 1.0
model.complete("S", "Where is order 1234?", "v")
```

- `assert (admitted, limited) == (5, 7) and model.rate_limited == 7`: checks that `(admitted, limited)` equals `(5, 7)` and `model.rate_limited` equals `7`. A false check stops the test as failed.
- `time.now += 1.0`: adds `1.0` to `time.now` and keeps the result there.
- `model.complete("S", "Where is order 1234?", "v")`: calling `model.complete("S", "Where is order 1234?", "v")`.

```python
def test_the_fake_model_fails_at_the_configured_error_rate_and_the_poison_marker_makes_a_non_ticket():
```

- Defines the test `test_the_fake_model_fails_at_the_configured_error_rate_and_the_poison_marker_makes_a_non_ticket`.

```python
model = FakeModel(error_rate=0.5, seed=3)
failures = 0
```

- `model = FakeModel(error_rate=0.5, seed=3)`: stores the result of calling `FakeModel(error_rate=0.5, seed=3)`, which is this repository's own `FakeModel` (in `src/inbox_worker/infrastructure/fake_model.py`): thread-safe; counts calls, rate-limit errors and injected errors in `model`.
- `failures = 0`: stores the number `0` in `failures`.

```python
for _ in range(200):
```

- Repeats the indented lines once for each item of `range(200)`, naming the current item `_`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
model.complete("S", "hello", "v")
```

- `model.complete("S", "hello", "v")`: calling `model.complete("S", "hello", "v")`.

```python
except RetryableModelError:
```

- If an error of kind `RetryableModelError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
failures += 1
```

- `failures += 1`: adds `1` to `failures` and keeps the result there.

```python
assert 60 < failures < 140 and model.injected_errors == failures
assert FakeModel().complete("S", "POISON-SCHEMA please cancel", "v").text == "not a ticket"
```

- `assert 60 < failures < 140 and model.injected_errors == failures`: checks that `60` is less than `failures` and `failures` is less than `140` and `model.injected_errors` equals `failures`. A false check stops the test as failed.
- `assert FakeModel().complete("S", "POISON-SCHEMA please cancel", "v"...`: checks that `FakeModel().complete("S", "POISON-SCHEMA please cancel", "v").text` equals `"not a ticket"`. A false check stops the test as failed.

```python
def _message(text="{}", stop_reason="end_turn"):
```

- Defines the function `_message`.
- Parameters:
  - `text`, optional (default `"{}"`).
  - `stop_reason`, optional (default `"end_turn"`).

```python
return SimpleNamespace(
    content=[SimpleNamespace(type="text", text=text)],
    stop_reason=stop_reason,
    model="m",
    usage=SimpleNamespace(input_tokens=50, output_tokens=9),
)
```

- `return SimpleNamespace( content=[SimpleNamespace(type="text", text=...`: ends the function and gives back the result of calling `SimpleNamespace( content=[SimpleNamespace(type="text", text=text)], stop_reason=stop_re...`, which makes a `SimpleNamespace` object with the named values `content`, `stop_reason`, `model`, `usage`.

```python
class Stub:
```

- Defines the class `Stub`.

```python
def __init__(self, outcome):
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `outcome`.

```python
self.outcome, self.calls, self.messages = outcome, [], self
```

- `self.outcome, self.calls, self.messages = outcome, [], self`: unpacks a tuple of 3 items into the names `self.outcome`, `self.calls`, `self.messages`, one item each.

```python
def create(self, **kwargs):
```

- Defines the method `create`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `**kwargs`: collects extra named arguments in a dict.

```python
self.calls.append(kwargs)
```

- `self.calls.append(kwargs)`: calling `self.calls.append(kwargs)`, which adds `kwargs` to the end of `self.calls`.

```python
if isinstance(self.outcome, Exception):
```

- Checks whether `isinstance(self.outcome, Exception)` is true (the call asks whether `self.outcome` is a `Exception`). If so, the indented lines run.

```python
raise self.outcome
```

- `raise self.outcome`: raises the error `self.outcome`.

```python
return self.outcome
```

- `return self.outcome`: ends the function and gives back `self.outcome`.

```python
def _status(code):
```

- Defines the function `_status`.
- Parameters:
  - `code`.

```python
response = SimpleNamespace(status_code=code, headers={}, request=SimpleNamespace(method="POST", url="x"))
return anthropic.APIStatusError("boom", response=response, body=None)  # type: ignore[arg-type]
```

- `response = SimpleNamespace(status_code=code, headers={}, request=Si...`: stores the result of calling `SimpleNamespace(status_code=code, headers={}, request=SimpleNamespace(method="POST", ur...`, which makes a `SimpleNamespace` object with the named values `status_code`, `headers`, `request` in `response`.
- `return anthropic.APIStatusError("boom", response=response, body=None)`: ends the function and gives back the result of calling `anthropic.APIStatusError("boom", response=response, body=None)`, which makes a `APIStatusError` object from `"boom"` with the named values `response`, `body`.

```python
def test_the_claude_adapter_sends_the_email_and_classifies_failures():
```

- Defines the test `test_the_claude_adapter_sends_the_email_and_classifies_failures`.

```python
client = Stub(_message('{"a": 1}'))
assert ClaudeModel("claude-haiku-5-5", None, client=client).complete("SYS", "email", "v1") == ModelReply(
    '{"a": 1}', "m", 50, 9
)
assert client.calls[0]["system"] == "SYS" and client.calls[0]["messages"] == [{"role": "user", "content": "email"}]
```

- `client = Stub(_message('{"a": 1}'))`: stores the result of calling `Stub(_message('{"a": 1}'))`, which makes a `Stub` object from `_message('{"a": 1}')` in `client`.
- `assert ClaudeModel("claude-haiku-5-5", None, client=client).complet...`: checks that `ClaudeModel("claude-haiku-5-5", None, client=client).complete("SYS", "email", "v1")` equals `ModelReply( '{"a": 1}', "m", 50, 9 )`. A false check stops the test as failed.
- `assert client.calls[0]["system"] == "SYS" and client.calls[0]["mess...`: checks that `client.calls[0]["system"]` equals `"SYS"` and `client.calls[0]["messages"]` equals `[{"role": "user", "content": "email"}]`. A false check stops the test as failed.

```python
for error, expected in (
    (anthropic.APIConnectionError(request=SimpleNamespace(method="POST", url="x")), RetryableModelError),  # type: ignore[arg-type]
    (_status(429), ModelCallError),
    (_status(503), RetryableModelError),
    (_status(401), ModelCallError),
):
```

- Repeats the indented lines once for each item of `( (anthropic.APIConnectionError(request=SimpleNamespace(method="POST", url="x")), Retry...`, naming the current item the names `error`, `expected`.

```python
if isinstance(error, anthropic.APIStatusError) and error.status_code == 429:
```

- Checks whether `isinstance(error, anthropic.APIStatusError)` is true (the call asks whether `error` is a `anthropic.APIStatusError`) and `error.status_code` equals `429`. If so, the indented lines run.

```python
continue
```

- `continue`: skips to the next round of the loop.

```python
with pytest.raises(expected):
```

- `pytest.raises(expected)`: the test passes only if the indented lines raise `expected`; it fails if nothing is raised.

```python
ClaudeModel("m", None, client=Stub(error)).complete("S", "u", "v")
```

- `ClaudeModel("m", None, client=Stub(error)).complete("S", "u", "v")`: calling `ClaudeModel("m", None, client=Stub(error)).complete("S", "u", "v")`.

```python
with pytest.raises(ModelCallError, match="declined"):
```

- `pytest.raises(ModelCallError, match="declined")`: the test passes only if the indented lines raise `ModelCallError`; it fails if nothing is raised.

```python
ClaudeModel("m", None, client=Stub(_message(stop_reason="refusal"))).complete("S", "u", "v")
```

- `ClaudeModel("m", None, client=Stub(_message(stop_reason="refusal"))...`: calling `ClaudeModel("m", None, client=Stub(_message(stop_reason="refusal"))).complete("S", "u",...`.

```python
with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
```

- `pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY")`: the test passes only if the indented lines raise `ConfigurationError`; it fails if nothing is raised.

```python
ClaudeModel("m", None)
```

- `ClaudeModel("m", None)`: calling `ClaudeModel("m", None)`, which is this repository's own `ClaudeModel` (in `src/inbox_worker/infrastructure/claude_model.py`): one Messages API call per request.

```python
def test_a_recording_replays_by_the_hash_of_the_request_and_a_changed_prompt_misses(tmp_path):
```

- Defines the test `test_a_recording_replays_by_the_hash_of_the_request_and_a_changed_prompt_misses`.
- Parameters:
  - `tmp_path`: a fixture; a fresh empty temporary folder for this test.

> **`tmp_path`.** A built-in fixture that gives each test a fresh empty temporary folder (a `Path`).

```python
path = tmp_path / "c.json"
RecordingModel(
    SimpleNamespace(complete=lambda s, u, v: ModelReply("text", "m", 5, 2)), path, "model-x", "test"
).complete("S", "u", "v1")
replay = RecordedModel(path)
assert replay.complete("S", "u", "v1").text == "text" and replay.provenance == "test"
```

- `path = tmp_path / "c.json"`: stores `tmp_path / "c.json"`, which divides `tmp_path` and `"c.json"` in `path`.
- `RecordingModel( SimpleNamespace(complete=lambda s, u, v: ModelReply...`: calling `RecordingModel( SimpleNamespace(complete=lambda s, u, v: ModelReply("text", "m", 5, 2))...`.
- `replay = RecordedModel(path)`: stores the result of calling `RecordedModel(path)`, which is this repository's own `RecordedModel` (in `src/inbox_worker/infrastructure/cassette.py`): replays replies from a cassette file; a request with no recording fails loudly in `replay`.
- `assert replay.complete("S", "u", "v1").text == "text" and replay.pr...`: checks that `replay.complete("S", "u", "v1").text` equals `"text"` and `replay.provenance` equals `"test"`. A false check stops the test as failed.

```python
with pytest.raises(MissingRecordingError, match="make record"):
```

- `pytest.raises(MissingRecordingError, match="make record")`: the test passes only if the indented lines raise `MissingRecordingError`; it fails if nothing is raised.

```python
replay.complete("S", "u", "v2")
```

- `replay.complete("S", "u", "v2")`: calling `replay.complete("S", "u", "v2")`.

```python
assert request_key("a", "S", "u", "v") != request_key("b", "S", "u", "v")
```

- `assert request_key("a", "S", "u", "v") != request_key("b", "S", "u"...`: checks that `request_key("a", "S", "u", "v")` is different from `request_key("b", "S", "u", "v")`. A false check stops the test as failed.

```python
def test_the_committed_smoke_cassette_is_labeled_and_replays_a_sample_email():
```

- Defines the test `test_the_committed_smoke_cassette_is_labeled_and_replays_a_sample_email`.

```python
from inbox_worker.application.extraction import PROMPT_VERSION, SYSTEM
from tests.conftest import REPO

replay = RecordedModel(REPO / "tests/fixtures/cassettes/smoke-v1.json")
assert "not a model recording" in replay.provenance
key_count = len(json.loads((REPO / "tests/fixtures/cassettes/smoke-v1.json").read_text())["entries"])
assert key_count == 20 and PROMPT_VERSION and SYSTEM
```

- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`PROMPT_VERSION`: a name defined in this repository.) (`SYSTEM`: a name defined in this repository.)
- `from tests.conftest import ...`: takes names from `tests.conftest`, this repository's own code. (`REPO`: a name defined in this repository.)
- `replay = RecordedModel(REPO / "tests/fixtures/cassettes/smoke-v1.js...`: stores the result of calling `RecordedModel(REPO / "tests/fixtures/cassettes/smoke-v1.json")`, which is this repository's own `RecordedModel` (in `src/inbox_worker/infrastructure/cassette.py`): replays replies from a cassette file; a request with no recording fails loudly in `replay`.
- `assert "not a model recording" in replay.provenance`: checks that `"not a model recording"` is among `replay.provenance`. A false check stops the test as failed.
- `key_count = len(json.loads((REPO / "tests/fixtures/cassettes/smoke-...`: stores the result of calling `len(json.loads((REPO / "tests/fixtures/cassettes/smoke-v1.json").read_text())["entries"])`, which counts the items in `json.loads((REPO / "tests/fixtures/cassettes/smoke-v1.json").read_text())["entries"]` in `key_count`.
- `assert key_count == 20 and PROMPT_VERSION and SYSTEM`: checks that `key_count` equals `20` and `PROMPT_VERSION` is truthy (not `None`, `False`, zero or empty) and `SYSTEM` is truthy (not `None`, `False`, zero or empty). A false check stops the test as failed.

```python
def test_settings_have_safe_defaults_and_reject_a_short_secret_and_bad_values():
```

- Defines the test `test_settings_have_safe_defaults_and_reject_a_short_secret_and_bad_values`.

```python
settings = Settings.from_environ({})
assert (
    settings.model_adapter == "fake"
    and settings.concurrency == 5
    and settings.database_url.startswith("postgresql://inbox:")
)
```

- `settings = Settings.from_environ({})`: stores the result of calling `Settings.from_environ({})`, which is this repository's own `from_environ` (in `src/inbox_worker/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable in `settings`.
- `assert ( settings.model_adapter == "fake" and settings.concurrency ...`: checks that `settings.model_adapter` equals `"fake"` and `settings.concurrency` equals `5` and `settings.database_url.startswith("postgresql://inbox:")` is true (the call asks whether `settings.database_url` begins with `"postgresql://inbox:"`). A false check stops the test as failed.

```python
for bad in (
    {"WEBHOOK_SECRET": "short"},
    {"MODEL_ADAPTER": "gpt"},
    {"CONCURRENCY": "0"},
    {"LEASE_SECONDS": "0"},
    {"LOG_LEVEL": "LOUD"},
):
```

- Repeats the indented lines once for each item of `( {"WEBHOOK_SECRET": "short"}, {"MODEL_ADAPTER": "gpt"}, {"CONCURRENCY": "0"}, {"LEASE_...`, naming the current item `bad`.

```python
with pytest.raises(ConfigurationError):
```

- `pytest.raises(ConfigurationError)`: the test passes only if the indented lines raise `ConfigurationError`; it fails if nothing is raised.

```python
Settings.from_environ(bad)
```

- `Settings.from_environ(bad)`: calling `Settings.from_environ(bad)`, which is this repository's own `from_environ` (in `src/inbox_worker/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable.

```python
assert (
    Settings.from_environ({"POSTGRES_PASSWORD": "pw", "POSTGRES_PORT": "6000"}).database_url
    == "postgresql://inbox:pw@localhost:6000/inbox"
)
```

- `assert ( Settings.from_environ({"POSTGRES_PASSWORD": "pw", "POSTGRE...`: checks that `Settings.from_environ({"POSTGRES_PASSWORD": "pw", "POSTGRES_PORT": "6000"}).database_url` equals `"postgresql://inbox:pw@localhost:6000/inbox"`. A false check stops the test as failed.

```python
def test_logs_are_logfmt_and_a_shutdown_signal_is_a_flag():
```

- Defines the test `test_logs_are_logfmt_and_a_shutdown_signal_is_a_flag`.

```python
stream = io.StringIO()
configure_logging("INFO", stream)
logging.getLogger("x").info("worker stopped", extra=fields(processed=10))
assert "processed=10" in stream.getvalue()
flag = ShutdownSignal()
assert not flag.requested
```

- `stream = io.StringIO()`: stores the result of calling `io.StringIO()`, which makes a `StringIO` object in `stream`.
- `configure_logging("INFO", stream)`: calling `configure_logging("INFO", stream)`, which is this repository's own `configure_logging` (in `src/inbox_worker/infrastructure/logging.py`): send every log record to `stream` (stderr by default) as logfmt.
- `logging.getLogger("x").info("worker stopped", extra=fields(processe...`: calling `logging.getLogger("x").info("worker stopped", extra=fields(processed=10))`, which writes an INFO log line The named values are `extra`..
- `assert "processed=10" in stream.getvalue()`: checks that `"processed=10"` is among `stream.getvalue()`. A false check stops the test as failed.
- `flag = ShutdownSignal()`: stores the result of calling `ShutdownSignal()`, which is this repository's own `ShutdownSignal` (in `src/inbox_worker/infrastructure/shutdown.py`): a flag that SIGINT and SIGTERM set, which work loops check between units of work in `flag`.
- `assert not flag.requested`: checks that it is not the case that `flag.requested` is truthy. A false check stops the test as failed.

```python
flag.request()
assert flag.requested and flag.wait(0.001)
flag.install()
assert FixedClock().now().tzinfo is not None
```

- `flag.request()`: calling `flag.request()`, which is this repository's own `request` (in `src/inbox_worker/infrastructure/shutdown.py`): ask the loops to stop after the unit of work in flight.
- `assert flag.requested and flag.wait(0.001)`: checks that `flag.requested` is truthy and `flag.wait(0.001)` is true (the call waits for `flag`). A false check stops the test as failed.
- `flag.install()`: calling `flag.install()`, which is this repository's own `install` (in `src/inbox_worker/infrastructure/shutdown.py`): route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close.
- `assert FixedClock().now().tzinfo is not None`: checks that `FixedClock().now().tzinfo` is something (not `None`). A false check stops the test as failed.

```python
def test_the_prompt_file_is_the_prompt_the_extractor_defaults_to():
```

- Defines the test `test_the_prompt_file_is_the_prompt_the_extractor_defaults_to`.

```python
from pathlib import Path

from inbox_worker.application.extraction import PROMPT_VERSION, SYSTEM
from inbox_worker.infrastructure.prompt_file import PromptFileError, read_prompt

prompt = read_prompt(Path(__file__).resolve().parents[3] / "prompts/extract.v1.md")
assert (prompt.version, prompt.text) == (PROMPT_VERSION, SYSTEM) and prompt.owner

broken = Path(__file__).with_name("not_a_prompt.md")
```

- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`PROMPT_VERSION`: a name defined in this repository.) (`SYSTEM`: a name defined in this repository.)
- `from inbox_worker.infrastructure.prompt_file import ...`: takes names from `inbox_worker.infrastructure.prompt_file`, this repository's own code. (`PromptFileError`: A prompt file does not have the two-fence header with a version and an owner.) (`read_prompt`: Read `---`, header lines, `---`, then the prompt text; both fences are required.)
- `prompt = read_prompt(Path(__file__).resolve().parents[3] / "prompts...`: stores the result of calling `read_prompt(Path(__file__).resolve().parents[3] / "prompts/extract.v1.md")`, which is this repository's own `read_prompt` (in `src/inbox_worker/infrastructure/prompt_file.py`): read `---`, header lines, `---`, then the prompt text; both fences are required in `prompt`.
- `assert (prompt.version, prompt.text) == (PROMPT_VERSION, SYSTEM) an...`: checks that `(prompt.version, prompt.text)` equals `(PROMPT_VERSION, SYSTEM)` and `prompt.owner` is truthy. A false check stops the test as failed.
- `broken = Path(__file__).with_name("not_a_prompt.md")`: stores the result of calling `Path(__file__).with_name("not_a_prompt.md")` in `broken`.

```python
broken.write_text("no fences here", encoding="utf-8")
```

- `broken.write_text("no fences here", encoding="utf-8")`: calling `broken.write_text("no fences here", encoding="utf-8")`, which writes text to the file `broken`, replacing it The named values are `encoding`..

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
with pytest.raises(PromptFileError):
```

- `pytest.raises(PromptFileError)`: the test passes only if the indented lines raise `PromptFileError`; it fails if nothing is raised.

```python
read_prompt(broken)
```

- `read_prompt(broken)`: calling `read_prompt(broken)`, which is this repository's own `read_prompt` (in `src/inbox_worker/infrastructure/prompt_file.py`): read `---`, header lines, `---`, then the prompt text; both fences are required.

```python
finally:
```

- Always runs last, whether or not an error happened. It is used to clean up.

```python
broken.unlink()
```

- `broken.unlink()`: calling `broken.unlink()`, which deletes the file `broken`.

#### `tests/unit/interfaces/__init__.py`

This file is empty. Its presence tells Python that the folder is a package.

#### `tests/unit/interfaces/test_webhook_and_cli.py`

- This file has no docstring at the top.

```python
import json

import pytest
from fastapi.testclient import TestClient

from inbox_worker.domain.signature import sign
from inbox_worker.interfaces import cli
from inbox_worker.interfaces.webhook import create_app
```

- `import json`: makes the module `json` available (reads and writes JSON text).
- `import pytest`: makes the module `pytest` available (the test framework).
- `from fastapi.testclient import ...`: takes names from `fastapi.testclient` (the web framework that turns Python functions into HTTP endpoints). (`TestClient`: calls a FastAPI app in-process, with no real network.)
- `from inbox_worker.domain.signature import ...`: takes names from `inbox_worker.domain.signature`, this repository's own code. (`sign`: The signature a sender attaches.)
- `from inbox_worker.interfaces import ...`: takes names from `inbox_worker.interfaces`, this repository's own code. (`cli`: a name defined in this repository.)
- `from inbox_worker.interfaces.webhook import ...`: takes names from `inbox_worker.interfaces.webhook`, this repository's own code. (`create_app`: Build the app.)

```python
from tests.unit.application.fakes import MemoryQueue

SECRET = b"unit-test-secret-0123456789"
NOW = 1_800_000_000.0
BODY = json.dumps({"event_id": "e-001", "body": "Please cancel order 4417"})
```

- `from tests.unit.application.fakes import ...`: takes names from `tests.unit.application.fakes`, this repository's own code. (`MemoryQueue`: The queue in memory: deliveries by id with a status, and the calls the handler made.)
- `SECRET = b"unit-test-secret-0123456789"`: stores the bytes `b'unit-test-secret-0123456789'` in `SECRET`.
- `NOW = 1_800_000_000.0`: stores the number `1800000000.0` in `NOW`.
- `BODY = json.dumps({"event_id": "e-001", "body": "Please cancel orde...`: stores the result of calling `json.dumps({"event_id": "e-001", "body": "Please cancel order 4417"})`, which turns `{"event_id": "e-001", "body": "Please cancel order 4417"}` into JSON text in `BODY`.

```python
def _client(queue=None, ready=True, max_bytes=1_000_000):
```

- Defines the function `_client`.
- Parameters:
  - `queue`, optional (default `None`).
  - `ready`, optional (default `True`).
  - `max_bytes`, optional (default `1_000_000`).

```python
queue = queue if queue is not None else MemoryQueue()
app = create_app(queue, SECRET, max_bytes, lambda: ready, clock=lambda: NOW)
return TestClient(app), queue
```

- `queue = queue if queue is not None else MemoryQueue()`: stores `queue` when `queue` is something (not `None`), otherwise `MemoryQueue()` in `queue`.
- `app = create_app(queue, SECRET, max_bytes, lambda: ready, clock=lam...`: stores the result of calling `create_app(queue, SECRET, max_bytes, lambda: ready, clock=lambda: NOW)`, which is this repository's own `create_app` (in `src/inbox_worker/interfaces/webhook.py`): build the app The named values are `clock`. in `app`.
- `return TestClient(app), queue`: ends the function and gives back a tuple of 2 items.

```python
def _headers(body=BODY, at=NOW):
```

- Defines the function `_headers`.
- Parameters:
  - `body`, optional (default `BODY`).
  - `at`, optional (default `NOW`).

```python
return {"X-Timestamp": str(at), "X-Signature": sign(SECRET, at, body)}
```

- `return {"X-Timestamp": str(at), "X-Signature": sign(SECRET, at, body)}`: ends the function and gives back a new dict with 2 entries.

```python
def test_a_signed_event_is_queued_and_answered_with_202():
```

- Defines the test `test_a_signed_event_is_queued_and_answered_with_202`.

```python
client, queue = _client()
response = client.post("/webhook/email", content=BODY, headers=_headers())
assert response.status_code == 202 and response.json() == {"delivery_id": 1}
assert queue.items[1]["event_id"] == "e-001" and queue.items[1]["payload"] == BODY
```

- `client, queue = _client()`: unpacks the result of calling `_client()` into the names `client`, `queue`, one item each.
- `response = client.post("/webhook/email", content=BODY, headers=_hea...`: stores the result of calling `client.post("/webhook/email", content=BODY, headers=_headers())`, which sends an HTTP POST request The named values are `content`, `headers`. in `response`.
- `assert response.status_code == 202 and response.json() == {"deliver...`: checks that `response.status_code` equals `202` and `response.json()` equals `{"delivery_id": 1}`. A false check stops the test as failed.
- `assert queue.items[1]["event_id"] == "e-001" and queue.items[1]["pa...`: checks that `queue.items[1]["event_id"]` equals `"e-001"` and `queue.items[1]["payload"]` equals `BODY`. A false check stops the test as failed.

```python
def test_a_tampered_body_and_a_replayed_old_request_both_get_401_with_different_reasons():
```

- Defines the test `test_a_tampered_body_and_a_replayed_old_request_both_get_401_with_different_reasons`.

```python
client, queue = _client()
tampered = client.post("/webhook/email", content=BODY.replace("4417", "9999"), headers=_headers())
replayed = client.post("/webhook/email", content=BODY, headers=_headers(at=NOW - 400))
assert (tampered.status_code, replayed.status_code) == (401, 401)
assert "signature mismatch" in tampered.json()["error"] and "too old" in replayed.json()["error"]
assert client.post("/webhook/email", content=BODY).status_code == 401
```

- `client, queue = _client()`: unpacks the result of calling `_client()` into the names `client`, `queue`, one item each.
- `tampered = client.post("/webhook/email", content=BODY.replace("4417...`: stores the result of calling `client.post("/webhook/email", content=BODY.replace("4417", "9999"), headers=_headers())`, which sends an HTTP POST request The named values are `content`, `headers`. in `tampered`.
- `replayed = client.post("/webhook/email", content=BODY, headers=_hea...`: stores the result of calling `client.post("/webhook/email", content=BODY, headers=_headers(at=NOW - 400))`, which sends an HTTP POST request The named values are `content`, `headers`. in `replayed`.
- `assert (tampered.status_code, replayed.status_code) == (401, 401)`: checks that `(tampered.status_code, replayed.status_code)` equals `(401, 401)`. A false check stops the test as failed.
- `assert "signature mismatch" in tampered.json()["error"] and "too ol...`: checks that `"signature mismatch"` is among `tampered.json()["error"]` and `"too old"` is among `replayed.json()["error"]`. A false check stops the test as failed.
- `assert client.post("/webhook/email", content=BODY).status_code == 401`: checks that `client.post("/webhook/email", content=BODY).status_code` equals `401`. A false check stops the test as failed.

```python
assert queue.items == {}
```

- `assert queue.items == {}`: checks that `queue.items` equals `{}`. A false check stops the test as failed.

```python
def test_a_body_over_the_limit_is_refused_with_413_and_a_300_kb_event_under_it_is_queued():
```

- Defines the test `test_a_body_over_the_limit_is_refused_with_413_and_a_300_kb_event_under_it_is_queued`.

```python
client, _ = _client(max_bytes=1000)
assert client.post("/webhook/email", content="x" * 5000, headers=_headers("x" * 5000)).status_code == 413
client, _ = _client()
big = json.dumps({"event_id": "e-2", "body": "y" * 300_000})
assert client.post("/webhook/email", content=big, headers=_headers(big)).status_code == 202
```

- `client, _ = _client(max_bytes=1000)`: unpacks the result of calling `_client(max_bytes=1000)` The named values are `max_bytes`. into the names `client`, `_`, one item each.
- `assert client.post("/webhook/email", content="x" * 5000, headers=_h...`: checks that `client.post("/webhook/email", content="x" * 5000, headers=_headers("x" * 5000)).status_...` equals `413`. A false check stops the test as failed.
- `client, _ = _client()`: unpacks the result of calling `_client()` into the names `client`, `_`, one item each.
- `big = json.dumps({"event_id": "e-2", "body": "y" * 300_000})`: stores the result of calling `json.dumps({"event_id": "e-2", "body": "y" * 300_000})`, which turns `{"event_id": "e-2", "body": "y" * 300_000}` into JSON text in `big`.
- `assert client.post("/webhook/email", content=big, headers=_headers(...`: checks that `client.post("/webhook/email", content=big, headers=_headers(big)).status_code` equals `202`. A false check stops the test as failed.

```python
def test_a_payload_that_is_not_json_is_still_queued_under_a_placeholder_id_so_it_can_be_parked():
```

- Defines the test `test_a_payload_that_is_not_json_is_still_queued_under_a_placeholder_id_so_it_can_be_parked`.

```python
client, queue = _client()
assert client.post("/webhook/email", content="{broken", headers=_headers("{broken")).status_code == 202
assert queue.items[1]["event_id"].startswith("unparsed-")
```

- `client, queue = _client()`: unpacks the result of calling `_client()` into the names `client`, `queue`, one item each.
- `assert client.post("/webhook/email", content="{broken", headers=_he...`: checks that `client.post("/webhook/email", content="{broken", headers=_headers("{broken")).status_code` equals `202`. A false check stops the test as failed.
- `assert queue.items[1]["event_id"].startswith("unparsed-")`: checks that `queue.items[1]["event_id"].startswith("unparsed-")` is true (the call asks whether `queue.items[1]["event_id"]` begins with `"unparsed-"`). A false check stops the test as failed.

```python
def test_health_and_readiness():
```

- Defines the test `test_health_and_readiness`.

```python
client, _ = _client()
assert client.get("/healthz").json() == {"status": "ok"} and client.get("/readyz").status_code == 200
down, _ = _client(ready=False)
assert down.get("/readyz").status_code == 503
```

- `client, _ = _client()`: unpacks the result of calling `_client()` into the names `client`, `_`, one item each.
- `assert client.get("/healthz").json() == {"status": "ok"} and client...`: checks that `client.get("/healthz").json()` equals `{"status": "ok"}` and `client.get("/readyz").status_code` equals `200`. A false check stops the test as failed.
- `down, _ = _client(ready=False)`: unpacks the result of calling `_client(ready=False)` The named values are `ready`. into the names `down`, `_`, one item each.
- `assert down.get("/readyz").status_code == 503`: checks that `down.get("/readyz").status_code` equals `503`. A false check stops the test as failed.

```python
def test_the_webhook_demo_prints_the_three_verdicts(monkeypatch, capsys):
```

- Defines the test `test_the_webhook_demo_prints_the_three_verdicts`.
- Parameters:
  - `monkeypatch`: a fixture; changes environment variables or attributes for this test only.
  - `capsys`: a fixture; captures what the code prints.

> **`monkeypatch`.** A built-in fixture that changes an environment variable or an attribute for the length of one test and restores it afterwards.

```python
assert cli.main(["webhook-demo"]) == 0
out = capsys.readouterr().out
assert "valid request: (True, 'ok')" in out and "signature mismatch" in out and "request too old" in out
```

- `assert cli.main(["webhook-demo"]) == 0`: checks that `cli.main(["webhook-demo"])` equals `0`. A false check stops the test as failed.
- `out = capsys.readouterr().out`: stores `capsys.readouterr().out` in `out`.
- `assert "valid request: (True, 'ok')" in out and "signature mismatch...`: checks that `"valid request: (True, 'ok')"` is among `out` and `"signature mismatch"` is among `out` and `"request too old"` is among `out`. A false check stops the test as failed.

```python
def test_a_bad_environment_stops_with_exit_code_two(monkeypatch, capsys):
```

- Defines the test `test_a_bad_environment_stops_with_exit_code_two`.
- Parameters:
  - `monkeypatch`: a fixture; changes environment variables or attributes for this test only.
  - `capsys`: a fixture; captures what the code prints.

```python
monkeypatch.setenv("WEBHOOK_SECRET", "short")
assert cli.main(["status"]) == 2
assert "WEBHOOK_SECRET" in capsys.readouterr().err
```

- `monkeypatch.setenv("WEBHOOK_SECRET", "short")`: calling `monkeypatch.setenv("WEBHOOK_SECRET", "short")`, which sets an environment variable for the duration of the test.
- `assert cli.main(["status"]) == 2`: checks that `cli.main(["status"])` equals `2`. A false check stops the test as failed.
- `assert "WEBHOOK_SECRET" in capsys.readouterr().err`: checks that `"WEBHOOK_SECRET"` is among `capsys.readouterr().err`. A false check stops the test as failed.

```python
@pytest.mark.parametrize("command", ["db", "worker", "burst"])
def test_each_database_command_is_a_known_subcommand(command):
```

- Defines the test `test_each_database_command_is_a_known_subcommand`.
- `@pytest.mark.parametrize("command", ["db", "worker", "burst"])`: runs the test once per listed set of values.
- Parameters:
  - `command`.

```python
assert cli._parser().parse_args([command]).command == command
```

- `assert cli._parser().parse_args([command]).command == command`: checks that `cli._parser().parse_args([command]).command` equals `command`. A false check stops the test as failed.

<!-- /fullwalk -->

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/pytest --version
```

`pytest 9.1.1`.

```bash
.venv/bin/pytest --collect-only -q | tail -3
```

Lists the tests it would run, then a line such as `N tests collected`.

```bash
make test
```

Runs the offline tests with coverage; ends with a `passed` summary and the coverage table.

```bash
.venv/bin/pytest -m live -q
```

With no key set, the live test is skipped: the summary shows `skipped`.

## Mistakes people make

- Tests that depend on each other's order or leftover files. Each test here builds its own state (an in-memory database, a temporary folder).
- Tests that call the real network or a paid API. The model sits behind a port, and tests use a fake or a recording.
- Asserting too little, for example only that code did not crash.
- Sleeping to wait for something. The code takes the clock and the waiter as parameters so tests can fake them.
- Misspelling a marker. `--strict-markers` turns that into an error.

## Check yourself

1. How does pytest decide a function is a test?
   *Answer:* Its name starts with `test_` and it is in a file named `test_*.py` under the test paths.
2. What is a fixture?
   *Answer:* A function that prepares something a test needs; the test receives it by naming it as a parameter.
3. What does `-m "not live"` do?
   *Answer:* Runs every test except those marked `live`.
4. What does `pytest.raises` check?
   *Answer:* That a block of code raises the named exception.
5. Why use `--strict-markers`?
   *Answer:* So a typo in a marker name is an error instead of silently selecting nothing.

## Further reading

- [pytest documentation (pinned version 9.1.1)](https://docs.pytest.org/en/stable/)
- [How to write and report assertions](https://docs.pytest.org/en/stable/how-to/assert.html)
- [Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Markers](https://docs.pytest.org/en/stable/how-to/mark.html)
