# argparse (command-line programs)

## What it is

`argparse` is Python's standard library module for command-line programs. You declare the commands, sub-commands and options your program accepts; `argparse` reads `sys.argv` (the words typed after the program name), checks them, converts them, and prints help and error messages for you.

## Why this repository uses it

The program's commands (`inbox-worker`) are how the Makefile and a person run each part of the lesson. `argparse` gives them sub-commands, options, validation and `--help` from the standard library, with no extra dependency.

## Where it appears

| File | What it does with argparse (command-line programs) |
| --- | --- |
| `src/inbox_worker/interfaces/cli.py` | the parser and `main` |

## How it works underneath

When you run `refund-agent gate --weaken ownership`, the operating system starts Python and hands the program the list of words `["gate", "--weaken", "ownership"]`. `ArgumentParser` builds a description of what is allowed. `add_subparsers(dest="command", required=True)` creates *sub-commands* (like `git commit`): the first word chooses one. `add_argument("--runs", type=int, default=3)` adds an *option* with a name, a converter and a default. `parse_args(argv)` returns an object whose attributes hold the values (`arguments.command`, `arguments.runs`); a bad value prints a usage message and exits with code 2.

The program's `main(argv=None)` function takes the list as an optional argument, so tests call `main(["gate"])` directly without starting a new process, and returns an integer that becomes the *exit code*: 0 for success. At the bottom, `raise SystemExit(main())` turns the return value into the process's exit code. Installing the package creates a console command that calls `main`.

## Walkthrough of this repository's use

The program is `inbox-worker` (created from `[project.scripts]` in `pyproject.toml`). First, the function that declares what the command line accepts:

From `src/inbox_worker/interfaces/cli.py`:

```python
def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="inbox-worker", description="A worker that runs a model step per inbox event."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("db", "rebuild the schema from sql/001_schema.sql and sql/002_seed.sql"),
        ("reset", "empty every table"),
        ("status", "counts, open dead letters and the lost-or-duplicated check"),
        ("webhook-demo", "valid, tampered and replayed requests"),
        ("serve-webhook", "start the webhook"),
        ("check", "exit 0 when the database answers"),
    ):
        commands.add_parser(name, help=text)
    enqueue = commands.add_parser("enqueue", help="generate the sample inbox and put every delivery on the queue")
    enqueue.add_argument("--events", type=int, default=1000)
    worker = commands.add_parser("worker", help="process deliveries until stopped")
    worker.add_argument("--until-idle", action="store_true")
    relay = commands.add_parser("relay", help="send the acknowledgments in the outbox")
    relay.add_argument("--once", action="store_true")
    redrive = commands.add_parser("redrive", help="put a dead letter back on the queue")
    redrive.add_argument("dead_id", type=int)
    commands.add_parser("bench-webhook", help="500 signed requests; report p50 and p95")
    burst = commands.add_parser("burst", help="500 events in ten seconds at two concurrency limits")
    burst.add_argument("--events", type=int, default=500)
    burst.add_argument("--seconds", type=float, default=10.0)
    burst.add_argument("--concurrency", type=int, nargs="+", default=[5, 20])
    burst.add_argument("--delay", type=float, default=0.15)
    burst.add_argument("--max-rps", type=float, default=30.0)
    crash = commands.add_parser("crash-test", help="kill the worker process at a point, restart it, compare event ids")
    crash.add_argument("--at", choices=["after_model", "after_commit"], required=True)
    return parser
```

- `def _parser() -> argparse.ArgumentParser:`: A function that builds the parser. `-> argparse.ArgumentParser` says it returns one.
- `parser = argparse.ArgumentParser(`: Creates the parser; its name and description follow.
- `prog="inbox-worker", description="A worker that runs a model step per inbox event."`: `prog` (`inbox-worker`) is the name shown in usage messages; `description` is the text under `--help`.
- `commands = parser.add_subparsers(dest="command", required=True)`: Makes room for sub-commands. `dest="command"` stores the chosen one in `arguments.command`; `required=True` means one must be chosen.
- `for name, text in (`: Starts a loop over a tuple of (name, help text) pairs, so several similar sub-commands are declared with one `add_parser` call.
- `("db", "rebuild the schema from sql/001_schema.sql and sql/002_seed.sql"),`: One pair: the sub-command `db` with its help text.
- `("reset", "empty every table"),`: One pair: the sub-command `reset` with its help text.
- `("status", "counts, open dead letters and the lost-or-duplicated check"),`: One pair: the sub-command `status` with its help text.
- `("webhook-demo", "valid, tampered and replayed requests"),`: One pair: the sub-command `webhook-demo` with its help text.
- `("serve-webhook", "start the webhook"),`: One pair: the sub-command `serve-webhook` with its help text.
- `("check", "exit 0 when the database answers"),`: One pair: the sub-command `check` with its help text.
- `commands.add_parser(name, help=text)`: Declares one sub-command per pair.
- `enqueue = commands.add_parser("enqueue", help="generate the sample inbox and put every delivery on the queue")`: Declares the sub-command `enqueue` and keeps its parser in `enqueue` so options can be added. Help text: generate the sample inbox and put every delivery on the queue
- `enqueue.add_argument("--events", type=int, default=1000)`: Adds the option `--events` to `enqueue`. `type=int` converts the text to a whole number and rejects anything else. `default=1000` is the value when the option is left out.
- `worker = commands.add_parser("worker", help="process deliveries until stopped")`: Declares the sub-command `worker` and keeps its parser in `worker` so options can be added. Help text: process deliveries until stopped
- `worker.add_argument("--until-idle", action="store_true")`: Adds the option `--until-idle` to `worker`. `action="store_true"` makes it a flag: no value is typed, and it is `True` when present.
- `relay = commands.add_parser("relay", help="send the acknowledgments in the outbox")`: Declares the sub-command `relay` and keeps its parser in `relay` so options can be added. Help text: send the acknowledgments in the outbox
- `relay.add_argument("--once", action="store_true")`: Adds the option `--once` to `relay`. `action="store_true"` makes it a flag: no value is typed, and it is `True` when present.
- `redrive = commands.add_parser("redrive", help="put a dead letter back on the queue")`: Declares the sub-command `redrive` and keeps its parser in `redrive` so options can be added. Help text: put a dead letter back on the queue
- `redrive.add_argument("dead_id", type=int)`: Adds the positional argument `dead_id` to `redrive`: a value typed after the sub-command, with no dashes. `type=int` converts it to a whole number.
- `commands.add_parser("bench-webhook", help="500 signed requests; report p50 and p95")`: Declares the sub-command `bench-webhook`. Help text: 500 signed requests; report p50 and p95
- `burst = commands.add_parser("burst", help="500 events in ten seconds at two concurrency limits")`: Declares the sub-command `burst` and keeps its parser in `burst` so options can be added. Help text: 500 events in ten seconds at two concurrency limits
- `burst.add_argument("--events", type=int, default=500)`: Adds the option `--events` to `burst`. `type=int` converts the text to a whole number and rejects anything else. `default=500` is the value when the option is left out.
- `burst.add_argument("--seconds", type=float, default=10.0)`: Adds the option `--seconds` to `burst`. `type=float` converts the text to a decimal number. `default=10.0` is the value when the option is left out.
- `burst.add_argument("--concurrency", type=int, nargs="+", default=[5, 20])`: Adds the option `--concurrency` to `burst`. `type=int` converts the text to a whole number and rejects anything else. `default=[5` is the value when the option is left out. `nargs` lets it take several values.
- `burst.add_argument("--delay", type=float, default=0.15)`: Adds the option `--delay` to `burst`. `type=float` converts the text to a decimal number. `default=0.15` is the value when the option is left out.
- `burst.add_argument("--max-rps", type=float, default=30.0)`: Adds the option `--max-rps` to `burst`. `type=float` converts the text to a decimal number. `default=30.0` is the value when the option is left out.
- `crash = commands.add_parser("crash-test", help="kill the worker process at a point, restart it, compare event ids")`: Declares the sub-command `crash-test` and keeps its parser in `crash` so options can be added. Help text: kill the worker process at a point, restart it, compare event ids
- `crash.add_argument("--at", choices=["after_model", "after_commit"], required=True)`: Adds the option `--at` to `crash`. `choices=["after_model"` accepts only the listed values. `required=True` means the command refuses to run without it.
- `return parser`: Hands the finished parser back.

Then the start of `main`, which every sub-command passes through:

```python
def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand; returns the process exit code."""
    arguments = _parser().parse_args(argv)
    try:
        settings = Settings.from_environ(os.environ)
    except ConfigurationError as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return 2
    configure_logging(settings.log_level)
```

- `def main(argv: Sequence[str] | None = None) -> int:`: The program's entry. `argv` is the list of arguments; `None` means 'use the real command line'. It returns the exit code.
- `"""Run one subcommand; returns the process exit code."""`: The docstring.
- `arguments = _parser().parse_args(argv)`: Builds the parser and parses the words. On a usage error argparse prints a message and exits with code 2 here.
- `try:`: Starts a block whose errors are handled below.
- `settings = Settings.from_environ(os.environ)`: Reads and validates every environment variable once (see `dotenv.md`).
- `except ConfigurationError as error:`: A bad setting.
- `print(f"configuration error: {error}", file=sys.stderr)`: Prints the message on standard error, where error messages belong.
- `return 2`: Exit code 2: the same code argparse uses for bad usage.
- `configure_logging(settings.log_level)`: Turns logging on at the chosen level (see `logging.md`).

After that, `main` chooses what to run by the sub-command. Each branch calls one helper; this table is read from the file:

| Sub-command | Help text | Helper `main` calls | What the helper's docstring says |
| --- | --- | --- | --- |
| `enqueue` | generate the sample inbox and put every delivery on the queue | (handled inline in `main`) |  |
| `worker` | process deliveries until stopped | `_worker` | Run one subcommand; returns the process exit code. |
| `relay` | send the acknowledgments in the outbox | `_relay` | Run one subcommand; returns the process exit code. |
| `redrive` | put a dead letter back on the queue | (handled inline in `main`) |  |
| `bench-webhook` | 500 signed requests; report p50 and p95 | `_bench_webhook` | Run one subcommand; returns the process exit code. |
| `burst` | 500 events in ten seconds at two concurrency limits | `_burst` | Run one subcommand; returns the process exit code. |
| `crash-test` | kill the worker process at a point, restart it, compare event ids | (handled inline in `main`) |  |
| `db` | rebuild the schema from sql/001_schema.sql and sql/002_seed.sql | (handled inline in `main`) |  |
| `reset` | empty every table | (handled inline in `main`) |  |
| `status` | counts, open dead letters and the lost-or-duplicated check | `_status` | A port nothing is listening on (the benchmark must not collide with a service already on the machine). |
| `webhook-demo` | valid, tampered and replayed requests | `_webhook_demo` | A port nothing is listening on (the benchmark must not collide with a service already on the machine). |
| `serve-webhook` | start the webhook | (handled inline in `main`) |  |
| `check` | exit 0 when the database answers | (handled inline in `main`) |  |
| `4417` | 9999 | (handled inline in `main`) |  |
| `WEBHOOK_P95_BUDGET_MS` | 100 | (handled inline in `main`) |  |

And the last two lines of the file:

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

- `if __name__ == "__main__":`: True only when the file is run directly, not when it is imported.
- `raise SystemExit(main())`: Runs `main` and ends the process with the number it returned as the exit code.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/inbox-worker --help
```

Prints the usage line and the list of sub-commands with their help text.

```bash
.venv/bin/inbox-worker not-a-command; echo $?
```

Prints a usage error and then `2`, argparse's exit code for bad usage.

## Mistakes people make

- Reading `sys.argv` by hand; `argparse` gives validation and `--help` for free.
- Calling `sys.exit` deep inside the code. The functions return codes to `main`, so tests can check them.
- Forgetting `required=True` on sub-parsers, which makes a bare command silently do nothing.
- Returning nothing instead of an exit code; shells and CI rely on a non-zero code to detect failure.
- Parsing numbers by hand. `type=int` and `type=float` report bad input clearly.

## Check yourself

1. What does `add_subparsers` do?
   *Answer:* Creates sub-commands, such as `program gate` and `program serve`.
2. What happens on an invalid option value?
   *Answer:* A usage message is printed and the program exits with code 2.
3. Why does `main` accept an optional list of arguments?
   *Answer:* So tests can call it directly with a list.
4. What is an exit code?
   *Answer:* A number a program returns to the shell: 0 for success, anything else for failure.
5. What does `type=int` do?
   *Answer:* Converts the text to an integer and rejects text that is not one.

## Further reading

- [argparse](https://docs.python.org/3.12/library/argparse.html)
- [argparse tutorial](https://docs.python.org/3.12/howto/argparse.html)
