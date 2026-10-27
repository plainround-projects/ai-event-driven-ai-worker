# pyproject.toml and the TOML format

## What it is

`pyproject.toml` is the standard file in which a Python project describes itself: its name, version, dependencies, how to build it, and the settings of its tools. TOML (Tom's Obvious Minimal Language) is the file format it is written in: plain text with `[tables]` of `key = value` lines.

## Why this repository uses it

One file describes the project for every tool: `pip` reads the dependencies and the build settings; `ruff`, `mypy`, `pytest`, `coverage` and `import-linter` each read their own table. Keeping all of it in one place means a reader finds every rule in one file.

## Where it appears

| File | What it does with pyproject.toml and the TOML format |
| --- | --- |
| `pyproject.toml` | the whole file |

## How it works underneath

TOML has a few shapes. A *table* is a group of settings introduced by a header such as `[project]`. A dotted header such as `[tool.ruff.lint]` is a table nested inside `tool` then `ruff`. Double brackets `[[tool.mypy.overrides]]` add one more item to a *list of tables*. Values are strings in double quotes, numbers, `true` / `false`, and lists in square brackets.

Three kinds of reader use this file. A *build front end* such as `pip` reads `[build-system]` to learn which build backend (`setuptools`) to call, and `[project]` for metadata and dependencies. The installer turns `[project.scripts]` into console commands. Every other tool looks for its own `[tool.NAME]` table and ignores the rest: `ruff` reads `[tool.ruff]`, `mypy` reads `[tool.mypy]`, `pytest` reads `[tool.pytest.ini_options]`, `coverage` reads `[tool.coverage.*]`, `import-linter` reads `[tool.importlinter]`.

Version specifiers follow PEP 440: `>=3.12` (at least), `<1` (below), `==2.3.0` (exactly), joined by commas (all must hold).

## Walkthrough of this repository's use

The whole file, in blocks, with every line explained:

```toml
[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"
```

- `[build-system]`: A TOML table header. This table tells `pip` how to build the project into an installable package.
- `requires = ["setuptools>=75"]`: The packages needed only to build this project: `setuptools`, version 75 or newer.
- `build-backend = "setuptools.build_meta"`: The Python module that does the build. `pip` imports it and calls it.

```toml
[project]
name = "ai-event-driven-ai-worker"
version = "0.1.0"
description = "A worker for the support inbox: a signed webhook, a Postgres queue, one model step per event, effects applied once, backoff, dead letters, crash recovery and a burst measurement."
readme = "README.md"
requires-python = ">=3.12"
license = { text = "MIT" }
authors = [{ name = "Sumit Srivastava" }]
dependencies = ["fastapi>=0.115,<1", "uvicorn>=0.32,<1", "anthropic>=2.3,<3", "psycopg[binary,pool]>=3.2,<4", "httpx>=0.27,<1"]
```

- `[project]`: The table that describes the project itself: its name, version and what it needs.
- `name = "ai-event-driven-ai-worker"`: The package name, `ai-event-driven-ai-worker`. It is the name `pip` shows and the name used in the lock files.
- `version = "0.1.0"`: The project version, `0.1.0`, in the `major.minor.patch` form.
- `description = "A worker for the support inbox: a signed webhook, a Postgres queue, one model step per event, effects applied once, backoff, dead letters, crash recovery and a burst measurement."`: One sentence that says what the project is. Package indexes and `pip show` print it.
- `readme = "README.md"`: The file that is the long description of the package.
- `requires-python = ">=3.12"`: The oldest Python allowed: 3.12. `pip` refuses to install the package on an older Python.
- `license = { text = "MIT" }`: The license is the MIT license, a short permissive license: anyone may use and change the code if they keep the notice.
- `authors = [{ name = "Sumit Srivastava" }]`: Who wrote it: a list with one entry that has a name.
- `dependencies = ["fastapi>=0.115,<1", "uvicorn>=0.32,<1", "anthropic>=2.3,<3", "psycopg[binary,pool]>=3.2,<4", "httpx>=0.27,<1"]`: The packages the program needs at run time, as a list of strings. Each string is a package name plus a version range. `>=2.3,<3` means version 2.3 or higher, but below 3. `pip` installs them with the project.

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8,<10",
    "pytest-cov>=5",
    "ruff>=0.6",
    "mypy>=1.11",
    "import-linter>=2.0",
    "pip-audit>=2.7",
]
```

- `[project.optional-dependencies]`: Extra groups of packages that are installed only when asked for, for example `pip install -e .[dev]`.
- `dev = [`: The group named `dev`: the tools used while working on the code (tests, linters), not needed to run it.
- `"pytest>=8,<10",`: The tool `pytest`, version range `>=8,<10`. It is described in its own file in this folder.
- `"pytest-cov>=5",`: The tool `pytest-cov`, version range `>=5`. It is described in its own file in this folder.
- `"ruff>=0.6",`: The tool `ruff`, version range `>=0.6`. It is described in its own file in this folder.
- `"mypy>=1.11",`: The tool `mypy`, version range `>=1.11`. It is described in its own file in this folder.
- `"import-linter>=2.0",`: The tool `import-linter`, version range `>=2.0`. It is described in its own file in this folder.
- `"pip-audit>=2.7",`: The tool `pip-audit`, version range `>=2.7`. It is described in its own file in this folder.

```toml
[project.scripts]
inbox-worker = "inbox_worker.interfaces.cli:main"
```

- `[project.scripts]`: Command names that `pip` creates when it installs the project.
- `inbox-worker = "inbox_worker.interfaces.cli:main"`: Installing the project creates a command named `inbox-worker`. Running it imports the module `inbox_worker.interfaces.cli` and calls its function `main`.

```toml
[tool.setuptools.packages.find]
where = ["src"]
```

- `[tool.setuptools.packages.find]`: Tells setuptools how to find the Python packages to put in the build.
- `where = ["src"]`: Look inside the `src` folder. Code lives in `src/`, so tests cannot import it by accident without installing it.

```toml
[tool.setuptools.package-data]
"inbox_worker" = ["py.typed"]
```

- `[tool.setuptools.package-data]`: Extra non-Python files that must be shipped inside a package.
- `"inbox_worker" = ["py.typed"]`: Ship the empty marker file `py.typed` with the package `inbox_worker`. It tells type checkers that this package has type hints.

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
src = ["src", "tests", "scripts"]
extend-exclude = ["inbox_worker.egg-info"]
```

- `[tool.ruff]`: Settings for `ruff`, the linter and formatter. Every `[tool.xxx]` table is read by the tool called `xxx`.
- `line-length = 120`: The formatter wraps code at 120 characters.
- `target-version = "py312"`: Write and check code for Python 3.12.
- `src = ["src", "tests", "scripts"]`: The folders that hold this project's own code, so `ruff` can tell its imports apart from third-party imports when it sorts them.
- `extend-exclude = ["inbox_worker.egg-info"]`: Skip this generated folder, `inbox_worker.egg-info`, in addition to the folders `ruff` skips already.

```toml
[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103", "D104"]
# The formatter owns line length; it cannot split long string literals (prose, data tables), so E501 adds only noise.
ignore = ["E501"]
```

- `[tool.ruff.lint]`: Settings for the linter part of `ruff`.
- `select = ["E", "F", "I", "B", "UP", "SIM", "N", "C4", "RUF", "PT", "D100", "D101", "D103", "D104"]`: The rule families to turn on. `E` and `F` are the classic style and error checks, `I` sorts imports, `B` finds likely bugs, `UP` suggests newer syntax, `SIM` suggests simpler code, `N` checks naming, `C4` checks list/dict/set building, `RUF` is ruff's own rules, `PT` checks pytest style, and `D100`, `D101`, `D103`, `D104` require a docstring (a text describing the code, placed first inside it) on every public module, class, function and package.
- `# The formatter owns line length; it cannot split long string literals (prose, data tables), so E501 adds only noise.`: A comment. Everything after the `#` is for people; the tool ignores it.
- `ignore = ["E501"]`: Turn off rule E501 (line too long). The formatter already wraps lines and cannot split long strings, so the rule would only add noise.

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["D", "PT018"]
"scripts/**" = ["D103"]
```

- `[tool.ruff.lint.per-file-ignores]`: Rules that are switched off for some files only.
- `"tests/**" = ["D", "PT018"]`: In test files, do not require docstrings (`D`), and allow `assert a and b` written as one assertion (`PT018`).
- `"scripts/**" = ["D103"]`: In the small helper scripts, do not require a docstring on every function.

```toml
[tool.mypy]
python_version = "3.12"
strict = true
files = ["src", "tests"]
```

- `[tool.mypy]`: Settings for `mypy`, the type checker.
- `python_version = "3.12"`: Check as if the code runs on Python 3.12.
- `strict = true`: Turn on mypy's strict bundle: every function needs type hints, no untyped calls, no implicit `Any`, and more.
- `files = ["src", "tests"]`: The folders to check when `mypy` runs with no arguments.

```toml
# Test functions are named for the behavior they check; annotating every one adds noise, not safety.
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false
```

- `# Test functions are named for the behavior they check; annotating every one adds noise, not safety.`: A comment. Everything after the `#` is for people; the tool ignores it.
- `[[tool.mypy.overrides]]`: Double brackets mean a list entry: one more override block that changes settings for some modules only.
- `module = ["tests.*"]`: The override applies to every module under `tests`.
- `disallow_untyped_defs = false`: Test functions may omit type hints.
- `disallow_incomplete_defs = false`: Test functions may be only partly annotated.
- `disallow_untyped_calls = false`: Tests may call functions that have no type hints.

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

```toml
[tool.coverage.run]
source = ["inbox_worker"]
branch = true
```

- `[tool.coverage.run]`: Settings for `coverage`, the tool that measures which lines of code the tests ran.
- `source = ["inbox_worker"]`: Measure only the package `inbox_worker`, not the tests or third-party code.
- `branch = true`: Also measure branches: for every `if`, did the tests take both the true and the false side?

```toml
[tool.coverage.report]
show_missing = true
skip_covered = false
```

- `[tool.coverage.report]`: Settings for the printed coverage report.
- `show_missing = true`: List the line numbers that no test ran.
- `skip_covered = false`: Still list files whose lines are all covered.

```toml
[tool.importlinter]
root_package = "inbox_worker"
include_external_packages = true
```

- `[tool.importlinter]`: Settings for `import-linter`, which checks which module may import which.
- `root_package = "inbox_worker"`: The package to analyze: `inbox_worker`.
- `include_external_packages = true`: Let contracts mention third-party packages (such as `anthropic`) as well as this project's own modules.

```toml
[[tool.importlinter.contracts]]
name = "Layers: interfaces -> infrastructure -> application -> domain, never upward"
type = "layers"
layers = [
    "inbox_worker.interfaces",
    "inbox_worker.infrastructure",
    "inbox_worker.application",
    "inbox_worker.domain",
]
```

- `[[tool.importlinter.contracts]]`: One more contract: a rule about imports that the tool must find kept.
- `name = "Layers: interfaces -> infrastructure -> application -> domain, never upward"`: The package name, `Layers: interfaces -> infrastructure -> application -> domain, never upward`. It is the name `pip` shows and the name used in the lock files.
- `type = "layers"`: A `layers` contract: modules listed first may import modules listed later, never the other way.
- `layers = [`: The layers, from the top (may import everything below) to the bottom (imports none of the others).
- `"inbox_worker.interfaces",`: The layer `inbox_worker.interfaces`.
- `"inbox_worker.infrastructure",`: The layer `inbox_worker.infrastructure`.
- `"inbox_worker.application",`: The layer `inbox_worker.application`.
- `"inbox_worker.domain",`: The layer `inbox_worker.domain`.

```toml
[[tool.importlinter.contracts]]
name = "Domain and application import no vendor SDK, web framework or database driver"
type = "forbidden"
source_modules = ["inbox_worker.domain", "inbox_worker.application"]
forbidden_modules = ["anthropic", "fastapi", "uvicorn", "starlette", "psycopg"]
```

- `[[tool.importlinter.contracts]]`: One more contract: a rule about imports that the tool must find kept.
- `name = "Domain and application import no vendor SDK, web framework or database driver"`: The package name, `Domain and application import no vendor SDK, web framework or database driver`. It is the name `pip` shows and the name used in the lock files.
- `type = "forbidden"`: A `forbidden` contract: the source modules must not import the forbidden modules, directly or through other modules.
- `source_modules = ["inbox_worker.domain", "inbox_worker.application"]`: Check these modules (and everything inside them).
- `forbidden_modules = ["anthropic", "fastapi", "uvicorn", "starlette", "psycopg"]`: They must not import any of these third-party packages.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
python3 -c "import tomllib,sys; d=tomllib.load(open('pyproject.toml','rb')); print(d['project']['name'], d['project']['version'])"
```

Reads the file with Python's own TOML parser and prints `ai-event-driven-ai-worker 0.1.0`.

```bash
python3 -c "import tomllib; d=tomllib.load(open('pyproject.toml','rb')); print(list(d['tool']))"
```

Prints the names of the tools that have a table: `ruff`, `mypy`, `pytest`, `coverage`, `importlinter`, `setuptools` (order may differ).

```bash
.venv/bin/pip show ai-event-driven-ai-worker
```

Shows the installed project's metadata, read from this file: the name, version, summary and `Requires`.

```bash
.venv/bin/inbox-worker --help
```

The console command created from `[project.scripts]`; it prints its usage.

## Mistakes people make

- Putting a tool's settings in the wrong table name; the tool silently ignores them.
- Writing the Python version as a number (`3.12`) where a string is needed. TOML treats `3.12` as a float.
- Pinning exact versions in `dependencies`. Ranges go here; exact versions go in the lock files.
- Forgetting that `[project.optional-dependencies]` groups are not installed by default.
- Mixing tabs and inconsistent indentation inside lists. The `.editorconfig` asks for two spaces in TOML files.

## Check yourself

1. What is a TOML table?
   *Answer:* A named group of settings introduced by a header like `[project]`.
2. What does `[tool.ruff]` configure?
   *Answer:* The `ruff` linter and formatter. Only `ruff` reads it.
3. What does `>=2.3,<3` mean?
   *Answer:* Version 2.3 or newer, but lower than 3.
4. What does `[project.scripts]` create?
   *Answer:* Console commands installed with the package.
5. Why are exact versions not in `pyproject.toml`?
   *Answer:* They live in the lock files; `pyproject.toml` states what is allowed, the lock states what was chosen.

## Further reading

- [pyproject.toml specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [TOML v1.0.0](https://toml.io/en/v1.0.0)
- [PEP 440 version specifiers](https://peps.python.org/pep-0440/)
