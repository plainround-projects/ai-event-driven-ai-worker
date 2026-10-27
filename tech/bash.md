# Bash and the shell

## What it is

A *shell* is a program that reads commands you type (or a script file) and runs other programs for you. Bash is the most common shell on Linux, and the one this repository's scripts and recipes are written for. A *shell script* is a text file of such commands.

## Why this repository uses it

Make runs every recipe line through the shell, so a little shell is unavoidable: testing whether `.env` exists, copying a template, printing a message, setting a variable for one command, removing a folder. The repository keeps the shell short and puts anything longer into tested Python.

## Where it appears

| File | What it does with Bash and the shell |
| --- | --- |
| `Makefile` | recipe lines are shell commands |

## How it works underneath

When a shell runs `ls -l src`, it splits the line into words (`ls`, `-l`, `src`), finds the program called `ls`, starts it as a new process, passes the other words as its *arguments*, and waits. The program prints to its *standard output* (a stream, usually the screen) and may print errors to *standard error*. When it ends it returns an *exit code*, a number: 0 means success, anything else means failure. The shell stores the last exit code in `$?`.

A *pipe* `a | b` connects the standard output of `a` to the standard input of `b`. `&&` runs the right side only if the left side succeeded, `||` only if it failed. `$(command)` runs the command and puts its output in place. `VAR=value command` sets an *environment variable* (a named value that child processes can read) for that one command. A *quote* decides whether the shell splits and expands the text: single quotes keep everything as written, double quotes still expand `$name`.

Scripts often start with `set -euo pipefail`: `-e` stop at the first failing command, `-u` treat an unset variable as an error, `-o pipefail` make a pipeline fail if any stage fails. A `trap 'command' EXIT` runs `command` when the script ends, however it ends.

`make` runs each recipe line with `/bin/sh -c`. On macOS that `sh` is a Bash in POSIX mode; on Debian and Ubuntu it is `dash`, a smaller shell. So recipe lines in this repository use only features both understand.

## Walkthrough of this repository's use

This repository has no long shell programs; the shell appears in the **Makefile recipes** and (in `ai-ship-an-ai-service`) in one script. Every shell construct the recipes use is explained here.

### Shell constructs in the Makefile

```sh
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
	$(PYTHON) -m venv $(VENV)
	touch $@
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort
	docker compose up -d --wait postgres
	docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql
	MODEL_ADAPTER=$(SMOKE_ADAPTER) $(PY) scripts/smoke.py
	MODEL_ADAPTER=claude $(PY) scripts/smoke.py --record
	RUN_LIVE=1 $(PY) -m pytest tests/live -m live
docker-build: ## build the image of the webhook and the worker
	docker build -t ai-event-driven-ai-worker:dev .
	docker compose down -v
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml
```

- `PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)`: `?=` sets the variable only if it is not already set. `$(shell ...)` runs a shell command and uses its output. `command -v NAME` prints where `NAME` is found and fails if it is not found. `||` means: if the left command failed, try the right one. So `PYTHON` becomes the first of `python3.13`, `python3.12`, `python3` that exists.
- `$(PYTHON) -m venv $(VENV)`: Create the virtual environment: a folder with its own Python and its own installed packages, so this project's packages do not mix with any others. `-m venv` runs Python's `venv` module.
- `touch $@`: Create or update the stamp file. `$@` is make's name for the target of the rule.
- `@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }`: The `@` stops make from printing the command itself. `[ -f .env ]` tests that the file exists. `||` runs the right side only if the test failed: copy the template to `.env` and print a message. The braces group the two commands.
- `@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort`: `grep -E` picks the lines of this Makefile that look like `name: ... ## text`. `$(MAKEFILE_LIST)` is the list of Makefiles read. The pipe `|` sends grep's output to `sed`, which replaces everything between the colon and `##` with a tab. `sort` orders the lines. That is the help screen.
- `docker compose up -d --wait postgres`: The last line of the `.PHONY` list.
- `docker compose exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql`: Run Docker Compose: `exec -T postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -v ON_ERROR_STOP=1 < sql/003_queries.sql`.
- `MODEL_ADAPTER=$(SMOKE_ADAPTER) $(PY) scripts/smoke.py`: Run the smoke script with the model chosen by `SMOKE_ADAPTER`.
- `MODEL_ADAPTER=claude $(PY) scripts/smoke.py --record`: Run the smoke script with the real model and `--record`, which writes the answers into a cassette file.
- `RUN_LIVE=1 $(PY) -m pytest tests/live -m live`: Put `RUN_LIVE=1` in the environment of this one command, then run only tests marked `live`. The live test refuses to run unless this variable is set.
- `docker-build: ## build the image of the webhook and the worker`: A target named `docker-build` that needs nothing first.
- `docker build -t ai-event-driven-ai-worker:dev .`: Build a Docker image: `-t ai-event-driven-ai-worker:dev .`.
- `docker compose down -v`: The last line of the `.PHONY` list.
- `rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml`: Delete `$(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage coverage.xml`, and everything inside, without asking and without an error if it is missing.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
sh -c 'echo "exit code of true: $?"; false; echo "exit code of false: $?"'
```

Prints `exit code of true: 0` and then `exit code of false: 1`, showing how success and failure are reported.

```bash
[ -f Makefile ] && echo yes || echo no
```

Prints `yes`: `[ -f FILE ]` tests that a regular file exists, `&&` runs the next command on success, `||` on failure.

```bash
MODEL_ADAPTER=recorded sh -c 'echo $MODEL_ADAPTER'
```

Prints `recorded`: a variable set in front of a command exists only for that command.

```bash
ls .venv/bin | head -5
```

Lists a few programs that `pip` installed into the virtual environment.

## Mistakes people make

- Leaving variables unquoted. `rm -rf $dir` with an empty or spaced `dir` can delete the wrong thing. Quote: `"$dir"`.
- Ignoring failures. Without `set -e` a script goes on after an error. The script here sets `set -euo pipefail`.
- Using Bash-only features in a Makefile recipe, which runs under `sh`. The recipes avoid arrays and `[[ ]]`.
- Forgetting that each Makefile recipe line is a separate shell, so `cd dir` on one line does not affect the next.
- Not cleaning up. A `trap ... EXIT` removes temporary files even when the script fails.

## Check yourself

1. What does the exit code 0 mean?
   *Answer:* The command succeeded. Any other number means it failed.
2. What does `a && b` do?
   *Answer:* Runs `b` only if `a` succeeded (exit code 0).
3. What does `VAR=1 command` do?
   *Answer:* Runs `command` with the environment variable `VAR` set to 1, for that command only.
4. What does `set -euo pipefail` change?
   *Answer:* It stops the script on the first error, on use of an unset variable, and when any stage of a pipeline fails.
5. Which shell runs the lines of a Makefile recipe?
   *Answer:* `/bin/sh`, by default; it is not necessarily Bash.

## Further reading

- [GNU Bash reference manual](https://www.gnu.org/software/bash/manual/bash.html)
- [POSIX shell command language](https://pubs.opengroup.org/onlinepubs/9699919799/utilities/V3_chap02.html)
