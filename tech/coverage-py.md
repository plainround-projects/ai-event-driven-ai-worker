# coverage.py and pytest-cov

## What it is

*Code coverage* measures which lines of your program ran while the tests ran. `coverage` (the package `coverage.py`) does the measuring and `pytest-cov` is the plugin that connects it to `pytest`. A line the tests never reach is a line nobody has checked.

## Why this repository uses it

The rules of the lesson live in `domain` and `application`; the Makefile demands 95 percent coverage there and reports the lines no test reached, so a rule without a test shows up as a number.

## Where it appears

| File | What it does with coverage.py and pytest-cov |
| --- | --- |
| `pyproject.toml` (`[tool.coverage.*]`) | what to measure and how to report |
| `Makefile` (`test`) | `--cov` and the `--fail-under=95` check |

## How it works underneath

While tests run, `coverage` registers a hook in the Python interpreter that records each executed line (and, with `branch = true`, each jump taken at an `if` or loop). When the run ends it saves a data file called `.coverage`. `coverage report` reads that file and prints, per source file, the number of statements, how many were missed, branch counts, the percentage, and with `show_missing = true` the line numbers that never ran.

`--fail-under=95` makes the report exit non-zero below 95 percent. Coverage can only say that a line ran; it cannot say the test checked the right thing. This repository requires 95 percent on its `domain` and `application` layers, where the rules live, and does not demand it of the thin wiring.

## Walkthrough of this repository's use

### The settings

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

### The commands

```make
test: install ## unit tests (no services) with coverage; domain and application stay at 95% or more
	$(PY) -m pytest tests/unit --cov=$(PKG) --cov-report=term
	$(PY) -m coverage report --include='src/$(PKG)/domain/*,src/$(PKG)/application/*' --fail-under=95
```

- `test: install ## unit tests (no services) with coverage; domain and application stay at 95% or more`: One rule that defines several targets at once (every name before the colon). Each is a pipeline stage; the `$@` in the recipe is whichever name was asked for.
- `$(PY) -m pytest tests/unit --cov=$(PKG) --cov-report=term`: Run the tests with pytest, using the virtual environment's Python (`-m` runs a module). The options: `tests/unit --cov=$(PKG) --cov-report=term`.
- `$(PY) -m coverage report --include='src/$(PKG)/domain/*,src/$(PKG)/application/*' --fail-under=95`: Print the coverage of the domain and application layers only (`--include`) and exit with an error if it is below 95 percent.

In the table that `coverage report` prints, the columns are: `Stmts` (statements), `Miss` (not run), `Branch` and `BrPart` (decision points and those with only one side taken), `Cover` (percent) and `Missing` (line numbers).

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/coverage --version
```

`Coverage.py, version 7.17.0 with C extension`.

```bash
make test
```

Ends with two tables: all code, and the `domain` and `application` code only with a `TOTAL` of at least 95 percent.

```bash
.venv/bin/coverage report --include='src/*/domain/*' | tail -3
```

Re-prints the domain part of the last run from `.coverage`.

```bash
ls -a | grep coverage
```

Shows the `.coverage` data file after a test run.

## Mistakes people make

- Chasing 100 percent with empty tests that run lines but assert nothing.
- Measuring the tests themselves; `source = ["package"]` limits it to the product code.
- Forgetting branch coverage: a line with an `if` can run while one side never does.
- Mixing data from old runs; delete `.coverage` or let each run overwrite it.
- Counting integration tests that need a database toward a bar that must hold without one.

## Check yourself

1. What does coverage measure?
   *Answer:* Which lines (and branches) of the product code ran during the tests.
2. What is branch coverage?
   *Answer:* Whether both outcomes of each decision (true and false) were taken.
3. What does `--fail-under=95` do?
   *Answer:* Makes the command fail if total coverage is below 95 percent.
4. What file stores the raw measurements?
   *Answer:* `.coverage`.
5. Can 100 percent coverage prove the code is correct?
   *Answer:* No. It proves the lines ran, not that the assertions were good.

## Further reading

- [coverage.py documentation (pinned version 7.17.0)](https://coverage.readthedocs.io/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/en/latest/)
