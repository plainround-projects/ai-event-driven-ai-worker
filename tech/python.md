# Python 3.12

## What it is

Python is a programming language: a way to write instructions that a computer follows. A program is a text file of those instructions; a program called the *interpreter* reads the file and carries the instructions out one after another. This repository is written in Python and needs version 3.12 or newer (the file `pyproject.toml` says `requires-python = ">=3.12"`).

## Why this repository uses it

The whole repository is Python: 32 modules under `src/inbox_worker/`, 7 test files and 1 helper scripts. It was chosen because the lesson's job — a worker that runs a model step per event from a webhook or queue, applies each event's effects once, retries with backoff, parks poison events and reports its throughput under a burst — is mostly reading, checking and routing data, which Python does in short readable code, and because every library the lesson needs (the model SDK, web framework, database driver) has a first-class Python version.

## Where it appears

| File | What it does with Python 3.12 |
| --- | --- |
| `src/inbox_worker/domain/` | 7 modules: pure rules and data, standard library only |
| `src/inbox_worker/application/` | 7 modules: the use cases and the ports (interfaces) they need |
| `src/inbox_worker/infrastructure/` | 12 modules: adapters: files, databases, models, the clock, settings |
| `src/inbox_worker/interfaces/` | 5 modules: the command line, the web server, the wiring |
| `tests/` | 7 test files |
| `scripts/` | helper programs run with `python scripts/NAME.py` |
| `pyproject.toml` | names the minimum version and the package |

## How it works underneath

When you run `python something.py`, the operating system starts one *process*: a running copy of the interpreter with its own memory. The interpreter turns your text into a simpler form called *bytecode* and runs it. Every value in memory is an *object* with a type: a number, a piece of text (a `str`), a list, a dictionary (`dict`, a set of key-and-value pairs).

Code is organised in *modules*. A module is one `.py` file. A *package* is a folder of modules that has an `__init__.py` file. `import x` finds the module or package called `x` and runs it once; `from x import y` brings one name out of it. Python looks for modules in a list of folders (`sys.path`): first the folder of the script, then the places where packages were installed.

A *function* is a named block of code that takes inputs and gives back a value. A *class* is a blueprint for objects that bundle data with functions (called methods). An *exception* is an error object that stops the normal flow; `try` / `except` catches it, and `raise` makes one.

*Type hints* are optional labels such as `def area(width: int) -> int`. Python itself ignores them when running. A separate tool (here `mypy`) reads them and finds mistakes before the program runs.

Python 3.12 added things this repository relies on: the shorter generic syntax `def first[T](items: list[T]) -> T`, and better error messages. Older Pythons would not run the code.

## Walkthrough of this repository's use

The code is organised in four *layers*, each a folder of modules. Imports only go downward (the `import-linter` note shows the rule):

| Layer | Role |
| --- | --- |
| `src/inbox_worker/domain/` | 7 modules: pure rules and data, standard library only |
| `src/inbox_worker/application/` | 7 modules: the use cases and the ports (interfaces) they need |
| `src/inbox_worker/infrastructure/` | 12 modules: adapters: files, databases, models, the clock, settings |
| `src/inbox_worker/interfaces/` | 5 modules: the command line, the web server, the wiring |

### Every module and what it is for

| Module | What it is for (its docstring's first sentence) |
| --- | --- |
| `src/inbox_worker/__init__.py` | A worker for the support inbox: a signed webhook, a Postgres queue, one model step per event, effects applied once, backoff, dead letters, crash recovery and a burst measurement. |
| `src/inbox_worker/application/__init__.py` | The application layer. |
| `src/inbox_worker/application/extraction.py` | The Module 2 extractor as a step: an email in, a ticket out, one bounded repair, errors classified. |
| `src/inbox_worker/application/generate_events.py` | The sample inbox: 1,000 email events with unique ids, 2% delivered twice and 1% poison, from a seed. |
| `src/inbox_worker/application/handler.py` | Handle one delivery: decode, skip a duplicate, run the model outside any transaction, apply the effects once. |
| `src/inbox_worker/application/outbox.py` | The outbox relay: send each acknowledgment, tolerate a send that happened before a crash, mark it sent. |
| `src/inbox_worker/application/ports.py` | The boundaries the worker talks through: the queue, the effects store, the model, the mail gateway. |
| `src/inbox_worker/application/worker.py` | The worker loop: claim deliveries, handle them on a bounded pool, and stop cleanly when asked. |
| `src/inbox_worker/domain/__init__.py` | The domain layer. |
| `src/inbox_worker/domain/backoff.py` | Backoff with full jitter, capped. |
| `src/inbox_worker/domain/errors.py` | Named errors of the inbox worker. |
| `src/inbox_worker/domain/events.py` | The inbox event: its envelope, and the checks that decide an event can never be processed. |
| `src/inbox_worker/domain/signature.py` | Webhook signatures: HMAC-SHA256 over the timestamp and the body together, with a maximum age. |
| `src/inbox_worker/domain/stats.py` | Small statistics for the burst report. |
| `src/inbox_worker/domain/ticket.py` | The ticket the extractor produces. |
| `src/inbox_worker/infrastructure/__init__.py` | The infrastructure layer. |
| `src/inbox_worker/infrastructure/cassette.py` | Recorded model replies: a cassette maps a hash of the whole request to the reply, so tests run offline. |
| `src/inbox_worker/infrastructure/claude_model.py` | The real adapter: Claude through the official SDK. |
| `src/inbox_worker/infrastructure/clock.py` | The system clock. |
| `src/inbox_worker/infrastructure/environment.py` | Configuration helpers: read and validate environment variables once at startup (twelve-factor). |
| `src/inbox_worker/infrastructure/fake_model.py` | A fake model for load tests: a configurable delay, an error rate and a rate limit. |
| `src/inbox_worker/infrastructure/logging.py` | Structured logging: one logfmt line per event. |
| `src/inbox_worker/infrastructure/postgres.py` | PostgreSQL adapters: the queue (rows claimed with SKIP LOCKED), the effects store, the outbox and the report queries. |
| `src/inbox_worker/infrastructure/prompt_file.py` | Prompts as files: a two-fence header (version, owner), then the prompt text. |
| `src/inbox_worker/infrastructure/retry.py` | Retry with exponential backoff and full jitter for calls that cross the network. |
| `src/inbox_worker/infrastructure/settings.py` | Configuration from the environment, validated once at startup (twelve-factor). |
| `src/inbox_worker/infrastructure/shutdown.py` | Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work. |
| `src/inbox_worker/interfaces/__init__.py` | The interfaces layer. |
| `src/inbox_worker/interfaces/cli.py` | The `inbox-worker` command: database, events, webhook, worker, relay, redrive, measurements. |
| `src/inbox_worker/interfaces/measure.py` | Measurements that need threads and a database: the burst, the crash recovery and the webhook latency. |
| `src/inbox_worker/interfaces/webhook.py` | The webhook: verify the signature, queue the event, answer 202. |
| `src/inbox_worker/interfaces/wiring.py` | Compose the database, model, handler, worker and relay the settings ask for. |

### The language features this code uses, with this repository's own examples

### Module docstring and `from __future__ import annotations`

Every module starts with a *docstring*: text in triple quotes that says what the module is for (the repository's linter requires it). The line `from __future__ import annotations` makes Python store type hints as text and evaluate them later, so a hint may mention a class defined further down the file.

In this repository, from `src/inbox_worker/domain/__init__.py` (The domain layer):

```python
"""The domain layer."""
```

### Type hints

After each parameter, `: type` says what is expected. After the closing parenthesis, `-> type` says what the function returns. `int | None` means 'an integer or nothing'. `list[str]`, `dict[str, int]`, `tuple[int, ...]` describe containers and what is inside them. Python ignores hints when running; `mypy` reads them.

In this repository, from `src/inbox_worker/domain/backoff.py` (Backoff with full jitter, capped):

```python
def backoff_delay(attempt: int, base_seconds: float, cap_seconds: float, rng: random.Random) -> float:
    """A random delay in [0, min(cap, base * 2**(attempt - 1))]. Full jitter spreads retries of many failing events
    over time; a fixed exponential schedule would have them all retry at the same moments and synchronize into bursts."""
    return rng.uniform(0, min(cap_seconds, base_seconds * 2 ** (attempt - 1)))
```

### Dataclasses

`@dataclass` (a *decorator*, a line starting with `@` that modifies the class below it) writes the boring parts of a data-holding class for you: the constructor, the printed form, and equality. `frozen=True` makes instances unchangeable after creation, so a value cannot be altered by accident. `slots=True` stores fields compactly and forbids stray attributes. Each `name: type` line is one field; `= value` gives a default.

In this repository, from `src/inbox_worker/domain/events.py` (The inbox event: its envelope, and the checks that decide an event can never be processed):

```python
@dataclass(frozen=True, slots=True)
class EmailEvent:
    """An "email received" event: a unique id and the email text."""

    event_id: str
    body: str
```

### Protocols (interfaces between layers)

A `Protocol` describes what an object must be able to do, without saying how. The application layer defines protocols (called *ports*), for example 'a model that can complete a request'. The infrastructure layer supplies classes that fit them (called *adapters*). The `...` body means 'no code here; this is only the shape'. Because a test can supply a fake that fits the same shape, the rest of the code never needs the real model, database or clock.

In this repository, from `src/inbox_worker/application/ports.py` (The boundaries the worker talks through: the queue, the effects store, the model, the mail gateway):

```python
class DeliveryQueue(Protocol):
    """A queue with acknowledgments and redelivery, in a database table read with row locks."""

    def put(self, event_id: str, payload: str) -> int:
        """Add a delivery; returns its id."""
        ...

    def claim(self, limit: int, lease_seconds: float) -> Sequence[Delivery]:
        """Take up to `limit` ready deliveries for `lease_seconds`. A claim that is never acknowledged expires, and the
        delivery is handed out again (this is the redelivery after a crash)."""
        ...
```

### Custom exceptions

An exception class is a named kind of error. Inheriting from a built-in one (`ValueError`, `RuntimeError`) makes it catchable by code that handles the parent. A specific name lets callers handle one failure differently from another.

In this repository, from `src/inbox_worker/domain/errors.py` (Named errors of the inbox worker):

```python
class PermanentEventError(Exception):
    """An event that can never succeed. `reason` is one of the dead-letter reasons; the message is what a person reads."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
```

### try / except / raise

Code in `try:` runs normally. If it raises an error of the type named after `except`, the matching `except` block runs instead of the program stopping. `raise` (alone) re-raises the current error; `raise X(...) from error` raises a new error and records the old one as its cause.

In this repository, from `src/inbox_worker/application/extraction.py` (The Module 2 extractor as a step: an email in, a ticket out, one bounded repair, errors classified):

```python
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ReplyInvalidError(f"not valid JSON: {error.msg}") from None
    if not isinstance(data, dict):
        raise ReplyInvalidError("not a JSON object")
    return Ticket.from_dict(data)
```

### Context managers (`with`)

`with thing:` runs a block and guarantees clean-up when it ends, even on an error: a file is closed, a lock is released, a transaction is committed or rolled back. `as name` gives the block a name for what `with` produced.

In this repository, from `src/inbox_worker/infrastructure/fake_model.py` (A fake model for load tests: a configurable delay, an error rate and a rate limit):

```python
        with self._lock:
            self.calls += 1
            if self._max_rps > 0:
                now = self._clock()
                self._tokens = min(self._max_rps, self._tokens + (now - self._refilled) * self._max_rps)
                self._refilled = now
```

### Comprehensions and generator expressions

`[f(x) for x in items if test(x)]` builds a list by looping in one line: for each `x` in `items` that passes the test, add `f(x)`. With round brackets (or inside `sum(...)`, `any(...)`, `all(...)`) it is a *generator expression*: the values are produced one at a time and not stored.

In this repository, from `src/inbox_worker/application/generate_events.py` (The sample inbox: 1,000 email events with unique ids, 2% delivered twice and 1% poison, from a seed):

```python
    healthy = [event_id for event_id, _ in deliveries if event_id not in poison]
    repeated = frozenset(rng.sample(healthy, round(count * duplicate_rate)))
    by_id = dict(deliveries)
    result = list(deliveries)
```

### f-strings

An f-string is text with a leading `f` whose `{...}` holes are filled with values: `f"{name} must be set"`. `{value!r}` shows the value as code would write it (with quotes), and `{number:.1f}` formats to one decimal place.

In this repository, from `src/inbox_worker/domain/events.py` (The inbox event: its envelope, and the checks that decide an event can never be processed):

```python
        raise PermanentEventError("malformed_event", f"the event is not valid JSON: {error.msg}") from None
    if not isinstance(data, dict) or not isinstance(data.get("event_id"), str) or not data["event_id"].strip():
        raise PermanentEventError("malformed_event", "the event needs a non-empty string event_id")
```

### Generic functions with `[T]`

`def retry[T](...) -> T` declares a *type parameter*: whatever type the passed-in function returns is the type `retry` returns, and `mypy` tracks that. This syntax is new in Python 3.12.

In this repository, from `src/inbox_worker/infrastructure/retry.py` (Retry with exponential backoff and full jitter for calls that cross the network):

```python
def retry[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
```

### async def and await

An `async def` function can pause at `await` (for example while waiting for the network) so other work can run meanwhile. Only the event loop (see `asyncio.md`) runs these functions.

In this repository, from `src/inbox_worker/interfaces/webhook.py` (The webhook: verify the signature, queue the event, answer 202):

```python
    async def receive(
        request: Request,
        x_timestamp: Annotated[str | None, Header()] = None,
        x_signature: Annotated[str | None, Header()] = None,
    ) -> JSONResponse:
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
```

### Properties

`@property` lets a method be read like an attribute (`thing.requested`, no parentheses), so callers see a value while the class keeps the freedom to compute it.

In this repository, from `src/inbox_worker/infrastructure/shutdown.py` (Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work):

```python
    @property
    def requested(self) -> bool:
        """True once a stop was requested."""
        return self._requested.is_set()
```

### The entry-point guard

A module's `__name__` is `"__main__"` only when the file is run directly (for example `python -m package.module`), and its package-qualified name when imported. The guard lets the same file be both importable and runnable. `raise SystemExit(main())` ends the process with the exit code `main` returned.

In this repository, from `src/inbox_worker/interfaces/cli.py` (The `inbox-worker` command: database, events, webhook, worker, relay, redrive, measurements):

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

### The infrastructure helpers shared by the repository

The lesson's logic is in `application/handler.py` (one delivery to a final outcome), `application/worker.py` (claim, handle on a pool, stop, survive a database restart), `domain/events.py` (decode an event or say why it can never succeed), `domain/signature.py` and `domain/backoff.py`. The shared infrastructure helpers are walked through below.

A reading guide to the central modules: every class and function, with its signature and the docstring that says what it is for.

#### `src/inbox_worker/application/handler.py`

The module's docstring says: *Handle one delivery: decode, skip a duplicate, run the model outside any transaction, apply the effects once.*

- `class RetryPolicy:` (class): How a failing event is retried before it is parked.
- `class EventHandler:` (class): Applies each event's effects once, however often the queue delivers it. `crash_at` is called with a point name ("after_model", "after_commit"); the crash tests make it kill the process.
  - `def __init__( self, queue: DeliveryQueue, effects: EffectsStore, extractor: TicketExtractor, clock: Clock, policy: RetryPolicy | None = None, *, rng: random.Random | None = None, crash_at: Callable[[str], None] = lambda point: None, ) -> None:`
  - `def handle(self, delivery: Delivery) -> str:`: Process one delivery to a final outcome, acknowledging it unless the process dies first.
  - `def _retry_or_park(self, delivery: Delivery, error: RetryableModelError | ModelCallError) -> str:`

#### `src/inbox_worker/application/worker.py`

The module's docstring says: *The worker loop: claim deliveries, handle them on a bounded pool, and stop cleanly when asked.*

- `class Worker:` (class): Pulls batches from the queue. A shutdown request finishes the deliveries in flight and then returns.
  - `def __init__( self, queue: DeliveryQueue, handler: EventHandler, *, concurrency: int, lease_seconds: float, stop_requested: Callable[[], bool], wait: Callable[[float], bool], idle_poll_seconds: float = 0.2, ) -> None:`
  - `def _handle_safely(self, delivery: Delivery) -> str:`: A failure the handler did not classify is logged and left to the lease: the delivery comes back.
  - `def run(self, *, until_idle: bool = False) -> Counter[str]:`: Process deliveries until a stop is requested (or, with `until_idle`, until the queue is empty).

#### `src/inbox_worker/application/outbox.py`

The module's docstring says: *The outbox relay: send each acknowledgment, tolerate a send that happened before a crash, mark it sent.*

- `class DuplicateSendError(RuntimeError):` (class): The mail gateway has already sent this event's acknowledgment.
- `class OutboxRelay:` (class): Sends unsent outbox rows. A row whose mail was already sent (the relay died before marking it) is just marked.
  - `def __init__(self, outbox: OutboxStore, gateway: MailGateway) -> None:`
  - `def run_once(self, limit: int = 100) -> int:`: Send up to `limit` rows; returns how many rows were marked sent.

#### `src/inbox_worker/application/extraction.py`

The module's docstring says: *The Module 2 extractor as a step: an email in, a ticket out, one bounded repair, errors classified.*

- `class Extraction:` (class): A ticket and the model calls it took.
- `def _parse(text: str) -> Ticket:`
- `class TicketExtractor:` (class): Model-backed extraction. A schema failure that survives one repair is permanent; model errors keep their type.
  - `def __init__(self, model: ChatModel, system: str = SYSTEM, version: str = PROMPT_VERSION) -> None:`
  - `def extract(self, email: str) -> Extraction:`: One call, and one repair call when the reply is not a valid ticket.

#### `src/inbox_worker/domain/events.py`

The module's docstring says: *The inbox event: its envelope, and the checks that decide an event can never be processed.*

- `class EmailEvent:` (class): An "email received" event: a unique id and the email text.
- `def parse_event(payload: str) -> EmailEvent:`: Decode a delivery's payload. Raises `PermanentEventError` for a body that is not an event, is not valid text, or is too large: none of those will be different on the next attempt, so they go to the dead-letter table.
- `def event_id_of(payload: str) -> str:`: The event id a receiver files a payload under; a payload that is not an event gets a stable placeholder so it can still be queued, parked and shown to a person.

#### `src/inbox_worker/domain/signature.py`

The module's docstring says: *Webhook signatures: HMAC-SHA256 over the timestamp and the body together, with a maximum age.*

- `def sign(secret: bytes, timestamp: float, body: str) -> str:`: The signature a sender attaches. Signing the timestamp too is what stops a captured request being replayed later.
- `def verify(secret: bytes, timestamp: str, body: str, signature: str, now: float) -> tuple[bool, str]:`: (ok, reason). Age is checked first and cheaply; the comparison is constant-time.

#### `src/inbox_worker/domain/backoff.py`

The module's docstring says: *Backoff with full jitter, capped.*

- `def backoff_delay(attempt: int, base_seconds: float, cap_seconds: float, rng: random.Random) -> float:`: A random delay in [0, min(cap, base * 2**(attempt - 1))]. Full jitter spreads retries of many failing events over time; a fixed exponential schedule would have them all retry at the same moments and synchronize into bursts.

#### `src/inbox_worker/infrastructure/postgres.py`

The module's docstring says: *PostgreSQL adapters: the queue (rows claimed with SKIP LOCKED), the effects store, the outbox and the report queries.*

- `class Database:` (class): A small connection pool over one database URL.
  - `def __init__(self, url: str, max_connections: int = 16) -> None:`
  - `def connection(self) -> psycopg.Connection:`: Borrow a connection (autocommit: one statement is one transaction and one round trip). Wrap several statements that must happen together in `with connection.transaction():`.
  - `def close(self) -> None:`: Close the pool.
  - `def ping(self) -> bool:`: True when a trivial query works.
- `def apply_scripts(database: Database, sql_dir: Path) -> list[str]:`: Drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran.
- `def reset_tables(database: Database, sql_dir: Path) -> None:`: Empty every table (sql/reset.sql).
- `class PostgresQueue:` (class): The delivery queue.
  - `def __init__(self, database: Database) -> None:`
  - `def put(self, event_id: str, payload: str) -> int:`: Insert one delivery.
  - `def put_many(self, items: Sequence[tuple[str, str]]) -> None:`: Insert many deliveries in one transaction (loading the sample events).
  - `def claim(self, limit: int, lease_seconds: float) -> Sequence[Delivery]:`: Claim ready deliveries; an expired claim is handed out again.
  - `def ack(self, delivery_id: int) -> None:`: Finish a delivery.
  - `def retry(self, delivery_id: int, delay_seconds: float, error: str) -> None:`: Release the claim and make the delivery available after a delay.
  - `def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:`: Park the delivery with what a person needs to act; both writes are one transaction.
  - `def depth(self) -> int:`: Deliveries that are queued or in flight.
  - `def redrive(self, dead_id: int) -> int | None:`: Put a dead letter's payload back on the queue as a new delivery and mark it redriven; None if unknown or done.
- `class PostgresEffects:` (class): The processed mark, the ticket and the outbox row.
  - `def __init__(self, database: Database) -> None:`
  - `def is_processed(self, event_id: str) -> bool:`: True when the event's effects were applied (read fresh from the database every time).
  - `def apply(self, event_id: str, ticket: Ticket) -> bool:`: Write the mark, the ticket and the outbox row in ONE statement (so one transaction and one round trip). The primary key on the mark settles a race: a twin delivery that commits first leaves this statement inserting nothing.
- `class PostgresOutbox:` (class): The unsent acknowledgments.
  - `def __init__(self, database: Database) -> None:`
  - `def unsent(self, limit: int) -> Sequence[tuple[int, str, str]]:`: Oldest unsent rows.
  - `def mark_sent(self, outbox_id: int) -> None:`: Record that the row was sent.
- `class FakeMailSender:` (class): Records every send in `sent_mail`; the unique event id refuses a second send of one acknowledgment.
  - `def __init__(self, database: Database) -> None:`
  - `def send(self, event_id: str, kind: str) -> None:`: Record one send.
- `class PostgresReports:` (class): Read-only queries for the reports and the verification steps.
  - `def __init__(self, database: Database) -> None:`
  - `def _one(self, sql: str) -> int:`
  - `def counts(self) -> dict[str, int]:`: Rows in the tables that matter.
  - `def ticket_event_ids(self) -> list[str]:`: Event id of every ticket (duplicates would show up twice).
  - `def dead_events(self) -> list[tuple[int, str, str, int, str, str]]:`: (dead id, event id, reason, attempts, last error, payload hash) of open dead letters.
  - `def event_to_ticket_seconds(self) -> list[float]:`: Seconds from the first delivery of each ticketed event to its ticket.
  - `def now(self) -> datetime:`: The database's clock.

#### `src/inbox_worker/interfaces/measure.py`

The module's docstring says: *Measurements that need threads and a database: the burst, the crash recovery and the webhook latency.*

- `class BurstResult:` (class): What one burst measured.
- `def run_burst( components: Components, *, events: int, seconds: float, concurrency: int, delay: float, max_rps: float ) -> BurstResult:`: Send `events` events over `seconds` to a worker with `concurrency` threads, against a fake model with a rate limit. Throughput is tickets over the time from the first event to an empty queue. The queue depth is sampled every 50 ms.
- `def run_crash_test(components: Components, point: str, events: int = 30) -> tuple[Counter[str], list[str], list[str]]:`: Kill the worker process at `point` (after the model call, or after the commit), restart it, and return the exit codes, the event ids sent and the event ids that have tickets.
- `def wait_for_port(url_ready: str, attempts: int = 100) -> None:`: Poll a URL until it answers 200.

#### `src/inbox_worker/infrastructure/fake_model.py`

The module's docstring says: *A fake model for load tests: a configurable delay, an error rate and a rate limit. It is not a model. It extracts a ticket with keyword rules, so a run has real tickets to count. The rate limit is a token bucket in requests per second; a call over it raises the same error a provider's 429 would, and the call is counted.*

- `class FakeModel:` (class): Thread-safe; counts calls, rate-limit errors and injected errors.
  - `def __init__( self, *, delay_seconds: float = 0.0, error_rate: float = 0.0, max_rps: float = 0.0, seed: int = 1, sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic, ) -> None:`
  - `def _admit(self) -> None:`
  - `def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:`: Wait for the delay, then answer; raises `RetryableModelError` over the rate limit or on an injected error.
  - `def _ticket(email: str) -> str:`


### Retry with full jitter (`infrastructure/retry.py`)

From `src/inbox_worker/infrastructure/retry.py`:

```python
def retry[T](
    operation: Callable[[], T],
    *,
    attempts: int,
    base_delay_seconds: float,
    retry_on: tuple[type[BaseException], ...],
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
    max_delay_seconds: float = 10.0,
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> T:
    """Call `operation` up to `attempts` times, backing off after each failure in `retry_on`.

    The pause after attempt n is a random value in [0, min(max_delay, base * 2**(n - 1))] (full jitter),
    so many clients do not retry in step. The last failure is raised.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    jitter = rng or random.Random()
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except retry_on as error:
            if attempt == attempts:
                raise
            if on_retry:
                on_retry(attempt, error)
            sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))))
    raise AssertionError("unreachable")  # pragma: no cover
```

- `def retry[T](`: A function with a *type parameter* `T` (new syntax in Python 3.12): whatever type `operation` returns is the type `retry` returns.
- `operation: Callable[[], T],`: `operation` is a function that takes no arguments and returns a `T`. Passing functions as values is normal in Python.
- `*,`: Everything after this bare `*` must be given by name (`attempts=3`), never by position, which keeps calls readable.
- `attempts: int,`: How many times to try in total.
- `base_delay_seconds: float,`: The starting pause.
- `retry_on: tuple[type[BaseException], ...],`: A tuple of exception classes worth retrying. `...` means any length.
- `sleep: Callable[[float], None] = time.sleep,`: The function used to wait. It defaults to the real `time.sleep` but a test passes a fake, so tests do not actually wait.
- `rng: random.Random | None = None,`: The random number generator, injectable for the same reason.
- `max_delay_seconds: float = 10.0,`: The longest allowed pause.
- `on_retry: Callable[[int, BaseException], None] | None = None,`: An optional function called before each pause, for logging.
- `) -> T:`: The declared return type.
- `` """Call `operation` up to `attempts` times, backing off after each failure in `retry_on`. ``: The docstring explains *full jitter*: after attempt n the pause is a random value between 0 and `min(max_delay, base * 2**(n-1))`. 'Exponential' means it doubles each time; 'jitter' means random, so many clients do not retry at the same moment.
- `The pause after attempt n is a random value in [0, min(max_delay, base * 2**(n - 1))] (full jitter),`: (Continuation of the docstring.)
- `so many clients do not retry in step. The last failure is raised.`: (Continuation of the docstring.)
- `"""`: Ends the docstring.
- `if attempts < 1:`: Rejects a nonsense setting.
- `raise ValueError("attempts must be at least 1")`: Stops with a clear error.
- `jitter = rng or random.Random()`: Uses the given generator or makes a new one.
- `for attempt in range(1, attempts + 1):`: Counts attempts 1, 2, ... up to `attempts`.
- `try:`: Start of the guarded call.
- `return operation()`: Calls the operation; if it works, return its result at once.
- `except retry_on as error:`: Catches only the retryable exception types; any other error passes through untouched.
- `if attempt == attempts:`: On the last attempt there is nothing left to try.
- `raise`: Re-raises the same error, so the caller sees the real failure.
- `if on_retry:`: Start of the guarded call.
- `on_retry(attempt, error)`: ...call it with the attempt number and the error.
- `sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))))`: Waits a random time between 0 and the capped doubling delay; `2 ** (attempt - 1)` is 1, 2, 4, 8...
- `raise AssertionError("unreachable")  # pragma: no cover`: Re-raises the same error, so the caller sees the real failure.

### Graceful shutdown (`infrastructure/shutdown.py`)

From `src/inbox_worker/infrastructure/shutdown.py`:

```python
"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""

from __future__ import annotations

import signal
import threading
from types import FrameType


class ShutdownSignal:
    """A flag that SIGINT and SIGTERM set, which work loops check between units of work."""

    def __init__(self) -> None:
        self._requested = threading.Event()

    def install(self) -> None:
        """Route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close."""
        for number in (signal.SIGINT, signal.SIGTERM):
            signal.signal(number, self._handle)

    def _handle(self, _number: int, _frame: FrameType | None) -> None:
        self.request()

    def request(self) -> None:
        """Ask the loops to stop after the unit of work in flight."""
        self._requested.set()

    @property
    def requested(self) -> bool:
        """True once a stop was requested."""
        return self._requested.is_set()

    def wait(self, seconds: float) -> bool:
        """Sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested."""
        return self._requested.wait(seconds)
```

- `"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""`: The module docstring: SIGINT and SIGTERM set a flag that work loops check between units of work. A *signal* is a small message the operating system sends to a process; SIGINT is sent by Ctrl-C and SIGTERM is the polite 'please stop' sent by `kill` and by Docker.
- `from __future__ import annotations`: Stores type hints as text.
- `import signal`: The standard module for catching signals.
- `import threading`: The standard module for threads; here only for `threading.Event`.
- `from types import FrameType`: Only for a type hint: the signal handler receives the current stack frame.
- `class ShutdownSignal:`: A small class that holds one flag, 'stop was requested'.
- `"""A flag that SIGINT and SIGTERM set, which work loops check between units of work."""`: The class docstring.
- `def __init__(self) -> None:`: The *constructor*, run when `ShutdownSignal()` is called.
- `self._requested = threading.Event()`: An `Event` is a thread-safe flag that starts unset. Other threads can wait on it.
- `def install(self) -> None:`: Connects the signals to the flag.
- `` """Route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close.""" ``: The docstring.
- `for number in (signal.SIGINT, signal.SIGTERM):`: Loops over the two signal numbers.
- `signal.signal(number, self._handle)`: Registers `self._handle` as the function to call when that signal arrives, instead of the default (which ends the process at once).
- `def _handle(self, _number: int, _frame: FrameType | None) -> None:`: The function Python calls on a signal. The leading underscores on the argument names say they are deliberately unused.
- `self.request()`: Sets the flag.
- `def request(self) -> None:`: Asks the loops to stop.
- `"""Ask the loops to stop after the unit of work in flight."""`: The docstring.
- `self._requested.set()`: Sets the Event; every waiting thread wakes.
- `@property`: A *decorator* that lets the method below be read like an attribute: `shutdown.requested` without parentheses.
- `def requested(self) -> bool:`: Reads the flag.
- `"""True once a stop was requested."""`: The docstring.
- `return self._requested.is_set()`: True once `set()` was called.
- `def wait(self, seconds: float) -> bool:`: Sleeps, but wakes early if a stop is requested.
- `` """Sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested.""" ``: The docstring.
- `return self._requested.wait(seconds)`: `Event.wait(timeout)` blocks up to that many seconds and returns True if the flag was set. Work loops use it instead of `time.sleep`, so a stop request interrupts the pause.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/python --version
```

Prints the interpreter version: `Python 3.13.12` on the machine this was written on. Any 3.12 or newer works.

```bash
.venv/bin/python -c "import inbox_worker; print(inbox_worker.__file__)"
```

Prints the path of `src/inbox_worker/__init__.py`. This shows the editable install: Python imports the package straight from the `src` folder.

```bash
.venv/bin/python -c "import sys; print(sys.prefix)"
```

Prints the path of the `.venv` folder, which proves this is the private environment and not the system Python.

```bash
grep -c 'def ' src/inbox_worker/domain/*.py | head -5
```

Counts the function definitions in a few domain modules (a quick way to see how much logic the layer holds).

## Mistakes people make

- Mixing the system Python with project packages. This repository always runs `.venv/bin/python`, the Python of its private virtual environment, so the packages it needs are exactly the pinned ones.
- Using a mutable default argument, such as `def f(items=[])`. The list is created once and shared by every call. The code here uses `field(default_factory=list)` in dataclasses and `None` defaults instead.
- Catching every exception with a bare `except:`. That hides real bugs. The code catches the specific exception types it expects.
- Comparing money or other exact amounts with floating-point numbers. `0.1 + 0.2` is not exactly `0.3`. Where exactness matters the code keeps the amount as text or uses `Decimal`.
- Forgetting that indentation is part of the syntax. A block is whatever is indented under its `:` line.

## Check yourself

1. What is the difference between a module and a package?
   *Answer:* A module is one `.py` file. A package is a folder of modules that contains an `__init__.py` file.
2. Does Python check type hints while the program runs?
   *Answer:* No. It stores them but ignores them. A separate tool such as `mypy` checks them before the program runs.
3. What does `import x` do the first time it runs for a module?
   *Answer:* It finds the module on `sys.path`, runs its top-level code once, and keeps the result so later imports reuse it.
4. Why does the repository run `.venv/bin/python` and not just `python`?
   *Answer:* So the program uses the private virtual environment with the pinned package versions, not whatever happens to be installed on the machine.
5. What is an exception, and how do you stop one from ending the program?
   *Answer:* An error object that interrupts the normal flow. Wrap the risky code in `try:` and handle the type you expect in `except ThatType:`.

## Further reading

- [The Python 3.12 tutorial](https://docs.python.org/3.12/tutorial/)
- [The Python 3.12 language reference](https://docs.python.org/3.12/reference/)
- [The Python 3.12 standard library](https://docs.python.org/3.12/library/)
- [What is new in Python 3.12](https://docs.python.org/3.12/whatsnew/3.12.html)
