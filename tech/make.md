# GNU Make

## What it is

`make` is a command-line tool that runs named recipes. You describe, in a file called `Makefile`, which *targets* exist, what each one needs first (its *prerequisites*), and the shell commands that produce it (its *recipe*). Then `make target` does the minimum needed. This repository uses it as the one front door: `make up`, `make run`, `make test`, `make lint`, `make down`.

## Why this repository uses it

The repository promises one front door: `make up`, `make run`, `make test`, `make lint`, `make down`. `make` is installed everywhere developers work, needs no language runtime of its own, and its rules express 'rebuild only when something changed', which is exactly what creating the virtual environment needs.

## Where it appears

| File | What it does with GNU Make |
| --- | --- |
| `Makefile` | every command a reader or CI runs |
| `.github/workflows/ci.yml` | calls `make check`, `make audit` and other targets |
| `README.md` | documents the targets and what each proves |

## How it works underneath

A Makefile is made of *rules*:

```
target: prerequisite1 prerequisite2
<TAB>command that builds the target
```

The recipe lines start with a *tab* character, not spaces. `make` first checks whether the target is a file. If the file exists and is newer than all its prerequisites, there is nothing to do. If not, `make` first builds each prerequisite (recursively), then runs the recipe. A target that is not really a file (like `test`) is declared in `.PHONY`, so it always runs.

Variables are written `NAME := value` (set once) or `NAME ?= value` (only if not set) and used as `$(NAME)`. Make also reads environment variables as variables, and `export` hands its variables to the commands it runs. A `@` before a command hides the command line itself; a `-` before `include` ignores a missing file. Inside a recipe `$@` is the target name.

Make runs each recipe line in a fresh `sh -c`. If a line exits non-zero, make stops and reports an error. The text after `##` on a rule line is just a comment; the `help` target here finds those comments with `grep` and prints them.

## Walkthrough of this repository's use

Here is the whole `Makefile`, in blocks, with every line explained. Blocks are separated by blank lines.

```make
# make up | run | burst | crash-test | test | lint | check | audit | down   (make help lists all)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
PKG := inbox_worker
```

- `# make up | run | burst | crash-test | test | lint | check | audit | down   (make help lists all)`: A comment: the short list of the most used targets.
- `PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)`: `?=` sets the variable only if it is not already set. `$(shell ...)` runs a shell command and uses its output. `command -v NAME` prints where `NAME` is found and fails if it is not found. `||` means: if the left command failed, try the right one. So `PYTHON` becomes the first of `python3.13`, `python3.12`, `python3` that exists.
- `VENV := .venv`: `:=` sets a variable once, right now. `VENV` is the name of the virtual-environment folder.
- `PY := $(VENV)/bin/python`: `$(VENV)` is replaced by the variable's value. `PY` is the path of the Python inside the virtual environment.
- `STAMP := $(VENV)/.installed`: `STAMP` is the path of an empty file that records that the installation finished.
- `PKG := inbox_worker`: `PKG` is the name of this project's Python package, `inbox_worker`, used in test and coverage commands.

```make
-include .env
export
```

- `-include .env`: Read the file `.env` and treat each `NAME=value` line as a make variable. The leading `-` means: do not fail if the file does not exist.
- `export`: Pass every make variable to the commands that make runs, as environment variables. This is how settings in `.env` reach the Python programs.

```make
$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@
```

- `$(STAMP): requirements-dev.lock pyproject.toml`: A rule. The target is the stamp file. After the colon are its prerequisites: if either file is newer than the stamp, the stamp is out of date and the commands below must run again.
- `$(PYTHON) -m venv $(VENV)`: Create the virtual environment: a folder with its own Python and its own installed packages, so this project's packages do not mix with any others. `-m venv` runs Python's `venv` module.
- `$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock`: Install every package listed in the lock file. `-q` is quiet. `--require-hashes` refuses a package whose file hash differs from the one in the lock file.
- `$(VENV)/bin/pip install -q --no-deps -e .`: Install this project itself in editable mode (`-e`): the installed copy points at the source files, so edits take effect at once. `--no-deps` skips dependencies; they are already installed.
- `touch $@`: Create or update the stamp file. `$@` is make's name for the target of the rule.

```make
install: $(STAMP) ## create .venv from the hash-pinned lock file
```

- `install: $(STAMP) ## create .venv from the hash-pinned lock file`: A target. Its only prerequisite is the stamp, so running `make install` runs the installation only when needed. The text after `##` is the help text that `make help` prints.

```make
env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
```

- `env:`: A target with no prerequisites and a help-free definition.
- `@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }`: The `@` stops make from printing the command itself. `[ -f .env ]` tests that the file exists. `||` runs the right side only if the test failed: copy the template to `.env` and print a message. The braces group the two commands.

```make
lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports
```

- `lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter`: A target that needs the installation first.
- `$(VENV)/bin/ruff check .`: Run the linter on the whole folder (`.`). A non-zero exit code means it found problems, and make stops.
- `$(VENV)/bin/ruff format --check .`: Check that the code is formatted the way the formatter would write it, without changing any file.
- `$(VENV)/bin/mypy`: Run the type checker. Its settings (which folders, strict mode) are in `pyproject.toml`.
- `$(VENV)/bin/lint-imports`: Run import-linter: it checks the contracts in `pyproject.toml`.

```make
format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .
```

- `format: $(STAMP) ## apply ruff's formatting and safe fixes`: A target that rewrites files.
- `$(VENV)/bin/ruff check --fix .`: Run the linter and apply the fixes it can make safely.
- `$(VENV)/bin/ruff format .`: Rewrite the files in the standard format.

```make
audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock
```

- `audit: $(STAMP) ## check the locked dependencies for known vulnerabilities`: A target that checks the pinned packages.
- `$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock`: Look up every pinned package and version in a database of known security problems. `--no-deps` and `--disable-pip` stop it from resolving or installing anything: it only reads the lock file.

```make
lock: ## re-resolve requirements.lock and requirements-dev.lock with hashes (needs uv)
	uv pip compile pyproject.toml --universal --generate-hashes -q -o requirements.lock
	uv pip compile pyproject.toml --universal --extra dev --generate-hashes -q -o requirements-dev.lock
```

- `lock: ## re-resolve requirements.lock and requirements-dev.lock with hashes (needs uv)`: A target with no prerequisites.
- `uv pip compile pyproject.toml --universal --generate-hashes -q -o requirements.lock`: `uv` works out exact versions for the runtime dependencies. `--universal` makes the result valid on every operating system, `--generate-hashes` records each file's hash, `-q` is quiet, `-o` names the output file.
- `uv pip compile pyproject.toml --universal --extra dev --generate-hashes -q -o requirements-dev.lock`: The same, including the `dev` group, written to `requirements-dev.lock`.

```make
.PHONY: help install env up db reset queries enqueue worker relay status webhook-demo serve-webhook bench-webhook run burst crash-test \
        redrive smoke record test test-integration test-e2e test-live lint format audit check docker-build down clean
```

- `.PHONY: help install env up db reset queries enqueue worker relay status webhook-demo serve-webhook bench-webhook run burst crash-test \`: Names of targets that are commands, not files. Without this line, a file called `test` or `docs` in the folder would make `make test` think there is nothing to do.
- `redrive smoke record test test-integration test-e2e test-live lint format audit check docker-build down clean`: The last line of the `.PHONY` list.

```make
help: ## list the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
```

- `help: ## list the targets`: The `help` target.
- `@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort`: `grep -E` picks the lines of this Makefile that look like `name: ... ## text`. `$(MAKEFILE_LIST)` is the list of Makefiles read. The pipe `|` sends grep's output to `sed`, which replaces everything between the colon and `##` with a tab. `sort` orders the lines. That is the help screen.

```make
WORKER := $(PY) -m inbox_worker.interfaces.cli
SMOKE_ADAPTER ?= recorded
PSQL := docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 -q
POSTGRES_USER ?= inbox
POSTGRES_DB ?= inbox
```

- `WORKER := $(PY) -m inbox_worker.interfaces.cli`: `WORKER` is a shortcut for running the project's command-line module `inbox_worker.interfaces.cli` with the virtual environment's Python.
- `SMOKE_ADAPTER ?= recorded`: Default for the smoke run: the recorded (offline) model.
- `PSQL := docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 -q`: A shortcut for running `psql`, PostgreSQL's command-line client, inside the database container: `-U` is the user, `-d` the database, `-v ON_ERROR_STOP=1` stops at the first SQL error, `-q` is quiet.
- `POSTGRES_USER ?= inbox`: Default database user name `inbox`.
- `POSTGRES_DB ?= inbox`: Default database name `inbox`.

```make
up: env install ## start PostgreSQL in a container and apply sql/001_schema.sql and sql/002_seed.sql
	docker compose up -d --wait postgres
	$(MAKE) --no-print-directory db
```

- `up: env install ## start PostgreSQL in a container and apply sql/001_schema.sql and sql/002_seed.sql`: A target named `up`. After the colon are the targets it needs first (`env install`). The text after `##` is the help text.
- `docker compose up -d --wait postgres`: The last line of the `.PHONY` list.
- `$(MAKE) --no-print-directory db`: Run make again, as a sub-step, for the target(s) `db`. `--no-print-directory` suppresses the noisy 'entering directory' lines.

```make
db: install ## rebuild the schema (DDL and seed) from the numbered scripts
	$(WORKER) db
```

- `db: install ## rebuild the schema (DDL and seed) from the numbered scripts`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) db`: Run the project's command `WORKER` (defined at the top) with the subcommand `db`.

```make
reset: install ## empty every table (sql/reset.sql)
	$(WORKER) reset
```

- `reset: install ## empty every table (sql/reset.sql)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) reset`: Run the project's command `WORKER` (defined at the top) with the subcommand `reset`.

```make
queries: ## run sql/003_queries.sql
	docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql
```

- `queries: ## run sql/003_queries.sql`: A target named `queries` that needs nothing first.
- `docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql`: Run Docker Compose: `exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql`.

```make
webhook-demo: install ## a valid, a tampered and a replayed request against the same signature code
	$(WORKER) webhook-demo
```

- `webhook-demo: install ## a valid, a tampered and a replayed request against the same signature code`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) webhook-demo`: Run the project's command `WORKER` (defined at the top) with the subcommand `webhook-demo`.

```make
bench-webhook: install ## 500 signed requests against the running webhook code: p95 must stay under 100 ms
	$(WORKER) bench-webhook
```

- `bench-webhook: install ## 500 signed requests against the running webhook code: p95 must stay under 100 ms`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) bench-webhook`: Run the project's command `WORKER` (defined at the top) with the subcommand `bench-webhook`.

```make
enqueue: install ## generate the 1,000 sample events (2% delivered twice, 1% poison) and queue every delivery
	$(WORKER) enqueue
```

- `enqueue: install ## generate the 1,000 sample events (2% delivered twice, 1% poison) and queue every delivery`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) enqueue`: Run the project's command `WORKER` (defined at the top) with the subcommand `enqueue`.

```make
worker: install ## process deliveries until idle with the fake model (set MODEL_ADAPTER=claude for the real one)
	$(WORKER) worker --until-idle
```

- `worker: install ## process deliveries until idle with the fake model (set MODEL_ADAPTER=claude for the real one)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) worker --until-idle`: Run the project's command `WORKER` (defined at the top) with the subcommand `worker` --until-idle.

```make
relay: install ## send the acknowledgments in the outbox through the fake mail sender
	$(WORKER) relay --once
```

- `relay: install ## send the acknowledgments in the outbox through the fake mail sender`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) relay --once`: Run the project's command `WORKER` (defined at the top) with the subcommand `relay` --once.

```make
status: install ## counts, open dead letters, and whether any event is lost or has two tickets
	$(WORKER) status
```

- `status: install ## counts, open dead letters, and whether any event is lost or has two tickets`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) status`: Run the project's command `WORKER` (defined at the top) with the subcommand `status`.

```make
redrive: install ## put dead letter DEAD_ID back on the queue (after the cause is fixed)
	$(WORKER) redrive $(DEAD_ID)
```

- `redrive: install ## put dead letter DEAD_ID back on the queue (after the cause is fixed)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) redrive $(DEAD_ID)`: Run the project's command `WORKER` (defined at the top) with the subcommand `redrive` $(DEAD_ID).

```make
run: install reset ## the happy path: queue the sample inbox, process it, replay it, send acknowledgments, show the counts
	$(WORKER) enqueue
	$(WORKER) worker --until-idle
	$(WORKER) status
	$(WORKER) enqueue
	$(WORKER) worker --until-idle
	$(WORKER) relay --once
	$(WORKER) status
	$(MAKE) --no-print-directory queries
```

- `run: install reset ## the happy path: queue the sample inbox, process it, replay it, send acknowledgments, show the counts`: A target named `run`. After the colon are the targets it needs first (`install reset`). The text after `##` is the help text.
- `$(WORKER) enqueue`: Run the project's command `WORKER` (defined at the top) with the subcommand `enqueue`.
- `$(WORKER) worker --until-idle`: Run the project's command `WORKER` (defined at the top) with the subcommand `worker` --until-idle.
- `$(WORKER) status`: Run the project's command `WORKER` (defined at the top) with the subcommand `status`.
- `$(WORKER) enqueue`: Run the project's command `WORKER` (defined at the top) with the subcommand `enqueue`.
- `$(WORKER) worker --until-idle`: Run the project's command `WORKER` (defined at the top) with the subcommand `worker` --until-idle.
- `$(WORKER) relay --once`: Run the project's command `WORKER` (defined at the top) with the subcommand `relay` --once.
- `$(WORKER) status`: Run the project's command `WORKER` (defined at the top) with the subcommand `status`.
- `$(MAKE) --no-print-directory queries`: Run make again, as a sub-step, for the target(s) `queries`. `--no-print-directory` suppresses the noisy 'entering directory' lines.

```make
burst: install ## 500 events in ten seconds at concurrency 5 and 20 against a fake model that allows 30 calls a second
	$(WORKER) burst
```

- `burst: install ## 500 events in ten seconds at concurrency 5 and 20 against a fake model that allows 30 calls a second`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) burst`: Run the project's command `WORKER` (defined at the top) with the subcommand `burst`.

```make
crash-test: install ## kill the worker after the model call and after the commit, restart it, compare event ids
	$(WORKER) crash-test --at after_model
	$(WORKER) crash-test --at after_commit
```

- `crash-test: install ## kill the worker after the model call and after the commit, restart it, compare event ids`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) crash-test --at after_model`: Run the project's command `WORKER` (defined at the top) with the subcommand `crash-test` --at after_model.
- `$(WORKER) crash-test --at after_commit`: Run the project's command `WORKER` (defined at the top) with the subcommand `crash-test` --at after_commit.

```make
smoke: install ## 20 events through the recorded model, or the real one with SMOKE_ADAPTER=claude (needs ANTHROPIC_API_KEY)
	MODEL_ADAPTER=$(SMOKE_ADAPTER) $(PY) scripts/smoke.py
```

- `smoke: install ## 20 events through the recorded model, or the real one with SMOKE_ADAPTER=claude (needs ANTHROPIC_API_KEY)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `MODEL_ADAPTER=$(SMOKE_ADAPTER) $(PY) scripts/smoke.py`: Run the smoke script with the model chosen by `SMOKE_ADAPTER`.

```make
record: install ## record the 20 smoke emails with the real model into tests/fixtures/cassettes/live-v1.json (needs ANTHROPIC_API_KEY)
	MODEL_ADAPTER=claude $(PY) scripts/smoke.py --record
```

- `record: install ## record the 20 smoke emails with the real model into tests/fixtures/cassettes/live-v1.json (needs ANTHROPIC_API_KEY)`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `MODEL_ADAPTER=claude $(PY) scripts/smoke.py --record`: Run the smoke script with the real model and `--record`, which writes the answers into a cassette file.

```make
serve-webhook: install ## start the webhook on WEBHOOK_PORT
	$(WORKER) serve-webhook
```

- `serve-webhook: install ## start the webhook on WEBHOOK_PORT`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(WORKER) serve-webhook`: Run the project's command `WORKER` (defined at the top) with the subcommand `serve-webhook`.

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

```make
check: lint test ## everything that needs no services
```

- `check: lint test ## everything that needs no services`: A target named `check`. After the colon are the targets it needs first (`lint test`). The text after `##` is the help text.

```make
docker-build: ## build the image of the webhook and the worker
	docker build -t ai-event-driven-ai-worker:dev .
```

- `docker-build: ## build the image of the webhook and the worker`: A target named `docker-build` that needs nothing first.
- `docker build -t ai-event-driven-ai-worker:dev .`: Build a Docker image: `-t ai-event-driven-ai-worker:dev .`.

```make
down: ## stop PostgreSQL and delete its data
	docker compose down -v
```

- `down: ## stop PostgreSQL and delete its data`: A target named `down` that needs nothing first.
- `docker compose down -v`: The last line of the `.PHONY` list.

```make
clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml
```

- `clean: down`: A target that first runs `down`, then its own commands.
- `rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml`: Delete `$(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml`, and everything inside, without asking and without an error if it is missing.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make help
```

Prints one line per target: the target name, a tab, and its help text taken from the `##` comment. For example `install` followed by `create .venv from the hash-pinned lock file`.

```bash
make -n lint
```

`-n` prints the commands that `lint` would run without running them: the four tool commands (`ruff check .`, `ruff format --check .`, `mypy`, `lint-imports`).

```bash
make -n test
```

Prints the pytest and coverage commands without running them.

```bash
make --version
```

Prints `GNU Make 3.81` on macOS (the old version Apple ships); the Makefile uses only features that version has.

## Mistakes people make

- Using spaces instead of a tab at the start of a recipe line. Make then says `missing separator`.
- Forgetting `.PHONY`. A file named `test` would make `make test` do nothing.
- Assuming `cd` on one recipe line carries to the next. Each line is its own shell.
- Writing `$VAR` for a make variable. Make needs `$(VAR)`; a single `$` belongs to the shell and must be doubled (`$$VAR`) to reach it.
- Hiding long pipelines inside a Makefile. This repository keeps long logic in Python scripts and keeps the Makefile as a list of short commands.

## Check yourself

1. What character must a recipe line start with?
   *Answer:* A tab.
2. When does `make install` skip its recipe?
   *Answer:* When the target file already exists and is newer than all its prerequisites. Here the stamp file `.venv/.installed` plays that role.
3. What does `.PHONY` do?
   *Answer:* It marks targets as commands, not files, so they always run.
4. What is `$@`?
   *Answer:* The name of the target being built.
5. What does `@` at the start of a recipe line do?
   *Answer:* It stops make from printing the command before running it.

## Further reading

- [GNU Make manual](https://www.gnu.org/software/make/manual/make.html)
- [Make: writing rules](https://www.gnu.org/software/make/manual/html_node/Rules.html)
