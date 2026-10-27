# mypy

## What it is

`mypy` is a static type checker for Python. *Static* means it reads the source without running it. It uses the *type hints* you wrote (`def total(items: list[int]) -> int`) to find mistakes such as passing text where a number is expected, or forgetting that a value might be `None`.

## Why this repository uses it

Strict type checking catches mistakes in the wiring between layers (a function returning `None` where a value is needed) before any test runs, and it keeps the ports and adapters honest: an adapter that does not fit its protocol fails the check.

## Where it appears

| File | What it does with mypy |
| --- | --- |
| `pyproject.toml` (`[tool.mypy]` and overrides) | strict mode and the exceptions |
| `Makefile` (`lint`) | runs `mypy` |
| `src/**/py.typed` | marks the package as typed |

## How it works underneath

`mypy` builds a picture of every function's declared input and output types. Then it walks the body of each function and checks that every operation fits those types. For `x: int | None`, using `x + 1` is an error until the code has checked `x is not None`; `mypy` understands that check and *narrows* the type inside the `if`.

`strict = true` turns on a bundle of options: functions must be fully annotated, calling an untyped function is an error, `Any` may not leak in, and unused `# type: ignore` comments are reported. Libraries that ship a `py.typed` marker file provide their own hints; for a library without hints, a per-module override with `ignore_missing_imports = true` tells `mypy` to treat it as untyped.

`mypy` exits non-zero if it finds an error. It keeps a cache in `.mypy_cache`.

## Walkthrough of this repository's use

### The settings

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
```

- `# Test functions are named for the behavior they check; annotating every one adds noise, not safety.`: A comment. Everything after the `#` is for people; the tool ignores it.

```toml
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false
disallow_untyped_calls = false
```

- `[[tool.mypy.overrides]]`: Double brackets mean a list entry: one more override block that changes settings for some modules only.
- `module = ["tests.*"]`: The override applies to every module under `tests`.
- `disallow_untyped_defs = false`: Test functions may omit type hints.
- `disallow_incomplete_defs = false`: Test functions may be only partly annotated.
- `disallow_untyped_calls = false`: Tests may call functions that have no type hints.

### The marker file

`src/inbox_worker/py.typed` is an empty file. Its presence tells type checkers that the package's type hints can be trusted by other projects. `pyproject.toml` ships it with `[tool.setuptools.package-data]`.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/mypy --version
```

`mypy 2.4.0 (compiled: yes)`.

```bash
.venv/bin/mypy
```

`Success: no issues found in N source files`, where N counts the files in `src` and `tests`.

```bash
.venv/bin/mypy --strict --no-incremental src/inbox_worker/domain 2>&1 | tail -1
```

The same strict check on one folder only; expect `Success`.

```bash
sed -n '1,12p' pyproject.toml >/dev/null && grep -n 'strict' pyproject.toml
```

Shows the line that turns strict mode on.

## Mistakes people make

- Sprinkling `Any` or `# type: ignore` to make an error vanish. In this repository each ignore names its error code and explains why.
- Annotating the outside of a function but not the inside variables that start empty (`items = []`); `mypy` then asks for `items: list[str] = []`.
- Expecting type hints to protect against bad data at run time. Data read from files or the network still has to be validated.
- Forgetting `-> None` on functions that return nothing.
- Skipping the tests directory. The configuration checks `src` and `tests`, with relaxed rules for tests.

## Check yourself

1. What does 'static' checking mean?
   *Answer:* The checker reads the code without running it.
2. What does `X | None` mean?
   *Answer:* The value is either an `X` or `None` (nothing).
3. What does `strict = true` change?
   *Answer:* It enables a bundle of stricter checks, for example that every function is fully annotated.
4. Why is there an override for a third-party package without hints?
   *Answer:* So `mypy` does not fail on a library that provides no type information.
5. Does a wrong type hint stop the program from running?
   *Answer:* No. Python ignores hints at run time; `mypy` is what reports the error.

## Further reading

- [mypy documentation (pinned version 2.4.0)](https://mypy.readthedocs.io/en/stable/)
- [The mypy command line](https://mypy.readthedocs.io/en/stable/command_line.html)
- [Type hints cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
