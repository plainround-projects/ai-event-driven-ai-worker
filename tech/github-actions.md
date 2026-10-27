# GitHub Actions

## What it is

GitHub Actions is GitHub's automation service. A *workflow* is a YAML file in `.github/workflows/` that says: when something happens in the repository (a push, a pull request), start a fresh virtual machine and run these steps. It is how this repository proves, on a clean machine and on every change, that the checks pass.

## Why this repository uses it

The Makefile's checks run on a clean Linux machine for every change, so a repository that only works on one laptop is caught. The workflow calls the same `make` targets a person runs; it adds no logic of its own.

## Where it appears

| File | What it does with GitHub Actions |
| --- | --- |
| `.github/workflows/ci.yml` | a workflow |

## How it works underneath

A workflow has `on:` (the *triggers*) and `jobs:`. Each *job* gets its own machine (`runs-on: ubuntu-latest` is a Linux virtual machine); jobs run in parallel unless one declares that it needs another. A job is a list of *steps*. A step either `uses:` a published *action* (a reusable piece, such as `actions/checkout`, which copies the repository onto the machine) or `run:`s a shell command. If any command exits non-zero the step fails, the job fails, and GitHub marks the change as failing.

The `paths:` filter under `pull_request:` limits a workflow to changes that touch certain files; a change touching only other files does not start it. `env:` sets environment variables for a job or a step. `if: always()` makes a step run even after earlier failures (used for cleanup).

The machine starts empty every time. That is why the workflow installs Python, and why the Makefile can rebuild everything from the lock file: if the steps pass there, the project does not depend on anything that happened to exist on one person's laptop.

## Walkthrough of this repository's use

### `.github/workflows/ci.yml`

```yaml
name: ci
```

- `name: ci`: A name for this workflow or job, shown in the GitHub Actions page.

```yaml
on: [push, pull_request]
```

- `on: [push, pull_request]`: When to run: on every `push` of commits and on every `pull_request`. The square brackets make a YAML list.

```yaml
jobs:
  check:
    name: Format, lint, types, import rules, offline tests with coverage, dependency audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: make check
      - run: make audit
```

- `jobs:`: The jobs of this workflow. Jobs run in parallel unless one says it needs another.
- `check:`: The identifier of one job. Everything indented below it belongs to that job.
- `name: Format, lint, types, import rules, offline tests with coverage, dependency audit`: A name for this workflow or job, shown in the GitHub Actions page.
- `runs-on: ubuntu-latest`: Run the job on a fresh virtual machine with the latest Ubuntu Linux that GitHub offers.
- `steps:`: The identifier of one job. Everything indented below it belongs to that job.
- `- uses: actions/checkout@v4`: Copy the repository's files onto the machine. `actions/checkout` is an official action, `@v4` its version.
- `- uses: actions/setup-python@v5`: Install Python on the machine (official action, version 5).
- `with:`: The identifier of one job. Everything indented below it belongs to that job.
- `python-version: "3.13"`: Install Python 3.13.
- `- run: make check`: Run the shell command `make check`. The step fails, and so does the job, if the command exits with a non-zero code.
- `- run: make audit`: Run the shell command `make audit`. The step fails, and so does the job, if the command exits with a non-zero code.

```yaml
  services:
    name: PostgreSQL integration tests, the lesson's scenarios, the image
    runs-on: ubuntu-latest
    env:
      WEBHOOK_P95_BUDGET_MS: "250"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: make up
      - run: make run
      - run: make test-integration
      - run: make test-e2e
      - run: make docker-build
      - if: always()
        run: make down
```

- `services:`: The identifier of one job. Everything indented below it belongs to that job.
- `name: PostgreSQL integration tests, the lesson's scenarios, the image`: A name for this workflow or job, shown in the GitHub Actions page.
- `runs-on: ubuntu-latest`: Run the job on a fresh virtual machine with the latest Ubuntu Linux that GitHub offers.
- `env:`: The identifier of one job. Everything indented below it belongs to that job.
- `WEBHOOK_P95_BUDGET_MS: "250"`: Allow a 250 ms 95th-percentile on the CI machine for the webhook timing check. The default of 100 ms is for a quiet developer machine.
- `steps:`: The identifier of one job. Everything indented below it belongs to that job.
- `- uses: actions/checkout@v4`: Copy the repository's files onto the machine. `actions/checkout` is an official action, `@v4` its version.
- `- uses: actions/setup-python@v5`: Install Python on the machine (official action, version 5).
- `with:`: The identifier of one job. Everything indented below it belongs to that job.
- `python-version: "3.13"`: Install Python 3.13.
- `- run: make up`: Run the shell command `make up`. The step fails, and so does the job, if the command exits with a non-zero code.
- `- run: make run`: Run the shell command `make run`. The step fails, and so does the job, if the command exits with a non-zero code.
- `- run: make test-integration`: Run the shell command `make test-integration`. The step fails, and so does the job, if the command exits with a non-zero code.
- `- run: make test-e2e`: Run the shell command `make test-e2e`. The step fails, and so does the job, if the command exits with a non-zero code.
- `- run: make docker-build`: Run the shell command `make docker-build`. The step fails, and so does the job, if the command exits with a non-zero code.
- `- if: always()`: Run the next step even if an earlier step failed, so the cleanup always happens.
- `run: make down`: Run `make down`, which stops the database container and deletes its data.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
ls .github/workflows
```

Lists the workflow files: `ci.yml`.

```bash
grep -n 'run:' .github/workflows/*.yml
```

Lists every command the workflows run; each is a `make` target you can run yourself.

```bash
python3 -c "import yaml" 2>/dev/null || echo 'PyYAML not installed (not needed)'
```

The repository does not depend on a YAML library; GitHub reads the files.

## Mistakes people make

- A workflow that passes only because of files that exist on one machine. Each job starts from a clean checkout.
- Unpinned or untrusted third-party actions. This repository uses only GitHub's own `actions/*` ones.
- Putting secrets in the file. Anything a model API key would need is read from the environment and a repository secret, never written here.
- A `paths` filter that forgets a file that can change behaviour.
- Running everything in one long job. Separate jobs show which part failed.

## Check yourself

1. What is a workflow?
   *Answer:* A YAML file under `.github/workflows/` describing when to run automation and what to run.
2. What is the difference between a job and a step?
   *Answer:* A job runs on one machine; a step is one command or action inside a job.
3. What does `actions/checkout` do?
   *Answer:* Copies the repository's files onto the machine.
4. What happens when a `run` command exits with code 1?
   *Answer:* The step fails, the job fails, and the change is marked as failing.
5. What does a `paths` filter do?
   *Answer:* Starts the workflow only when a changed file matches one of the patterns.

## Further reading

- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [Workflow syntax](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions)
