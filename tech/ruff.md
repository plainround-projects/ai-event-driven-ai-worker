# ruff

## What it is

`ruff` is a *linter* and a *formatter* for Python, written in Rust. A linter reads your code without running it and reports mistakes and bad habits (an unused import, a variable that is never used, a risky pattern). A formatter rewrites the code into one standard layout so nobody argues about spaces and line breaks.

## Why this repository uses it

A fixed set of rules and one formatting style removes whole classes of mistakes and review arguments. Docstring rules force every module, class and function to say what it is for, which the notes in this folder rely on.

## Where it appears

| File | What it does with ruff |
| --- | --- |
| `pyproject.toml` (`[tool.ruff*]`) | which rules, line length, per-file exceptions |
| `Makefile` (`lint`, `format`) | the commands |
| `.github/workflows/ci.yml` | runs them through `make check` |

## How it works underneath

`ruff` parses each Python file into a tree (the *abstract syntax tree*, AST) and runs many small *rules* over it. Each rule has a code: a letter prefix for the family and a number, such as `F401` (imported but unused) or `E501` (line too long). The `select` setting says which families are on; `ignore` turns single rules off; `per-file-ignores` turns rules off for some files.

`ruff check` reports problems and exits non-zero if it finds any. `ruff check --fix` also applies the fixes that cannot change the program's meaning. `ruff format` rewrites files; `ruff format --check` only says whether the files would change. Results are cached in `.ruff_cache` so unchanged files are skipped. Everything is configured in `pyproject.toml`, under `[tool.ruff]`.

## Walkthrough of this repository's use

### The settings

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

### The commands

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

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/ruff --version
```

`ruff 0.17.2`.

```bash
.venv/bin/ruff check .
```

`All checks passed!` when the code is clean.

```bash
.venv/bin/ruff format --check .
```

Prints how many files are already formatted and exits 0 when nothing would change.

```bash
.venv/bin/ruff check --select D100 --statistics . ; true
```

Shows how many files break the single rule D100 (module without docstring); the expected count is none.

## Mistakes people make

- Fixing a warning by silencing it with `# noqa` instead of understanding it. The code here uses configuration, not blanket silencing.
- Running the formatter and the linter in different orders and getting churn. The Makefile runs `check --fix` first, then `format`.
- Letting the line-length rule fight the formatter. The configuration turns `E501` off because the formatter owns line breaks.
- Enabling every rule. The selection here is deliberate and small enough to explain.
- Forgetting that `ruff` does not check types; that is `mypy`'s job.

## Check yourself

1. What is a linter?
   *Answer:* A tool that reads code without running it and reports likely mistakes and style problems.
2. What does `ruff format --check` do?
   *Answer:* It reports whether files would be reformatted, without changing them; it exits non-zero if any would change.
3. What does a code like `F401` mean?
   *Answer:* A rule identifier: family `F` (pyflakes), rule 401, an unused import.
4. Where does ruff read its settings?
   *Answer:* From the `[tool.ruff]` tables in `pyproject.toml`.
5. What is `ruff check --fix` allowed to change?
   *Answer:* Only fixes that are safe: they do not change what the program does.

## Further reading

- [ruff documentation (pinned version 0.17.2)](https://docs.astral.sh/ruff/)
- [ruff rules](https://docs.astral.sh/ruff/rules/)
- [ruff configuration](https://docs.astral.sh/ruff/configuration/)
