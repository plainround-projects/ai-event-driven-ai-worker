# pip, virtual environments and hash-pinned lock files

## What it is

`pip` is Python's package installer: it downloads libraries (packages) from the Python Package Index (PyPI) and installs them. A *virtual environment* (`venv`) is a private folder holding its own Python and its own installed packages, so one project's libraries cannot clash with another's. A *lock file* lists the exact version of every package, and here also a hash of every downloaded file.

## Why this repository uses it

The lesson's checks must give the same result on any machine and in CI. A private virtual environment built only from a hash-pinned lock file guarantees that every package is the exact version that was tested, and that a swapped file would be refused.

## Where it appears

| File | What it does with pip, virtual environments and hash-pinned lock files |
| --- | --- |
| `Makefile` (the `$(STAMP)` rule) | creates `.venv` and installs from the lock |
| `requirements.lock` | exact runtime packages with SHA-256 hashes |
| `requirements-dev.lock` | runtime plus development tools, with hashes |
| `.venv/` | the environment itself (not committed) |
| `Dockerfile` | installs from `requirements.lock` with `--require-hashes` |

## How it works underneath

`python -m venv .venv` creates the folder `.venv` with a copy (or link) of Python and an empty `site-packages` folder. The scripts in `.venv/bin` (`python`, `pip`, and the tools installed later) are set up to use that folder only. You do not need to "activate" the environment if you call `.venv/bin/python` directly, which is what the Makefile does.

`pip install name` asks PyPI for the package, picks a version that satisfies all declared ranges, downloads a *wheel* (a ready-to-unpack archive with the extension `.whl`), and unpacks it into `site-packages`. A package may need other packages (its *dependencies*), which pip installs too.

A range such as `fastapi>=0.115,<1` allows many versions, so two installs on different days can differ. A lock file removes that freedom: every line is `name==exact.version \` followed by `--hash=sha256:...` lines. With `--require-hashes`, pip computes the SHA-256 hash of each downloaded file and refuses to install it if the hash is not in the list. That protects against a package being replaced on the index. Because `--require-hashes` demands that everything is pinned, the lock lists the dependencies of dependencies as well.

`pip install -e .` installs the project itself in *editable* mode: instead of copying the code, pip records a link, so changes to the source files take effect without reinstalling.

## Walkthrough of this repository's use

### The install rule

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

### One entry of the lock file

The lock files are long (one block per package, including packages your code never imports directly). The first lines of one entry look like this:

```
anthropic==2.3.0 \
    --hash=sha256:aa6a3984f9276f307933d42dc6f58b6efc821a5ecafbc8d1bb5993a066767622 \
    --hash=sha256:edfdea1e3fa7b3ce25df1511953408b2f03bfa61eb6f6268f766101a9e18ad53
    # via ai-event-driven-ai-worker (pyproject.toml)
```

- `anthropic==2.3.0 \`: the package name, `==` and the exact version. The `\` at the end joins this line to the next.
- `--hash=sha256:...`: one line per file the package can be installed from (the source archive and each wheel). `pip` accepts a download only if its SHA-256 hash is in this list.
- Packages needed only on some systems carry a *marker* after a semicolon, for example `psycopg-binary==... ; implementation_name != 'pypy'`.

The runtime lock (`requirements.lock`) has no test tools; the development lock (`requirements-dev.lock`) has them too. The Makefile installs the development lock; the Dockerfile installs the runtime lock.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
ls .venv/bin | head -8
```

Lists programs in the virtual environment, among them `python`, `pip` and the installed tools.

```bash
.venv/bin/pip list --format=freeze | head -5
```

Prints installed packages in `name==version` form.

```bash
grep -c '^[a-z]' requirements-dev.lock
```

Counts the pinned packages in the development lock (lines that start a package entry).

```bash
.venv/bin/pip show anthropic | head -3
```

Shows the installed `anthropic` package: version 2.3.0, the one in the lock.

## Mistakes people make

- Installing packages into the system Python. Always use the project's virtual environment.
- Installing from a range and hoping for the same result later. The lock file with hashes makes installs repeatable.
- Hand-editing the lock file. It is generated by `uv pip compile` (see `uv.md`) so the hashes stay right.
- Forgetting `--no-deps` when installing the project after the lock. Without it pip may re-resolve dependencies and ignore the lock.
- Committing `.venv`. It is rebuilt from the lock in a minute and is machine-specific.

## Check yourself

1. Why use a virtual environment?
   *Answer:* So the project has its own Python packages, independent of the system and other projects.
2. What does `--require-hashes` protect against?
   *Answer:* Installing a file that differs from the one that was locked, for example a tampered or replaced package.
3. What is a wheel?
   *Answer:* A pre-built package archive (`.whl`) that pip unpacks into `site-packages`.
4. What does `pip install -e .` do?
   *Answer:* Installs the current project in editable mode, linked to the source files.
5. Why does the lock file contain packages the project never imports directly?
   *Answer:* Because dependencies of dependencies must be pinned too for `--require-hashes` to work.

## Further reading

- [pip documentation](https://pip.pypa.io/en/stable/)
- [pip: Secure installs and hash-checking mode](https://pip.pypa.io/en/stable/topics/secure-installs/)
- [venv, the standard library module](https://docs.python.org/3.12/library/venv.html)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
