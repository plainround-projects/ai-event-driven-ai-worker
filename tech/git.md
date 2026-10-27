# Git

## What it is

Git is a program that records the history of a folder of files. Each saved snapshot is a *commit*: it stores which files changed, who changed them, when, and a message that says why. The folder plus its history is a *repository*. Git lets you go back to any commit, compare versions, and work on a copy in parallel (a *branch*).

## Why this repository uses it

Git keeps the history of the repository and decides what is never stored: `.gitignore` keeps the virtual environment, caches, local databases and `.env` out. The commits are grouped by purpose so a reader can follow how the project was built, and the clean working tree after the last commit is part of the definition of done.

## Where it appears

| File | What it does with Git |
| --- | --- |
| `.gitignore` | names what Git must not track |
| `.git/` | the hidden folder where Git keeps the history |
| `.env.example` | is tracked; `.env` (not tracked) is its private copy |

## How it works underneath

Git keeps its data in a hidden folder named `.git`. Everything in it is stored by *hash*: Git computes a SHA-1 or SHA-256 fingerprint of each file's content and each commit, and uses the fingerprint as the name. A commit points to a *tree* (the folder contents at that moment) and to its *parent* commit. Because each commit name depends on the parent's name, changing history changes every later name; that makes the history tamper-evident.

Three places matter: the *working tree* (your files), the *index* or staging area (what the next commit will contain), and the history. `git add file` copies the file's current content into the index. `git commit` turns the index into a new commit. `git status` compares the three. `git log` lists commits. `.gitignore` lists names Git must not track, such as the virtual environment and caches.

A *clone* is a full copy of a repository, including its history. This repository was tested by cloning it into a temporary folder and following the README from the top.

## Walkthrough of this repository's use

### The ignore file

```gitignore
.venv/
__pycache__/
*.pyc
*.egg-info/
build/
dist/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.import_linter_cache/
.coverage
coverage.xml
htmlcov/
.env
.DS_Store
logs/
.omc/
models/
work/
```

- `.venv/`: The virtual environment folder (the private copy of Python packages). It can be rebuilt, so it is not stored in git.
- `__pycache__/`: Folders where Python stores compiled copies of modules.
- `*.pyc`: Compiled Python files.
- `*.egg-info/`: Build metadata that `pip install -e .` writes next to the source.
- `build/`: Output folder of package builds.
- `dist/`: Output folder of package builds.
- `.pytest_cache/`: pytest's own cache.
- `.mypy_cache/`: mypy's cache of earlier results.
- `.ruff_cache/`: ruff's cache.
- `.import_linter_cache/`: import-linter's cache of the import graph.
- `.coverage`: The data file `coverage` writes while tests run.
- `coverage.xml`: A coverage report in XML form.
- `htmlcov/`: A coverage report in HTML form.
- `.env`: The local settings file. It may hold secrets, so it is never committed. `.env.example` is the committed template.
- `.DS_Store`: macOS folder-view metadata.
- `logs/`: Log files.
- `.omc/`: Scratch folder of a tool used while building the repository.
- `models/`: Downloaded model weights are never committed.
- `work/`: Scratch output folder.

### The history

The commits, oldest first (`git log --reverse --format='%h %s'`):

```
23bdf05 chore: add project scaffolding, license, editor config, build and dependency pins
06e3a4e feat: add the domain: signatures, event decoding with reasons, backoff, statistics, the ticket
bc50461 feat: add the handler, the worker loop, the extractor, the outbox relay and event generation
aeb85b7 feat: add the PostgreSQL queue and stores, the fake, recorded and Claude models, the prompt file loader and settings
e1b334f feat: add the command line, the signed webhook, the burst and crash-test measurements
182bb6a feat: add the schema and queries, the versioned prompt, the smoke script and its cassette
7fc2001 test: add unit, PostgreSQL integration and end-to-end tests and the opt-in live test
36f0892 docs: add README, ARCHITECTURE, decision records and CHANGELOG; add the image and CI
8aa8700 docs: say that the image was not built during this work
79db99c docs: mark the unverified container and timing steps as pending capacity
d0157b6 docs: list the Docker-dependent checks as pending capacity
```

Each message starts with a *type* and a colon: `chore` for set-up files, `feat` for working code, `test` for tests, `docs` for documentation. The short hash on the left is the beginning of the commit's fingerprint. Each commit also ends with a line `Co-Authored-By: ...` (a *trailer*) that records that an AI assistant helped write it.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
git log --oneline
```

Lists the commits, newest first, one line each.

```bash
git status --short
```

Prints nothing when every change is committed.

```bash
git ls-files | wc -l
```

Counts the files Git tracks.

```bash
git check-ignore -v .venv
```

Prints the `.gitignore` line that ignores `.venv`.

## Mistakes people make

- Committing secrets or generated files. `.gitignore` here excludes `.env`, `.venv/`, databases and caches.
- Committing everything with `git add .` without looking. The commits here were made group by group so each commit has one purpose.
- Rewriting history that others already have. Nothing in this repository is pushed; history is local.
- Large binary files. Git keeps every version forever; the largest tracked file here is a short text file.
- Vague messages. Each commit message here starts with a type (`feat`, `test`, `docs`, `chore`) and says what changed.

## Check yourself

1. What is a commit?
   *Answer:* A saved snapshot of the tracked files together with an author, a time and a message.
2. What does `git add` do?
   *Answer:* It copies the current content of a file into the index, the staging area for the next commit.
3. Why is `.env` in `.gitignore`?
   *Answer:* It can hold secrets and is specific to one machine, so it must never be committed.
4. What does `git status --short` print when everything is committed?
   *Answer:* Nothing.
5. What is a clone?
   *Answer:* A complete copy of a repository with its whole history.

## Further reading

- [Git documentation](https://git-scm.com/docs)
- [Pro Git, the book](https://git-scm.com/book/en/v2)
