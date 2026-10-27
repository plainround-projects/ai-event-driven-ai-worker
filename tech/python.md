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



<!-- fullwalk -->
### Every Python file of the program, statement by statement

This part quotes every Python file under `src/` and `scripts/`, in the order they are listed by git, and says in plain words what each statement does. Each quoted block is the file's own text; the bullets underneath explain it. A grey note (a block starting with `>`) explains a Python idea the first time it appears.

#### `scripts/smoke.py`

```python
"""Run 20 sample emails through the extractor with the chosen model: the real-model smoke run of the lesson.

python scripts/smoke.py             # MODEL_ADAPTER=recorded (default) replays tests/fixtures/cassettes/smoke-v1.json
python scripts/smoke.py --author    # write that cassette from the fake model (not a model recording)
python scripts/smoke.py --record    # MODEL_ADAPTER=claude: call the real model and write live-v1.json (needs a key)
"""
```

- The docstring (documentation kept with the code) says: *Run 20 sample emails through the extractor with the chosen model: the real-model smoke run of the lesson. python scripts/smoke.py # MODEL_ADAPTER=recorded (default) replays tests/fixtures/cassettes/smoke-v1.json python scripts/smoke.py --author # write that cassette from the fake model (not a model recording) python scripts/smoke.py --record # MODEL_ADAPTER=claude: call the real model and write...*

> **A Python file is a module.** When another file writes `import` or `from ... import`, Python runs this file once and hands over the names it defines. A docstring is a string that sits first in a module, class or function; Python keeps it as the documentation of that thing.

```python
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from inbox_worker.application.extraction import PROMPT_VERSION, SYSTEM
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`PROMPT_VERSION`: a name defined in this repository.) (`SYSTEM`: a name defined in this repository.)

> **`if __name__ == "__main__":`.** Python sets `__name__` to `"__main__"` only when the file is run directly (`python file.py`), not when another file imports it. So the block runs only for a direct start.

> **`import` and `from ... import`.** `import x` makes the module `x` available under that name. `from x import y` fetches only the name `y` from `x` so it can be used without the prefix. `as` renames what you import. Imports at the top mean: this file needs those things from elsewhere.

> **`from __future__ import annotations`.** The type hints written after a colon or an arrow are saved as text and only looked at by type checkers, so a hint may name a class that is defined later in the file.

```python
from inbox_worker.application.generate_events import generate_events
from inbox_worker.domain.errors import ModelCallError, PermanentEventError, RetryableModelError
from inbox_worker.infrastructure.cassette import RecordingModel, request_key
from inbox_worker.infrastructure.claude_model import ClaudeModel
from inbox_worker.infrastructure.fake_model import FakeModel
from inbox_worker.infrastructure.settings import Settings
```

- `from inbox_worker.application.generate_events import ...`: takes names from `inbox_worker.application.generate_events`, this repository's own code. (`generate_events`: `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable.)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`ModelCallError`: A model call failed in a way a retry will not fix.) (`PermanentEventError`: An event that can never succeed.) (`RetryableModelError`: A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection.)
- `from inbox_worker.infrastructure.cassette import ...`: takes names from `inbox_worker.infrastructure.cassette`, this repository's own code. (`RecordingModel`: Wraps a real model and writes every reply to a cassette, keyed like `RecordedModel` expects.) (`request_key`: Hash of everything that decides the reply.)
- `from inbox_worker.infrastructure.claude_model import ...`: takes names from `inbox_worker.infrastructure.claude_model`, this repository's own code. (`ClaudeModel`: One Messages API call per request.)
- `from inbox_worker.infrastructure.fake_model import ...`: takes names from `inbox_worker.infrastructure.fake_model`, this repository's own code. (`FakeModel`: Thread-safe; counts calls, rate-limit errors and injected errors.)
- `from inbox_worker.infrastructure.settings import ...`: takes names from `inbox_worker.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)

```python
from inbox_worker.interfaces.wiring import build_extractor, build_model

ROOT = Path(__file__).resolve().parents[1]
CASSETTE = ROOT / "tests/fixtures/cassettes/smoke-v1.json"
```

- `from inbox_worker.interfaces.wiring import ...`: takes names from `inbox_worker.interfaces.wiring`, this repository's own code. (`build_extractor`: The extractor over the model, with the prompt text and version read from the versioned prompt file.) (`build_model`: The fake model (load tests), the recorded adapter (offline smoke run), or Claude.)
- `ROOT = Path(__file__).resolve().parents[1]`: stores the item `Path(__file__).resolve().parents[1]` in `ROOT`.
- `CASSETTE = ROOT / "tests/fixtures/cassettes/smoke-v1.json"`: stores the path `ROOT / "tests/fixtures/cassettes/smoke-v1.json"` (`/` joins path parts) in `CASSETTE`.

> **A name is a label for a value.** `x = 5` makes the name `x` point to the value 5. Names are not boxes with a fixed type; Python looks at the value at run time. A name written in CAPITALS by habit marks a constant: nobody should change it.

> **Indexing and slicing.** `items[0]` is the first item; `items[-1]` the last; `items[a:b]` is a new list from position `a` up to but not including `b`; `d['key']` looks a key up in a dict (and raises `KeyError` if it is missing).

```python
def emails() -> list[str]:
```

- Defines the function `emails`.
- Gives back a value of type `list[str]`.

> **A function.** `def name(parameters):` defines a reusable block of code. The indented lines below it are the body; they run each time the function is called. `return` ends the call and hands a value back. A function that reaches its end without `return` hands back `None`, Python's 'nothing'.

```python
"""The first 20 healthy sample emails."""
```

- The docstring (documentation kept with the code) says: *The first 20 healthy sample emails.*

```python
inbox = generate_events(200, poison_rate=0.0, duplicate_rate=0.0)
return [json.loads(payload)["body"] for _, payload in inbox.deliveries[:20]]
```

- `inbox = generate_events(200, poison_rate=0.0, duplicate_rate=0.0)`: stores the result of calling `generate_events(200, poison_rate=0.0, duplicate_rate=0.0)`, which is this repository's own `generate_events` (in `src/inbox_worker/application/generate_events.py`): `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable The named values are `poison_rate`, `duplicate_rate`. in `inbox`.
- `return [json.loads(payload)["body"] for _, payload in inbox.deliver...`: ends the function and gives back a list built by running `json.loads(payload)["body"]` for each `_, payload` in `inbox.deliveries[:20]`.

> **Comprehensions.** `[f(x) for x in items if test(x)]` builds a new list: run `f` on every item that passes the test. With `{k: v for ...}` it builds a dict, with `{x for ...}` a set. With round brackets it is a generator expression: the values are produced one at a time, only when something asks for the next one.

```python
def author() -> None:
```

- Defines the function `author`.
- Gives back a value of type `None`.

```python
"""Write the cassette from the fake model."""
```

- The docstring (documentation kept with the code) says: *Write the cassette from the fake model.*

```python
fake = FakeModel()
entries = {}
```

- `fake = FakeModel()`: stores the result of calling `FakeModel()`, which is this repository's own `FakeModel` (in `src/inbox_worker/infrastructure/fake_model.py`): thread-safe; counts calls, rate-limit errors and injected errors in `fake`.
- `entries = {}`: stores a new dict (empty) in `entries`.

```python
for email in emails():
```

- Repeats the indented lines once for each item of `emails()`, naming the current item `email`.

> **`for`.** `for item in things:` runs the indented lines once per item, giving the name `item` the next value each time. `break` leaves the loop early; `continue` jumps to the next item.

```python
reply = fake.complete(SYSTEM, email, PROMPT_VERSION)
entries[request_key("authored-fake-model", SYSTEM, email, PROMPT_VERSION)] = {
    "text": reply.text,
    "input_tokens": reply.input_tokens,
    "output_tokens": reply.output_tokens,
}
```

- `reply = fake.complete(SYSTEM, email, PROMPT_VERSION)`: stores the result of calling `fake.complete(SYSTEM, email, PROMPT_VERSION)` in `reply`.
- `entries[request_key("authored-fake-model", SYSTEM, email, PROMPT_VE...`: stores a new dict with 3 entries in the slot `entries[request_key("authored-fake-model", SYSTEM, email, PROMPT_VERSION)]`.

```python
document = {
    "provenance": "authored by scripts/smoke.py --author from the fake model; not a model recording. Replace with `make record`.",
    "model": "authored-fake-model",
    "entries": entries,
}
CASSETTE.parent.mkdir(parents=True, exist_ok=True)
CASSETTE.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {len(entries)} replies to {CASSETTE.relative_to(ROOT)}")
```

- `document = { "provenance": "authored by scripts/smoke.py --author f...`: stores a new dict with 3 entries in `document`.
- `CASSETTE.parent.mkdir(parents=True, exist_ok=True)`: calling `CASSETTE.parent.mkdir(parents=True, exist_ok=True)`, which creates the folder `CASSETTE.parent` The named values are `parents`, `exist_ok`..
- `CASSETTE.write_text(json.dumps(document, indent=1, sort_keys=True) ...`: calling `CASSETTE.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="ut...`, which writes text to the file `CASSETTE`, replacing it The named values are `encoding`..
- `print(f"wrote {len(entries)} replies to {CASSETTE.relative_to(ROOT)}")`: calling `print(f"wrote {len(entries)} replies to {CASSETTE.relative_to(ROOT)}")`, which writes `f"wrote {len(entries)} replies to {CASSETTE.relative_to(ROOT)}"` to the screen (standard output).

```python
def run(record: bool) -> int:
```

- Defines the function `run`.
- Parameters:
  - `record`, type `bool`.
- Gives back a value of type `int`.

> **Parameters.** A parameter with `= value` is optional: if the caller gives nothing, the default is used. A bare `*` in the list means everything after it must be passed by name (`f(x=1)`). `*args` collects extra positional arguments in a tuple and `**kwargs` collects extra named ones in a dict. `->` followed by a type says what the function gives back.

```python
"""Extract all 20 emails and print the tickets and the totals."""
```

- The docstring (documentation kept with the code) says: *Extract all 20 emails and print the tickets and the totals.*

```python
settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str(ROOT)})
model = build_model(settings)
```

- `settings = Settings.from_environ({**os.environ, "PROJECT_ROOT": str...`: stores the result of calling `Settings.from_environ({**os.environ, "PROJECT_ROOT": str(ROOT)})`, which is this repository's own `from_environ` (in `src/inbox_worker/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable in `settings`.
- `model = build_model(settings)`: stores the result of calling `build_model(settings)`, which is this repository's own `build_model` (in `src/inbox_worker/interfaces/wiring.py`): the fake model (load tests), the recorded adapter (offline smoke run), or Claude in `model`.

```python
if record:
```

- Checks whether `record` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

> **`if`.** `if condition:` runs the indented lines only when the condition is true. `elif` adds another condition to try, `else` runs when none held. 'Truthy' values count as true; 'falsy' ones are `False`, `None`, zero and anything empty (`''`, `[]`, `{}`).

```python
model = RecordingModel(
    ClaudeModel(settings.model_id, settings.anthropic_api_key),
    ROOT / "tests/fixtures/cassettes/live-v1.json",
    settings.model_id,
    f"recorded from {settings.model_id}",
)
```

- `model = RecordingModel( ClaudeModel(settings.model_id, settings.ant...`: stores the result of calling `RecordingModel( ClaudeModel(settings.model_id, settings.anthropic_api_key), ROOT / "tes...`, which is this repository's own `RecordingModel` (in `src/inbox_worker/infrastructure/cassette.py`): wraps a real model and writes every reply to a cassette, keyed like `RecordedModel` expects in `model`.

```python
extractor = build_extractor(settings, model)
done = calls = 0
```

- `extractor = build_extractor(settings, model)`: stores the result of calling `build_extractor(settings, model)`, which is this repository's own `build_extractor` (in `src/inbox_worker/interfaces/wiring.py`): the extractor over the model, with the prompt text and version read from the versioned prompt file in `extractor`.
- `done = calls = 0`: stores the number `0` in `done`, `calls`.

```python
for email in emails():
```

- Repeats the indented lines once for each item of `emails()`, naming the current item `email`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

> **`try` / `except` / `finally`.** Code in `try` runs; if it raises an error of the kind named in `except`, that block runs instead of the program stopping. `else` runs only if there was no error. `finally` always runs last. `raise` makes an error on purpose; `raise ... from other` records the earlier error as its cause.

```python
result = extractor.extract(email)
```

- `result = extractor.extract(email)`: stores the result of calling `extractor.extract(email)`, which is this repository's own `extract` (in `src/inbox_worker/application/extraction.py`): one call, and one repair call when the reply is not a valid ticket in `result`.

```python
except (PermanentEventError, RetryableModelError, ModelCallError) as error:
```

- If an error of kind `(PermanentEventError, RetryableModelError, ModelCallError)` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
print(f"FAILED {email[:50]!r}: {error}")
continue
```

- `print(f"FAILED {email[:50]!r}: {error}")`: calling `print(f"FAILED {email[:50]!r}: {error}")`, which writes `f"FAILED {email[:50]!r}: {error}"` to the screen (standard output).
- `continue`: skips to the next round of the loop.

```python
done += 1
calls += result.calls
print(
    f"{result.ticket.intent:12} {result.ticket.order_number} {result.ticket.sentiment:8} {result.ticket.requested_action}"
)
```

- `done += 1`: adds `1` to `done` and keeps the result there.
- `calls += result.calls`: adds `result.calls` to `calls` and keeps the result there.
- `print( f"{result.ticket.intent:12} {result.ticket.order_number} {re...`: calling `print( f"{result.ticket.intent:12} {result.ticket.order_number} {result.ticket.sentimen...`, which writes `f"{result.ticket.intent:12} {result.ticket.order_number} {result.ticket.sentiment:8} {r...` to the screen (standard output).

```python
print(f"{done}/20 emails gave a ticket in {calls} model calls (adapter: {settings.model_adapter})")
return 0 if done == 20 else 1
```

- `print(f"{done}/20 emails gave a ticket in {calls} model calls (adap...`: calling `print(f"{done}/20 emails gave a ticket in {calls} model calls (adapter: {settings.model...`, which writes `f"{done}/20 emails gave a ticket in {calls} model calls (adapter: {settings.model_adapt...` to the screen (standard output).
- `return 0 if done == 20 else 1`: ends the function and gives back `0` when `done` equals `20`, otherwise `1`.

> **`a if cond else b`.** An expression that gives `a` when the condition holds and `b` otherwise.

> **Operators.** `//` divides and rounds down; `%` is the remainder; `**` is the power; `a and b` / `a or b` / `not a` combine conditions and stop at the first answer that decides the result; `x in items` asks whether `x` is among them; `x is None` asks whether it is exactly `None`.

```python
if __name__ == "__main__":
```

- Checks whether `__name__` equals `"__main__"`. If so, the indented lines run.

```python
if "--author" in sys.argv:
```

- Checks whether `"--author"` is among `sys.argv`. If so, the indented lines run.

```python
author()
sys.exit(0)
```

- `author()`: calling `author()`, which is this repository's own `author` (in `scripts/smoke.py`): write the cassette from the fake model.
- `sys.exit(0)`: calling `sys.exit(0)`, which ends the program with the given exit code.

```python
sys.exit(run("--record" in sys.argv))
```

- `sys.exit(run("--record" in sys.argv))`: calling `sys.exit(run("--record" in sys.argv))`, which ends the program with the given exit code.

#### `src/inbox_worker/__init__.py`

```python
"""A worker for the support inbox: a signed webhook, a Postgres queue, one model step per event, effects applied once, backoff, dead letters, crash recovery and a burst measurement."""
```

- The docstring (documentation kept with the code) says: *A worker for the support inbox: a signed webhook, a Postgres queue, one model step per event, effects applied once, backoff, dead letters, crash recovery and a burst measurement.*

#### `src/inbox_worker/application/__init__.py`

```python
"""The application layer."""
```

- The docstring (documentation kept with the code) says: *The application layer.*

#### `src/inbox_worker/application/extraction.py`

```python
"""The Module 2 extractor as a step: an email in, a ticket out, one bounded repair, errors classified."""
```

- The docstring (documentation kept with the code) says: *The Module 2 extractor as a step: an email in, a ticket out, one bounded repair, errors classified.*

```python
from __future__ import annotations

import json
from dataclasses import dataclass

from inbox_worker.application.ports import ChatModel
from inbox_worker.domain.errors import PermanentEventError, ReplyInvalidError
from inbox_worker.domain.ticket import Ticket
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import json`: makes the module `json` available (reads and writes JSON text).
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`ChatModel`: A text model.)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`PermanentEventError`: An event that can never succeed.) (`ReplyInvalidError`: A model reply is not a valid ticket; the message says why.)
- `from inbox_worker.domain.ticket import ...`: takes names from `inbox_worker.domain.ticket`, this repository's own code. (`Ticket`: What the customer wants, about which order, in what mood, and the action it asks for.)

```python
PROMPT_VERSION = "extract.v1"
SYSTEM = (
    "Extract intent (cancel, refund, order_status or other), order_number (four digits or null), sentiment "
    "(positive, neutral or negative) and requested_action (cancel_order, issue_refund, send_tracking or none) "
    "from this support email. Reply with one JSON object only."
)
```

- `PROMPT_VERSION = "extract.v1"`: stores the text `'extract.v1'` in `PROMPT_VERSION`.
- `SYSTEM = ( "Extract intent (cancel, refund, order_status or other),...`: stores the text `'Extract intent (cancel, refund, order_status or other), order_number (four digits or n...` in `SYSTEM`.

```python
@dataclass(frozen=True, slots=True)
class Extraction:
```

- Defines the class `Extraction`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

> **A class.** `class Name:` defines a new kind of object. The functions inside it are methods; the first parameter, called `self` by habit, is the object the method was called on. `__init__` runs when an object is made. `Name(...)` makes an object (an instance) of the class. A class listed in brackets after the name is a base class: the new class inherits its methods.

> **Decorators.** A line `@something` above a function or class passes the definition through `something`, and the name then refers to what comes back.

> **`@dataclass`.** A decorator is a line starting with `@` that wraps the definition below it. `@dataclass` reads the annotated fields in the class body and writes `__init__`, `__repr__` and `__eq__` for the class. `frozen=True` makes the objects read-only after creation, so an accidental change raises an error. `slots=True` stores attributes more compactly.

```python
"""A ticket and the model calls it took."""
```

- The docstring (documentation kept with the code) says: *A ticket and the model calls it took.*

```python
ticket: Ticket
calls: int
```

- `ticket: Ticket`: a field named `ticket` of type `Ticket`, no default (must be given).
- `calls: int`: a field named `calls` of type `int`, no default (must be given).

```python
def _parse(text: str) -> Ticket:
```

- Defines the function `_parse`.
- Parameters:
  - `text`, type `str`.
- Gives back a value of type `Ticket`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
data = json.loads(text)
```

- `data = json.loads(text)`: stores the result of calling `json.loads(text)`, which turns the JSON text `text` into Python values in `data`.

```python
except json.JSONDecodeError as error:
```

- If an error of kind `json.JSONDecodeError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
raise ReplyInvalidError(f"not valid JSON: {error.msg}") from None
```

- `raise ReplyInvalidError(f"not valid JSON: {error.msg}") from None`: stops with an error of kind `ReplyInvalidError` with the message `f"not valid JSON: {error.msg}"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
if not isinstance(data, dict):
```

- Checks whether it is not the case that `isinstance(data, dict)` is true (the call asks whether `data` is a `dict`). If so, the indented lines run.

```python
raise ReplyInvalidError("not a JSON object")
```

- `raise ReplyInvalidError("not a JSON object")`: stops with an error of kind `ReplyInvalidError` with the message `"not a JSON object"`. Whoever called this code must handle it or the program stops.

```python
return Ticket.from_dict(data)
```

- `return Ticket.from_dict(data)`: ends the function and gives back the result of calling `Ticket.from_dict(data)`, which is this repository's own `from_dict` (in `src/inbox_worker/domain/ticket.py`): build a ticket from a decoded reply, checking every field.

```python
class TicketExtractor:
```

- Defines the class `TicketExtractor`.

```python
"""Model-backed extraction. A schema failure that survives one repair is permanent; model errors keep their type."""
```

- The docstring (documentation kept with the code) says: *Model-backed extraction. A schema failure that survives one repair is permanent; model errors keep their type.*

```python
def __init__(self, model: ChatModel, system: str = SYSTEM, version: str = PROMPT_VERSION) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `model`, type `ChatModel`.
  - `system`, type `str`, optional (default `SYSTEM`).
  - `version`, type `str`, optional (default `PROMPT_VERSION`).
- Gives back a value of type `None`.

```python
self._model = model
self._system = system
self._version = version
```

- `self._model = model`: stores the value of `model` in `self._model`.
- `self._system = system`: stores the value of `system` in `self._system`.
- `self._version = version`: stores the value of `version` in `self._version`.

```python
def extract(self, email: str) -> Extraction:
```

- Defines the method `extract`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `email`, type `str`.
- Gives back a value of type `Extraction`.

```python
"""One call, and one repair call when the reply is not a valid ticket."""
```

- The docstring (documentation kept with the code) says: *One call, and one repair call when the reply is not a valid ticket.*

```python
first = self._model.complete(self._system, email, self._version)
```

- `first = self._model.complete(self._system, email, self._version)`: stores the result of calling `self._model.complete(self._system, email, self._version)` in `first`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
return Extraction(_parse(first.text), 1)
```

- `return Extraction(_parse(first.text), 1)`: ends the function and gives back the result of calling `Extraction(_parse(first.text), 1)`, which is this repository's own `Extraction` (in `src/inbox_worker/application/extraction.py`): a ticket and the model calls it took.

```python
except ReplyInvalidError as reason:
```

- If an error of kind `ReplyInvalidError` happened above, runs the indented lines, keeping the error in `reason`. The error is then handled and the program carries on after the whole `try`.

```python
second = self._model.complete(
    self._system,
    f"{email}\n\nYour reply was not a valid ticket ({reason}). Return only the JSON.",
    self._version,
)
```

- `second = self._model.complete( self._system, f"{email}\n\nYour repl...`: stores the result of calling `self._model.complete( self._system, f"{email}\n\nYour reply was not a valid ticket ({re...` in `second`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
return Extraction(_parse(second.text), 2)
```

- `return Extraction(_parse(second.text), 2)`: ends the function and gives back the result of calling `Extraction(_parse(second.text), 2)`, which is this repository's own `Extraction` (in `src/inbox_worker/application/extraction.py`): a ticket and the model calls it took.

```python
except ReplyInvalidError as final:
```

- If an error of kind `ReplyInvalidError` happened above, runs the indented lines, keeping the error in `final`. The error is then handled and the program carries on after the whole `try`.

```python
raise PermanentEventError(
    "permanent_error", f"schema validation failed after one repair: {final}"
) from None
```

- `raise PermanentEventError( "permanent_error", f"schema validation f...`: stops with an error of kind `PermanentEventError` with the message `"permanent_error"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

#### `src/inbox_worker/application/generate_events.py`

```python
"""The sample inbox: 1,000 email events with unique ids, 2% delivered twice and 1% poison, from a seed."""
```

- The docstring (documentation kept with the code) says: *The sample inbox: 1,000 email events with unique ids, 2% delivered twice and 1% poison, from a seed.*

```python
from __future__ import annotations

import base64
import json
import random
from dataclasses import dataclass

from inbox_worker.domain.events import POISON_MARKER
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import base64`: makes the module `base64` available (encodes bytes as text made of 64 safe characters and decodes them back).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from inbox_worker.domain.events import ...`: takes names from `inbox_worker.domain.events`, this repository's own code. (`POISON_MARKER`: a name defined in this repository.)

```python
TEMPLATES = (
    "Hi, please cancel order {n}. I ordered it by mistake.",
    "I would like my money back for order {n}, it arrived damaged.",
    "Where is my order {n}? It has not arrived yet.",
    "This is unacceptable, order {n} is late again and I want a refund.",
    "Could you cancel {n}? I found it cheaper elsewhere.",
    "Can I get the tracking for order {n}, please?",
)
```

- `TEMPLATES = ( "Hi, please cancel order {n}. I ordered it by mistake...`: stores a tuple of 6 items in `TEMPLATES`.

> **Tuples and unpacking.** `(a, b)` is a fixed-length group. `x, y = pair` unpacks the two items into two names at once.

```python
POISON_KINDS = (
    "malformed_body",
    "malformed_body",
    "malformed_body",
    "too_large",
    "too_large",
    "too_large",
    "bad_encoding",
    "bad_encoding",
    "schema_failure",
    "schema_failure",
)
```

- `POISON_KINDS = ( "malformed_body", "malformed_body", "malformed_bod...`: stores a tuple of 10 items in `POISON_KINDS`.

```python
@dataclass(frozen=True, slots=True)
class GeneratedInbox:
```

- Defines the class `GeneratedInbox`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""The deliveries in arrival order, and what was planted: duplicates and poison by event id."""
```

- The docstring (documentation kept with the code) says: *The deliveries in arrival order, and what was planted: duplicates and poison by event id.*

```python
deliveries: tuple[tuple[str, str], ...]
duplicates: frozenset[str]
poison: dict[str, str]
```

- `deliveries: tuple[tuple[str, str], ...]`: a field named `deliveries` of type `tuple[tuple[str, str], ...]`, no default (must be given).
- `duplicates: frozenset[str]`: a field named `duplicates` of type `frozenset[str]`, no default (must be given).
- `poison: dict[str, str]`: a field named `poison` of type `dict[str, str]`, no default (must be given).

```python
def _payload(event_id: str, body: str) -> str:
```

- Defines the function `_payload`.
- Parameters:
  - `event_id`, type `str`.
  - `body`, type `str`.
- Gives back a value of type `str`.

```python
return json.dumps({"event_id": event_id, "body": body})
```

- `return json.dumps({"event_id": event_id, "body": body})`: ends the function and gives back the result of calling `json.dumps({"event_id": event_id, "body": body})`, which turns `{"event_id": event_id, "body": body}` into JSON text.

```python
def generate_events(
    count: int = 1000, seed: int = 2610, duplicate_rate: float = 0.02, poison_rate: float = 0.01
) -> GeneratedInbox:
```

- Defines the function `generate_events`.
- Parameters:
  - `count`, type `int`, optional (default `1000`).
  - `seed`, type `int`, optional (default `2610`).
  - `duplicate_rate`, type `float`, optional (default `0.02`).
  - `poison_rate`, type `float`, optional (default `0.01`).
- Gives back a value of type `GeneratedInbox`.

```python
"""`count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable."""
```

- The docstring (documentation kept with the code) says: *`count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable.*

```python
rng = random.Random(seed)
poison_count = round(count * poison_rate)
poison_slots = set(rng.sample(range(count), poison_count))
kinds = list(POISON_KINDS[:poison_count])
rng.shuffle(kinds)
deliveries: list[tuple[str, str]] = []
```

- `rng = random.Random(seed)`: stores the result of calling `random.Random(seed)`, which makes a random number generator; the same seed gives the same sequence in `rng`.
- `poison_count = round(count * poison_rate)`: stores the result of calling `round(count * poison_rate)`, which rounds `count * poison_rate` in `poison_count`.
- `poison_slots = set(rng.sample(range(count), poison_count))`: stores the result of calling `set(rng.sample(range(count), poison_count))`, which sets  in `poison_slots`.
- `kinds = list(POISON_KINDS[:poison_count])`: stores the result of calling `list(POISON_KINDS[:poison_count])`, which builds a new list from `POISON_KINDS[:poison_count]` in `kinds`.
- `rng.shuffle(kinds)`: calling `rng.shuffle(kinds)`, which mixes the order of a list in place.
- `deliveries: list[tuple[str, str]] = []`: stores a new list (empty) in `deliveries`, whose type is declared as `list[tuple[str, str]]`.

> **A type hint.** `x: int = 5` stores 5 in `x` and records that `x` is meant to hold an `int`. Python itself does not enforce the hint; the type checker `mypy` reads it before the program runs and complains if the code disagrees.

```python
poison: dict[str, str] = {}
```

- `poison: dict[str, str] = {}`: stores a new dict (empty) in `poison`, whose type is declared as `dict[str, str]`.

```python
for number in range(count):
```

- Repeats the indented lines once for each item of `range(count)`, naming the current item `number`.

```python
event_id = f"e-{number + 1:04d}"
```

- `event_id = f"e-{number + 1:04d}"`: stores the text built by the f-string `f"e-{number + 1:04d}"` in `event_id`.

> **f-strings.** A string starting with `f` can hold `{expression}` marks; Python evaluates each and puts the result into the text. After a colon you can give a format, such as `{x:.2f}` for two decimals or `{n:>5}` for right-aligned in 5 characters.

```python
if number in poison_slots:
```

- Checks whether `number` is among `poison_slots`. If so, the indented lines run.

```python
kind = kinds.pop()
poison[event_id] = kind
```

- `kind = kinds.pop()`: stores the result of calling `kinds.pop()`, which removes and returns an item of `kinds` in `kind`.
- `poison[event_id] = kind`: stores the value of `kind` in the slot `poison[event_id]`.

```python
if kind == "malformed_body":
```

- Checks whether `kind` equals `"malformed_body"`. If so, the indented lines run.

```python
deliveries.append((event_id, '{"event_id": "' + event_id + '", "body": '))
```

- `deliveries.append((event_id, '{"event_id": "' + event_id + '", "bod...`: calling `deliveries.append((event_id, '{"event_id": "' + event_id + '", "body": '))`, which adds `(event_id, '{"event_id": "' + event_id + '", "body": ')` to the end of `deliveries`.

```python
elif kind == "too_large":
```

- Otherwise, checks whether `kind` equals `"too_large"`. If so, the indented lines run.

```python
deliveries.append((event_id, _payload(event_id, "Please cancel order 4417. " + "x" * 300_000)))
```

- `deliveries.append((event_id, _payload(event_id, "Please cancel orde...`: calling `deliveries.append((event_id, _payload(event_id, "Please cancel order 4417. " + "x" * 30...`, which adds `(event_id, _payload(event_id, "Please cancel order 4417. " + "x" * 300_000))` to the end of `deliveries`.

```python
elif kind == "bad_encoding":
```

- Otherwise, checks whether `kind` equals `"bad_encoding"`. If so, the indented lines run.

```python
broken = base64.b64encode(b"Please cancel order 4417 \xff\xfe\xfa").decode()
deliveries.append((event_id, json.dumps({"event_id": event_id, "body_b64": broken})))
```

- `broken = base64.b64encode(b"Please cancel order 4417 \xff\xfe\xfa")...`: stores the result of calling `base64.b64encode(b"Please cancel order 4417 \xff\xfe\xfa").decode()`, which turns the bytes `base64.b64encode(b"Please cancel order 4417 \xff\xfe\xfa")` into text in `broken`.
- `deliveries.append((event_id, json.dumps({"event_id": event_id, "bod...`: calling `deliveries.append((event_id, json.dumps({"event_id": event_id, "body_b64": broken})))`, which adds `(event_id, json.dumps({"event_id": event_id, "body_b64": broken}))` to the end of `deliveries`.

```python
else:
```

- Runs when none of the conditions above held.

```python
deliveries.append((event_id, _payload(event_id, f"{POISON_MARKER} please cancel order 4417.")))
```

- `deliveries.append((event_id, _payload(event_id, f"{POISON_MARKER} p...`: calling `deliveries.append((event_id, _payload(event_id, f"{POISON_MARKER} please cancel order 4...`, which adds `(event_id, _payload(event_id, f"{POISON_MARKER} please cancel order 4417."))` to the end of `deliveries`.

```python
else:
```

- Runs when none of the conditions above held.

```python
deliveries.append((event_id, _payload(event_id, rng.choice(TEMPLATES).format(n=rng.randint(1000, 9999)))))
```

- `deliveries.append((event_id, _payload(event_id, rng.choice(TEMPLATE...`: calling `deliveries.append((event_id, _payload(event_id, rng.choice(TEMPLATES).format(n=rng.rand...`, which adds `(event_id, _payload(event_id, rng.choice(TEMPLATES).format(n=rng.randint(1000, 9999))))` to the end of `deliveries`.

```python
healthy = [event_id for event_id, _ in deliveries if event_id not in poison]
repeated = frozenset(rng.sample(healthy, round(count * duplicate_rate)))
by_id = dict(deliveries)
result = list(deliveries)
```

- `healthy = [event_id for event_id, _ in deliveries if event_id not i...`: stores a list built by running `event_id` for each `event_id, _` in `deliveries` keeping only those where `event_id` is not among `poison` in `healthy`.
- `repeated = frozenset(rng.sample(healthy, round(count * duplicate_ra...`: stores the result of calling `frozenset(rng.sample(healthy, round(count * duplicate_rate)))`, which builds a set that cannot change from `rng.sample(healthy, round(count * duplicate_rate))` in `repeated`.
- `by_id = dict(deliveries)`: stores the result of calling `dict(deliveries)`, which builds a dict in `by_id`.
- `result = list(deliveries)`: stores the result of calling `list(deliveries)`, which builds a new list from `deliveries` in `result`.

```python
for event_id in sorted(repeated):
```

- Repeats the indented lines once for each item of `sorted(repeated)`, naming the current item `event_id`.

```python
result.insert(
    rng.randint(result.index((event_id, by_id[event_id])) + 1, len(result)), (event_id, by_id[event_id])
)
```

- `result.insert( rng.randint(result.index((event_id, by_id[event_id])...`: calling `result.insert( rng.randint(result.index((event_id, by_id[event_id])) + 1, len(result)),...`, which puts `(event_id, by_id[event_id])` into `result` at position `rng.randint(result.index((event_id, by_id[event_id])) + 1, len(result))`.

```python
return GeneratedInbox(tuple(result), repeated, poison)
```

- `return GeneratedInbox(tuple(result), repeated, poison)`: ends the function and gives back the result of calling `GeneratedInbox(tuple(result), repeated, poison)`, which is this repository's own `GeneratedInbox` (in `src/inbox_worker/application/generate_events.py`): the deliveries in arrival order, and what was planted: duplicates and poison by event id.

#### `src/inbox_worker/application/handler.py`

```python
"""Handle one delivery: decode, skip a duplicate, run the model outside any transaction, apply the effects once."""
```

- The docstring (documentation kept with the code) says: *Handle one delivery: decode, skip a duplicate, run the model outside any transaction, apply the effects once.*

```python
from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

from inbox_worker.application.extraction import TicketExtractor
from inbox_worker.application.ports import Clock, Delivery, DeliveryQueue, EffectsStore
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Callable`: the type hint for a function value.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`TicketExtractor`: Model-backed extraction.)
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`Clock`: The current time, injected so tests are deterministic.) (`Delivery`: One queue message: a delivery of an event.) (`DeliveryQueue`: A queue with acknowledgments and redelivery, in a database table read with row locks.) (`EffectsStore`: Where an event's effects land: the processed mark, the ticket and the outbox row.)

```python
from inbox_worker.domain.backoff import backoff_delay
from inbox_worker.domain.errors import ModelCallError, PermanentEventError, RetryableModelError
from inbox_worker.domain.events import parse_event

PROCESSED = "processed"
DUPLICATE = "duplicate"
RETRY = "retry"
```

- `from inbox_worker.domain.backoff import ...`: takes names from `inbox_worker.domain.backoff`, this repository's own code. (`backoff_delay`: A random delay in [0, min(cap, base * 2**(attempt - 1))].)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`ModelCallError`: A model call failed in a way a retry will not fix.) (`PermanentEventError`: An event that can never succeed.) (`RetryableModelError`: A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection.)
- `from inbox_worker.domain.events import ...`: takes names from `inbox_worker.domain.events`, this repository's own code. (`parse_event`: Decode a delivery's payload.)
- `PROCESSED = "processed"`: stores the text `'processed'` in `PROCESSED`.
- `DUPLICATE = "duplicate"`: stores the text `'duplicate'` in `DUPLICATE`.
- `RETRY = "retry"`: stores the text `'retry'` in `RETRY`.

```python
DEAD = "dead_lettered"
```

- `DEAD = "dead_lettered"`: stores the text `'dead_lettered'` in `DEAD`.

```python
@dataclass(frozen=True, slots=True)
class RetryPolicy:
```

- Defines the class `RetryPolicy`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""How a failing event is retried before it is parked."""
```

- The docstring (documentation kept with the code) says: *How a failing event is retried before it is parked.*

```python
max_attempts: int = 5
base_seconds: float = 0.5
cap_seconds: float = 30.0
event_deadline_seconds: float = 300.0
```

- `max_attempts: int = 5`: a field named `max_attempts` of type `int`, default `5`.
- `base_seconds: float = 0.5`: a field named `base_seconds` of type `float`, default `0.5`.
- `cap_seconds: float = 30.0`: a field named `cap_seconds` of type `float`, default `30.0`.
- `event_deadline_seconds: float = 300.0`: a field named `event_deadline_seconds` of type `float`, default `300.0`.

```python
class EventHandler:
```

- Defines the class `EventHandler`.

```python
"""Applies each event's effects once, however often the queue delivers it.

`crash_at` is called with a point name ("after_model", "after_commit"); the crash tests make it kill the process.
"""
```

- The docstring (documentation kept with the code) says: *Applies each event's effects once, however often the queue delivers it. `crash_at` is called with a point name ("after_model", "after_commit"); the crash tests make it kill the process.*

```python
def __init__(
    self,
    queue: DeliveryQueue,
    effects: EffectsStore,
    extractor: TicketExtractor,
    clock: Clock,
    policy: RetryPolicy | None = None,
    *,
    rng: random.Random | None = None,
    crash_at: Callable[[str], None] = lambda point: None,
) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `queue`, type `DeliveryQueue`.
  - `effects`, type `EffectsStore`.
  - `extractor`, type `TicketExtractor`.
  - `clock`, type `Clock`.
  - `policy`, type `RetryPolicy | None`, optional (default `None`).
  - `rng`, type `random.Random | None`, optional (default `None`). Must be passed by name.
  - `crash_at`, type `Callable[[str], None]`, optional (default `lambda point: None`). Must be passed by name.
- Gives back a value of type `None`.

```python
self._queue = queue
self._effects = effects
self._extractor = extractor
self._clock = clock
self._policy = policy or RetryPolicy()
self._rng = rng or random.Random()
```

- `self._queue = queue`: stores the value of `queue` in `self._queue`.
- `self._effects = effects`: stores the value of `effects` in `self._effects`.
- `self._extractor = extractor`: stores the value of `extractor` in `self._extractor`.
- `self._clock = clock`: stores the value of `clock` in `self._clock`.
- `self._policy = policy or RetryPolicy()`: stores `policy or RetryPolicy()` (the first operand that decides the or) in `self._policy`.
- `self._rng = rng or random.Random()`: stores `rng or random.Random()` (the first operand that decides the or) in `self._rng`.

```python
self._crash_at = crash_at
```

- `self._crash_at = crash_at`: stores the value of `crash_at` in `self._crash_at`.

```python
def handle(self, delivery: Delivery) -> str:
```

- Defines the method `handle`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery`, type `Delivery`.
- Gives back a value of type `str`.

```python
"""Process one delivery to a final outcome, acknowledging it unless the process dies first."""
```

- The docstring (documentation kept with the code) says: *Process one delivery to a final outcome, acknowledging it unless the process dies first.*

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
event = parse_event(delivery.payload)
```

- `event = parse_event(delivery.payload)`: stores the result of calling `parse_event(delivery.payload)`, which is this repository's own `parse_event` (in `src/inbox_worker/domain/events.py`): decode a delivery's payload in `event`.

```python
if self._effects.is_processed(event.event_id):
```

- Checks whether `self._effects.is_processed(event.event_id)` is true. If so, the indented lines run.

```python
self._queue.ack(delivery.delivery_id)
return DUPLICATE
```

- `self._queue.ack(delivery.delivery_id)`: calling `self._queue.ack(delivery.delivery_id)`.
- `return DUPLICATE`: ends the function and gives back the value of `DUPLICATE`.

```python
if (self._clock.now() - delivery.received_at).total_seconds() > self._policy.event_deadline_seconds:
```

- Checks whether `(self._clock.now() - delivery.received_at).total_seconds()` is greater than `self._policy.event_deadline_seconds`. If so, the indented lines run.

```python
raise PermanentEventError("deadline_exceeded", "the event waited longer than its deadline")
```

- `raise PermanentEventError("deadline_exceeded", "the event waited lo...`: stops with an error of kind `PermanentEventError` with the message `"deadline_exceeded"`. Whoever called this code must handle it or the program stops.

```python
extraction = self._extractor.extract(event.body)
self._crash_at("after_model")
applied = self._effects.apply(event.event_id, extraction.ticket)
self._crash_at("after_commit")
self._queue.ack(delivery.delivery_id)
return PROCESSED if applied else DUPLICATE
```

- `extraction = self._extractor.extract(event.body)`: stores the result of calling `self._extractor.extract(event.body)`, which is this repository's own `extract` (in `src/inbox_worker/application/extraction.py`): one call, and one repair call when the reply is not a valid ticket in `extraction`.
- `self._crash_at("after_model")`: calling `self._crash_at("after_model")`.
- `applied = self._effects.apply(event.event_id, extraction.ticket)`: stores the result of calling `self._effects.apply(event.event_id, extraction.ticket)` in `applied`.
- `self._crash_at("after_commit")`: calling `self._crash_at("after_commit")`.
- `self._queue.ack(delivery.delivery_id)`: calling `self._queue.ack(delivery.delivery_id)`.
- `return PROCESSED if applied else DUPLICATE`: ends the function and gives back `PROCESSED` when `applied` is truthy (not `None`, `False`, zero or empty), otherwise `DUPLICATE`.

```python
except PermanentEventError as error:
```

- If an error of kind `PermanentEventError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
self._queue.dead_letter(delivery, error.reason, str(error))
return DEAD
```

- `self._queue.dead_letter(delivery, error.reason, str(error))`: calling `self._queue.dead_letter(delivery, error.reason, str(error))`.
- `return DEAD`: ends the function and gives back the value of `DEAD`.

```python
except (RetryableModelError, ModelCallError) as error:
```

- If an error of kind `(RetryableModelError, ModelCallError)` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
return self._retry_or_park(delivery, error)
```

- `return self._retry_or_park(delivery, error)`: ends the function and gives back the result of calling `self._retry_or_park(delivery, error)`.

```python
def _retry_or_park(self, delivery: Delivery, error: RetryableModelError | ModelCallError) -> str:
```

- Defines the method `_retry_or_park`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery`, type `Delivery`.
  - `error`, type `RetryableModelError | ModelCallError`.
- Gives back a value of type `str`.

```python
if isinstance(error, ModelCallError):
```

- Checks whether `isinstance(error, ModelCallError)` is true (the call asks whether `error` is a `ModelCallError`). If so, the indented lines run.

```python
self._queue.dead_letter(delivery, "permanent_error", f"{type(error).__name__}: {error}")
return DEAD
```

- `self._queue.dead_letter(delivery, "permanent_error", f"{type(error)...`: calling `self._queue.dead_letter(delivery, "permanent_error", f"{type(error).__name__}: {error}")`.
- `return DEAD`: ends the function and gives back the value of `DEAD`.

```python
if delivery.attempts >= self._policy.max_attempts:
```

- Checks whether `delivery.attempts` is greater than or equal to `self._policy.max_attempts`. If so, the indented lines run.

```python
self._queue.dead_letter(delivery, "attempts_exhausted", f"{type(error).__name__}: {error}")
return DEAD
```

- `self._queue.dead_letter(delivery, "attempts_exhausted", f"{type(err...`: calling `self._queue.dead_letter(delivery, "attempts_exhausted", f"{type(error).__name__}: {erro...`.
- `return DEAD`: ends the function and gives back the value of `DEAD`.

```python
delay = backoff_delay(delivery.attempts, self._policy.base_seconds, self._policy.cap_seconds, self._rng)
self._queue.retry(delivery.delivery_id, delay, f"{type(error).__name__}: {error}")
return RETRY
```

- `delay = backoff_delay(delivery.attempts, self._policy.base_seconds,...`: stores the result of calling `backoff_delay(delivery.attempts, self._policy.base_seconds, self._policy.cap_seconds, s...`, which is this repository's own `backoff_delay` (in `src/inbox_worker/domain/backoff.py`): a random delay in [0, min(cap, base * 2**(attempt - 1))] in `delay`.
- `self._queue.retry(delivery.delivery_id, delay, f"{type(error).__nam...`: calling `self._queue.retry(delivery.delivery_id, delay, f"{type(error).__name__}: {error}")`.
- `return RETRY`: ends the function and gives back the value of `RETRY`.

#### `src/inbox_worker/application/outbox.py`

```python
"""The outbox relay: send each acknowledgment, tolerate a send that happened before a crash, mark it sent."""
```

- The docstring (documentation kept with the code) says: *The outbox relay: send each acknowledgment, tolerate a send that happened before a crash, mark it sent.*

```python
from __future__ import annotations

import contextlib

from inbox_worker.application.ports import MailGateway, OutboxStore
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import contextlib`: makes the module `contextlib` available (helpers for building `with` blocks).
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`MailGateway`: Sends an acknowledgment.) (`OutboxStore`: The acknowledgments waiting to be sent.)

```python
class DuplicateSendError(RuntimeError):
```

- Defines the class `DuplicateSendError`.
- It extends `RuntimeError`: it is a kind of error that can be raised and caught.

```python
"""The mail gateway has already sent this event's acknowledgment."""
```

- The docstring (documentation kept with the code) says: *The mail gateway has already sent this event's acknowledgment.*

```python
class OutboxRelay:
```

- Defines the class `OutboxRelay`.

```python
"""Sends unsent outbox rows. A row whose mail was already sent (the relay died before marking it) is just marked."""
```

- The docstring (documentation kept with the code) says: *Sends unsent outbox rows. A row whose mail was already sent (the relay died before marking it) is just marked.*

```python
def __init__(self, outbox: OutboxStore, gateway: MailGateway) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `outbox`, type `OutboxStore`.
  - `gateway`, type `MailGateway`.
- Gives back a value of type `None`.

```python
self._outbox = outbox
self._gateway = gateway
```

- `self._outbox = outbox`: stores the value of `outbox` in `self._outbox`.
- `self._gateway = gateway`: stores the value of `gateway` in `self._gateway`.

```python
def run_once(self, limit: int = 100) -> int:
```

- Defines the method `run_once`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`, optional (default `100`).
- Gives back a value of type `int`.

```python
"""Send up to `limit` rows; returns how many rows were marked sent."""
```

- The docstring (documentation kept with the code) says: *Send up to `limit` rows; returns how many rows were marked sent.*

```python
done = 0
```

- `done = 0`: stores the number `0` in `done`.

```python
for outbox_id, event_id, kind in self._outbox.unsent(limit):
```

- Repeats the indented lines once for each item of `self._outbox.unsent(limit)`, naming the current item the names `outbox_id`, `event_id`, `kind`.

```python
with contextlib.suppress(DuplicateSendError):
```

- Opens `contextlib.suppress(DuplicateSendError)` for the indented lines, and cleans it up when they end (even after an error).

> **`with`.** `with thing as name:` uses a resource for the indented lines and then cleans it up, even if an error happens: a file is closed, a lock is released, a database transaction is committed or rolled back.

```python
self._gateway.send(event_id, kind)
```

- `self._gateway.send(event_id, kind)`: calling `self._gateway.send(event_id, kind)`.

```python
self._outbox.mark_sent(outbox_id)
done += 1
```

- `self._outbox.mark_sent(outbox_id)`: calling `self._outbox.mark_sent(outbox_id)`, which is this repository's own `mark_sent` (in `src/inbox_worker/application/ports.py`): record that the row was sent.
- `done += 1`: adds `1` to `done` and keeps the result there.

```python
return done
```

- `return done`: ends the function and gives back the value of `done`.

#### `src/inbox_worker/application/ports.py`

```python
"""The boundaries the worker talks through: the queue, the effects store, the model, the mail gateway."""
```

- The docstring (documentation kept with the code) says: *The boundaries the worker talks through: the queue, the effects store, the model, the mail gateway.*

```python
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from inbox_worker.domain.ticket import Ticket
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`datetime`: the date-and-time type.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Protocol`: the base class for an interface: a list of methods something must have.)
- `from inbox_worker.domain.ticket import ...`: takes names from `inbox_worker.domain.ticket`, this repository's own code. (`Ticket`: What the customer wants, about which order, in what mood, and the action it asks for.)

```python
@dataclass(frozen=True, slots=True)
class Delivery:
```

- Defines the class `Delivery`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""One queue message: a delivery of an event. The same event can arrive in more than one delivery."""
```

- The docstring (documentation kept with the code) says: *One queue message: a delivery of an event. The same event can arrive in more than one delivery.*

```python
delivery_id: int
event_id: str
payload: str
received_at: datetime
attempts: int
```

- `delivery_id: int`: a field named `delivery_id` of type `int`, no default (must be given).
- `event_id: str`: a field named `event_id` of type `str`, no default (must be given).
- `payload: str`: a field named `payload` of type `str`, no default (must be given).
- `received_at: datetime`: a field named `received_at` of type `datetime`, no default (must be given).
- `attempts: int`: a field named `attempts` of type `int`, no default (must be given).

```python
class DeliveryQueue(Protocol):
```

- Defines the class `DeliveryQueue`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

> **`Protocol`.** A class that lists methods without an implementation. It describes the shape something must have (an interface); any class with those methods fits, without naming the Protocol. The type checker enforces the match.

```python
"""A queue with acknowledgments and redelivery, in a database table read with row locks."""
```

- The docstring (documentation kept with the code) says: *A queue with acknowledgments and redelivery, in a database table read with row locks.*

```python
def put(self, event_id: str, payload: str) -> int:
```

- Defines the method `put`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
  - `payload`, type `str`.
- Gives back a value of type `int`.

```python
"""Add a delivery; returns its id."""
```

- The docstring (documentation kept with the code) says: *Add a delivery; returns its id.*

```python
...
```

- `...`: evaluates `...`.

```python
def claim(self, limit: int, lease_seconds: float) -> Sequence[Delivery]:
```

- Defines the method `claim`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`.
  - `lease_seconds`, type `float`.
- Gives back a value of type `Sequence[Delivery]`.

```python
"""Take up to `limit` ready deliveries for `lease_seconds`. A claim that is never acknowledged expires, and the
delivery is handed out again (this is the redelivery after a crash)."""
```

- The docstring (documentation kept with the code) says: *Take up to `limit` ready deliveries for `lease_seconds`. A claim that is never acknowledged expires, and the delivery is handed out again (this is the redelivery after a crash).*

```python
...
```

- `...`: evaluates `...`.

```python
def ack(self, delivery_id: int) -> None:
```

- Defines the method `ack`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery_id`, type `int`.
- Gives back a value of type `None`.

```python
"""The delivery is finished."""
```

- The docstring (documentation kept with the code) says: *The delivery is finished.*

```python
...
```

- `...`: evaluates `...`.

```python
def retry(self, delivery_id: int, delay_seconds: float, error: str) -> None:
```

- Defines the method `retry`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery_id`, type `int`.
  - `delay_seconds`, type `float`.
  - `error`, type `str`.
- Gives back a value of type `None`.

```python
"""Make the delivery available again after `delay_seconds`, remembering the error."""
```

- The docstring (documentation kept with the code) says: *Make the delivery available again after `delay_seconds`, remembering the error.*

```python
...
```

- `...`: evaluates `...`.

```python
def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:
```

- Defines the method `dead_letter`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery`, type `Delivery`.
  - `reason`, type `str`.
  - `error`, type `str`.
- Gives back a value of type `None`.

```python
"""Move the delivery to the dead-letter table with a reason, the attempt count, the last error and a payload hash."""
```

- The docstring (documentation kept with the code) says: *Move the delivery to the dead-letter table with a reason, the attempt count, the last error and a payload hash.*

```python
...
```

- `...`: evaluates `...`.

```python
def depth(self) -> int:
```

- Defines the method `depth`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `int`.

```python
"""Deliveries waiting or in flight."""
```

- The docstring (documentation kept with the code) says: *Deliveries waiting or in flight.*

```python
...
```

- `...`: evaluates `...`.

```python
class EffectsStore(Protocol):
```

- Defines the class `EffectsStore`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""Where an event's effects land: the processed mark, the ticket and the outbox row."""
```

- The docstring (documentation kept with the code) says: *Where an event's effects land: the processed mark, the ticket and the outbox row.*

```python
def is_processed(self, event_id: str) -> bool:
```

- Defines the method `is_processed`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
- Gives back a value of type `bool`.

```python
"""True when this event's effects were already applied."""
```

- The docstring (documentation kept with the code) says: *True when this event's effects were already applied.*

```python
...
```

- `...`: evaluates `...`.

```python
def apply(self, event_id: str, ticket: Ticket) -> bool:
```

- Defines the method `apply`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
  - `ticket`, type `Ticket`.
- Gives back a value of type `bool`.

```python
"""Write the processed mark, the ticket and the outbox row in one transaction. Returns False when a twin
delivery committed first (the primary key on the mark settles the race); nothing is written then."""
```

- The docstring (documentation kept with the code) says: *Write the processed mark, the ticket and the outbox row in one transaction. Returns False when a twin delivery committed first (the primary key on the mark settles the race); nothing is written then.*

```python
...
```

- `...`: evaluates `...`.

```python
class MailGateway(Protocol):
```

- Defines the class `MailGateway`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""Sends an acknowledgment. The fake implementation records every send."""
```

- The docstring (documentation kept with the code) says: *Sends an acknowledgment. The fake implementation records every send.*

```python
def send(self, event_id: str, kind: str) -> None:
```

- Defines the method `send`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
  - `kind`, type `str`.
- Gives back a value of type `None`.

```python
"""Send one acknowledgment; sending the same event's twice must fail or be refused."""
```

- The docstring (documentation kept with the code) says: *Send one acknowledgment; sending the same event's twice must fail or be refused.*

```python
...
```

- `...`: evaluates `...`.

```python
class OutboxStore(Protocol):
```

- Defines the class `OutboxStore`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""The acknowledgments waiting to be sent."""
```

- The docstring (documentation kept with the code) says: *The acknowledgments waiting to be sent.*

```python
def unsent(self, limit: int) -> Sequence[tuple[int, str, str]]:
```

- Defines the method `unsent`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`.
- Gives back a value of type `Sequence[tuple[int, str, str]]`.

```python
"""(outbox id, event id, kind) of unsent rows, oldest first."""
```

- The docstring (documentation kept with the code) says: *(outbox id, event id, kind) of unsent rows, oldest first.*

```python
...
```

- `...`: evaluates `...`.

```python
def mark_sent(self, outbox_id: int) -> None:
```

- Defines the method `mark_sent`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `outbox_id`, type `int`.
- Gives back a value of type `None`.

```python
"""Record that the row was sent."""
```

- The docstring (documentation kept with the code) says: *Record that the row was sent.*

```python
...
```

- `...`: evaluates `...`.

```python
@dataclass(frozen=True, slots=True)
class ModelReply:
```

- Defines the class `ModelReply`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""The model's text and what the call used."""
```

- The docstring (documentation kept with the code) says: *The model's text and what the call used.*

```python
text: str
model: str
input_tokens: int
output_tokens: int
```

- `text: str`: a field named `text` of type `str`, no default (must be given).
- `model: str`: a field named `model` of type `str`, no default (must be given).
- `input_tokens: int`: a field named `input_tokens` of type `int`, no default (must be given).
- `output_tokens: int`: a field named `output_tokens` of type `int`, no default (must be given).

```python
class ChatModel(Protocol):
```

- Defines the class `ChatModel`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""A text model. Raises `RetryableModelError` for failures worth retrying and `ModelCallError` for the rest."""
```

- The docstring (documentation kept with the code) says: *A text model. Raises `RetryableModelError` for failures worth retrying and `ModelCallError` for the rest.*

```python
def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
```

- Defines the method `complete`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `system`, type `str`.
  - `user`, type `str`.
  - `prompt_version`, type `str`.
- Gives back a value of type `ModelReply`.

```python
"""Answer one request."""
```

- The docstring (documentation kept with the code) says: *Answer one request.*

```python
...
```

- `...`: evaluates `...`.

```python
class Clock(Protocol):
```

- Defines the class `Clock`.
- It extends `Protocol`: it only lists the methods something must have (an interface), with no behavior of its own.

```python
"""The current time, injected so tests are deterministic."""
```

- The docstring (documentation kept with the code) says: *The current time, injected so tests are deterministic.*

```python
def now(self) -> datetime:
```

- Defines the method `now`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `datetime`.

```python
"""Now, timezone-aware."""
```

- The docstring (documentation kept with the code) says: *Now, timezone-aware.*

```python
...
```

- `...`: evaluates `...`.

#### `src/inbox_worker/application/worker.py`

```python
"""The worker loop: claim deliveries, handle them on a bounded pool, and stop cleanly when asked."""
```

- The docstring (documentation kept with the code) says: *The worker loop: claim deliveries, handle them on a bounded pool, and stop cleanly when asked.*

```python
from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor

from inbox_worker.application.handler import EventHandler
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import logging`: makes the module `logging` available (the standard library's logging system).
- `from collections import ...`: takes names from `collections` (the standard library's extra container types (Counter, defaultdict, deque)). (`Counter`: a dict that counts: `counter[x] += 1`.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Callable`: the type hint for a function value.)
- `from concurrent.futures import ...`: takes names from `concurrent.futures` (the standard library's package for running work on several threads or processes). (`ThreadPoolExecutor`: runs functions on a pool of threads.)
- `from inbox_worker.application.handler import ...`: takes names from `inbox_worker.application.handler`, this repository's own code. (`EventHandler`: Applies each event's effects once, however often the queue delivers it.)

```python
from inbox_worker.application.ports import Delivery, DeliveryQueue

LOGGER = logging.getLogger("inbox_worker.worker")
MAX_BACKOFF_SECONDS = 10.0
```

- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`Delivery`: One queue message: a delivery of an event.) (`DeliveryQueue`: A queue with acknowledgments and redelivery, in a database table read with row locks.)
- `LOGGER = logging.getLogger("inbox_worker.worker")`: stores the result of calling `logging.getLogger("inbox_worker.worker")`, which gets the logger named `"inbox_worker.worker"` in `LOGGER`.
- `MAX_BACKOFF_SECONDS = 10.0`: stores the number `10.0` in `MAX_BACKOFF_SECONDS`.

```python
class Worker:
```

- Defines the class `Worker`.

```python
"""Pulls batches from the queue. A shutdown request finishes the deliveries in flight and then returns."""
```

- The docstring (documentation kept with the code) says: *Pulls batches from the queue. A shutdown request finishes the deliveries in flight and then returns.*

```python
def __init__(
    self,
    queue: DeliveryQueue,
    handler: EventHandler,
    *,
    concurrency: int,
    lease_seconds: float,
    stop_requested: Callable[[], bool],
    wait: Callable[[float], bool],
    idle_poll_seconds: float = 0.2,
) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `queue`, type `DeliveryQueue`.
  - `handler`, type `EventHandler`.
  - `concurrency`, type `int`. Must be passed by name.
  - `lease_seconds`, type `float`. Must be passed by name.
  - `stop_requested`, type `Callable[[], bool]`. Must be passed by name.
  - `wait`, type `Callable[[float], bool]`. Must be passed by name.
  - `idle_poll_seconds`, type `float`, optional (default `0.2`). Must be passed by name.
- Gives back a value of type `None`.

```python
self._queue = queue
self._handler = handler
self._concurrency = concurrency
self._lease = lease_seconds
self._stop = stop_requested
self._wait = wait
```

- `self._queue = queue`: stores the value of `queue` in `self._queue`.
- `self._handler = handler`: stores the value of `handler` in `self._handler`.
- `self._concurrency = concurrency`: stores the value of `concurrency` in `self._concurrency`.
- `self._lease = lease_seconds`: stores the value of `lease_seconds` in `self._lease`.
- `self._stop = stop_requested`: stores the value of `stop_requested` in `self._stop`.
- `self._wait = wait`: stores the value of `wait` in `self._wait`.

```python
self._idle = idle_poll_seconds
```

- `self._idle = idle_poll_seconds`: stores the value of `idle_poll_seconds` in `self._idle`.

```python
def _handle_safely(self, delivery: Delivery) -> str:
```

- Defines the method `_handle_safely`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery`, type `Delivery`.
- Gives back a value of type `str`.

```python
"""A failure the handler did not classify is logged and left to the lease: the delivery comes back."""
```

- The docstring (documentation kept with the code) says: *A failure the handler did not classify is logged and left to the lease: the delivery comes back.*

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
return self._handler.handle(delivery)
```

- `return self._handler.handle(delivery)`: ends the function and gives back the result of calling `self._handler.handle(delivery)`, which is this repository's own `handle` (in `src/inbox_worker/application/handler.py`): process one delivery to a final outcome, acknowledging it unless the process dies first.

```python
except Exception:
```

- If an error of kind `Exception` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
LOGGER.exception("delivery failed unexpectedly", extra={"fields": {"delivery_id": delivery.delivery_id}})
return "error"
```

- `LOGGER.exception("delivery failed unexpectedly", extra={"fields": {...`: calling `LOGGER.exception("delivery failed unexpectedly", extra={"fields": {"delivery_id": deliv...`, which writes an ERROR log line with the traceback of the current error The named values are `extra`..
- `return "error"`: ends the function and gives back the text `'error'`.

```python
def run(self, *, until_idle: bool = False) -> Counter[str]:
```

- Defines the method `run`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `until_idle`, type `bool`, optional (default `False`). Must be passed by name.
- Gives back a value of type `Counter[str]`.

```python
"""Process deliveries until a stop is requested (or, with `until_idle`, until the queue is empty)."""
```

- The docstring (documentation kept with the code) says: *Process deliveries until a stop is requested (or, with `until_idle`, until the queue is empty).*

```python
outcomes: Counter[str] = Counter()
```

- `outcomes: Counter[str] = Counter()`: stores the result of calling `Counter()`, which makes a `Counter` object in `outcomes`, whose type is declared as `Counter[str]`.

```python
with ThreadPoolExecutor(max_workers=self._concurrency, thread_name_prefix="handle") as pool:
```

- Opens `ThreadPoolExecutor(max_workers=self._concurrency, thread_name_prefix="handle")` as `pool` for the indented lines, and cleans it up when they end (even after an error).

```python
failures = 0
```

- `failures = 0`: stores the number `0` in `failures`.

```python
while not self._stop():
```

- Repeats the indented lines for as long as it is not the case that `self._stop()` is true.

> **`while`.** `while condition:` repeats the indented lines for as long as the condition stays true.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
batch = self._queue.claim(self._concurrency, self._lease)
```

- `batch = self._queue.claim(self._concurrency, self._lease)`: stores the result of calling `self._queue.claim(self._concurrency, self._lease)` in `batch`.

```python
if not batch and until_idle and self._queue.depth() == 0:
```

- Checks whether it is not the case that `batch` is truthy (not `None`, `False`, zero or empty) and `until_idle` is truthy (not `None`, `False`, zero or empty) and `self._queue.depth()` equals `0`. If so, the indented lines run.

```python
break
```

- `break`: leaves the loop now.

```python
except Exception:
```

- If an error of kind `Exception` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
failures += 1
LOGGER.exception("queue unavailable", extra={"fields": {"consecutive_failures": failures}})
outcomes["queue_error"] += 1
self._wait(min(self._idle * 2**failures, MAX_BACKOFF_SECONDS))
continue
```

- `failures += 1`: adds `1` to `failures` and keeps the result there.
- `LOGGER.exception("queue unavailable", extra={"fields": {"consecutiv...`: calling `LOGGER.exception("queue unavailable", extra={"fields": {"consecutive_failures": failure...`, which writes an ERROR log line with the traceback of the current error The named values are `extra`..
- `outcomes["queue_error"] += 1`: adds `1` to `outcomes["queue_error"]` and keeps the result there.
- `self._wait(min(self._idle * 2**failures, MAX_BACKOFF_SECONDS))`: calling `self._wait(min(self._idle * 2**failures, MAX_BACKOFF_SECONDS))`.
- `continue`: skips to the next round of the loop.

```python
failures = 0
```

- `failures = 0`: stores the number `0` in `failures`.

```python
if not batch:
```

- Checks whether it is not the case that `batch` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
self._wait(self._idle)
continue
```

- `self._wait(self._idle)`: calling `self._wait(self._idle)`.
- `continue`: skips to the next round of the loop.

```python
for outcome in pool.map(self._handle_safely, batch):
```

- Repeats the indented lines once for each item of `pool.map(self._handle_safely, batch)`, naming the current item `outcome`.

```python
outcomes[outcome] += 1
```

- `outcomes[outcome] += 1`: adds `1` to `outcomes[outcome]` and keeps the result there.

```python
LOGGER.info("worker stopped", extra={"fields": dict(outcomes)})
return outcomes
```

- `LOGGER.info("worker stopped", extra={"fields": dict(outcomes)})`: calling `LOGGER.info("worker stopped", extra={"fields": dict(outcomes)})`, which writes an INFO log line The named values are `extra`..
- `return outcomes`: ends the function and gives back the value of `outcomes`.

#### `src/inbox_worker/domain/__init__.py`

```python
"""The domain layer."""
```

- The docstring (documentation kept with the code) says: *The domain layer.*

#### `src/inbox_worker/domain/backoff.py`

```python
"""Backoff with full jitter, capped."""
```

- The docstring (documentation kept with the code) says: *Backoff with full jitter, capped.*

```python
from __future__ import annotations

import random
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).

```python
def backoff_delay(attempt: int, base_seconds: float, cap_seconds: float, rng: random.Random) -> float:
```

- Defines the function `backoff_delay`.
- Parameters:
  - `attempt`, type `int`.
  - `base_seconds`, type `float`.
  - `cap_seconds`, type `float`.
  - `rng`, type `random.Random`.
- Gives back a value of type `float`.

```python
"""A random delay in [0, min(cap, base * 2**(attempt - 1))]. Full jitter spreads retries of many failing events
over time; a fixed exponential schedule would have them all retry at the same moments and synchronize into bursts."""
```

- The docstring (documentation kept with the code) says: *A random delay in [0, min(cap, base * 2**(attempt - 1))]. Full jitter spreads retries of many failing events over time; a fixed exponential schedule would have them all retry at the same moments and synchronize into bursts.*

```python
return rng.uniform(0, min(cap_seconds, base_seconds * 2 ** (attempt - 1)))
```

- `return rng.uniform(0, min(cap_seconds, base_seconds * 2 ** (attempt...`: ends the function and gives back the result of calling `rng.uniform(0, min(cap_seconds, base_seconds * 2 ** (attempt - 1)))`, which draws a random decimal in a range.

#### `src/inbox_worker/domain/errors.py`

```python
"""Named errors of the inbox worker. Retryable and permanent failures are different types so no code has to guess."""
```

- The docstring (documentation kept with the code) says: *Named errors of the inbox worker. Retryable and permanent failures are different types so no code has to guess.*

```python
from __future__ import annotations
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)

```python
class PermanentEventError(Exception):
```

- Defines the class `PermanentEventError`.
- It extends `Exception`: it is a kind of error that can be raised and caught.

```python
"""An event that can never succeed. `reason` is one of the dead-letter reasons; the message is what a person reads."""
```

- The docstring (documentation kept with the code) says: *An event that can never succeed. `reason` is one of the dead-letter reasons; the message is what a person reads.*

```python
def __init__(self, reason: str, message: str) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `reason`, type `str`.
  - `message`, type `str`.
- Gives back a value of type `None`.

```python
super().__init__(message)
self.reason = reason
```

- `super().__init__(message)`: calling `super().__init__(message)`.
- `self.reason = reason`: stores the value of `reason` in `self.reason`.

```python
class RetryableModelError(RuntimeError):
```

- Defines the class `RetryableModelError`.
- It extends `RuntimeError`: it is a kind of error that can be raised and caught.

```python
"""A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection."""
```

- The docstring (documentation kept with the code) says: *A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection.*

```python
class ModelCallError(RuntimeError):
```

- Defines the class `ModelCallError`.
- It extends `RuntimeError`: it is a kind of error that can be raised and caught.

```python
"""A model call failed in a way a retry will not fix."""
```

- The docstring (documentation kept with the code) says: *A model call failed in a way a retry will not fix.*

```python
class ReplyInvalidError(ValueError):
```

- Defines the class `ReplyInvalidError`.
- It extends `ValueError`: it is a kind of error that can be raised and caught.

```python
"""A model reply is not a valid ticket; the message says why."""
```

- The docstring (documentation kept with the code) says: *A model reply is not a valid ticket; the message says why.*

```python
class WebhookRejectedError(Exception):
```

- Defines the class `WebhookRejectedError`.
- It extends `Exception`: it is a kind of error that can be raised and caught.

```python
"""A webhook request failed verification; `reason` is the text of the 401."""
```

- The docstring (documentation kept with the code) says: *A webhook request failed verification; `reason` is the text of the 401.*

```python
def __init__(self, reason: str) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `reason`, type `str`.
- Gives back a value of type `None`.

```python
super().__init__(reason)
self.reason = reason
```

- `super().__init__(reason)`: calling `super().__init__(reason)`.
- `self.reason = reason`: stores the value of `reason` in `self.reason`.

#### `src/inbox_worker/domain/events.py`

```python
"""The inbox event: its envelope, and the checks that decide an event can never be processed."""
```

- The docstring (documentation kept with the code) says: *The inbox event: its envelope, and the checks that decide an event can never be processed.*

```python
from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import base64`: makes the module `base64` available (encodes bytes as text made of 64 safe characters and decodes them back).
- `import binascii`: makes the module `binascii` available (converts between binary data and text forms such as hexadecimal).
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)

```python
from inbox_worker.domain.errors import PermanentEventError

MAX_EMAIL_BYTES = 100_000
POISON_MARKER = (
    "POISON-SCHEMA"  # an email containing this makes the fake model answer with something that is not a ticket
)
```

- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`PermanentEventError`: An event that can never succeed.)
- `MAX_EMAIL_BYTES = 100_000`: stores the number `100000` in `MAX_EMAIL_BYTES`.
- `POISON_MARKER = ( "POISON-SCHEMA" # an email containing this makes ...`: stores the text `'POISON-SCHEMA'` in `POISON_MARKER`.

```python
@dataclass(frozen=True, slots=True)
class EmailEvent:
```

- Defines the class `EmailEvent`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""An "email received" event: a unique id and the email text."""
```

- The docstring (documentation kept with the code) says: *An "email received" event: a unique id and the email text.*

```python
event_id: str
body: str
```

- `event_id: str`: a field named `event_id` of type `str`, no default (must be given).
- `body: str`: a field named `body` of type `str`, no default (must be given).

```python
def parse_event(payload: str) -> EmailEvent:
```

- Defines the function `parse_event`.
- Parameters:
  - `payload`, type `str`.
- Gives back a value of type `EmailEvent`.

```python
"""Decode a delivery's payload. Raises `PermanentEventError` for a body that is not an event, is not valid text, or
is too large: none of those will be different on the next attempt, so they go to the dead-letter table."""
```

- The docstring (documentation kept with the code) says: *Decode a delivery's payload. Raises `PermanentEventError` for a body that is not an event, is not valid text, or is too large: none of those will be different on the next attempt, so they go to the dead-letter table.*

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
data = json.loads(payload)
```

- `data = json.loads(payload)`: stores the result of calling `json.loads(payload)`, which turns the JSON text `payload` into Python values in `data`.

```python
except json.JSONDecodeError as error:
```

- If an error of kind `json.JSONDecodeError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
raise PermanentEventError("malformed_event", f"the event is not valid JSON: {error.msg}") from None
```

- `raise PermanentEventError("malformed_event", f"the event is not val...`: stops with an error of kind `PermanentEventError` with the message `"malformed_event"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
if not isinstance(data, dict) or not isinstance(data.get("event_id"), str) or not data["event_id"].strip():
```

- Checks whether it is not the case that `isinstance(data, dict)` is true (the call asks whether `data` is a `dict`) or it is not the case that `isinstance(data.get("event_id"), str)` is true (the call asks whether `data.get("event_id")` is a `str`) or it is not the case that `data["event_id"].strip()` is true (the call removes spaces and line breaks from both ends of `data["event_id"]` (or the characters its argument)). If so, the indented lines run.

```python
raise PermanentEventError("malformed_event", "the event needs a non-empty string event_id")
```

- `raise PermanentEventError("malformed_event", "the event needs a non...`: stops with an error of kind `PermanentEventError` with the message `"malformed_event"`. Whoever called this code must handle it or the program stops.

```python
if "body_b64" in data:
```

- Checks whether `"body_b64"` is among `data`. If so, the indented lines run.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
raw = base64.b64decode(str(data["body_b64"]), validate=True)
```

- `raw = base64.b64decode(str(data["body_b64"]), validate=True)`: stores the result of calling `base64.b64decode(str(data["body_b64"]), validate=True)`, which decodes base64 text to bytes The named values are `validate`. in `raw`.

```python
except (binascii.Error, ValueError):
```

- If an error of kind `(binascii.Error, ValueError)` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise PermanentEventError("malformed_event", "body_b64 is not valid base64") from None
```

- `raise PermanentEventError("malformed_event", "body_b64 is not valid...`: stops with an error of kind `PermanentEventError` with the message `"malformed_event"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
body = raw.decode("utf-8")
```

- `body = raw.decode("utf-8")`: stores the result of calling `raw.decode("utf-8")`, which turns the bytes `raw` into text in `body`.

```python
except UnicodeDecodeError as error:
```

- If an error of kind `UnicodeDecodeError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
raise PermanentEventError(
    "bad_encoding", f"the email is not valid UTF-8: {error.reason} at byte {error.start}"
) from None
```

- `raise PermanentEventError( "bad_encoding", f"the email is not valid...`: stops with an error of kind `PermanentEventError` with the message `"bad_encoding"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
else:
```

- Runs when none of the conditions above held.

```python
found = data.get("body")
```

- `found = data.get("body")`: stores the result of calling `data.get("body")`, which looks up `"body"` in `data`; a second value is the answer when the key is missing in `found`.

```python
if not isinstance(found, str) or not found.strip():
```

- Checks whether it is not the case that `isinstance(found, str)` is true (the call asks whether `found` is a `str`) or it is not the case that `found.strip()` is true (the call removes spaces and line breaks from both ends of `found` (or the characters its argument)). If so, the indented lines run.

```python
raise PermanentEventError("malformed_event", "the event needs a non-empty string body")
```

- `raise PermanentEventError("malformed_event", "the event needs a non...`: stops with an error of kind `PermanentEventError` with the message `"malformed_event"`. Whoever called this code must handle it or the program stops.

```python
body = found
```

- `body = found`: stores the value of `found` in `body`.

```python
size = len(body.encode("utf-8"))
```

- `size = len(body.encode("utf-8"))`: stores the result of calling `len(body.encode("utf-8"))`, which counts the items in `body.encode("utf-8")` in `size`.

```python
if size > MAX_EMAIL_BYTES:
```

- Checks whether `size` is greater than `MAX_EMAIL_BYTES`. If so, the indented lines run.

```python
raise PermanentEventError("event_too_large", f"the email is {size} bytes; the limit is {MAX_EMAIL_BYTES}")
```

- `raise PermanentEventError("event_too_large", f"the email is {size} ...`: stops with an error of kind `PermanentEventError` with the message `"event_too_large"`. Whoever called this code must handle it or the program stops.

```python
return EmailEvent(data["event_id"].strip(), body)
```

- `return EmailEvent(data["event_id"].strip(), body)`: ends the function and gives back the result of calling `EmailEvent(data["event_id"].strip(), body)`, which is this repository's own `EmailEvent` (in `src/inbox_worker/domain/events.py`): an "email received" event: a unique id and the email text.

```python
def event_id_of(payload: str) -> str:
```

- Defines the function `event_id_of`.
- Parameters:
  - `payload`, type `str`.
- Gives back a value of type `str`.

```python
"""The event id a receiver files a payload under; a payload that is not an event gets a stable placeholder so it can
still be queued, parked and shown to a person."""
```

- The docstring (documentation kept with the code) says: *The event id a receiver files a payload under; a payload that is not an event gets a stable placeholder so it can still be queued, parked and shown to a person.*

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
data = json.loads(payload)
```

- `data = json.loads(payload)`: stores the result of calling `json.loads(payload)`, which turns the JSON text `payload` into Python values in `data`.

```python
except json.JSONDecodeError:
```

- If an error of kind `json.JSONDecodeError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
data = None
```

- `data = None`: stores nothing (`None`) in `data`.

```python
if isinstance(data, dict) and isinstance(data.get("event_id"), str) and data["event_id"].strip():
```

- Checks whether `isinstance(data, dict)` is true (the call asks whether `data` is a `dict`) and `isinstance(data.get("event_id"), str)` is true (the call asks whether `data.get("event_id")` is a `str`) and `data["event_id"].strip()` is true (the call removes spaces and line breaks from both ends of `data["event_id"]` (or the characters its argument)). If so, the indented lines run.

```python
return str(data["event_id"]).strip()
```

- `return str(data["event_id"]).strip()`: ends the function and gives back the result of calling `str(data["event_id"]).strip()`, which removes spaces and line breaks from both ends of `str(data["event_id"])` (or the characters its argument).

```python
return "unparsed-" + hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]
```

- `return "unparsed-" + hashlib.sha256(payload.encode("utf-8", "replac...`: ends the function and gives back `"unparsed-" + hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]`, which adds `"unparsed-"` and `hashlib.sha256(payload.encode("utf-8", "replace")).hexdigest()[:12]`.

#### `src/inbox_worker/domain/signature.py`

```python
"""Webhook signatures: HMAC-SHA256 over the timestamp and the body together, with a maximum age."""
```

- The docstring (documentation kept with the code) says: *Webhook signatures: HMAC-SHA256 over the timestamp and the body together, with a maximum age.*

```python
from __future__ import annotations

import hashlib
import hmac

MAX_AGE_SECONDS = 300
TAMPERED = "signature mismatch (tampered or wrong secret)"
TOO_OLD = "request too old (replay rejected)"
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `import hmac`: makes the module `hmac` available (keyed hashing: signatures only a holder of the secret can make).
- `MAX_AGE_SECONDS = 300`: stores the number `300` in `MAX_AGE_SECONDS`.
- `TAMPERED = "signature mismatch (tampered or wrong secret)"`: stores the text `'signature mismatch (tampered or wrong secret)'` in `TAMPERED`.
- `TOO_OLD = "request too old (replay rejected)"`: stores the text `'request too old (replay rejected)'` in `TOO_OLD`.

```python
BAD_TIMESTAMP = "timestamp is not a number"
```

- `BAD_TIMESTAMP = "timestamp is not a number"`: stores the text `'timestamp is not a number'` in `BAD_TIMESTAMP`.

```python
def sign(secret: bytes, timestamp: float, body: str) -> str:
```

- Defines the function `sign`.
- Parameters:
  - `secret`, type `bytes`.
  - `timestamp`, type `float`.
  - `body`, type `str`.
- Gives back a value of type `str`.

```python
"""The signature a sender attaches. Signing the timestamp too is what stops a captured request being replayed later."""
```

- The docstring (documentation kept with the code) says: *The signature a sender attaches. Signing the timestamp too is what stops a captured request being replayed later.*

```python
return hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashlib.sha256).hexdigest()
```

- `return hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashli...`: ends the function and gives back the result of calling `hmac.new(secret, f"{int(timestamp)}.{body}".encode(), hashlib.sha256).hexdigest()`, which writes the hash as hexadecimal text.

```python
def verify(secret: bytes, timestamp: str, body: str, signature: str, now: float) -> tuple[bool, str]:
```

- Defines the function `verify`.
- Parameters:
  - `secret`, type `bytes`.
  - `timestamp`, type `str`.
  - `body`, type `str`.
  - `signature`, type `str`.
  - `now`, type `float`.
- Gives back a value of type `tuple[bool, str]`.

```python
"""(ok, reason). Age is checked first and cheaply; the comparison is constant-time."""
```

- The docstring (documentation kept with the code) says: *(ok, reason). Age is checked first and cheaply; the comparison is constant-time.*

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
sent_at = float(timestamp)
```

- `sent_at = float(timestamp)`: stores the result of calling `float(timestamp)`, which turns `timestamp` into a decimal number in `sent_at`.

```python
except ValueError:
```

- If an error of kind `ValueError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
return False, BAD_TIMESTAMP
```

- `return False, BAD_TIMESTAMP`: ends the function and gives back a tuple of 2 items.

```python
if abs(now - sent_at) > MAX_AGE_SECONDS:
```

- Checks whether `abs(now - sent_at)` is greater than `MAX_AGE_SECONDS`. If so, the indented lines run.

```python
return False, TOO_OLD
```

- `return False, TOO_OLD`: ends the function and gives back a tuple of 2 items.

```python
if not hmac.compare_digest(sign(secret, sent_at, body), signature):
```

- Checks whether it is not the case that `hmac.compare_digest(sign(secret, sent_at, body), signature)` is true (the call compares `sign(secret, sent_at, body)` and `signature` in constant time (the time does not reveal where they differ)). If so, the indented lines run.

```python
return False, TAMPERED
```

- `return False, TAMPERED`: ends the function and gives back a tuple of 2 items.

```python
return True, "ok"
```

- `return True, "ok"`: ends the function and gives back a tuple of 2 items.

#### `src/inbox_worker/domain/stats.py`

```python
"""Small statistics for the burst report."""
```

- The docstring (documentation kept with the code) says: *Small statistics for the burst report.*

```python
from __future__ import annotations

import math
from collections.abc import Sequence
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import math`: makes the module `math` available (mathematical functions).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)

```python
def percentile(values: Sequence[float], fraction: float) -> float:
```

- Defines the function `percentile`.
- Parameters:
  - `values`, type `Sequence[float]`.
  - `fraction`, type `float`.
- Gives back a value of type `float`.

```python
"""Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values."""
```

- The docstring (documentation kept with the code) says: *Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values.*

```python
if not values:
```

- Checks whether it is not the case that `values` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
return 0.0
```

- `return 0.0`: ends the function and gives back the number `0.0`.

```python
ordered = sorted(values)
return ordered[min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))]
```

- `ordered = sorted(values)`: stores the result of calling `sorted(values)`, which builds a new list with the items of `values` in order in `ordered`.
- `return ordered[min(len(ordered) - 1, max(0, math.ceil(fraction * le...`: ends the function and gives back the item `ordered[min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))]`.

#### `src/inbox_worker/domain/ticket.py`

```python
"""The ticket the extractor produces."""
```

- The docstring (documentation kept with the code) says: *The ticket the extractor produces.*

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from inbox_worker.domain.errors import ReplyInvalidError

INTENTS = ("cancel", "refund", "order_status", "other")
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Mapping`: the type hint for a read-only dict-like collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`ReplyInvalidError`: A model reply is not a valid ticket; the message says why.)
- `INTENTS = ("cancel", "refund", "order_status", "other")`: stores a tuple of 4 items in `INTENTS`.

```python
SENTIMENTS = ("positive", "neutral", "negative")
ACTIONS = ("cancel_order", "issue_refund", "send_tracking", "none")
```

- `SENTIMENTS = ("positive", "neutral", "negative")`: stores a tuple of 3 items in `SENTIMENTS`.
- `ACTIONS = ("cancel_order", "issue_refund", "send_tracking", "none")`: stores a tuple of 4 items in `ACTIONS`.

```python
@dataclass(frozen=True, slots=True)
class Ticket:
```

- Defines the class `Ticket`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""What the customer wants, about which order, in what mood, and the action it asks for."""
```

- The docstring (documentation kept with the code) says: *What the customer wants, about which order, in what mood, and the action it asks for.*

```python
intent: str
order_number: str | None
sentiment: str
requested_action: str
```

- `intent: str`: a field named `intent` of type `str`, no default (must be given).
- `order_number: str | None`: a field named `order_number` of type `str | None`, no default (must be given).
- `sentiment: str`: a field named `sentiment` of type `str`, no default (must be given).
- `requested_action: str`: a field named `requested_action` of type `str`, no default (must be given).

```python
@classmethod
def from_dict(cls, data: Mapping[str, Any]) -> Ticket:
```

- Defines the method `from_dict`.
- `@classmethod`: a method that receives the class itself as `cls`.
- Parameters:
  - `cls`: the object (or class) the method was called on.
  - `data`, type `Mapping[str, Any]`.
- Gives back a value of type `Ticket`.

> **`@property`, `@staticmethod`, `@classmethod`.** `@property` lets a method be read like an attribute (`obj.size` instead of `obj.size()`). `@staticmethod` is a function that lives in the class but needs no object. `@classmethod` receives the class itself (named `cls`) instead of an object, often to build objects in another way.

```python
"""Build a ticket from a decoded reply, checking every field."""
```

- The docstring (documentation kept with the code) says: *Build a ticket from a decoded reply, checking every field.*

```python
order = data.get("order_number")
valid = (
    data.get("intent") in INTENTS
    and data.get("sentiment") in SENTIMENTS
    and data.get("requested_action") in ACTIONS
    and (order is None or (isinstance(order, str) and len(order) == 4 and order.isdigit()))
)
```

- `order = data.get("order_number")`: stores the result of calling `data.get("order_number")`, which looks up `"order_number"` in `data`; a second value is the answer when the key is missing in `order`.
- `valid = ( data.get("intent") in INTENTS and data.get("sentiment") i...`: stores `data.get("intent") in INTENTS and data.get("sentiment") in SENTIMENTS and data.get("req...` (the first operand that decides the and) in `valid`.

```python
if not valid:
```

- Checks whether it is not the case that `valid` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
raise ReplyInvalidError("the reply does not match the ticket schema")
```

- `raise ReplyInvalidError("the reply does not match the ticket schema")`: stops with an error of kind `ReplyInvalidError` with the message `"the reply does not match the ticket schema"`. Whoever called this code must handle it or the program stops.

```python
return cls(data["intent"], order, data["sentiment"], data["requested_action"])
```

- `return cls(data["intent"], order, data["sentiment"], data["requeste...`: ends the function and gives back the result of calling `cls(data["intent"], order, data["sentiment"], data["requested_action"])`.

#### `src/inbox_worker/infrastructure/__init__.py`

```python
"""The infrastructure layer."""
```

- The docstring (documentation kept with the code) says: *The infrastructure layer.*

#### `src/inbox_worker/infrastructure/cassette.py`

```python
"""Recorded model replies: a cassette maps a hash of the whole request to the reply, so tests run offline."""
```

- The docstring (documentation kept with the code) says: *Recorded model replies: a cassette maps a hash of the whole request to the reply, so tests run offline.*

```python
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from inbox_worker.application.ports import ChatModel, ModelReply
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.)
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`ChatModel`: A text model.) (`ModelReply`: The model's text and what the call used.)

```python
class MissingRecordingError(LookupError):
```

- Defines the class `MissingRecordingError`.
- It extends `LookupError` (it starts with all of that class's methods and may add or replace some).

```python
"""No recording matches this request; the message says how to re-record."""
```

- The docstring (documentation kept with the code) says: *No recording matches this request; the message says how to re-record.*

```python
def request_key(model_id: str, system: str, user: str, prompt_version: str) -> str:
```

- Defines the function `request_key`.
- Parameters:
  - `model_id`, type `str`.
  - `system`, type `str`.
  - `user`, type `str`.
  - `prompt_version`, type `str`.
- Gives back a value of type `str`.

```python
"""Hash of everything that decides the reply."""
```

- The docstring (documentation kept with the code) says: *Hash of everything that decides the reply.*

```python
return hashlib.sha256(json.dumps([model_id, prompt_version, system, user]).encode()).hexdigest()
```

- `return hashlib.sha256(json.dumps([model_id, prompt_version, system,...`: ends the function and gives back the result of calling `hashlib.sha256(json.dumps([model_id, prompt_version, system, user]).encode()).hexdigest()`, which writes the hash as hexadecimal text.

```python
class RecordedModel:
```

- Defines the class `RecordedModel`.

```python
"""Replays replies from a cassette file; a request with no recording fails loudly."""
```

- The docstring (documentation kept with the code) says: *Replays replies from a cassette file; a request with no recording fails loudly.*

```python
def __init__(self, path: Path) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `path`, type `Path`.
- Gives back a value of type `None`.

```python
data = json.loads(path.read_text(encoding="utf-8"))
self.model_id: str = data["model"]
self.provenance: str = data["provenance"]
self._entries: dict[str, dict[str, Any]] = data["entries"]
```

- `data = json.loads(path.read_text(encoding="utf-8"))`: stores the result of calling `json.loads(path.read_text(encoding="utf-8"))`, which turns the JSON text `path.read_text(encoding="utf-8")` into Python values in `data`.
- `self.model_id: str = data["model"]`: stores the item `data["model"]` in `self.model_id`, whose type is declared as `str`.
- `self.provenance: str = data["provenance"]`: stores the item `data["provenance"]` in `self.provenance`, whose type is declared as `str`.
- `self._entries: dict[str, dict[str, Any]] = data["entries"]`: stores the item `data["entries"]` in `self._entries`, whose type is declared as `dict[str, dict[str, Any]]`.

```python
def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
```

- Defines the method `complete`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `system`, type `str`.
  - `user`, type `str`.
  - `prompt_version`, type `str`.
- Gives back a value of type `ModelReply`.

```python
"""The recorded reply for this exact request."""
```

- The docstring (documentation kept with the code) says: *The recorded reply for this exact request.*

```python
key = request_key(self.model_id, system, user, prompt_version)
entry = self._entries.get(key)
```

- `key = request_key(self.model_id, system, user, prompt_version)`: stores the result of calling `request_key(self.model_id, system, user, prompt_version)`, which is this repository's own `request_key` (in `src/inbox_worker/infrastructure/cassette.py`): hash of everything that decides the reply in `key`.
- `entry = self._entries.get(key)`: stores the result of calling `self._entries.get(key)`, which looks up `key` in `self._entries`; a second value is the answer when the key is missing in `entry`.

```python
if entry is None:
```

- Checks whether `entry` is nothing (`None`). If so, the indented lines run.

```python
raise MissingRecordingError(
    f"no recording for prompt {prompt_version} (key {key[:12]}); re-record with `make record` (needs ANTHROPIC_API_KEY)"
)
```

- `raise MissingRecordingError( f"no recording for prompt {prompt_vers...`: stops with an error of kind `MissingRecordingError` with the message ``f"no recording for prompt {prompt_version} (key {key[:12]}); re-record with `make recor...``. Whoever called this code must handle it or the program stops.

```python
return ModelReply(entry["text"], self.model_id, int(entry["input_tokens"]), int(entry["output_tokens"]))
```

- `return ModelReply(entry["text"], self.model_id, int(entry["input_to...`: ends the function and gives back the result of calling `ModelReply(entry["text"], self.model_id, int(entry["input_tokens"]), int(entry["output_...`, which is this repository's own `ModelReply` (in `src/inbox_worker/application/ports.py`): the model's text and what the call used.

```python
class RecordingModel:
```

- Defines the class `RecordingModel`.

```python
"""Wraps a real model and writes every reply to a cassette, keyed like `RecordedModel` expects."""
```

- The docstring (documentation kept with the code) says: *Wraps a real model and writes every reply to a cassette, keyed like `RecordedModel` expects.*

```python
def __init__(self, inner: ChatModel, path: Path, model_id: str, provenance: str) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `inner`, type `ChatModel`.
  - `path`, type `Path`.
  - `model_id`, type `str`.
  - `provenance`, type `str`.
- Gives back a value of type `None`.

```python
self._inner = inner
self._path = path
self._model_id = model_id
self._provenance = provenance
self._entries: dict[str, dict[str, Any]] = {}
```

- `self._inner = inner`: stores the value of `inner` in `self._inner`.
- `self._path = path`: stores the value of `path` in `self._path`.
- `self._model_id = model_id`: stores the value of `model_id` in `self._model_id`.
- `self._provenance = provenance`: stores the value of `provenance` in `self._provenance`.
- `self._entries: dict[str, dict[str, Any]] = {}`: stores a new dict (empty) in `self._entries`, whose type is declared as `dict[str, dict[str, Any]]`.

```python
def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
```

- Defines the method `complete`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `system`, type `str`.
  - `user`, type `str`.
  - `prompt_version`, type `str`.
- Gives back a value of type `ModelReply`.

```python
"""Call the wrapped model, remember the reply and rewrite the cassette."""
```

- The docstring (documentation kept with the code) says: *Call the wrapped model, remember the reply and rewrite the cassette.*

```python
reply = self._inner.complete(system, user, prompt_version)
self._entries[request_key(self._model_id, system, user, prompt_version)] = {
    "text": reply.text,
    "input_tokens": reply.input_tokens,
    "output_tokens": reply.output_tokens,
}
document = {"provenance": self._provenance, "model": self._model_id, "entries": self._entries}
self._path.parent.mkdir(parents=True, exist_ok=True)
self._path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="utf-8")
return reply
```

- `reply = self._inner.complete(system, user, prompt_version)`: stores the result of calling `self._inner.complete(system, user, prompt_version)` in `reply`.
- `self._entries[request_key(self._model_id, system, user, prompt_vers...`: stores a new dict with 3 entries in the slot `self._entries[request_key(self._model_id, system, user, prompt_version)]`.
- `document = {"provenance": self._provenance, "model": self._model_id...`: stores a new dict with 3 entries in `document`.
- `self._path.parent.mkdir(parents=True, exist_ok=True)`: calling `self._path.parent.mkdir(parents=True, exist_ok=True)`, which creates the folder `self._path.parent` The named values are `parents`, `exist_ok`..
- `self._path.write_text(json.dumps(document, indent=1, sort_keys=True...`: calling `self._path.write_text(json.dumps(document, indent=1, sort_keys=True) + "\n", encoding="...`, which writes text to the file `self._path`, replacing it The named values are `encoding`..
- `return reply`: ends the function and gives back the value of `reply`.

#### `src/inbox_worker/infrastructure/claude_model.py`

```python
"""The real adapter: Claude through the official SDK. The key comes from the environment, never from code."""
```

- The docstring (documentation kept with the code) says: *The real adapter: Claude through the official SDK. The key comes from the environment, never from code.*

```python
from __future__ import annotations

from typing import Any

import anthropic

from inbox_worker.application.ports import ModelReply
from inbox_worker.domain.errors import ModelCallError, RetryableModelError
from inbox_worker.infrastructure.environment import ConfigurationError
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.)
- `import anthropic`: makes the module `anthropic` available (Anthropic's official Python library for calling Claude).
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`ModelReply`: The model's text and what the call used.)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`ModelCallError`: A model call failed in a way a retry will not fix.) (`RetryableModelError`: A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection.)
- `from inbox_worker.infrastructure.environment import ...`: takes names from `inbox_worker.infrastructure.environment`, this repository's own code. (`ConfigurationError`: An environment variable is missing or has an unusable value.)

```python
class ClaudeModel:
```

- Defines the class `ClaudeModel`.

```python
"""One Messages API call per request. Rate limits, server errors, timeouts and dropped connections are retryable."""
```

- The docstring (documentation kept with the code) says: *One Messages API call per request. Rate limits, server errors, timeouts and dropped connections are retryable.*

```python
def __init__(
    self, model_id: str, api_key: str | None, *, timeout_seconds: float = 30.0, client: Any = None
) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `model_id`, type `str`.
  - `api_key`, type `str | None`.
  - `timeout_seconds`, type `float`, optional (default `30.0`). Must be passed by name.
  - `client`, type `Any`, optional (default `None`). Must be passed by name.
- Gives back a value of type `None`.

```python
if client is None:
```

- Checks whether `client` is nothing (`None`). If so, the indented lines run.

```python
if not api_key:
```

- Checks whether it is not the case that `api_key` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
raise ConfigurationError("ANTHROPIC_API_KEY must be set to use the Claude adapter")
```

- `raise ConfigurationError("ANTHROPIC_API_KEY must be set to use the ...`: stops with an error of kind `ConfigurationError` with the message `"ANTHROPIC_API_KEY must be set to use the Claude adapter"`. Whoever called this code must handle it or the program stops.

```python
client = anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)
```

- `client = anthropic.Anthropic(api_key=api_key, timeout=timeout_secon...`: stores the result of calling `anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds, max_retries=0)`, which makes a `Anthropic` object with the named values `api_key`, `timeout`, `max_retries` in `client`.

```python
self._client = client
self._model_id = model_id
```

- `self._client = client`: stores the value of `client` in `self._client`.
- `self._model_id = model_id`: stores the value of `model_id` in `self._model_id`.

```python
def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
```

- Defines the method `complete`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `system`, type `str`.
  - `user`, type `str`.
  - `prompt_version`, type `str`.
- Gives back a value of type `ModelReply`.

```python
"""Send the prompt as the system text and the email as the user message."""
```

- The docstring (documentation kept with the code) says: *Send the prompt as the system text and the email as the user message.*

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
message = self._client.messages.create(
    model=self._model_id, max_tokens=300, system=system, messages=[{"role": "user", "content": user}]
)
```

- `message = self._client.messages.create( model=self._model_id, max_t...`: stores the result of calling `self._client.messages.create( model=self._model_id, max_tokens=300, system=system, mess...` The named values are `model`, `max_tokens`, `system`, `messages`. in `message`.

```python
except (anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError) as error:
```

- If an error of kind `(anthropic.RateLimitError, anthropic.APITimeoutError, anthropic.APIConnectionError)` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
raise RetryableModelError(f"{type(error).__name__}: {error}") from error
```

- `raise RetryableModelError(f"{type(error).__name__}: {error}") from ...`: stops with an error of kind `RetryableModelError` with the message `f"{type(error).__name__}: {error}"`, recording `error` as the cause. Whoever called this code must handle it or the program stops.

```python
except anthropic.APIStatusError as error:
```

- If an error of kind `anthropic.APIStatusError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
if error.status_code >= 500:
```

- Checks whether `error.status_code` is greater than or equal to `500`. If so, the indented lines run.

```python
raise RetryableModelError(f"{type(error).__name__}: {error}") from error
```

- `raise RetryableModelError(f"{type(error).__name__}: {error}") from ...`: stops with an error of kind `RetryableModelError` with the message `f"{type(error).__name__}: {error}"`, recording `error` as the cause. Whoever called this code must handle it or the program stops.

```python
raise ModelCallError(f"{type(error).__name__}: {error}") from error
```

- `raise ModelCallError(f"{type(error).__name__}: {error}") from error`: stops with an error of kind `ModelCallError` with the message `f"{type(error).__name__}: {error}"`, recording `error` as the cause. Whoever called this code must handle it or the program stops.

```python
if message.stop_reason == "refusal":
```

- Checks whether `message.stop_reason` equals `"refusal"`. If so, the indented lines run.

```python
raise ModelCallError("the model declined the request (stop_reason=refusal)")
```

- `raise ModelCallError("the model declined the request (stop_reason=r...`: stops with an error of kind `ModelCallError` with the message `"the model declined the request (stop_reason=refusal)"`. Whoever called this code must handle it or the program stops.

```python
text = "".join(block.text for block in message.content if block.type == "text")
return ModelReply(text, message.model, message.usage.input_tokens, message.usage.output_tokens)
```

- `text = "".join(block.text for block in message.content if block.typ...`: stores the result of calling `"".join(block.text for block in message.content if block.type == "text")`, which glues the items of `(block.text for block in message.content if block.type == "text")` together with `""` between them in `text`.
- `return ModelReply(text, message.model, message.usage.input_tokens, ...`: ends the function and gives back the result of calling `ModelReply(text, message.model, message.usage.input_tokens, message.usage.output_tokens)`, which is this repository's own `ModelReply` (in `src/inbox_worker/application/ports.py`): the model's text and what the call used.

#### `src/inbox_worker/infrastructure/clock.py`

```python
"""The system clock."""
```

- The docstring (documentation kept with the code) says: *The system clock.*

```python
from __future__ import annotations

from datetime import UTC, datetime
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`UTC`: the UTC time zone.) (`datetime`: the date-and-time type.)

```python
class SystemClock:
```

- Defines the class `SystemClock`.

```python
"""Now, in UTC."""
```

- The docstring (documentation kept with the code) says: *Now, in UTC.*

```python
def now(self) -> datetime:
```

- Defines the method `now`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `datetime`.

```python
"""The current time, timezone-aware."""
```

- The docstring (documentation kept with the code) says: *The current time, timezone-aware.*

```python
return datetime.now(UTC)
```

- `return datetime.now(UTC)`: ends the function and gives back the result of calling `datetime.now(UTC)`, which reads the current date and time.

#### `src/inbox_worker/infrastructure/environment.py`

```python
"""Configuration helpers: read and validate environment variables once at startup (twelve-factor)."""
```

- The docstring (documentation kept with the code) says: *Configuration helpers: read and validate environment variables once at startup (twelve-factor).*

```python
from __future__ import annotations

from collections.abc import Mapping
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Mapping`: the type hint for a read-only dict-like collection.)

```python
class ConfigurationError(ValueError):
```

- Defines the class `ConfigurationError`.
- It extends `ValueError`: it is a kind of error that can be raised and caught.

```python
"""An environment variable is missing or has an unusable value."""
```

- The docstring (documentation kept with the code) says: *An environment variable is missing or has an unusable value.*

```python
def read_text(environ: Mapping[str, str], name: str, default: str | None = None) -> str:
```

- Defines the function `read_text`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `str | None`, optional (default `None`).
- Gives back a value of type `str`.

```python
"""A non-empty string variable, or `default`."""
```

- The docstring (documentation kept with the code) says: *A non-empty string variable, or `default`.*

```python
value = environ.get(name, default if default is not None else "").strip()
```

- `value = environ.get(name, default if default is not None else "").s...`: stores the result of calling `environ.get(name, default if default is not None else "").strip()`, which removes spaces and line breaks from both ends of `environ.get(name, default if default is not None else "")` (or the characters its argument) in `value`.

```python
if not value:
```

- Checks whether it is not the case that `value` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
raise ConfigurationError(f"{name} must be set and not empty")
```

- `raise ConfigurationError(f"{name} must be set and not empty")`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be set and not empty"`. Whoever called this code must handle it or the program stops.

```python
return value
```

- `return value`: ends the function and gives back the value of `value`.

```python
def read_optional(environ: Mapping[str, str], name: str) -> str | None:
```

- Defines the function `read_optional`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
- Gives back a value of type `str | None`.

```python
"""A string variable that may be absent or empty (for example an API key)."""
```

- The docstring (documentation kept with the code) says: *A string variable that may be absent or empty (for example an API key).*

```python
value = environ.get(name, "").strip()
return value or None
```

- `value = environ.get(name, "").strip()`: stores the result of calling `environ.get(name, "").strip()`, which removes spaces and line breaks from both ends of `environ.get(name, "")` (or the characters its argument) in `value`.
- `return value or None`: ends the function and gives back `value or None` (the first operand that decides the or).

```python
def read_int(environ: Mapping[str, str], name: str, default: int, minimum: int = 1) -> int:
```

- Defines the function `read_int`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `int`.
  - `minimum`, type `int`, optional (default `1`).
- Gives back a value of type `int`.

```python
"""An integer variable of at least `minimum`."""
```

- The docstring (documentation kept with the code) says: *An integer variable of at least `minimum`.*

```python
raw = environ.get(name, str(default)).strip()
```

- `raw = environ.get(name, str(default)).strip()`: stores the result of calling `environ.get(name, str(default)).strip()`, which removes spaces and line breaks from both ends of `environ.get(name, str(default))` (or the characters its argument) in `raw`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
value = int(raw)
```

- `value = int(raw)`: stores the result of calling `int(raw)`, which turns `raw` into a whole number in `value`.

```python
except ValueError:
```

- If an error of kind `ValueError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise ConfigurationError(f"{name} must be an integer, got {raw!r}") from None
```

- `raise ConfigurationError(f"{name} must be an integer, got {raw!r}")...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be an integer, got {raw!r}"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
if value < minimum:
```

- Checks whether `value` is less than `minimum`. If so, the indented lines run.

```python
raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")
```

- `raise ConfigurationError(f"{name} must be at least {minimum}, got {...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be at least {minimum}, got {value}"`. Whoever called this code must handle it or the program stops.

```python
return value
```

- `return value`: ends the function and gives back the value of `value`.

```python
def read_float(environ: Mapping[str, str], name: str, default: float, minimum: float = 0.0) -> float:
```

- Defines the function `read_float`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `float`.
  - `minimum`, type `float`, optional (default `0.0`).
- Gives back a value of type `float`.

```python
"""A float variable of at least `minimum`."""
```

- The docstring (documentation kept with the code) says: *A float variable of at least `minimum`.*

```python
raw = environ.get(name, str(default)).strip()
```

- `raw = environ.get(name, str(default)).strip()`: stores the result of calling `environ.get(name, str(default)).strip()`, which removes spaces and line breaks from both ends of `environ.get(name, str(default))` (or the characters its argument) in `raw`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
value = float(raw)
```

- `value = float(raw)`: stores the result of calling `float(raw)`, which turns `raw` into a decimal number in `value`.

```python
except ValueError:
```

- If an error of kind `ValueError` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise ConfigurationError(f"{name} must be a number, got {raw!r}") from None
```

- `raise ConfigurationError(f"{name} must be a number, got {raw!r}") f...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be a number, got {raw!r}"`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
if value < minimum:
```

- Checks whether `value` is less than `minimum`. If so, the indented lines run.

```python
raise ConfigurationError(f"{name} must be at least {minimum}, got {value}")
```

- `raise ConfigurationError(f"{name} must be at least {minimum}, got {...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be at least {minimum}, got {value}"`. Whoever called this code must handle it or the program stops.

```python
return value
```

- `return value`: ends the function and gives back the value of `value`.

```python
def read_choice(environ: Mapping[str, str], name: str, default: str, choices: frozenset[str]) -> str:
```

- Defines the function `read_choice`.
- Parameters:
  - `environ`, type `Mapping[str, str]`.
  - `name`, type `str`.
  - `default`, type `str`.
  - `choices`, type `frozenset[str]`.
- Gives back a value of type `str`.

```python
"""A string variable restricted to `choices`."""
```

- The docstring (documentation kept with the code) says: *A string variable restricted to `choices`.*

```python
value = environ.get(name, default).strip()
```

- `value = environ.get(name, default).strip()`: stores the result of calling `environ.get(name, default).strip()`, which removes spaces and line breaks from both ends of `environ.get(name, default)` (or the characters its argument) in `value`.

```python
if value not in choices:
```

- Checks whether `value` is not among `choices`. If so, the indented lines run.

```python
raise ConfigurationError(f"{name} must be one of {sorted(choices)}, got {value!r}")
```

- `raise ConfigurationError(f"{name} must be one of {sorted(choices)},...`: stops with an error of kind `ConfigurationError` with the message `f"{name} must be one of {sorted(choices)}, got {value!r}"`. Whoever called this code must handle it or the program stops.

```python
return value
```

- `return value`: ends the function and gives back the value of `value`.

#### `src/inbox_worker/infrastructure/fake_model.py`

```python
"""A fake model for load tests: a configurable delay, an error rate and a rate limit. It is not a model.

It extracts a ticket with keyword rules, so a run has real tickets to count. The rate limit is a token bucket in requests
per second; a call over it raises the same error a provider's 429 would, and the call is counted.
"""
```

- The docstring (documentation kept with the code) says: *A fake model for load tests: a configurable delay, an error rate and a rate limit. It is not a model. It extracts a ticket with keyword rules, so a run has real tickets to count. The rate limit is a token bucket in requests per second; a call over it raises the same error a provider's 429 would, and the call is counted.*

```python
from __future__ import annotations

import json
import math
import random
import re
import threading
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import math`: makes the module `math` available (mathematical functions).
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `import re`: makes the module `re` available (regular expressions: patterns that match text).
- `import threading`: makes the module `threading` available (threads, locks and events).

```python
import time
from collections.abc import Callable

from inbox_worker.application.ports import ModelReply
from inbox_worker.domain.errors import RetryableModelError
from inbox_worker.domain.events import POISON_MARKER

_ORDER = re.compile(r"(?<!\d)\d{4}(?!\d)")
```

- `import time`: makes the module `time` available (clocks and sleeping).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Callable`: the type hint for a function value.)
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`ModelReply`: The model's text and what the call used.)
- `from inbox_worker.domain.errors import ...`: takes names from `inbox_worker.domain.errors`, this repository's own code. (`RetryableModelError`: A model call failed in a way that may work next time: rate limit, server error, timeout, dropped connection.)
- `from inbox_worker.domain.events import ...`: takes names from `inbox_worker.domain.events`, this repository's own code. (`POISON_MARKER`: a name defined in this repository.)
- `_ORDER = re.compile(r"(?<!\d)\d{4}(?!\d)")`: stores the result of calling `re.compile(r"(?<!\d)\d{4}(?!\d)")`, which compiles the pattern `r"(?<!\d)\d{4}(?!\d)"` so it can be matched many times in `_ORDER`.

```python
class FakeModel:
```

- Defines the class `FakeModel`.

```python
"""Thread-safe; counts calls, rate-limit errors and injected errors."""
```

- The docstring (documentation kept with the code) says: *Thread-safe; counts calls, rate-limit errors and injected errors.*

```python
name = "fake-model"
```

- `name = "fake-model"`: a class-level value `name` shared by all objects of the class: the text `'fake-model'`.

```python
def __init__(
    self,
    *,
    delay_seconds: float = 0.0,
    error_rate: float = 0.0,
    max_rps: float = 0.0,
    seed: int = 1,
    sleep: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.monotonic,
) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delay_seconds`, type `float`, optional (default `0.0`). Must be passed by name.
  - `error_rate`, type `float`, optional (default `0.0`). Must be passed by name.
  - `max_rps`, type `float`, optional (default `0.0`). Must be passed by name.
  - `seed`, type `int`, optional (default `1`). Must be passed by name.
  - `sleep`, type `Callable[[float], None]`, optional (default `time.sleep`). Must be passed by name.
  - `clock`, type `Callable[[], float]`, optional (default `time.monotonic`). Must be passed by name.
- Gives back a value of type `None`.

```python
self._delay = delay_seconds
self._error_rate = error_rate
self._max_rps = max_rps
self._rng = random.Random(seed)
self._sleep = sleep
self._clock = clock
```

- `self._delay = delay_seconds`: stores the value of `delay_seconds` in `self._delay`.
- `self._error_rate = error_rate`: stores the value of `error_rate` in `self._error_rate`.
- `self._max_rps = max_rps`: stores the value of `max_rps` in `self._max_rps`.
- `self._rng = random.Random(seed)`: stores the result of calling `random.Random(seed)`, which makes a random number generator; the same seed gives the same sequence in `self._rng`.
- `self._sleep = sleep`: stores the value of `sleep` in `self._sleep`.
- `self._clock = clock`: stores the value of `clock` in `self._clock`.

```python
self._lock = threading.Lock()
self._tokens = max_rps
self._refilled = clock()
self.calls = 0
self.rate_limited = 0
self.injected_errors = 0
```

- `self._lock = threading.Lock()`: stores the result of calling `threading.Lock()`, which makes a `Lock` object in `self._lock`.
- `self._tokens = max_rps`: stores the value of `max_rps` in `self._tokens`.
- `self._refilled = clock()`: stores the result of calling `clock()` in `self._refilled`.
- `self.calls = 0`: stores the number `0` in `self.calls`.
- `self.rate_limited = 0`: stores the number `0` in `self.rate_limited`.
- `self.injected_errors = 0`: stores the number `0` in `self.injected_errors`.

```python
def _admit(self) -> None:
```

- Defines the method `_admit`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
with self._lock:
```

- Opens `self._lock` for the indented lines, and releases it when they end (even after an error).

```python
self.calls += 1
```

- `self.calls += 1`: adds `1` to `self.calls` and keeps the result there.

```python
if self._max_rps > 0:
```

- Checks whether `self._max_rps` is greater than `0`. If so, the indented lines run.

```python
now = self._clock()
self._tokens = min(self._max_rps, self._tokens + (now - self._refilled) * self._max_rps)
self._refilled = now
```

- `now = self._clock()`: stores the result of calling `self._clock()` in `now`.
- `self._tokens = min(self._max_rps, self._tokens + (now - self._refil...`: stores the result of calling `min(self._max_rps, self._tokens + (now - self._refilled) * self._max_rps)`, which picks the smallest of `self._max_rps`, `self._tokens + (now - self._refilled) * self._max_rps` in `self._tokens`.
- `self._refilled = now`: stores the value of `now` in `self._refilled`.

```python
if self._tokens < 1:
```

- Checks whether `self._tokens` is less than `1`. If so, the indented lines run.

```python
self.rate_limited += 1
raise RetryableModelError("rate limited (429)")
```

- `self.rate_limited += 1`: adds `1` to `self.rate_limited` and keeps the result there.
- `raise RetryableModelError("rate limited (429)")`: stops with an error of kind `RetryableModelError` with the message `"rate limited (429)"`. Whoever called this code must handle it or the program stops.

```python
self._tokens -= 1
```

- `self._tokens -= 1`: subtracts `1` from `self._tokens` and keeps the result there.

```python
if self._error_rate > 0 and self._rng.random() < self._error_rate:
```

- Checks whether `self._error_rate` is greater than `0` and `self._rng.random()` is less than `self._error_rate`. If so, the indented lines run.

```python
self.injected_errors += 1
raise RetryableModelError("server error (503)")
```

- `self.injected_errors += 1`: adds `1` to `self.injected_errors` and keeps the result there.
- `raise RetryableModelError("server error (503)")`: stops with an error of kind `RetryableModelError` with the message `"server error (503)"`. Whoever called this code must handle it or the program stops.

```python
def complete(self, system: str, user: str, prompt_version: str) -> ModelReply:
```

- Defines the method `complete`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `system`, type `str`.
  - `user`, type `str`.
  - `prompt_version`, type `str`.
- Gives back a value of type `ModelReply`.

```python
"""Wait for the delay, then answer; raises `RetryableModelError` over the rate limit or on an injected error."""
```

- The docstring (documentation kept with the code) says: *Wait for the delay, then answer; raises `RetryableModelError` over the rate limit or on an injected error.*

```python
self._admit()
```

- `self._admit()`: calling `self._admit()`.

```python
if self._delay:
```

- Checks whether `self._delay` is truthy. If so, the indented lines run.

```python
self._sleep(self._delay)
```

- `self._sleep(self._delay)`: calling `self._sleep(self._delay)`.

```python
text = "not a ticket" if POISON_MARKER in user else self._ticket(user)
return ModelReply(text, self.name, math.ceil((len(system) + len(user)) / 4), math.ceil(len(text) / 4))
```

- `text = "not a ticket" if POISON_MARKER in user else self._ticket(user)`: stores `"not a ticket"` when `POISON_MARKER` is among `user`, otherwise `self._ticket(user)` in `text`.
- `return ModelReply(text, self.name, math.ceil((len(system) + len(use...`: ends the function and gives back the result of calling `ModelReply(text, self.name, math.ceil((len(system) + len(user)) / 4), math.ceil(len(tex...`, which is this repository's own `ModelReply` (in `src/inbox_worker/application/ports.py`): the model's text and what the call used.

```python
@staticmethod
def _ticket(email: str) -> str:
```

- Defines the method `_ticket`.
- `@staticmethod`: a method of the class that does not receive an object
- Parameters:
  - `email`, type `str`.
- Gives back a value of type `str`.

```python
lowered = email.lower()
```

- `lowered = email.lower()`: stores the result of calling `email.lower()`, which makes `email` lowercase in `lowered`.

```python
if "cancel" in lowered:
```

- Checks whether `"cancel"` is among `lowered`. If so, the indented lines run.

```python
intent, action = "cancel", "cancel_order"
```

- `intent, action = "cancel", "cancel_order"`: unpacks a tuple of 2 items into the names `intent`, `action`, one item each.

```python
elif "refund" in lowered or "money back" in lowered:
```

- Otherwise, checks whether `"refund"` is among `lowered` or `"money back"` is among `lowered`. If so, the indented lines run.

```python
intent, action = "refund", "issue_refund"
```

- `intent, action = "refund", "issue_refund"`: unpacks a tuple of 2 items into the names `intent`, `action`, one item each.

```python
elif "where" in lowered or "tracking" in lowered:
```

- Otherwise, checks whether `"where"` is among `lowered` or `"tracking"` is among `lowered`. If so, the indented lines run.

```python
intent, action = "order_status", "send_tracking"
```

- `intent, action = "order_status", "send_tracking"`: unpacks a tuple of 2 items into the names `intent`, `action`, one item each.

```python
else:
```

- Runs when none of the conditions above held.

```python
intent, action = "other", "none"
```

- `intent, action = "other", "none"`: unpacks a tuple of 2 items into the names `intent`, `action`, one item each.

```python
found = _ORDER.search(email)
sentiment = (
    "negative" if any(word in lowered for word in ("furious", "unacceptable", "terrible")) else "neutral"
)
return json.dumps(
    {
        "intent": intent,
        "order_number": found.group(0) if found else None,
        "sentiment": sentiment,
        "requested_action": action,
    }
)
```

- `found = _ORDER.search(email)`: stores the result of calling `_ORDER.search(email)`, which looks for the pattern anywhere in the text in `found`.
- `sentiment = ( "negative" if any(word in lowered for word in ("furio...`: stores `"negative"` when `any(word in lowered for word in ("furious", "unacceptable", "terrible"))` is true (the call is true if at least one item of `(word in lowered for word in ("furious", "unacceptable", "terrible"))` is true), otherwise `"neutral"` in `sentiment`.
- `return json.dumps( { "intent": intent, "order_number": found.group(...`: ends the function and gives back the result of calling `json.dumps( { "intent": intent, "order_number": found.group(0) if found else None, "sen...`, which turns `{ "intent": intent, "order_number": found.group(0) if found else None, "sentiment": sen...` into JSON text.

#### `src/inbox_worker/infrastructure/logging.py`

```python
"""Structured logging: one logfmt line per event. Prompt and completion text is never logged at INFO."""
```

- The docstring (documentation kept with the code) says: *Structured logging: one logfmt line per event. Prompt and completion text is never logged at INFO.*

```python
from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any, TextIO
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import logging`: makes the module `logging` available (the standard library's logging system).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`UTC`: the UTC time zone.) (`datetime`: the date-and-time type.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Any`: the type hint meaning 'anything'.) (`TextIO`: a name provided by that module.)

```python
def _quote(value: object) -> str:
```

- Defines the function `_quote`.
- Parameters:
  - `value`, type `object`.
- Gives back a value of type `str`.

```python
text = str(value)
return json.dumps(text) if not text or any(char in text for char in ' ="\n') else text
```

- `text = str(value)`: stores the result of calling `str(value)`, which turns `value` into text in `text`.
- `return json.dumps(text) if not text or any(char in text for char in...`: ends the function and gives back `json.dumps(text)` when it is not the case that `text` is truthy (not `None`, `False`, zero or empty) or `any(char in text for char in ' ="\n')` is true (the call is true if at least one item of `(char in text for char in ' ="\n')` is true), otherwise `text`.

```python
class LogfmtFormatter(logging.Formatter):
```

- Defines the class `LogfmtFormatter`.
- It extends `logging.Formatter` (it starts with all of that class's methods and may add or replace some).

```python
"""Format a log record as one logfmt line, with the record's extra fields as key=value pairs."""
```

- The docstring (documentation kept with the code) says: *Format a log record as one logfmt line, with the record's extra fields as key=value pairs.*

```python
def format(self, record: logging.LogRecord) -> str:
```

- Defines the method `format`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `record`, type `logging.LogRecord`.
- Gives back a value of type `str`.

```python
timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")
parts = [
    f"ts={timestamp}",
    f"level={record.levelname}",
    f"logger={record.name}",
    f"msg={_quote(record.getMessage())}",
]
parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())
```

- `timestamp = datetime.fromtimestamp(record.created, tz=UTC).isoforma...`: stores the result of calling `datetime.fromtimestamp(record.created, tz=UTC).isoformat(timespec="milliseconds")`, which writes the date or time as ISO text The named values are `timespec`. in `timestamp`.
- `parts = [ f"ts={timestamp}", f"level={record.levelname}", f"logger=...`: stores a new list holding 4 items in `parts`.
- `parts.extend(f"{key}={_quote(value)}" for key, value in getattr(rec...`: calling `parts.extend(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).i...`, which adds every item of `(f"{key}={_quote(value)}" for key, value in getattr(record, "fields", {}).items())` to the end of `parts`.

```python
if record.exc_info:
```

- Checks whether `record.exc_info` is truthy. If so, the indented lines run.

```python
parts.append(f"exc={_quote(self.formatException(record.exc_info))}")
```

- `parts.append(f"exc={_quote(self.formatException(record.exc_info))}")`: calling `parts.append(f"exc={_quote(self.formatException(record.exc_info))}")`, which adds `f"exc={_quote(self.formatException(record.exc_info))}"` to the end of `parts`.

```python
return " ".join(parts)
```

- `return " ".join(parts)`: ends the function and gives back the result of calling `" ".join(parts)`, which glues the items of `parts` together with `" "` between them.

```python
def fields(**values: Any) -> dict[str, Any]:
```

- Defines the function `fields`.
- Parameters:
  - `**values`: collects extra named arguments in a dict.
- Gives back a value of type `dict[str, Any]`.

```python
"""Use as `logger.info("message", extra=fields(order_id=...))` to attach key=value pairs."""
```

- The docstring (documentation kept with the code) says: *Use as `logger.info("message", extra=fields(order_id=...))` to attach key=value pairs.*

```python
return {"fields": values}
```

- `return {"fields": values}`: ends the function and gives back a new dict with 1 entries.

```python
def configure_logging(level: str, stream: TextIO | None = None) -> None:
```

- Defines the function `configure_logging`.
- Parameters:
  - `level`, type `str`.
  - `stream`, type `TextIO | None`, optional (default `None`).
- Gives back a value of type `None`.

```python
"""Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice."""
```

- The docstring (documentation kept with the code) says: *Send every log record to `stream` (stderr by default) as logfmt. Safe to call twice.*

```python
handler = logging.StreamHandler(stream or sys.stderr)
handler.setFormatter(LogfmtFormatter())
root = logging.getLogger()
root.handlers[:] = [handler]
root.setLevel(level)
```

- `handler = logging.StreamHandler(stream or sys.stderr)`: stores the result of calling `logging.StreamHandler(stream or sys.stderr)`, which makes a `StreamHandler` object from `stream or sys.stderr` in `handler`.
- `handler.setFormatter(LogfmtFormatter())`: calling `handler.setFormatter(LogfmtFormatter())`.
- `root = logging.getLogger()`: stores the result of calling `logging.getLogger()`, which gets the logger named its argument in `root`.
- `root.handlers[:] = [handler]`: stores a new list holding 1 items in the slot `root.handlers[:]`.
- `root.setLevel(level)`: calling `root.setLevel(level)`.

```python
for noisy in ("httpx", "httpcore", "anthropic", "uvicorn.access"):
```

- Repeats the indented lines once for each item of `("httpx", "httpcore", "anthropic", "uvicorn.access")`, naming the current item `noisy`.

```python
logging.getLogger(noisy).setLevel(max(logging.getLevelName(level), logging.WARNING))
```

- `logging.getLogger(noisy).setLevel(max(logging.getLevelName(level), ...`: calling `logging.getLogger(noisy).setLevel(max(logging.getLevelName(level), logging.WARNING))`.

#### `src/inbox_worker/infrastructure/postgres.py`

```python
"""PostgreSQL adapters: the queue (rows claimed with SKIP LOCKED), the effects store, the outbox and the report queries."""
```

- The docstring (documentation kept with the code) says: *PostgreSQL adapters: the queue (rows claimed with SKIP LOCKED), the effects store, the outbox and the report queries.*

```python
from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

import psycopg
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import hashlib`: makes the module `hashlib` available (hash functions such as SHA-256).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)
- `from datetime import ...`: takes names from `datetime` (dates, times and time spans). (`datetime`: the date-and-time type.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `import psycopg`: makes the module `psycopg` available (the PostgreSQL driver).

```python
from psycopg import errors
from psycopg_pool import ConnectionPool

from inbox_worker.application.outbox import DuplicateSendError
from inbox_worker.application.ports import Delivery
from inbox_worker.domain.ticket import Ticket

SCRIPTS = ("001_schema.sql", "002_seed.sql")
```

- `from psycopg import ...`: takes names from `psycopg` (the PostgreSQL driver). (`errors`: a name provided by that module.)
- `from psycopg_pool import ...`: takes names from `psycopg_pool` (a connection pool for psycopg). (`ConnectionPool`: a pool of database connections that are opened once and lent out.)
- `from inbox_worker.application.outbox import ...`: takes names from `inbox_worker.application.outbox`, this repository's own code. (`DuplicateSendError`: The mail gateway has already sent this event's acknowledgment.)
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`Delivery`: One queue message: a delivery of an event.)
- `from inbox_worker.domain.ticket import ...`: takes names from `inbox_worker.domain.ticket`, this repository's own code. (`Ticket`: What the customer wants, about which order, in what mood, and the action it asks for.)
- `SCRIPTS = ("001_schema.sql", "002_seed.sql")`: stores a tuple of 2 items in `SCRIPTS`.

```python
class Database:
```

- Defines the class `Database`.

```python
"""A small connection pool over one database URL."""
```

- The docstring (documentation kept with the code) says: *A small connection pool over one database URL.*

```python
def __init__(self, url: str, max_connections: int = 16) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `url`, type `str`.
  - `max_connections`, type `int`, optional (default `16`).
- Gives back a value of type `None`.

```python
self._pool = ConnectionPool(url, min_size=1, max_size=max_connections, open=True, kwargs={"autocommit": True})
```

- `self._pool = ConnectionPool(url, min_size=1, max_size=max_connectio...`: stores the result of calling `ConnectionPool(url, min_size=1, max_size=max_connections, open=True, kwargs={"autocommi...`, which makes a `ConnectionPool` object from `url` with the named values `min_size`, `max_size`, `open`, `kwargs` in `self._pool`.

```python
def connection(self) -> psycopg.Connection:
```

- Defines the method `connection`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `psycopg.Connection`.

```python
"""Borrow a connection (autocommit: one statement is one transaction and one round trip). Wrap several
statements that must happen together in `with connection.transaction():`."""
```

- The docstring (documentation kept with the code) says: *Borrow a connection (autocommit: one statement is one transaction and one round trip). Wrap several statements that must happen together in `with connection.transaction():`.*

```python
return self._pool.connection()  # type: ignore[return-value]
```

- `return self._pool.connection()`: ends the function and gives back the result of calling `self._pool.connection()`, which is this repository's own `connection` (in `src/inbox_worker/infrastructure/postgres.py`): borrow a connection (autocommit: one statement is one transaction and one round trip).

```python
def close(self) -> None:
```

- Defines the method `close`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
"""Close the pool."""
```

- The docstring (documentation kept with the code) says: *Close the pool.*

```python
self._pool.close()
```

- `self._pool.close()`: calling `self._pool.close()`, which is this repository's own `close` (in `src/inbox_worker/infrastructure/postgres.py`): close the pool.

```python
def ping(self) -> bool:
```

- Defines the method `ping`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `bool`.

```python
"""True when a trivial query works."""
```

- The docstring (documentation kept with the code) says: *True when a trivial query works.*

```python
with self.connection() as connection:
```

- `self.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
return connection.execute("SELECT 1").fetchone() == (1,)
```

- `return connection.execute("SELECT 1").fetchone() == (1,)`: ends the function and gives back whether `connection.execute("SELECT 1").fetchone()` equals `(1,)`.

```python
def apply_scripts(database: Database, sql_dir: Path) -> list[str]:
```

- Defines the function `apply_scripts`.
- Parameters:
  - `database`, type `Database`.
  - `sql_dir`, type `Path`.
- Gives back a value of type `list[str]`.

```python
"""Drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran."""
```

- The docstring (documentation kept with the code) says: *Drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran.*

```python
ran = []
```

- `ran = []`: stores a new list (empty) in `ran`.

```python
with database.connection() as connection:
```

- `database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
connection.execute("DROP SCHEMA public CASCADE")
connection.execute("CREATE SCHEMA public")
```

- `connection.execute("DROP SCHEMA public CASCADE")`: calling `connection.execute("DROP SCHEMA public CASCADE")`, which sends the SQL statement `"DROP SCHEMA public CASCADE"` to the database.
- `connection.execute("CREATE SCHEMA public")`: calling `connection.execute("CREATE SCHEMA public")`, which sends the SQL statement `"CREATE SCHEMA public"` to the database.

```python
for name in SCRIPTS:
```

- Repeats the indented lines once for each item of `SCRIPTS`, naming the current item `name`.

```python
connection.execute((sql_dir / name).read_text(encoding="utf-8"))
ran.append(name)
```

- `connection.execute((sql_dir / name).read_text(encoding="utf-8"))`: calling `connection.execute((sql_dir / name).read_text(encoding="utf-8"))`, which sends the SQL statement `(sql_dir / name).read_text(encoding="utf-8")` to the database.
- `ran.append(name)`: calling `ran.append(name)`, which adds `name` to the end of `ran`.

```python
return ran
```

- `return ran`: ends the function and gives back the value of `ran`.

```python
def reset_tables(database: Database, sql_dir: Path) -> None:
```

- Defines the function `reset_tables`.
- Parameters:
  - `database`, type `Database`.
  - `sql_dir`, type `Path`.
- Gives back a value of type `None`.

```python
"""Empty every table (sql/reset.sql)."""
```

- The docstring (documentation kept with the code) says: *Empty every table (sql/reset.sql).*

```python
with database.connection() as connection:
```

- `database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
connection.execute((sql_dir / "reset.sql").read_text(encoding="utf-8"))
```

- `connection.execute((sql_dir / "reset.sql").read_text(encoding="utf-...`: calling `connection.execute((sql_dir / "reset.sql").read_text(encoding="utf-8"))`, which sends the SQL statement `(sql_dir / "reset.sql").read_text(encoding="utf-8")` to the database.

```python
class PostgresQueue:
```

- Defines the class `PostgresQueue`.

```python
"""The delivery queue."""
```

- The docstring (documentation kept with the code) says: *The delivery queue.*

```python
def __init__(self, database: Database) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `database`, type `Database`.
- Gives back a value of type `None`.

```python
self._database = database
```

- `self._database = database`: stores the value of `database` in `self._database`.

```python
def put(self, event_id: str, payload: str) -> int:
```

- Defines the method `put`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
  - `payload`, type `str`.
- Gives back a value of type `int`.

```python
"""Insert one delivery."""
```

- The docstring (documentation kept with the code) says: *Insert one delivery.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
row = connection.execute(
    "INSERT INTO deliveries (event_id, payload) VALUES (%s, %s) RETURNING delivery_id", (event_id, payload)
).fetchone()
```

- `row = connection.execute( "INSERT INTO deliveries (event_id, payloa...`: stores the result of calling `connection.execute( "INSERT INTO deliveries (event_id, payload) VALUES (%s, %s) RETURNI...`, which takes the next row of the result in `row`.

```python
return int(row[0]) if row else 0
```

- `return int(row[0]) if row else 0`: ends the function and gives back `int(row[0])` when `row` is truthy (not `None`, `False`, zero or empty), otherwise `0`.

```python
def put_many(self, items: Sequence[tuple[str, str]]) -> None:
```

- Defines the method `put_many`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `items`, type `Sequence[tuple[str, str]]`.
- Gives back a value of type `None`.

```python
"""Insert many deliveries in one transaction (loading the sample events)."""
```

- The docstring (documentation kept with the code) says: *Insert many deliveries in one transaction (loading the sample events).*

```python
with self._database.connection() as connection, connection.transaction(), connection.cursor() as cursor:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.
- `connection.transaction()`: uses a database transaction for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.
- Opens `connection.cursor()` as `cursor` for the indented lines, and cleans it up when they end (even after an error).

```python
cursor.executemany("INSERT INTO deliveries (event_id, payload) VALUES (%s, %s)", list(items))
```

- `cursor.executemany("INSERT INTO deliveries (event_id, payload) VALU...`: calling `cursor.executemany("INSERT INTO deliveries (event_id, payload) VALUES (%s, %s)", list(i...`, which runs one SQL statement once for each row of parameters.

```python
def claim(self, limit: int, lease_seconds: float) -> Sequence[Delivery]:
```

- Defines the method `claim`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`.
  - `lease_seconds`, type `float`.
- Gives back a value of type `Sequence[Delivery]`.

```python
"""Claim ready deliveries; an expired claim is handed out again."""
```

- The docstring (documentation kept with the code) says: *Claim ready deliveries; an expired claim is handed out again.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
rows = connection.execute(
    """
    WITH ready AS (
        SELECT delivery_id FROM deliveries
        WHERE (status = 'queued' AND available_at <= now()) OR (status = 'processing' AND locked_until < now())
        ORDER BY available_at, delivery_id
        LIMIT %s FOR UPDATE SKIP LOCKED)
    UPDATE deliveries d SET status = 'processing', attempts = d.attempts + 1,
           locked_until = now() + make_interval(secs => %s)
    FROM ready WHERE d.delivery_id = ready.delivery_id
    RETURNING d.delivery_id, d.event_id, d.payload, d.received_at, d.attempts
    """,
    (limit, lease_seconds),
).fetchall()
```

- `rows = connection.execute( """ WITH ready AS ( SELECT delivery_id F...`: stores the result of calling `connection.execute( """ WITH ready AS ( SELECT delivery_id FROM deliveries WHERE (statu...`, which takes all remaining rows of the result in `rows`.

```python
return [Delivery(*row) for row in rows]
```

- `return [Delivery(*row) for row in rows]`: ends the function and gives back a list built by running `Delivery(*row)` for each `row` in `rows`.

```python
def ack(self, delivery_id: int) -> None:
```

- Defines the method `ack`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery_id`, type `int`.
- Gives back a value of type `None`.

```python
"""Finish a delivery."""
```

- The docstring (documentation kept with the code) says: *Finish a delivery.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
connection.execute(
    "UPDATE deliveries SET status = 'done', locked_until = NULL WHERE delivery_id = %s", (delivery_id,)
)
```

- `connection.execute( "UPDATE deliveries SET status = 'done', locked_...`: calling `connection.execute( "UPDATE deliveries SET status = 'done', locked_until = NULL WHERE d...`, which sends the SQL statement `"UPDATE deliveries SET status = 'done', locked_until = NULL WHERE delivery_id = %s"` to the database.

```python
def retry(self, delivery_id: int, delay_seconds: float, error: str) -> None:
```

- Defines the method `retry`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery_id`, type `int`.
  - `delay_seconds`, type `float`.
  - `error`, type `str`.
- Gives back a value of type `None`.

```python
"""Release the claim and make the delivery available after a delay."""
```

- The docstring (documentation kept with the code) says: *Release the claim and make the delivery available after a delay.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
connection.execute(
    "UPDATE deliveries SET status = 'queued', locked_until = NULL, last_error = %s, "
    "available_at = now() + make_interval(secs => %s) WHERE delivery_id = %s",
    (error, delay_seconds, delivery_id),
)
```

- `connection.execute( "UPDATE deliveries SET status = 'queued', locke...`: calling `connection.execute( "UPDATE deliveries SET status = 'queued', locked_until = NULL, last...`, which sends the SQL statement `"UPDATE deliveries SET status = 'queued', locked_until = NULL, last_error = %s, " "avai...` to the database.

```python
def dead_letter(self, delivery: Delivery, reason: str, error: str) -> None:
```

- Defines the method `dead_letter`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `delivery`, type `Delivery`.
  - `reason`, type `str`.
  - `error`, type `str`.
- Gives back a value of type `None`.

```python
"""Park the delivery with what a person needs to act; both writes are one transaction."""
```

- The docstring (documentation kept with the code) says: *Park the delivery with what a person needs to act; both writes are one transaction.*

```python
digest = hashlib.sha256(delivery.payload.encode("utf-8", "replace")).hexdigest()[:12]
```

- `digest = hashlib.sha256(delivery.payload.encode("utf-8", "replace")...`: stores the item `hashlib.sha256(delivery.payload.encode("utf-8", "replace")).hexdigest()[:12]` in `digest`.

```python
with self._database.connection() as connection, connection.transaction():
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.
- `connection.transaction()`: uses a database transaction for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
connection.execute(
    "INSERT INTO dead_letters (event_id, reason, attempts, last_error, payload_hash, payload) VALUES (%s, %s, %s, %s, %s, %s)",
    (delivery.event_id, reason, delivery.attempts, error, digest, delivery.payload),
)
connection.execute(
    "UPDATE deliveries SET status = 'dead', locked_until = NULL, last_error = %s WHERE delivery_id = %s",
    (error, delivery.delivery_id),
)
```

- `connection.execute( "INSERT INTO dead_letters (event_id, reason, at...`: calling `connection.execute( "INSERT INTO dead_letters (event_id, reason, attempts, last_error, ...`, which sends the SQL statement `"INSERT INTO dead_letters (event_id, reason, attempts, last_error, payload_hash, payloa...` to the database.
- `connection.execute( "UPDATE deliveries SET status = 'dead', locked_...`: calling `connection.execute( "UPDATE deliveries SET status = 'dead', locked_until = NULL, last_e...`, which sends the SQL statement `"UPDATE deliveries SET status = 'dead', locked_until = NULL, last_error = %s WHERE deli...` to the database.

```python
def depth(self) -> int:
```

- Defines the method `depth`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `int`.

```python
"""Deliveries that are queued or in flight."""
```

- The docstring (documentation kept with the code) says: *Deliveries that are queued or in flight.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
row = connection.execute(
    "SELECT COUNT(*) FROM deliveries WHERE status IN ('queued', 'processing')"
).fetchone()
```

- `row = connection.execute( "SELECT COUNT(*) FROM deliveries WHERE st...`: stores the result of calling `connection.execute( "SELECT COUNT(*) FROM deliveries WHERE status IN ('queued', 'proces...`, which takes the next row of the result in `row`.

```python
return int(row[0]) if row else 0
```

- `return int(row[0]) if row else 0`: ends the function and gives back `int(row[0])` when `row` is truthy (not `None`, `False`, zero or empty), otherwise `0`.

```python
def redrive(self, dead_id: int) -> int | None:
```

- Defines the method `redrive`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `dead_id`, type `int`.
- Gives back a value of type `int | None`.

```python
"""Put a dead letter's payload back on the queue as a new delivery and mark it redriven; None if unknown or done."""
```

- The docstring (documentation kept with the code) says: *Put a dead letter's payload back on the queue as a new delivery and mark it redriven; None if unknown or done.*

```python
with self._database.connection() as connection, connection.transaction():
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.
- `connection.transaction()`: uses a database transaction for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
row = connection.execute(
    "SELECT event_id, payload FROM dead_letters WHERE dead_id = %s AND redriven_at IS NULL FOR UPDATE",
    (dead_id,),
).fetchone()
```

- `row = connection.execute( "SELECT event_id, payload FROM dead_lette...`: stores the result of calling `connection.execute( "SELECT event_id, payload FROM dead_letters WHERE dead_id = %s AND ...`, which takes the next row of the result in `row`.

```python
if row is None:
```

- Checks whether `row` is nothing (`None`). If so, the indented lines run.

```python
return None
```

- `return None`: ends the function and gives back nothing (`None`).

```python
new = connection.execute(
    "INSERT INTO deliveries (event_id, payload) VALUES (%s, %s) RETURNING delivery_id", row
).fetchone()
connection.execute("UPDATE dead_letters SET redriven_at = now() WHERE dead_id = %s", (dead_id,))
```

- `new = connection.execute( "INSERT INTO deliveries (event_id, payloa...`: stores the result of calling `connection.execute( "INSERT INTO deliveries (event_id, payload) VALUES (%s, %s) RETURNI...`, which takes the next row of the result in `new`.
- `connection.execute("UPDATE dead_letters SET redriven_at = now() WHE...`: calling `connection.execute("UPDATE dead_letters SET redriven_at = now() WHERE dead_id = %s", (d...`, which sends the SQL statement `"UPDATE dead_letters SET redriven_at = now() WHERE dead_id = %s"` to the database.

```python
return int(new[0]) if new else None
```

- `return int(new[0]) if new else None`: ends the function and gives back `int(new[0])` when `new` is truthy (not `None`, `False`, zero or empty), otherwise `None`.

```python
class PostgresEffects:
```

- Defines the class `PostgresEffects`.

```python
"""The processed mark, the ticket and the outbox row."""
```

- The docstring (documentation kept with the code) says: *The processed mark, the ticket and the outbox row.*

```python
def __init__(self, database: Database) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `database`, type `Database`.
- Gives back a value of type `None`.

```python
self._database = database
```

- `self._database = database`: stores the value of `database` in `self._database`.

```python
def is_processed(self, event_id: str) -> bool:
```

- Defines the method `is_processed`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
- Gives back a value of type `bool`.

```python
"""True when the event's effects were applied (read fresh from the database every time)."""
```

- The docstring (documentation kept with the code) says: *True when the event's effects were applied (read fresh from the database every time).*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
return (
    connection.execute("SELECT 1 FROM processed_events WHERE event_id = %s", (event_id,)).fetchone()
    is not None
)
```

- `return ( connection.execute("SELECT 1 FROM processed_events WHERE e...`: ends the function and gives back whether `connection.execute("SELECT 1 FROM processed_events WHERE event_id = %s", (event_id,)).f...` is something (not `None`).

```python
def apply(self, event_id: str, ticket: Ticket) -> bool:
```

- Defines the method `apply`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
  - `ticket`, type `Ticket`.
- Gives back a value of type `bool`.

```python
"""Write the mark, the ticket and the outbox row in ONE statement (so one transaction and one round trip). The
primary key on the mark settles a race: a twin delivery that commits first leaves this statement inserting nothing."""
```

- The docstring (documentation kept with the code) says: *Write the mark, the ticket and the outbox row in ONE statement (so one transaction and one round trip). The primary key on the mark settles a race: a twin delivery that commits first leaves this statement inserting nothing.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
row = connection.execute(
    """
    WITH mark AS (
        INSERT INTO processed_events (event_id) VALUES (%(event)s) ON CONFLICT (event_id) DO NOTHING RETURNING event_id),
    made AS (
        INSERT INTO tickets (event_id, intent, order_number, sentiment, requested_action)
        SELECT event_id, %(intent)s, %(order)s, %(sentiment)s, %(action)s FROM mark RETURNING 1),
    queued AS (
        INSERT INTO outbox (event_id, kind) SELECT event_id, 'acknowledge' FROM mark RETURNING 1)
    SELECT (SELECT COUNT(*) FROM mark), (SELECT COUNT(*) FROM made), (SELECT COUNT(*) FROM queued)
    """,
    {
        "event": event_id,
        "intent": ticket.intent,
        "order": ticket.order_number,
        "sentiment": ticket.sentiment,
        "action": ticket.requested_action,
    },
).fetchone()
```

- `row = connection.execute( """ WITH mark AS ( INSERT INTO processed_...`: stores the result of calling `connection.execute( """ WITH mark AS ( INSERT INTO processed_events (event_id) VALUES (...`, which takes the next row of the result in `row`.

```python
return bool(row and row[0] == 1)
```

- `return bool(row and row[0] == 1)`: ends the function and gives back the result of calling `bool(row and row[0] == 1)`, which turns `row and row[0] == 1` into True or False.

```python
class PostgresOutbox:
```

- Defines the class `PostgresOutbox`.

```python
"""The unsent acknowledgments."""
```

- The docstring (documentation kept with the code) says: *The unsent acknowledgments.*

```python
def __init__(self, database: Database) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `database`, type `Database`.
- Gives back a value of type `None`.

```python
self._database = database
```

- `self._database = database`: stores the value of `database` in `self._database`.

```python
def unsent(self, limit: int) -> Sequence[tuple[int, str, str]]:
```

- Defines the method `unsent`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `limit`, type `int`.
- Gives back a value of type `Sequence[tuple[int, str, str]]`.

```python
"""Oldest unsent rows."""
```

- The docstring (documentation kept with the code) says: *Oldest unsent rows.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
rows = connection.execute(
    "SELECT outbox_id, event_id, kind FROM outbox WHERE sent_at IS NULL ORDER BY outbox_id LIMIT %s",
    (limit,),
).fetchall()
```

- `rows = connection.execute( "SELECT outbox_id, event_id, kind FROM o...`: stores the result of calling `connection.execute( "SELECT outbox_id, event_id, kind FROM outbox WHERE sent_at IS NULL...`, which takes all remaining rows of the result in `rows`.

```python
return [(int(a), b, c) for a, b, c in rows]
```

- `return [(int(a), b, c) for a, b, c in rows]`: ends the function and gives back a list built by running `(int(a), b, c)` for each `a, b, c` in `rows`.

```python
def mark_sent(self, outbox_id: int) -> None:
```

- Defines the method `mark_sent`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `outbox_id`, type `int`.
- Gives back a value of type `None`.

```python
"""Record that the row was sent."""
```

- The docstring (documentation kept with the code) says: *Record that the row was sent.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
connection.execute("UPDATE outbox SET sent_at = now() WHERE outbox_id = %s", (outbox_id,))
```

- `connection.execute("UPDATE outbox SET sent_at = now() WHERE outbox_...`: calling `connection.execute("UPDATE outbox SET sent_at = now() WHERE outbox_id = %s", (outbox_id,))`, which sends the SQL statement `"UPDATE outbox SET sent_at = now() WHERE outbox_id = %s"` to the database.

```python
class FakeMailSender:
```

- Defines the class `FakeMailSender`.

```python
"""Records every send in `sent_mail`; the unique event id refuses a second send of one acknowledgment."""
```

- The docstring (documentation kept with the code) says: *Records every send in `sent_mail`; the unique event id refuses a second send of one acknowledgment.*

```python
def __init__(self, database: Database) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `database`, type `Database`.
- Gives back a value of type `None`.

```python
self._database = database
```

- `self._database = database`: stores the value of `database` in `self._database`.

```python
def send(self, event_id: str, kind: str) -> None:
```

- Defines the method `send`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `event_id`, type `str`.
  - `kind`, type `str`.
- Gives back a value of type `None`.

```python
"""Record one send."""
```

- The docstring (documentation kept with the code) says: *Record one send.*

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
connection.execute("INSERT INTO sent_mail (event_id, kind) VALUES (%s, %s)", (event_id, kind))
```

- `connection.execute("INSERT INTO sent_mail (event_id, kind) VALUES (...`: calling `connection.execute("INSERT INTO sent_mail (event_id, kind) VALUES (%s, %s)", (event_id,...`, which sends the SQL statement `"INSERT INTO sent_mail (event_id, kind) VALUES (%s, %s)"` to the database.

```python
except errors.UniqueViolation:
```

- If an error of kind `errors.UniqueViolation` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
raise DuplicateSendError(event_id) from None
```

- `raise DuplicateSendError(event_id) from None`: stops with an error of kind `DuplicateSendError` with the message `event_id`, recording `None` as the cause. Whoever called this code must handle it or the program stops.

```python
class PostgresReports:
```

- Defines the class `PostgresReports`.

```python
"""Read-only queries for the reports and the verification steps."""
```

- The docstring (documentation kept with the code) says: *Read-only queries for the reports and the verification steps.*

```python
def __init__(self, database: Database) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `database`, type `Database`.
- Gives back a value of type `None`.

```python
self._database = database
```

- `self._database = database`: stores the value of `database` in `self._database`.

```python
def _one(self, sql: str) -> int:
```

- Defines the method `_one`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `sql`, type `str`.
- Gives back a value of type `int`.

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
row = connection.execute(sql).fetchone()
```

- `row = connection.execute(sql).fetchone()`: stores the result of calling `connection.execute(sql).fetchone()`, which takes the next row of the result in `row`.

```python
return int(row[0]) if row else 0
```

- `return int(row[0]) if row else 0`: ends the function and gives back `int(row[0])` when `row` is truthy (not `None`, `False`, zero or empty), otherwise `0`.

```python
def counts(self) -> dict[str, int]:
```

- Defines the method `counts`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `dict[str, int]`.

```python
"""Rows in the tables that matter."""
```

- The docstring (documentation kept with the code) says: *Rows in the tables that matter.*

```python
return {
    "deliveries": self._one("SELECT COUNT(*) FROM deliveries"),
    "processed": self._one("SELECT COUNT(*) FROM processed_events"),
    "tickets": self._one("SELECT COUNT(*) FROM tickets"),
    "outbox": self._one("SELECT COUNT(*) FROM outbox"),
    "mails_sent": self._one("SELECT COUNT(*) FROM sent_mail"),
    "dead_letters": self._one("SELECT COUNT(*) FROM dead_letters"),
}
```

- `return { "deliveries": self._one("SELECT COUNT(*) FROM deliveries")...`: ends the function and gives back a new dict with 6 entries.

```python
def ticket_event_ids(self) -> list[str]:
```

- Defines the method `ticket_event_ids`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `list[str]`.

```python
"""Event id of every ticket (duplicates would show up twice)."""
```

- The docstring (documentation kept with the code) says: *Event id of every ticket (duplicates would show up twice).*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
return [row[0] for row in connection.execute("SELECT event_id FROM tickets ORDER BY ticket_id").fetchall()]
```

- `return [row[0] for row in connection.execute("SELECT event_id FROM ...`: ends the function and gives back a list built by running `row[0]` for each `row` in `connection.execute("SELECT event_id FROM tickets ORDER BY ticket_id").fetchall()`.

```python
def dead_events(self) -> list[tuple[int, str, str, int, str, str]]:
```

- Defines the method `dead_events`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `list[tuple[int, str, str, int, str, str]]`.

```python
"""(dead id, event id, reason, attempts, last error, payload hash) of open dead letters."""
```

- The docstring (documentation kept with the code) says: *(dead id, event id, reason, attempts, last error, payload hash) of open dead letters.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
rows = connection.execute(
    "SELECT dead_id, event_id, reason, attempts, last_error, payload_hash FROM dead_letters WHERE redriven_at IS NULL ORDER BY dead_id"
).fetchall()
```

- `rows = connection.execute( "SELECT dead_id, event_id, reason, attem...`: stores the result of calling `connection.execute( "SELECT dead_id, event_id, reason, attempts, last_error, payload_ha...`, which takes all remaining rows of the result in `rows`.

```python
return [(int(r[0]), r[1], r[2], int(r[3]), r[4], r[5]) for r in rows]
```

- `return [(int(r[0]), r[1], r[2], int(r[3]), r[4], r[5]) for r in rows]`: ends the function and gives back a list built by running `(int(r[0]), r[1], r[2], int(r[3]), r[4], r[5])` for each `r` in `rows`.

```python
def event_to_ticket_seconds(self) -> list[float]:
```

- Defines the method `event_to_ticket_seconds`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `list[float]`.

```python
"""Seconds from the first delivery of each ticketed event to its ticket."""
```

- The docstring (documentation kept with the code) says: *Seconds from the first delivery of each ticketed event to its ticket.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
rows = connection.execute(
    "SELECT EXTRACT(EPOCH FROM t.created_at - d.first_seen) FROM tickets t JOIN "
    "(SELECT event_id, MIN(received_at) AS first_seen FROM deliveries GROUP BY event_id) d USING (event_id)"
).fetchall()
```

- `rows = connection.execute( "SELECT EXTRACT(EPOCH FROM t.created_at ...`: stores the result of calling `connection.execute( "SELECT EXTRACT(EPOCH FROM t.created_at - d.first_seen) FROM ticket...`, which takes all remaining rows of the result in `rows`.

```python
return [float(row[0]) for row in rows]
```

- `return [float(row[0]) for row in rows]`: ends the function and gives back a list built by running `float(row[0])` for each `row` in `rows`.

```python
def now(self) -> datetime:
```

- Defines the method `now`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `datetime`.

```python
"""The database's clock."""
```

- The docstring (documentation kept with the code) says: *The database's clock.*

```python
with self._database.connection() as connection:
```

- `self._database.connection()`: uses a database connection for the indented lines; a transaction commits at the end or rolls back if an error leaves the block.

```python
row = connection.execute("SELECT now()").fetchone()
```

- `row = connection.execute("SELECT now()").fetchone()`: stores the result of calling `connection.execute("SELECT now()").fetchone()`, which takes the next row of the result in `row`.

```python
return row[0] if row else datetime.min
```

- `return row[0] if row else datetime.min`: ends the function and gives back `row[0]` when `row` is truthy (not `None`, `False`, zero or empty), otherwise `datetime.min`.

#### `src/inbox_worker/infrastructure/prompt_file.py`

```python
"""Prompts as files: a two-fence header (version, owner), then the prompt text."""
```

- The docstring (documentation kept with the code) says: *Prompts as files: a two-fence header (version, owner), then the prompt text.*

```python
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`NamedTuple`: a tuple whose slots have names.)

```python
class PromptFileError(ValueError):
```

- Defines the class `PromptFileError`.
- It extends `ValueError`: it is a kind of error that can be raised and caught.

```python
"""A prompt file does not have the two-fence header with a version and an owner."""
```

- The docstring (documentation kept with the code) says: *A prompt file does not have the two-fence header with a version and an owner.*

```python
class PromptFile(NamedTuple):
```

- Defines the class `PromptFile`.
- It extends `NamedTuple` (it starts with all of that class's methods and may add or replace some).

```python
"""A versioned prompt."""
```

- The docstring (documentation kept with the code) says: *A versioned prompt.*

```python
version: str
owner: str
text: str
```

- `version: str`: a field named `version` of type `str`, no default (must be given).
- `owner: str`: a field named `owner` of type `str`, no default (must be given).
- `text: str`: a field named `text` of type `str`, no default (must be given).

```python
def read_prompt(path: Path) -> PromptFile:
```

- Defines the function `read_prompt`.
- Parameters:
  - `path`, type `Path`.
- Gives back a value of type `PromptFile`.

```python
"""Read `---`, header lines, `---`, then the prompt text; both fences are required."""
```

- The docstring (documentation kept with the code) says: *Read `---`, header lines, `---`, then the prompt text; both fences are required.*

```python
parts = path.read_text(encoding="utf-8").split("---\n", 2)
```

- `parts = path.read_text(encoding="utf-8").split("---\n", 2)`: stores the result of calling `path.read_text(encoding="utf-8").split("---\n", 2)`, which cuts `path.read_text(encoding="utf-8")` into pieces at `"---\n"` (whitespace if nothing is given) in `parts`.

```python
if len(parts) != 3 or parts[0].strip():
```

- Checks whether `len(parts)` is different from `3` or `parts[0].strip()` is true (the call removes spaces and line breaks from both ends of `parts[0]` (or the characters its argument)). If so, the indented lines run.

```python
raise PromptFileError(f"{path.name}: expected a leading '---' fence, a header and a closing '---' fence")
```

- `raise PromptFileError(f"{path.name}: expected a leading '---' fence...`: stops with an error of kind `PromptFileError` with the message `f"{path.name}: expected a leading '---' fence, a header and a closing '---' fence"`. Whoever called this code must handle it or the program stops.

```python
fields = dict(line.split(": ", 1) for line in parts[1].strip().splitlines() if ": " in line)
```

- `fields = dict(line.split(": ", 1) for line in parts[1].strip().spli...`: stores the result of calling `dict(line.split(": ", 1) for line in parts[1].strip().splitlines() if ": " in line)`, which builds a dict in `fields`.

```python
for required in ("version", "owner"):
```

- Repeats the indented lines once for each item of `("version", "owner")`, naming the current item `required`.

```python
if required not in fields:
```

- Checks whether `required` is not among `fields`. If so, the indented lines run.

```python
raise PromptFileError(f"{path.name}: header lacks {required}")
```

- `raise PromptFileError(f"{path.name}: header lacks {required}")`: stops with an error of kind `PromptFileError` with the message `f"{path.name}: header lacks {required}"`. Whoever called this code must handle it or the program stops.

```python
return PromptFile(fields["version"], fields["owner"], parts[2].strip())
```

- `return PromptFile(fields["version"], fields["owner"], parts[2].stri...`: ends the function and gives back the result of calling `PromptFile(fields["version"], fields["owner"], parts[2].strip())`, which is this repository's own `PromptFile` (in `src/inbox_worker/infrastructure/prompt_file.py`): a versioned prompt.

#### `src/inbox_worker/infrastructure/retry.py`

```python
"""Retry with exponential backoff and full jitter for calls that cross the network."""
```

- The docstring (documentation kept with the code) says: *Retry with exponential backoff and full jitter for calls that cross the network.*

```python
from __future__ import annotations

import random
import time
from collections.abc import Callable
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import random`: makes the module `random` available (random numbers (a seeded generator gives the same numbers every run)).
- `import time`: makes the module `time` available (clocks and sleeping).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Callable`: the type hint for a function value.)

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
```

- Defines the function `retry`.
- Parameters:
  - `operation`, type `Callable[[], T]`.
  - `attempts`, type `int`. Must be passed by name.
  - `base_delay_seconds`, type `float`. Must be passed by name.
  - `retry_on`, type `tuple[type[BaseException], ...]`. Must be passed by name.
  - `sleep`, type `Callable[[float], None]`, optional (default `time.sleep`). Must be passed by name.
  - `rng`, type `random.Random | None`, optional (default `None`). Must be passed by name.
  - `max_delay_seconds`, type `float`, optional (default `10.0`). Must be passed by name.
  - `on_retry`, type `Callable[[int, BaseException], None] | None`, optional (default `None`). Must be passed by name.
- Gives back a value of type `T`.

```python
"""Call `operation` up to `attempts` times, backing off after each failure in `retry_on`.

The pause after attempt n is a random value in [0, min(max_delay, base * 2**(n - 1))] (full jitter),
so many clients do not retry in step. The last failure is raised.
"""
```

- The docstring (documentation kept with the code) says: *Call `operation` up to `attempts` times, backing off after each failure in `retry_on`. The pause after attempt n is a random value in [0, min(max_delay, base * 2**(n - 1))] (full jitter), so many clients do not retry in step. The last failure is raised.*

```python
if attempts < 1:
```

- Checks whether `attempts` is less than `1`. If so, the indented lines run.

```python
raise ValueError("attempts must be at least 1")
```

- `raise ValueError("attempts must be at least 1")`: stops with an error of kind `ValueError` with the message `"attempts must be at least 1"`. Whoever called this code must handle it or the program stops.

```python
jitter = rng or random.Random()
```

- `jitter = rng or random.Random()`: stores `rng or random.Random()` (the first operand that decides the or) in `jitter`.

```python
for attempt in range(1, attempts + 1):
```

- Repeats the indented lines once for each item of `range(1, attempts + 1)`, naming the current item `attempt`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
return operation()
```

- `return operation()`: ends the function and gives back the result of calling `operation()`.

```python
except retry_on as error:
```

- If an error of kind `retry_on` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
if attempt == attempts:
```

- Checks whether `attempt` equals `attempts`. If so, the indented lines run.

```python
raise
```

- `raise`: raises the error again.

```python
if on_retry:
```

- Checks whether `on_retry` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
on_retry(attempt, error)
```

- `on_retry(attempt, error)`: calling `on_retry(attempt, error)`.

```python
sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))))
```

- `sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds *...`: calling `sleep(jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1))))`, which waits `jitter.uniform(0, min(max_delay_seconds, base_delay_seconds * 2 ** (attempt - 1)))` seconds.

```python
raise AssertionError("unreachable")  # pragma: no cover
```

- `raise AssertionError("unreachable")`: stops with an error of kind `AssertionError` with the message `"unreachable"`. Whoever called this code must handle it or the program stops.

#### `src/inbox_worker/infrastructure/settings.py`

```python
"""Configuration from the environment, validated once at startup (twelve-factor). Secrets only from here."""
```

- The docstring (documentation kept with the code) says: *Configuration from the environment, validated once at startup (twelve-factor). Secrets only from here.*

```python
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from inbox_worker.infrastructure.environment import (
    ConfigurationError,
    read_choice,
    read_float,
    read_int,
    read_optional,
    read_text,
)
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Mapping`: the type hint for a read-only dict-like collection.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from inbox_worker.infrastructure.environment import ...`: takes names from `inbox_worker.infrastructure.environment`, this repository's own code. (`ConfigurationError`: An environment variable is missing or has an unusable value.) (`read_choice`: A string variable restricted to `choices`.) (`read_float`: A float variable of at least `minimum`.) (`read_int`: An integer variable of at least `minimum`.) (`read_optional`: A string variable that may be absent or empty (for example an API key).) (`read_text`: A non-empty string variable, or `default`.)

```python
@dataclass(frozen=True, slots=True)
class Settings:
```

- Defines the class `Settings`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""Everything the programs read from the environment."""
```

- The docstring (documentation kept with the code) says: *Everything the programs read from the environment.*

```python
log_level: str
root: Path
database_url: str
webhook_secret: bytes
model_adapter: str
model_id: str
anthropic_api_key: str | None
cassette: Path
```

- `log_level: str`: a field named `log_level` of type `str`, no default (must be given).
- `root: Path`: a field named `root` of type `Path`, no default (must be given).
- `database_url: str`: a field named `database_url` of type `str`, no default (must be given).
- `webhook_secret: bytes`: a field named `webhook_secret` of type `bytes`, no default (must be given).
- `model_adapter: str`: a field named `model_adapter` of type `str`, no default (must be given).
- `model_id: str`: a field named `model_id` of type `str`, no default (must be given).
- `anthropic_api_key: str | None`: a field named `anthropic_api_key` of type `str | None`, no default (must be given).
- `cassette: Path`: a field named `cassette` of type `Path`, no default (must be given).

```python
fake_delay_seconds: float
fake_error_rate: float
fake_max_rps: float
concurrency: int
lease_seconds: float
max_attempts: int
backoff_base_seconds: float
backoff_cap_seconds: float
```

- `fake_delay_seconds: float`: a field named `fake_delay_seconds` of type `float`, no default (must be given).
- `fake_error_rate: float`: a field named `fake_error_rate` of type `float`, no default (must be given).
- `fake_max_rps: float`: a field named `fake_max_rps` of type `float`, no default (must be given).
- `concurrency: int`: a field named `concurrency` of type `int`, no default (must be given).
- `lease_seconds: float`: a field named `lease_seconds` of type `float`, no default (must be given).
- `max_attempts: int`: a field named `max_attempts` of type `int`, no default (must be given).
- `backoff_base_seconds: float`: a field named `backoff_base_seconds` of type `float`, no default (must be given).
- `backoff_cap_seconds: float`: a field named `backoff_cap_seconds` of type `float`, no default (must be given).

```python
event_deadline_seconds: float
host: str
port: int
max_webhook_bytes: int
```

- `event_deadline_seconds: float`: a field named `event_deadline_seconds` of type `float`, no default (must be given).
- `host: str`: a field named `host` of type `str`, no default (must be given).
- `port: int`: a field named `port` of type `int`, no default (must be given).
- `max_webhook_bytes: int`: a field named `max_webhook_bytes` of type `int`, no default (must be given).

```python
@classmethod
def from_environ(cls, environ: Mapping[str, str]) -> Settings:
```

- Defines the method `from_environ`.
- `@classmethod`: a method that receives the class itself as `cls`.
- Parameters:
  - `cls`: the object (or class) the method was called on.
  - `environ`, type `Mapping[str, str]`.
- Gives back a value of type `Settings`.

```python
"""Read and validate; raises `ConfigurationError` naming the first bad variable."""
```

- The docstring (documentation kept with the code) says: *Read and validate; raises `ConfigurationError` naming the first bad variable.*

```python
secret = read_text(environ, "WEBHOOK_SECRET", "unset-secret-for-tests-only-0000")
```

- `secret = read_text(environ, "WEBHOOK_SECRET", "unset-secret-for-tes...`: stores the result of calling `read_text(environ, "WEBHOOK_SECRET", "unset-secret-for-tests-only-0000")`, which reads the whole file  as text in `secret`.

```python
if len(secret) < 16:
```

- Checks whether `len(secret)` is less than `16`. If so, the indented lines run.

```python
raise ConfigurationError("WEBHOOK_SECRET must be at least 16 characters")
```

- `raise ConfigurationError("WEBHOOK_SECRET must be at least 16 charac...`: stops with an error of kind `ConfigurationError` with the message `"WEBHOOK_SECRET must be at least 16 characters"`. Whoever called this code must handle it or the program stops.

```python
user, database = read_text(environ, "POSTGRES_USER", "inbox"), read_text(environ, "POSTGRES_DB", "inbox")
password, port = (
    read_text(environ, "POSTGRES_PASSWORD", "inbox-local-only"),
    read_int(environ, "POSTGRES_PORT", 5434),
)
```

- `user, database = read_text(environ, "POSTGRES_USER", "inbox"), read...`: unpacks a tuple of 2 items into the names `user`, `database`, one item each.
- `password, port = ( read_text(environ, "POSTGRES_PASSWORD", "inbox-l...`: unpacks a tuple of 2 items into the names `password`, `port`, one item each.

```python
return cls(
    log_level=read_choice(environ, "LOG_LEVEL", "INFO", frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})),
    root=Path(read_text(environ, "PROJECT_ROOT", ".")),
    database_url=read_text(
        environ, "DATABASE_URL", f"postgresql://{user}:{password}@localhost:{port}/{database}"
    ),
    webhook_secret=secret.encode(),
    model_adapter=read_choice(environ, "MODEL_ADAPTER", "fake", frozenset({"fake", "recorded", "claude"})),
    model_id=read_text(environ, "MODEL_ID", "claude-haiku-5-5"),
    anthropic_api_key=read_optional(environ, "ANTHROPIC_API_KEY"),
    cassette=Path(read_text(environ, "CASSETTE", "tests/fixtures/cassettes/smoke-v1.json")),
    fake_delay_seconds=read_float(environ, "FAKE_MODEL_DELAY_SECONDS", 0.0),
    fake_error_rate=read_float(environ, "FAKE_MODEL_ERROR_RATE", 0.0),
    fake_max_rps=read_float(environ, "FAKE_MODEL_MAX_RPS", 0.0),
    concurrency=read_int(environ, "CONCURRENCY", 5),
    lease_seconds=read_float(environ, "LEASE_SECONDS", 30.0, 0.1),
    max_attempts=read_int(environ, "MAX_ATTEMPTS", 5),
    backoff_base_seconds=read_float(environ, "BACKOFF_BASE_SECONDS", 0.5),
    backoff_cap_seconds=read_float(environ, "BACKOFF_CAP_SECONDS", 30.0),
    event_deadline_seconds=read_float(environ, "EVENT_DEADLINE_SECONDS", 300.0, 1.0),
    host=read_text(environ, "HOST", "127.0.0.1"),
    port=read_int(environ, "WEBHOOK_PORT", 8090),
    max_webhook_bytes=read_int(environ, "MAX_WEBHOOK_BYTES", 1_000_000),
)
```

- `return cls( log_level=read_choice(environ, "LOG_LEVEL", "INFO", fro...`: ends the function and gives back the result of calling `cls( log_level=read_choice(environ, "LOG_LEVEL", "INFO", frozenset({"DEBUG", "INFO", "W...` The named values are `log_level`, `root`, `database_url`, `webhook_secret`, `model_adapter`, `model_id`, `anthropic_api_key`, `cassette`, `fake_delay_seconds`, `fake_error_rate`, `fake_max_rps`, `concurrency`, `lease_seconds`, `max_attempts`, `backoff_base_seconds`, `backoff_cap_seconds`, `event_deadline_seconds`, `host`, `port`, `max_webhook_bytes`..

#### `src/inbox_worker/infrastructure/shutdown.py`

```python
"""Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work."""
```

- The docstring (documentation kept with the code) says: *Graceful shutdown: SIGINT and SIGTERM set a flag the work loops check between units of work.*

```python
from __future__ import annotations

import signal
import threading
from types import FrameType
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import signal`: makes the module `signal` available (operating-system signals such as SIGTERM).
- `import threading`: makes the module `threading` available (threads, locks and events).
- `from types import ...`: takes names from `types` (names for built-in types such as a module or a function). (`FrameType`: a name provided by that module.)

```python
class ShutdownSignal:
```

- Defines the class `ShutdownSignal`.

```python
"""A flag that SIGINT and SIGTERM set, which work loops check between units of work."""
```

- The docstring (documentation kept with the code) says: *A flag that SIGINT and SIGTERM set, which work loops check between units of work.*

```python
def __init__(self) -> None:
```

- Defines the constructor `__init__`, which runs when an object of the class is made.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
self._requested = threading.Event()
```

- `self._requested = threading.Event()`: stores the result of calling `threading.Event()`, which makes a `Event` object in `self._requested`.

```python
def install(self) -> None:
```

- Defines the method `install`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
"""Route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close."""
```

- The docstring (documentation kept with the code) says: *Route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close.*

```python
for number in (signal.SIGINT, signal.SIGTERM):
```

- Repeats the indented lines once for each item of `(signal.SIGINT, signal.SIGTERM)`, naming the current item `number`.

```python
signal.signal(number, self._handle)
```

- `signal.signal(number, self._handle)`: calling `signal.signal(number, self._handle)`, which installs a handler for an operating-system signal.

```python
def _handle(self, _number: int, _frame: FrameType | None) -> None:
```

- Defines the method `_handle`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `_number`, type `int`.
  - `_frame`, type `FrameType | None`.
- Gives back a value of type `None`.

```python
self.request()
```

- `self.request()`: calling `self.request()`, which is this repository's own `request` (in `src/inbox_worker/infrastructure/shutdown.py`): ask the loops to stop after the unit of work in flight.

```python
def request(self) -> None:
```

- Defines the method `request`.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `None`.

```python
"""Ask the loops to stop after the unit of work in flight."""
```

- The docstring (documentation kept with the code) says: *Ask the loops to stop after the unit of work in flight.*

```python
self._requested.set()
```

- `self._requested.set()`: calling `self._requested.set()`, which sets `self._requested`.

```python
@property
def requested(self) -> bool:
```

- Defines the method `requested`.
- `@property`: the method is read like an attribute.
- Parameters:
  - `self`: the object (or class) the method was called on.
- Gives back a value of type `bool`.

```python
"""True once a stop was requested."""
```

- The docstring (documentation kept with the code) says: *True once a stop was requested.*

```python
return self._requested.is_set()
```

- `return self._requested.is_set()`: ends the function and gives back the result of calling `self._requested.is_set()`, which asks whether the event `self._requested` is set.

```python
def wait(self, seconds: float) -> bool:
```

- Defines the method `wait`.
- Parameters:
  - `self`: the object (or class) the method was called on.
  - `seconds`, type `float`.
- Gives back a value of type `bool`.

```python
"""Sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested."""
```

- The docstring (documentation kept with the code) says: *Sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested.*

```python
return self._requested.wait(seconds)
```

- `return self._requested.wait(seconds)`: ends the function and gives back the result of calling `self._requested.wait(seconds)`, which is this repository's own `wait` (in `src/inbox_worker/infrastructure/shutdown.py`): sleep up to `seconds`, waking early on a stop request; returns True when a stop was requested.

#### `src/inbox_worker/interfaces/__init__.py`

```python
"""The interfaces layer."""
```

- The docstring (documentation kept with the code) says: *The interfaces layer.*

#### `src/inbox_worker/interfaces/cli.py`

```python
"""The `inbox-worker` command: database, events, webhook, worker, relay, redrive, measurements."""
```

- The docstring (documentation kept with the code) says: *The `inbox-worker` command: database, events, webhook, worker, relay, redrive, measurements.*

```python
import argparse
import json
import logging
import os
import socket
import sys
```

- `import argparse`: makes the module `argparse` available (the standard library's command-line argument parser).
- `import json`: makes the module `json` available (reads and writes JSON text).
- `import logging`: makes the module `logging` available (the standard library's logging system).
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import socket`: makes the module `socket` available (network connections at the lowest level).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).

```python
import threading
import time
from collections.abc import Sequence

import httpx

from inbox_worker.application.generate_events import generate_events
from inbox_worker.application.outbox import OutboxRelay
```

- `import threading`: makes the module `threading` available (threads, locks and events).
- `import time`: makes the module `time` available (clocks and sleeping).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Sequence`: the type hint for an ordered, indexable collection.)
- `import httpx`: makes the module `httpx` available (an HTTP client library).
- `from inbox_worker.application.generate_events import ...`: takes names from `inbox_worker.application.generate_events`, this repository's own code. (`generate_events`: `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable.)
- `from inbox_worker.application.outbox import ...`: takes names from `inbox_worker.application.outbox`, this repository's own code. (`OutboxRelay`: Sends unsent outbox rows.)

```python
from inbox_worker.application.worker import Worker
from inbox_worker.domain.signature import sign, verify
from inbox_worker.domain.stats import percentile
from inbox_worker.infrastructure.cassette import MissingRecordingError
from inbox_worker.infrastructure.environment import ConfigurationError
from inbox_worker.infrastructure.logging import configure_logging
```

- `from inbox_worker.application.worker import ...`: takes names from `inbox_worker.application.worker`, this repository's own code. (`Worker`: Pulls batches from the queue.)
- `from inbox_worker.domain.signature import ...`: takes names from `inbox_worker.domain.signature`, this repository's own code. (`sign`: The signature a sender attaches.) (`verify`: (ok, reason).)
- `from inbox_worker.domain.stats import ...`: takes names from `inbox_worker.domain.stats`, this repository's own code. (`percentile`: Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values.)
- `from inbox_worker.infrastructure.cassette import ...`: takes names from `inbox_worker.infrastructure.cassette`, this repository's own code. (`MissingRecordingError`: No recording matches this request; the message says how to re-record.)
- `from inbox_worker.infrastructure.environment import ...`: takes names from `inbox_worker.infrastructure.environment`, this repository's own code. (`ConfigurationError`: An environment variable is missing or has an unusable value.)
- `from inbox_worker.infrastructure.logging import ...`: takes names from `inbox_worker.infrastructure.logging`, this repository's own code. (`configure_logging`: Send every log record to `stream` (stderr by default) as logfmt.)

```python
from inbox_worker.infrastructure.postgres import apply_scripts, reset_tables
from inbox_worker.infrastructure.settings import Settings
from inbox_worker.infrastructure.shutdown import ShutdownSignal
from inbox_worker.interfaces.measure import run_burst, run_crash_test, wait_for_port
from inbox_worker.interfaces.webhook import create_app
from inbox_worker.interfaces.wiring import (
    Components,
    build_components,
    build_handler,
    build_model,
    crash_hook_from_environment,
)
```

- `from inbox_worker.infrastructure.postgres import ...`: takes names from `inbox_worker.infrastructure.postgres`, this repository's own code. (`apply_scripts`: Drop and recreate the schema from the numbered scripts, in order; returns the scripts that ran.) (`reset_tables`: Empty every table (sql/reset.sql).)
- `from inbox_worker.infrastructure.settings import ...`: takes names from `inbox_worker.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)
- `from inbox_worker.infrastructure.shutdown import ...`: takes names from `inbox_worker.infrastructure.shutdown`, this repository's own code. (`ShutdownSignal`: A flag that SIGINT and SIGTERM set, which work loops check between units of work.)
- `from inbox_worker.interfaces.measure import ...`: takes names from `inbox_worker.interfaces.measure`, this repository's own code. (`run_burst`: Send `events` events over `seconds` to a worker with `concurrency` threads, against a fake model with a rate limit.) (`run_crash_test`: Kill the worker process at `point` (after the model call, or after the commit), restart it, and return the exit codes, the event ids sent....) (`wait_for_port`: Poll a URL until it answers 200.)
- `from inbox_worker.interfaces.webhook import ...`: takes names from `inbox_worker.interfaces.webhook`, this repository's own code. (`create_app`: Build the app.)
- `from inbox_worker.interfaces.wiring import ...`: takes names from `inbox_worker.interfaces.wiring`, this repository's own code. (`Components`: Everything a command needs, built once.) (`build_components`: Wire the PostgreSQL adapters over one pool sized for the worker's concurrency.) (`build_handler`: The event handler over the components' queue and effects store.) (`build_model`: The fake model (load tests), the recorded adapter (offline smoke run), or Claude.) (`crash_hook_from_environment`: For the crash tests: `CRASH_AT=<point>` and `CRASH_AFTER=<n>` kill the process (exit code 137, as SIGKILL would) the n-th time the handle....)

```python
LOGGER = logging.getLogger("inbox_worker")
```

- `LOGGER = logging.getLogger("inbox_worker")`: stores the result of calling `logging.getLogger("inbox_worker")`, which gets the logger named `"inbox_worker"` in `LOGGER`.

```python
def _parser() -> argparse.ArgumentParser:
```

- Defines the function `_parser`.
- Gives back a value of type `argparse.ArgumentParser`.

```python
parser = argparse.ArgumentParser(
    prog="inbox-worker", description="A worker that runs a model step per inbox event."
)
commands = parser.add_subparsers(dest="command", required=True)
```

- `parser = argparse.ArgumentParser( prog="inbox-worker", description=...`: stores the result of calling `argparse.ArgumentParser( prog="inbox-worker", description="A worker that runs a model s...`, which makes a `ArgumentParser` object with the named values `prog`, `description` in `parser`.
- `commands = parser.add_subparsers(dest="command", required=True)`: stores the result of calling `parser.add_subparsers(dest="command", required=True)`, which prepares sub-commands The named values are `dest`, `required`. in `commands`.

```python
for name, text in (
    ("db", "rebuild the schema from sql/001_schema.sql and sql/002_seed.sql"),
    ("reset", "empty every table"),
    ("status", "counts, open dead letters and the lost-or-duplicated check"),
    ("webhook-demo", "valid, tampered and replayed requests"),
    ("serve-webhook", "start the webhook"),
    ("check", "exit 0 when the database answers"),
):
```

- Repeats the indented lines once for each item of `( ("db", "rebuild the schema from sql/001_schema.sql and sql/002_seed.sql"), ("reset", ...`, naming the current item the names `name`, `text`.

```python
commands.add_parser(name, help=text)
```

- `commands.add_parser(name, help=text)`: calling `commands.add_parser(name, help=text)`, which declares the sub-command `name` The named values are `help`..

```python
enqueue = commands.add_parser("enqueue", help="generate the sample inbox and put every delivery on the queue")
enqueue.add_argument("--events", type=int, default=1000)
worker = commands.add_parser("worker", help="process deliveries until stopped")
worker.add_argument("--until-idle", action="store_true")
relay = commands.add_parser("relay", help="send the acknowledgments in the outbox")
relay.add_argument("--once", action="store_true")
```

- `enqueue = commands.add_parser("enqueue", help="generate the sample ...`: stores the result of calling `commands.add_parser("enqueue", help="generate the sample inbox and put every delivery o...`, which declares the sub-command `"enqueue"` The named values are `help`. in `enqueue`.
- `enqueue.add_argument("--events", type=int, default=1000)`: calling `enqueue.add_argument("--events", type=int, default=1000)`, which declares a command-line argument `"--events"` The named values are `type`, `default`..
- `worker = commands.add_parser("worker", help="process deliveries unt...`: stores the result of calling `commands.add_parser("worker", help="process deliveries until stopped")`, which declares the sub-command `"worker"` The named values are `help`. in `worker`.
- `worker.add_argument("--until-idle", action="store_true")`: calling `worker.add_argument("--until-idle", action="store_true")`, which declares a command-line argument `"--until-idle"` The named values are `action`..
- `relay = commands.add_parser("relay", help="send the acknowledgments...`: stores the result of calling `commands.add_parser("relay", help="send the acknowledgments in the outbox")`, which declares the sub-command `"relay"` The named values are `help`. in `relay`.
- `relay.add_argument("--once", action="store_true")`: calling `relay.add_argument("--once", action="store_true")`, which declares a command-line argument `"--once"` The named values are `action`..

```python
redrive = commands.add_parser("redrive", help="put a dead letter back on the queue")
redrive.add_argument("dead_id", type=int)
commands.add_parser("bench-webhook", help="500 signed requests; report p50 and p95")
burst = commands.add_parser("burst", help="500 events in ten seconds at two concurrency limits")
burst.add_argument("--events", type=int, default=500)
burst.add_argument("--seconds", type=float, default=10.0)
```

- `redrive = commands.add_parser("redrive", help="put a dead letter ba...`: stores the result of calling `commands.add_parser("redrive", help="put a dead letter back on the queue")`, which declares the sub-command `"redrive"` The named values are `help`. in `redrive`.
- `redrive.add_argument("dead_id", type=int)`: calling `redrive.add_argument("dead_id", type=int)`, which declares a command-line argument `"dead_id"` The named values are `type`..
- `commands.add_parser("bench-webhook", help="500 signed requests; rep...`: calling `commands.add_parser("bench-webhook", help="500 signed requests; report p50 and p95")`, which declares the sub-command `"bench-webhook"` The named values are `help`..
- `burst = commands.add_parser("burst", help="500 events in ten second...`: stores the result of calling `commands.add_parser("burst", help="500 events in ten seconds at two concurrency limits")`, which declares the sub-command `"burst"` The named values are `help`. in `burst`.
- `burst.add_argument("--events", type=int, default=500)`: calling `burst.add_argument("--events", type=int, default=500)`, which declares a command-line argument `"--events"` The named values are `type`, `default`..
- `burst.add_argument("--seconds", type=float, default=10.0)`: calling `burst.add_argument("--seconds", type=float, default=10.0)`, which declares a command-line argument `"--seconds"` The named values are `type`, `default`..

```python
burst.add_argument("--concurrency", type=int, nargs="+", default=[5, 20])
burst.add_argument("--delay", type=float, default=0.15)
burst.add_argument("--max-rps", type=float, default=30.0)
crash = commands.add_parser("crash-test", help="kill the worker process at a point, restart it, compare event ids")
crash.add_argument("--at", choices=["after_model", "after_commit"], required=True)
return parser
```

- `burst.add_argument("--concurrency", type=int, nargs="+", default=[5...`: calling `burst.add_argument("--concurrency", type=int, nargs="+", default=[5, 20])`, which declares a command-line argument `"--concurrency"` The named values are `type`, `nargs`, `default`..
- `burst.add_argument("--delay", type=float, default=0.15)`: calling `burst.add_argument("--delay", type=float, default=0.15)`, which declares a command-line argument `"--delay"` The named values are `type`, `default`..
- `burst.add_argument("--max-rps", type=float, default=30.0)`: calling `burst.add_argument("--max-rps", type=float, default=30.0)`, which declares a command-line argument `"--max-rps"` The named values are `type`, `default`..
- `crash = commands.add_parser("crash-test", help="kill the worker pro...`: stores the result of calling `commands.add_parser("crash-test", help="kill the worker process at a point, restart it,...`, which declares the sub-command `"crash-test"` The named values are `help`. in `crash`.
- `crash.add_argument("--at", choices=["after_model", "after_commit"],...`: calling `crash.add_argument("--at", choices=["after_model", "after_commit"], required=True)`, which declares a command-line argument `"--at"` The named values are `choices`, `required`..
- `return parser`: ends the function and gives back the value of `parser`.

```python
def _status(components: Components) -> int:
```

- Defines the function `_status`.
- Parameters:
  - `components`, type `Components`.
- Gives back a value of type `int`.

```python
counts = components.reports.counts()
print("counts:", counts)
```

- `counts = components.reports.counts()`: stores the result of calling `components.reports.counts()`, which is this repository's own `counts` (in `src/inbox_worker/infrastructure/postgres.py`): rows in the tables that matter in `counts`.
- `print("counts:", counts)`: calling `print("counts:", counts)`, which writes `"counts:"`, `counts` to the screen (standard output).

```python
for dead_id, event_id, reason, attempts, error, digest in components.reports.dead_events():
```

- Repeats the indented lines once for each item of `components.reports.dead_events()`, naming the current item the names `dead_id`, `event_id`, `reason`, `attempts`, `error`, `digest`.

```python
print(f"dead letter {dead_id}: {event_id} reason={reason} attempts={attempts} hash={digest} error={error[:80]}")
```

- `print(f"dead letter {dead_id}: {event_id} reason={reason} attempts=...`: calling `print(f"dead letter {dead_id}: {event_id} reason={reason} attempts={attempts} hash={dig...`, which writes `f"dead letter {dead_id}: {event_id} reason={reason} attempts={attempts} hash={digest} e...` to the screen (standard output).

```python
ids = components.reports.ticket_event_ids()
print(f"tickets: {len(ids)}; distinct events with a ticket: {len(set(ids))}")
return 0
```

- `ids = components.reports.ticket_event_ids()`: stores the result of calling `components.reports.ticket_event_ids()`, which is this repository's own `ticket_event_ids` (in `src/inbox_worker/infrastructure/postgres.py`): event id of every ticket (duplicates would show up twice) in `ids`.
- `print(f"tickets: {len(ids)}; distinct events with a ticket: {len(se...`: calling `print(f"tickets: {len(ids)}; distinct events with a ticket: {len(set(ids))}")`, which writes `f"tickets: {len(ids)}; distinct events with a ticket: {len(set(ids))}"` to the screen (standard output).
- `return 0`: ends the function and gives back the number `0`.

```python
def _webhook_demo(settings: Settings) -> int:
```

- Defines the function `_webhook_demo`.
- Parameters:
  - `settings`, type `Settings`.
- Gives back a value of type `int`.

```python
secret = settings.webhook_secret
now = time.time()
body = '{"event_id": "e-001", "body": "Please cancel order 4417"}'
signature = sign(secret, now, body)
print("valid request:", verify(secret, str(now), body, signature, now))
print("tampered body:", verify(secret, str(now), body.replace("4417", "9999"), signature, now))
```

- `secret = settings.webhook_secret`: stores `settings.webhook_secret` in `secret`.
- `now = time.time()`: stores the result of calling `time.time()`, which reads the clock in `now`.
- `body = '{"event_id": "e-001", "body": "Please cancel order 4417"}'`: stores the text `'{"event_id": "e-001", "body": "Please cancel order 4417"}'` in `body`.
- `signature = sign(secret, now, body)`: stores the result of calling `sign(secret, now, body)`, which is this repository's own `sign` (in `src/inbox_worker/domain/signature.py`): the signature a sender attaches in `signature`.
- `print("valid request:", verify(secret, str(now), body, signature, n...`: calling `print("valid request:", verify(secret, str(now), body, signature, now))`, which writes `"valid request:"`, `verify(secret, str(now), body, signature, now)` to the screen (standard output).
- `print("tampered body:", verify(secret, str(now), body.replace("4417...`: calling `print("tampered body:", verify(secret, str(now), body.replace("4417", "9999"), signatur...`, which writes `"tampered body:"`, `verify(secret, str(now), body.replace("4417", "9999"), signature, now)` to the screen (standard output).

```python
print("replayed old request:", verify(secret, str(now - 400), body, sign(secret, now - 400, body), now))
return 0
```

- `print("replayed old request:", verify(secret, str(now - 400), body,...`: calling `print("replayed old request:", verify(secret, str(now - 400), body, sign(secret, now - ...`, which writes `"replayed old request:"`, `verify(secret, str(now - 400), body, sign(secret, now - 400, body), now)` to the screen (standard output).
- `return 0`: ends the function and gives back the number `0`.

```python
def _free_port() -> int:
```

- Defines the function `_free_port`.
- Gives back a value of type `int`.

```python
"""A port nothing is listening on (the benchmark must not collide with a service already on the machine)."""
```

- The docstring (documentation kept with the code) says: *A port nothing is listening on (the benchmark must not collide with a service already on the machine).*

```python
with socket.socket() as probe:
```

- Opens `socket.socket()` as `probe` for the indented lines, and cleans it up when they end (even after an error).

```python
probe.bind(("127.0.0.1", 0))
return int(probe.getsockname()[1])
```

- `probe.bind(("127.0.0.1", 0))`: calling `probe.bind(("127.0.0.1", 0))`, which attaches a socket to an address and port.
- `return int(probe.getsockname()[1])`: ends the function and gives back the result of calling `int(probe.getsockname()[1])`, which turns `probe.getsockname()[1]` into a whole number.

```python
def _bench_webhook(components: Components) -> int:
```

- Defines the function `_bench_webhook`.
- Parameters:
  - `components`, type `Components`.
- Gives back a value of type `int`.

```python
import uvicorn

settings = components.settings
app = create_app(components.queue, settings.webhook_secret, settings.max_webhook_bytes, components.database.ping)
port = _free_port()
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
thread = threading.Thread(target=server.run, daemon=True)
```

- `import uvicorn`: makes the module `uvicorn` available (the web server that runs a FastAPI application).
- `settings = components.settings`: stores `components.settings` in `settings`.
- `app = create_app(components.queue, settings.webhook_secret, setting...`: stores the result of calling `create_app(components.queue, settings.webhook_secret, settings.max_webhook_bytes, compo...`, which is this repository's own `create_app` (in `src/inbox_worker/interfaces/webhook.py`): build the app in `app`.
- `port = _free_port()`: stores the result of calling `_free_port()`, which is this repository's own `_free_port` (in `src/inbox_worker/interfaces/cli.py`): a port nothing is listening on (the benchmark must not collide with a service already on the machine) in `port`.
- `server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=...`: stores the result of calling `uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))`, which makes a `Server` object from `uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")` in `server`.
- `thread = threading.Thread(target=server.run, daemon=True)`: stores the result of calling `threading.Thread(target=server.run, daemon=True)`, which makes a `Thread` object with the named values `target`, `daemon` in `thread`.

```python
thread.start()
base = f"http://127.0.0.1:{port}"
wait_for_port(base + "/healthz")
reset_tables(components.database, settings.root / "sql")
timings = []
```

- `thread.start()`: calling `thread.start()`, which starts `thread`.
- `base = f"http://127.0.0.1:{port}"`: stores the text built by the f-string `f"http://127.0.0.1:{port}"` in `base`.
- `wait_for_port(base + "/healthz")`: calling `wait_for_port(base + "/healthz")`, which is this repository's own `wait_for_port` (in `src/inbox_worker/interfaces/measure.py`): poll a URL until it answers 200.
- `reset_tables(components.database, settings.root / "sql")`: calling `reset_tables(components.database, settings.root / "sql")`, which is this repository's own `reset_tables` (in `src/inbox_worker/infrastructure/postgres.py`): empty every table (sql/reset.sql).
- `timings = []`: stores a new list (empty) in `timings`.

```python
with httpx.Client(base_url=base) as client:
```

- Opens `httpx.Client(base_url=base)` as `client` for the indented lines, and cleans it up when they end (even after an error).

```python
for number in range(500):
```

- Repeats the indented lines once for each item of `range(500)`, naming the current item `number`.

```python
body = json.dumps({"event_id": f"e-{number:04d}", "body": "Please cancel order 4417."})
now = time.time()
headers = {"X-Timestamp": str(now), "X-Signature": sign(settings.webhook_secret, now, body)}
started = time.perf_counter()
response = client.post("/webhook/email", content=body, headers=headers)
timings.append((time.perf_counter() - started) * 1000)
```

- `body = json.dumps({"event_id": f"e-{number:04d}", "body": "Please c...`: stores the result of calling `json.dumps({"event_id": f"e-{number:04d}", "body": "Please cancel order 4417."})`, which turns `{"event_id": f"e-{number:04d}", "body": "Please cancel order 4417."}` into JSON text in `body`.
- `now = time.time()`: stores the result of calling `time.time()`, which reads the clock in `now`.
- `headers = {"X-Timestamp": str(now), "X-Signature": sign(settings.we...`: stores a new dict with 2 entries in `headers`.
- `started = time.perf_counter()`: stores the result of calling `time.perf_counter()`, which reads the high-resolution timer in seconds in `started`.
- `response = client.post("/webhook/email", content=body, headers=head...`: stores the result of calling `client.post("/webhook/email", content=body, headers=headers)`, which sends an HTTP POST request The named values are `content`, `headers`. in `response`.
- `timings.append((time.perf_counter() - started) * 1000)`: calling `timings.append((time.perf_counter() - started) * 1000)`, which adds `(time.perf_counter() - started) * 1000` to the end of `timings`.

```python
assert response.status_code == 202, response.text
```

- `assert response.status_code == 202, response.text`: checks that `response.status_code` equals `202`. A false check stops the test as failed. If it is false, the message `response.text` is shown.

> **`assert`.** `assert condition` does nothing when the condition is true and stops with an `AssertionError` when it is false. In a test file, a failing assert is how a test fails. `pytest` rewrites assert lines so its failure message shows the values involved.

```python
tampered = client.post("/webhook/email", content=body.replace("4417", "9999"), headers=headers)
old = str(time.time() - 400)
replayed = client.post(
    "/webhook/email",
    content=body,
    headers={"X-Timestamp": old, "X-Signature": sign(settings.webhook_secret, float(old), body)},
)
```

- `tampered = client.post("/webhook/email", content=body.replace("4417...`: stores the result of calling `client.post("/webhook/email", content=body.replace("4417", "9999"), headers=headers)`, which sends an HTTP POST request The named values are `content`, `headers`. in `tampered`.
- `old = str(time.time() - 400)`: stores the result of calling `str(time.time() - 400)`, which turns `time.time() - 400` into text in `old`.
- `replayed = client.post( "/webhook/email", content=body, headers={"X...`: stores the result of calling `client.post( "/webhook/email", content=body, headers={"X-Timestamp": old, "X-Signature"...`, which sends an HTTP POST request The named values are `content`, `headers`. in `replayed`.

```python
server.should_exit = True
thread.join(timeout=10)
print(
    f"500 requests: p50 {percentile(timings, 0.5):.1f} ms, p95 {percentile(timings, 0.95):.1f} ms, max {max(timings):.1f} ms"
)
print(
    f"tampered body -> {tampered.status_code} {tampered.json()}; replayed old request -> {replayed.status_code} {replayed.json()}"
)
print(f"deliveries queued: {components.reports.counts()['deliveries']}")
budget = float(os.environ.get("WEBHOOK_P95_BUDGET_MS", "100"))
```

- `server.should_exit = True`: stores `True` in `server.should_exit`.
- `thread.join(timeout=10)`: calling `thread.join(timeout=10)`, which glues the items of its argument together with `thread` between them The named values are `timeout`..
- `print( f"500 requests: p50 {percentile(timings, 0.5):.1f} ms, p95 {...`: calling `print( f"500 requests: p50 {percentile(timings, 0.5):.1f} ms, p95 {percentile(timings, ...`, which writes `f"500 requests: p50 {percentile(timings, 0.5):.1f} ms, p95 {percentile(timings, 0.95):....` to the screen (standard output).
- `print( f"tampered body -> {tampered.status_code} {tampered.json()};...`: calling `print( f"tampered body -> {tampered.status_code} {tampered.json()}; replayed old reques...`, which writes `f"tampered body -> {tampered.status_code} {tampered.json()}; replayed old request -> {r...` to the screen (standard output).
- `print(f"deliveries queued: {components.reports.counts()['deliveries...`: calling `print(f"deliveries queued: {components.reports.counts()['deliveries']}")`, which writes `f"deliveries queued: {components.reports.counts()['deliveries']}"` to the screen (standard output).
- `budget = float(os.environ.get("WEBHOOK_P95_BUDGET_MS", "100"))`: stores the result of calling `float(os.environ.get("WEBHOOK_P95_BUDGET_MS", "100"))`, which turns `os.environ.get("WEBHOOK_P95_BUDGET_MS", "100")` into a decimal number in `budget`.

```python
print(f"p95 budget {budget:.0f} ms: {'met' if percentile(timings, 0.95) < budget else 'NOT met'}")
return 0 if percentile(timings, 0.95) < budget else 1
```

- `print(f"p95 budget {budget:.0f} ms: {'met' if percentile(timings, 0...`: calling `print(f"p95 budget {budget:.0f} ms: {'met' if percentile(timings, 0.95) < budget else '...`, which writes `f"p95 budget {budget:.0f} ms: {'met' if percentile(timings, 0.95) < budget else 'NOT me...` to the screen (standard output).
- `return 0 if percentile(timings, 0.95) < budget else 1`: ends the function and gives back `0` when `percentile(timings, 0.95)` is less than `budget`, otherwise `1`.

```python
def _worker(components: Components, until_idle: bool) -> int:
```

- Defines the function `_worker`.
- Parameters:
  - `components`, type `Components`.
  - `until_idle`, type `bool`.
- Gives back a value of type `int`.

```python
settings = components.settings
shutdown = ShutdownSignal()
shutdown.install()
handler = build_handler(components, build_model(settings), crash_hook_from_environment())
worker = Worker(
    components.queue,
    handler,
    concurrency=settings.concurrency,
    lease_seconds=settings.lease_seconds,
    stop_requested=lambda: shutdown.requested,
    wait=shutdown.wait,
)
```

- `settings = components.settings`: stores `components.settings` in `settings`.
- `shutdown = ShutdownSignal()`: stores the result of calling `ShutdownSignal()`, which is this repository's own `ShutdownSignal` (in `src/inbox_worker/infrastructure/shutdown.py`): a flag that SIGINT and SIGTERM set, which work loops check between units of work in `shutdown`.
- `shutdown.install()`: calling `shutdown.install()`, which is this repository's own `install` (in `src/inbox_worker/infrastructure/shutdown.py`): route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close.
- `handler = build_handler(components, build_model(settings), crash_ho...`: stores the result of calling `build_handler(components, build_model(settings), crash_hook_from_environment())`, which is this repository's own `build_handler` (in `src/inbox_worker/interfaces/wiring.py`): the event handler over the components' queue and effects store in `handler`.
- `worker = Worker( components.queue, handler, concurrency=settings.co...`: stores the result of calling `Worker( components.queue, handler, concurrency=settings.concurrency, lease_seconds=sett...`, which is this repository's own `Worker` (in `src/inbox_worker/application/worker.py`): pulls batches from the queue in `worker`.

```python
outcomes = worker.run(until_idle=until_idle)
print("outcomes:", dict(outcomes))
return 0
```

- `outcomes = worker.run(until_idle=until_idle)`: stores the result of calling `worker.run(until_idle=until_idle)`, which runs a program or a coroutine The named values are `until_idle`. in `outcomes`.
- `print("outcomes:", dict(outcomes))`: calling `print("outcomes:", dict(outcomes))`, which writes `"outcomes:"`, `dict(outcomes)` to the screen (standard output).
- `return 0`: ends the function and gives back the number `0`.

```python
def _relay(components: Components, once: bool) -> int:
```

- Defines the function `_relay`.
- Parameters:
  - `components`, type `Components`.
  - `once`, type `bool`.
- Gives back a value of type `int`.

```python
shutdown = ShutdownSignal()
shutdown.install()
relay = OutboxRelay(components.outbox, components.mail)
total = 0
```

- `shutdown = ShutdownSignal()`: stores the result of calling `ShutdownSignal()`, which is this repository's own `ShutdownSignal` (in `src/inbox_worker/infrastructure/shutdown.py`): a flag that SIGINT and SIGTERM set, which work loops check between units of work in `shutdown`.
- `shutdown.install()`: calling `shutdown.install()`, which is this repository's own `install` (in `src/inbox_worker/infrastructure/shutdown.py`): route SIGINT and SIGTERM to `request`, so in-flight work finishes and connections close.
- `relay = OutboxRelay(components.outbox, components.mail)`: stores the result of calling `OutboxRelay(components.outbox, components.mail)`, which is this repository's own `OutboxRelay` (in `src/inbox_worker/application/outbox.py`): sends unsent outbox rows in `relay`.
- `total = 0`: stores the number `0` in `total`.

```python
while not shutdown.requested:
```

- Repeats the indented lines for as long as it is not the case that `shutdown.requested` is truthy.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
sent = relay.run_once()
```

- `sent = relay.run_once()`: stores the result of calling `relay.run_once()`, which is this repository's own `run_once` (in `src/inbox_worker/application/outbox.py`): send up to `limit` rows; returns how many rows were marked sent in `sent`.

```python
except Exception:
```

- If an error of kind `Exception` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
LOGGER.exception("outbox unavailable, retrying")
shutdown.wait(2.0)
continue
```

- `LOGGER.exception("outbox unavailable, retrying")`: calling `LOGGER.exception("outbox unavailable, retrying")`, which writes an ERROR log line with the traceback of the current error.
- `shutdown.wait(2.0)`: calling `shutdown.wait(2.0)`, which waits for `shutdown`.
- `continue`: skips to the next round of the loop.

```python
total += sent
```

- `total += sent`: adds `sent` to `total` and keeps the result there.

```python
if once and sent == 0:
```

- Checks whether `once` is truthy (not `None`, `False`, zero or empty) and `sent` equals `0`. If so, the indented lines run.

```python
break
```

- `break`: leaves the loop now.

```python
if sent == 0:
```

- Checks whether `sent` equals `0`. If so, the indented lines run.

```python
shutdown.wait(0.5)
```

- `shutdown.wait(0.5)`: calling `shutdown.wait(0.5)`, which waits for `shutdown`.

```python
print(f"acknowledgments sent: {total}")
return 0
```

- `print(f"acknowledgments sent: {total}")`: calling `print(f"acknowledgments sent: {total}")`, which writes `f"acknowledgments sent: {total}"` to the screen (standard output).
- `return 0`: ends the function and gives back the number `0`.

```python
def _burst(components: Components, arguments: argparse.Namespace) -> int:
```

- Defines the function `_burst`.
- Parameters:
  - `components`, type `Components`.
  - `arguments`, type `argparse.Namespace`.
- Gives back a value of type `int`.

```python
print(
    "| Concurrency | Throughput (events/s) | Peak queue depth | p95 event to ticket (s) | Rate-limit errors | Tickets | Dead letters | Drained |"
)
print("| --- | --- | --- | --- | --- | --- | --- | --- |")
```

- `print( "| Concurrency | Throughput (events/s) | Peak queue depth | ...`: calling `print( "| Concurrency | Throughput (events/s) | Peak queue depth | p95 event to ticket ...`, which writes `"| Concurrency | Throughput (events/s) | Peak queue depth | p95 event to ticket (s) | R...` to the screen (standard output).
- `print("| --- | --- | --- | --- | --- | --- | --- | --- |")`: calling `print("| --- | --- | --- | --- | --- | --- | --- | --- |")`, which writes `"| --- | --- | --- | --- | --- | --- | --- | --- |"` to the screen (standard output).

```python
for concurrency in arguments.concurrency:
```

- Repeats the indented lines once for each item of `arguments.concurrency`, naming the current item `concurrency`.

```python
result = run_burst(
    components,
    events=arguments.events,
    seconds=arguments.seconds,
    concurrency=concurrency,
    delay=arguments.delay,
    max_rps=arguments.max_rps,
)
```

- `result = run_burst( components, events=arguments.events, seconds=ar...`: stores the result of calling `run_burst( components, events=arguments.events, seconds=arguments.seconds, concurrency=...`, which is this repository's own `run_burst` (in `src/inbox_worker/interfaces/measure.py`): send `events` events over `seconds` to a worker with `concurrency` threads, against a fake model with a rate limit The named values are `events`, `seconds`, `concurrency`, `delay`, `max_rps`. in `result`.

```python
print(
    f"| {result.concurrency} | {result.throughput_per_second:.1f} | {result.peak_queue_depth} | "
    f"{result.p95_event_to_ticket_seconds:.2f} | {result.rate_limit_errors} | {result.tickets} | {result.dead_letters} | {result.drained} |"
)
```

- `print( f"| {result.concurrency} | {result.throughput_per_second:.1f...`: calling `print( f"| {result.concurrency} | {result.throughput_per_second:.1f} | {result.peak_que...`, which writes `f"| {result.concurrency} | {result.throughput_per_second:.1f} | {result.peak_queue_dept...` to the screen (standard output).

```python
return 0
```

- `return 0`: ends the function and gives back the number `0`.

```python
def main(argv: Sequence[str] | None = None) -> int:
```

- Defines the function `main`.
- Parameters:
  - `argv`, type `Sequence[str] | None`, optional (default `None`).
- Gives back a value of type `int`.

```python
"""Run one subcommand; returns the process exit code."""
```

- The docstring (documentation kept with the code) says: *Run one subcommand; returns the process exit code.*

```python
arguments = _parser().parse_args(argv)
```

- `arguments = _parser().parse_args(argv)`: stores the result of calling `_parser().parse_args(argv)`, which reads the command line into an object in `arguments`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
settings = Settings.from_environ(os.environ)
```

- `settings = Settings.from_environ(os.environ)`: stores the result of calling `Settings.from_environ(os.environ)`, which is this repository's own `from_environ` (in `src/inbox_worker/infrastructure/settings.py`): read and validate; raises `ConfigurationError` naming the first bad variable in `settings`.

```python
except ConfigurationError as error:
```

- If an error of kind `ConfigurationError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
print(f"configuration error: {error}", file=sys.stderr)
return 2
```

- `print(f"configuration error: {error}", file=sys.stderr)`: calling `print(f"configuration error: {error}", file=sys.stderr)`, which writes `f"configuration error: {error}"` to the screen (standard output) The named values are `file`..
- `return 2`: ends the function and gives back the number `2`.

```python
configure_logging(settings.log_level)
```

- `configure_logging(settings.log_level)`: calling `configure_logging(settings.log_level)`, which is this repository's own `configure_logging` (in `src/inbox_worker/infrastructure/logging.py`): send every log record to `stream` (stderr by default) as logfmt.

```python
if arguments.command == "webhook-demo":
```

- Checks whether `arguments.command` equals `"webhook-demo"`. If so, the indented lines run.

```python
return _webhook_demo(settings)
```

- `return _webhook_demo(settings)`: ends the function and gives back the result of calling `_webhook_demo(settings)`.

```python
components = build_components(settings)
```

- `components = build_components(settings)`: stores the result of calling `build_components(settings)`, which is this repository's own `build_components` (in `src/inbox_worker/interfaces/wiring.py`): wire the PostgreSQL adapters over one pool sized for the worker's concurrency in `components`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
if arguments.command == "db":
```

- Checks whether `arguments.command` equals `"db"`. If so, the indented lines run.

```python
print("applied " + ", ".join(apply_scripts(components.database, settings.root / "sql")))
```

- `print("applied " + ", ".join(apply_scripts(components.database, set...`: calling `print("applied " + ", ".join(apply_scripts(components.database, settings.root / "sql")))`, which writes `"applied " + ", ".join(apply_scripts(components.database, settings.root / "sql"))` to the screen (standard output).

```python
elif arguments.command == "reset":
```

- Otherwise, checks whether `arguments.command` equals `"reset"`. If so, the indented lines run.

```python
reset_tables(components.database, settings.root / "sql")
print("tables emptied")
```

- `reset_tables(components.database, settings.root / "sql")`: calling `reset_tables(components.database, settings.root / "sql")`, which is this repository's own `reset_tables` (in `src/inbox_worker/infrastructure/postgres.py`): empty every table (sql/reset.sql).
- `print("tables emptied")`: calling `print("tables emptied")`, which writes `"tables emptied"` to the screen (standard output).

```python
elif arguments.command == "check":
```

- Otherwise, checks whether `arguments.command` equals `"check"`. If so, the indented lines run.

```python
return 0 if components.database.ping() else 1
```

- `return 0 if components.database.ping() else 1`: ends the function and gives back `0` when `components.database.ping()` is true (the call is this repository's own `ping` (in `src/inbox_worker/infrastructure/postgres.py`): true when a trivial query works), otherwise `1`.

```python
elif arguments.command == "status":
```

- Otherwise, checks whether `arguments.command` equals `"status"`. If so, the indented lines run.

```python
return _status(components)
```

- `return _status(components)`: ends the function and gives back the result of calling `_status(components)`.

```python
elif arguments.command == "enqueue":
```

- Otherwise, checks whether `arguments.command` equals `"enqueue"`. If so, the indented lines run.

```python
inbox = generate_events(arguments.events, 2610)
components.queue.put_many(list(inbox.deliveries))
print(
    f"queued {len(inbox.deliveries)} deliveries of {arguments.events} events ({len(inbox.duplicates)} delivered twice, {len(inbox.poison)} poison)"
)
```

- `inbox = generate_events(arguments.events, 2610)`: stores the result of calling `generate_events(arguments.events, 2610)`, which is this repository's own `generate_events` (in `src/inbox_worker/application/generate_events.py`): `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable in `inbox`.
- `components.queue.put_many(list(inbox.deliveries))`: calling `components.queue.put_many(list(inbox.deliveries))`, which is this repository's own `put_many` (in `src/inbox_worker/infrastructure/postgres.py`): insert many deliveries in one transaction (loading the sample events).
- `print( f"queued {len(inbox.deliveries)} deliveries of {arguments.ev...`: calling `print( f"queued {len(inbox.deliveries)} deliveries of {arguments.events} events ({len(i...`, which writes `f"queued {len(inbox.deliveries)} deliveries of {arguments.events} events ({len(inbox.du...` to the screen (standard output).

```python
elif arguments.command == "serve-webhook":
```

- Otherwise, checks whether `arguments.command` equals `"serve-webhook"`. If so, the indented lines run.

```python
import uvicorn

app = create_app(
    components.queue, settings.webhook_secret, settings.max_webhook_bytes, components.database.ping
)
uvicorn.run(
    app,
    host=settings.host,
    port=settings.port,
    log_level=settings.log_level.lower(),
    timeout_graceful_shutdown=10,
)
```

- `import uvicorn`: makes the module `uvicorn` available (the web server that runs a FastAPI application).
- `app = create_app( components.queue, settings.webhook_secret, settin...`: stores the result of calling `create_app( components.queue, settings.webhook_secret, settings.max_webhook_bytes, comp...`, which is this repository's own `create_app` (in `src/inbox_worker/interfaces/webhook.py`): build the app in `app`.
- `uvicorn.run( app, host=settings.host, port=settings.port, log_level...`: calling `uvicorn.run( app, host=settings.host, port=settings.port, log_level=settings.log_level....`, which runs a program or a coroutine The named values are `host`, `port`, `log_level`, `timeout_graceful_shutdown`..

```python
elif arguments.command == "worker":
```

- Otherwise, checks whether `arguments.command` equals `"worker"`. If so, the indented lines run.

```python
return _worker(components, arguments.until_idle)
```

- `return _worker(components, arguments.until_idle)`: ends the function and gives back the result of calling `_worker(components, arguments.until_idle)`.

```python
elif arguments.command == "relay":
```

- Otherwise, checks whether `arguments.command` equals `"relay"`. If so, the indented lines run.

```python
return _relay(components, arguments.once)
```

- `return _relay(components, arguments.once)`: ends the function and gives back the result of calling `_relay(components, arguments.once)`.

```python
elif arguments.command == "redrive":
```

- Otherwise, checks whether `arguments.command` equals `"redrive"`. If so, the indented lines run.

```python
new = components.queue.redrive(arguments.dead_id)
print(
    f"redriven as delivery {new}"
    if new
    else f"dead letter {arguments.dead_id} not found or already redriven"
)
return 0 if new else 1
```

- `new = components.queue.redrive(arguments.dead_id)`: stores the result of calling `components.queue.redrive(arguments.dead_id)`, which is this repository's own `redrive` (in `src/inbox_worker/infrastructure/postgres.py`): put a dead letter's payload back on the queue as a new delivery and mark it redriven; None if unknown or done in `new`.
- `print( f"redriven as delivery {new}" if new else f"dead letter {arg...`: calling `print( f"redriven as delivery {new}" if new else f"dead letter {arguments.dead_id} not ...`, which writes `f"redriven as delivery {new}" if new else f"dead letter {arguments.dead_id} not found o...` to the screen (standard output).
- `return 0 if new else 1`: ends the function and gives back `0` when `new` is truthy (not `None`, `False`, zero or empty), otherwise `1`.

```python
elif arguments.command == "bench-webhook":
```

- Otherwise, checks whether `arguments.command` equals `"bench-webhook"`. If so, the indented lines run.

```python
return _bench_webhook(components)
```

- `return _bench_webhook(components)`: ends the function and gives back the result of calling `_bench_webhook(components)`.

```python
elif arguments.command == "burst":
```

- Otherwise, checks whether `arguments.command` equals `"burst"`. If so, the indented lines run.

```python
return _burst(components, arguments)
```

- `return _burst(components, arguments)`: ends the function and gives back the result of calling `_burst(components, arguments)`.

```python
elif arguments.command == "crash-test":
```

- Otherwise, checks whether `arguments.command` equals `"crash-test"`. If so, the indented lines run.

```python
codes, sent, ticketed = run_crash_test(components, arguments.at)
print(dict(codes))
print(
    f"event ids sent: {len(set(sent))}; tickets: {len(ticketed)}; distinct events with a ticket: {len(set(ticketed))}"
)
lost, duplicated = sorted(set(sent) - set(ticketed)), len(ticketed) - len(set(ticketed))
print(f"lost: {lost}; duplicated tickets: {duplicated}")
return 0 if not lost and not duplicated else 1
```

- `codes, sent, ticketed = run_crash_test(components, arguments.at)`: unpacks the result of calling `run_crash_test(components, arguments.at)`, which is this repository's own `run_crash_test` (in `src/inbox_worker/interfaces/measure.py`): kill the worker process at `point` (after the model call, or after the commit), restart it, and return the exit codes, the event ids sent... into the names `codes`, `sent`, `ticketed`, one item each.
- `print(dict(codes))`: calling `print(dict(codes))`, which writes `dict(codes)` to the screen (standard output).
- `print( f"event ids sent: {len(set(sent))}; tickets: {len(ticketed)}...`: calling `print( f"event ids sent: {len(set(sent))}; tickets: {len(ticketed)}; distinct events wi...`, which writes `f"event ids sent: {len(set(sent))}; tickets: {len(ticketed)}; distinct events with a ti...` to the screen (standard output).
- `lost, duplicated = sorted(set(sent) - set(ticketed)), len(ticketed)...`: unpacks a tuple of 2 items into the names `lost`, `duplicated`, one item each.
- `print(f"lost: {lost}; duplicated tickets: {duplicated}")`: calling `print(f"lost: {lost}; duplicated tickets: {duplicated}")`, which writes `f"lost: {lost}; duplicated tickets: {duplicated}"` to the screen (standard output).
- `return 0 if not lost and not duplicated else 1`: ends the function and gives back `0` when it is not the case that `lost` is truthy (not `None`, `False`, zero or empty) and it is not the case that `duplicated` is truthy (not `None`, `False`, zero or empty), otherwise `1`.

```python
return 0
```

- `return 0`: ends the function and gives back the number `0`.

```python
except MissingRecordingError as error:
```

- If an error of kind `MissingRecordingError` happened above, runs the indented lines, keeping the error in `error`. The error is then handled and the program carries on after the whole `try`.

```python
LOGGER.error("%s", error)
return 1
```

- `LOGGER.error("%s", error)`: calling `LOGGER.error("%s", error)`, which writes an ERROR log line.
- `return 1`: ends the function and gives back the number `1`.

```python
finally:
```

- Always runs last, whether or not an error happened. It is used to clean up.

```python
components.database.close()
```

- `components.database.close()`: calling `components.database.close()`, which closes `components.database`.

```python
if __name__ == "__main__":
```

- Checks whether `__name__` equals `"__main__"`. If so, the indented lines run.

```python
raise SystemExit(main())
```

- `raise SystemExit(main())`: stops with an error of kind `SystemExit` with the message `main()`. Whoever called this code must handle it or the program stops.

#### `src/inbox_worker/interfaces/measure.py`

```python
"""Measurements that need threads and a database: the burst, the crash recovery and the webhook latency."""
```

- The docstring (documentation kept with the code) says: *Measurements that need threads and a database: the burst, the crash recovery and the webhook latency.*

```python
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `import subprocess`: makes the module `subprocess` available (starting other programs).
- `import sys`: makes the module `sys` available (facts about the running Python program: arguments, exit, standard streams).
- `import threading`: makes the module `threading` available (threads, locks and events).
- `import time`: makes the module `time` available (clocks and sleeping).

```python
from collections import Counter
from dataclasses import dataclass, replace

from inbox_worker.application.generate_events import generate_events
from inbox_worker.application.handler import EventHandler, RetryPolicy
from inbox_worker.application.worker import Worker
from inbox_worker.domain.stats import percentile
```

- `from collections import ...`: takes names from `collections` (the standard library's extra container types (Counter, defaultdict, deque)). (`Counter`: a dict that counts: `counter[x] += 1`.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.) (`replace`: a name provided by that module.)
- `from inbox_worker.application.generate_events import ...`: takes names from `inbox_worker.application.generate_events`, this repository's own code. (`generate_events`: `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable.)
- `from inbox_worker.application.handler import ...`: takes names from `inbox_worker.application.handler`, this repository's own code. (`EventHandler`: Applies each event's effects once, however often the queue delivers it.) (`RetryPolicy`: How a failing event is retried before it is parked.)
- `from inbox_worker.application.worker import ...`: takes names from `inbox_worker.application.worker`, this repository's own code. (`Worker`: Pulls batches from the queue.)
- `from inbox_worker.domain.stats import ...`: takes names from `inbox_worker.domain.stats`, this repository's own code. (`percentile`: Nearest-rank percentile of `values` (0.95 for p95); 0.0 for no values.)

```python
from inbox_worker.infrastructure.clock import SystemClock
from inbox_worker.infrastructure.fake_model import FakeModel
from inbox_worker.infrastructure.postgres import reset_tables
from inbox_worker.interfaces.wiring import Components, build_extractor
```

- `from inbox_worker.infrastructure.clock import ...`: takes names from `inbox_worker.infrastructure.clock`, this repository's own code. (`SystemClock`: Now, in UTC.)
- `from inbox_worker.infrastructure.fake_model import ...`: takes names from `inbox_worker.infrastructure.fake_model`, this repository's own code. (`FakeModel`: Thread-safe; counts calls, rate-limit errors and injected errors.)
- `from inbox_worker.infrastructure.postgres import ...`: takes names from `inbox_worker.infrastructure.postgres`, this repository's own code. (`reset_tables`: Empty every table (sql/reset.sql).)
- `from inbox_worker.interfaces.wiring import ...`: takes names from `inbox_worker.interfaces.wiring`, this repository's own code. (`Components`: Everything a command needs, built once.) (`build_extractor`: The extractor over the model, with the prompt text and version read from the versioned prompt file.)

```python
@dataclass(frozen=True, slots=True)
class BurstResult:
```

- Defines the class `BurstResult`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""What one burst measured."""
```

- The docstring (documentation kept with the code) says: *What one burst measured.*

```python
concurrency: int
events: int
seconds_to_drain: float
throughput_per_second: float
peak_queue_depth: int
p95_event_to_ticket_seconds: float
rate_limit_errors: int
tickets: int
```

- `concurrency: int`: a field named `concurrency` of type `int`, no default (must be given).
- `events: int`: a field named `events` of type `int`, no default (must be given).
- `seconds_to_drain: float`: a field named `seconds_to_drain` of type `float`, no default (must be given).
- `throughput_per_second: float`: a field named `throughput_per_second` of type `float`, no default (must be given).
- `peak_queue_depth: int`: a field named `peak_queue_depth` of type `int`, no default (must be given).
- `p95_event_to_ticket_seconds: float`: a field named `p95_event_to_ticket_seconds` of type `float`, no default (must be given).
- `rate_limit_errors: int`: a field named `rate_limit_errors` of type `int`, no default (must be given).
- `tickets: int`: a field named `tickets` of type `int`, no default (must be given).

```python
dead_letters: int
drained: bool
```

- `dead_letters: int`: a field named `dead_letters` of type `int`, no default (must be given).
- `drained: bool`: a field named `drained` of type `bool`, no default (must be given).

```python
def run_burst(
    components: Components, *, events: int, seconds: float, concurrency: int, delay: float, max_rps: float
) -> BurstResult:
```

- Defines the function `run_burst`.
- Parameters:
  - `components`, type `Components`.
  - `events`, type `int`. Must be passed by name.
  - `seconds`, type `float`. Must be passed by name.
  - `concurrency`, type `int`. Must be passed by name.
  - `delay`, type `float`. Must be passed by name.
  - `max_rps`, type `float`. Must be passed by name.
- Gives back a value of type `BurstResult`.

```python
"""Send `events` events over `seconds` to a worker with `concurrency` threads, against a fake model with a rate limit.

Throughput is tickets over the time from the first event to an empty queue. The queue depth is sampled every 50 ms.
"""
```

- The docstring (documentation kept with the code) says: *Send `events` events over `seconds` to a worker with `concurrency` threads, against a fake model with a rate limit. Throughput is tickets over the time from the first event to an empty queue. The queue depth is sampled every 50 ms.*

```python
settings = replace(components.settings, concurrency=concurrency)
reset_tables(components.database, settings.root / "sql")
model = FakeModel(delay_seconds=delay, max_rps=max_rps)
handler = EventHandler(
    components.queue,
    components.effects,
    build_extractor(settings, model),
    SystemClock(),
    RetryPolicy(max_attempts=12, base_seconds=0.2, cap_seconds=2.0, event_deadline_seconds=600.0),
)
```

- `settings = replace(components.settings, concurrency=concurrency)`: stores the result of calling `replace(components.settings, concurrency=concurrency)`, which replaces `components.settings` with the second argument in  The named values are `concurrency`. in `settings`.
- `reset_tables(components.database, settings.root / "sql")`: calling `reset_tables(components.database, settings.root / "sql")`, which is this repository's own `reset_tables` (in `src/inbox_worker/infrastructure/postgres.py`): empty every table (sql/reset.sql).
- `model = FakeModel(delay_seconds=delay, max_rps=max_rps)`: stores the result of calling `FakeModel(delay_seconds=delay, max_rps=max_rps)`, which is this repository's own `FakeModel` (in `src/inbox_worker/infrastructure/fake_model.py`): thread-safe; counts calls, rate-limit errors and injected errors in `model`.
- `handler = EventHandler( components.queue, components.effects, build...`: stores the result of calling `EventHandler( components.queue, components.effects, build_extractor(settings, model), S...`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it in `handler`.

```python
stop = threading.Event()
worker = Worker(
    components.queue,
    handler,
    concurrency=concurrency,
    lease_seconds=30.0,
    stop_requested=stop.is_set,
    wait=stop.wait,
    idle_poll_seconds=0.02,
)
```

- `stop = threading.Event()`: stores the result of calling `threading.Event()`, which makes a `Event` object in `stop`.
- `worker = Worker( components.queue, handler, concurrency=concurrency...`: stores the result of calling `Worker( components.queue, handler, concurrency=concurrency, lease_seconds=30.0, stop_re...`, which is this repository's own `Worker` (in `src/inbox_worker/application/worker.py`): pulls batches from the queue in `worker`.

```python
inbox = generate_events(events, duplicate_rate=0.0, poison_rate=0.0)
depths: list[int] = []
sampling = threading.Event()
```

- `inbox = generate_events(events, duplicate_rate=0.0, poison_rate=0.0)`: stores the result of calling `generate_events(events, duplicate_rate=0.0, poison_rate=0.0)`, which is this repository's own `generate_events` (in `src/inbox_worker/application/generate_events.py`): `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable The named values are `duplicate_rate`, `poison_rate`. in `inbox`.
- `depths: list[int] = []`: stores a new list (empty) in `depths`, whose type is declared as `list[int]`.
- `sampling = threading.Event()`: stores the result of calling `threading.Event()`, which makes a `Event` object in `sampling`.

```python
def sample() -> None:
```

- Defines the function `sample`.
- Gives back a value of type `None`.

```python
while not sampling.is_set():
```

- Repeats the indented lines for as long as it is not the case that `sampling.is_set()` is true (the call asks whether the event `sampling` is set).

```python
depths.append(components.queue.depth())
sampling.wait(0.05)
```

- `depths.append(components.queue.depth())`: calling `depths.append(components.queue.depth())`, which adds `components.queue.depth()` to the end of `depths`.
- `sampling.wait(0.05)`: calling `sampling.wait(0.05)`, which waits for `sampling`.

```python
runner = threading.Thread(target=worker.run, daemon=True)
sampler = threading.Thread(target=sample, daemon=True)
started = time.monotonic()
runner.start()
sampler.start()
interval = seconds / events
```

- `runner = threading.Thread(target=worker.run, daemon=True)`: stores the result of calling `threading.Thread(target=worker.run, daemon=True)`, which makes a `Thread` object with the named values `target`, `daemon` in `runner`.
- `sampler = threading.Thread(target=sample, daemon=True)`: stores the result of calling `threading.Thread(target=sample, daemon=True)`, which makes a `Thread` object with the named values `target`, `daemon` in `sampler`.
- `started = time.monotonic()`: stores the result of calling `time.monotonic()`, which reads the monotonic clock (seconds; only differences mean anything) in `started`.
- `runner.start()`: calling `runner.start()`, which starts `runner`.
- `sampler.start()`: calling `sampler.start()`, which starts `sampler`.
- `interval = seconds / events`: stores `seconds / events`, which divides `seconds` and `events` in `interval`.

```python
for index, (event_id, payload) in enumerate(inbox.deliveries):
```

- Repeats the indented lines once for each item of `enumerate(inbox.deliveries)`, naming the current item the names `index`, `(event_id, payload)`.

```python
components.queue.put(event_id, payload)
pause = started + (index + 1) * interval - time.monotonic()
```

- `components.queue.put(event_id, payload)`: calling `components.queue.put(event_id, payload)`.
- `pause = started + (index + 1) * interval - time.monotonic()`: stores `started + (index + 1) * interval - time.monotonic()`, which subtracts `started + (index + 1) * interval` and `time.monotonic()` in `pause`.

```python
if pause > 0:
```

- Checks whether `pause` is greater than `0`. If so, the indented lines run.

```python
time.sleep(pause)
```

- `time.sleep(pause)`: calling `time.sleep(pause)`, which waits `pause` seconds.

```python
deadline = time.monotonic() + 120
```

- `deadline = time.monotonic() + 120`: stores `time.monotonic() + 120`, which adds `time.monotonic()` and `120` in `deadline`.

```python
while components.queue.depth() > 0 and time.monotonic() < deadline:
```

- Repeats the indented lines for as long as `components.queue.depth()` is greater than `0` and `time.monotonic()` is less than `deadline`.

```python
time.sleep(0.05)
```

- `time.sleep(0.05)`: calling `time.sleep(0.05)`, which waits `0.05` seconds.

```python
elapsed = time.monotonic() - started
stop.set()
sampling.set()
runner.join(timeout=10)
counts = components.reports.counts()
latencies = components.reports.event_to_ticket_seconds()
```

- `elapsed = time.monotonic() - started`: stores `time.monotonic() - started`, which subtracts `time.monotonic()` and `started` in `elapsed`.
- `stop.set()`: calling `stop.set()`, which sets `stop`.
- `sampling.set()`: calling `sampling.set()`, which sets `sampling`.
- `runner.join(timeout=10)`: calling `runner.join(timeout=10)`, which glues the items of its argument together with `runner` between them The named values are `timeout`..
- `counts = components.reports.counts()`: stores the result of calling `components.reports.counts()`, which is this repository's own `counts` (in `src/inbox_worker/infrastructure/postgres.py`): rows in the tables that matter in `counts`.
- `latencies = components.reports.event_to_ticket_seconds()`: stores the result of calling `components.reports.event_to_ticket_seconds()`, which is this repository's own `event_to_ticket_seconds` (in `src/inbox_worker/infrastructure/postgres.py`): seconds from the first delivery of each ticketed event to its ticket in `latencies`.

```python
return BurstResult(
    concurrency,
    events,
    elapsed,
    counts["tickets"] / elapsed,
    max(depths, default=0),
    percentile(latencies, 0.95),
    model.rate_limited,
    counts["tickets"],
    counts["dead_letters"],
    components.queue.depth() == 0,
)
```

- `return BurstResult( concurrency, events, elapsed, counts["tickets"]...`: ends the function and gives back the result of calling `BurstResult( concurrency, events, elapsed, counts["tickets"] / elapsed, max(depths, def...`, which is this repository's own `BurstResult` (in `src/inbox_worker/interfaces/measure.py`): what one burst measured.

```python
def run_crash_test(components: Components, point: str, events: int = 30) -> tuple[Counter[str], list[str], list[str]]:
```

- Defines the function `run_crash_test`.
- Parameters:
  - `components`, type `Components`.
  - `point`, type `str`.
  - `events`, type `int`, optional (default `30`).
- Gives back a value of type `tuple[Counter[str], list[str], list[str]]`.

```python
"""Kill the worker process at `point` (after the model call, or after the commit), restart it, and return the exit
codes, the event ids sent and the event ids that have tickets."""
```

- The docstring (documentation kept with the code) says: *Kill the worker process at `point` (after the model call, or after the commit), restart it, and return the exit codes, the event ids sent and the event ids that have tickets.*

```python
root = components.settings.root
reset_tables(components.database, root / "sql")
inbox = generate_events(events, duplicate_rate=0.0, poison_rate=0.0)
components.queue.put_many(list(inbox.deliveries))
base = {**os.environ, "CONCURRENCY": "1", "LEASE_SECONDS": "2", "MODEL_ADAPTER": "fake", "PROJECT_ROOT": str(root)}
command = [sys.executable, "-m", "inbox_worker.interfaces.cli", "worker", "--until-idle"]
```

- `root = components.settings.root`: stores `components.settings.root` in `root`.
- `reset_tables(components.database, root / "sql")`: calling `reset_tables(components.database, root / "sql")`, which is this repository's own `reset_tables` (in `src/inbox_worker/infrastructure/postgres.py`): empty every table (sql/reset.sql).
- `inbox = generate_events(events, duplicate_rate=0.0, poison_rate=0.0)`: stores the result of calling `generate_events(events, duplicate_rate=0.0, poison_rate=0.0)`, which is this repository's own `generate_events` (in `src/inbox_worker/application/generate_events.py`): `count` events, `duplicate_rate` of them delivered twice, `poison_rate` of them unprocessable The named values are `duplicate_rate`, `poison_rate`. in `inbox`.
- `components.queue.put_many(list(inbox.deliveries))`: calling `components.queue.put_many(list(inbox.deliveries))`, which is this repository's own `put_many` (in `src/inbox_worker/infrastructure/postgres.py`): insert many deliveries in one transaction (loading the sample events).
- `base = {**os.environ, "CONCURRENCY": "1", "LEASE_SECONDS": "2", "MO...`: stores a new dict with 5 entries in `base`.
- `command = [sys.executable, "-m", "inbox_worker.interfaces.cli", "wo...`: stores a new list holding 5 items in `command`.

```python
crashed = subprocess.run(command, env={**base, "CRASH_AT": point, "CRASH_AFTER": "7"}, cwd=root, check=False)
mid = components.reports.counts()
restarted = subprocess.run(command, env=base, cwd=root, check=False)
codes: Counter[str] = Counter(
    {f"crash run exit {crashed.returncode}": 1, f"restart exit {restarted.returncode}": 1}
)
codes[f"tickets after the crash: {mid['tickets']}"] = 1
return codes, [event_id for event_id, _ in inbox.deliveries], components.reports.ticket_event_ids()
```

- `crashed = subprocess.run(command, env={**base, "CRASH_AT": point, "...`: stores the result of calling `subprocess.run(command, env={**base, "CRASH_AT": point, "CRASH_AFTER": "7"}, cwd=root, ...`, which runs a program or a coroutine The named values are `env`, `cwd`, `check`. in `crashed`.
- `mid = components.reports.counts()`: stores the result of calling `components.reports.counts()`, which is this repository's own `counts` (in `src/inbox_worker/infrastructure/postgres.py`): rows in the tables that matter in `mid`.
- `restarted = subprocess.run(command, env=base, cwd=root, check=False)`: stores the result of calling `subprocess.run(command, env=base, cwd=root, check=False)`, which runs a program or a coroutine The named values are `env`, `cwd`, `check`. in `restarted`.
- `codes: Counter[str] = Counter( {f"crash run exit {crashed.returncod...`: stores the result of calling `Counter( {f"crash run exit {crashed.returncode}": 1, f"restart exit {restarted.returnco...`, which makes a `Counter` object from `{f"crash run exit {crashed.returncode}": 1, f"restart exit {restarted.returncode}": 1}` in `codes`, whose type is declared as `Counter[str]`.
- `codes[f"tickets after the crash: {mid['tickets']}"] = 1`: stores the number `1` in the slot `codes[f"tickets after the crash: {mid['tickets']}"]`.
- `return codes, [event_id for event_id, _ in inbox.deliveries], compo...`: ends the function and gives back a tuple of 3 items.

```python
def wait_for_port(url_ready: str, attempts: int = 100) -> None:
```

- Defines the function `wait_for_port`.
- Parameters:
  - `url_ready`, type `str`.
  - `attempts`, type `int`, optional (default `100`).
- Gives back a value of type `None`.

```python
"""Poll a URL until it answers 200."""
```

- The docstring (documentation kept with the code) says: *Poll a URL until it answers 200.*

```python
import urllib.error
import urllib.request
```

- `import urllib.error`: makes the module `urllib.error` available (the standard library's URL tools).
- `import urllib.request`: makes the module `urllib.request` available (the standard library's URL tools).

```python
for _ in range(attempts):
```

- Repeats the indented lines once for each item of `range(attempts)`, naming the current item `_`.

```python
try:
```

- Tries the indented lines. If an error happens inside, Python jumps to the matching `except` below.

```python
with urllib.request.urlopen(url_ready, timeout=1) as response:
```

- Opens `urllib.request.urlopen(url_ready, timeout=1)` as `response` for the indented lines, and cleans it up when they end (even after an error).

```python
if response.status == 200:
```

- Checks whether `response.status` equals `200`. If so, the indented lines run.

```python
return
```

- `return`: ends the function, giving back nothing (`None`).

```python
except (urllib.error.URLError, ConnectionError, TimeoutError):
```

- If an error of kind `(urllib.error.URLError, ConnectionError, TimeoutError)` happened above, runs the indented lines. The error is then handled and the program carries on after the whole `try`.

```python
time.sleep(0.1)
```

- `time.sleep(0.1)`: calling `time.sleep(0.1)`, which waits `0.1` seconds.

```python
raise RuntimeError(f"{url_ready} did not become ready")
```

- `raise RuntimeError(f"{url_ready} did not become ready")`: stops with an error of kind `RuntimeError` with the message `f"{url_ready} did not become ready"`. Whoever called this code must handle it or the program stops.

#### `src/inbox_worker/interfaces/webhook.py`

```python
"""The webhook: verify the signature, queue the event, answer 202. The model is nowhere on this path."""
```

- The docstring (documentation kept with the code) says: *The webhook: verify the signature, queue the event, answer 202. The model is nowhere on this path.*

```python
import logging
import time
from collections.abc import Callable
from typing import Annotated

from fastapi import FastAPI, Header, Request
from fastapi.concurrency import run_in_threadpool
```

- `import logging`: makes the module `logging` available (the standard library's logging system).
- `import time`: makes the module `time` available (clocks and sleeping).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Callable`: the type hint for a function value.)
- `from typing import ...`: takes names from `typing` (names used in type hints). (`Annotated`: attaches extra information to a type hint.)
- `from fastapi import ...`: takes names from `fastapi` (the web framework that turns Python functions into HTTP endpoints). (`FastAPI`: the application class.) (`Header`: reads an HTTP header into a parameter.) (`Request`: the incoming HTTP request.)
- `from fastapi.concurrency import ...`: takes names from `fastapi.concurrency` (the web framework that turns Python functions into HTTP endpoints). (`run_in_threadpool`: a name provided by that module.)

```python
from fastapi.responses import JSONResponse

from inbox_worker.application.ports import DeliveryQueue
from inbox_worker.domain.events import event_id_of
from inbox_worker.domain.signature import verify

LOGGER = logging.getLogger("inbox_worker.webhook")
```

- `from fastapi.responses import ...`: takes names from `fastapi.responses` (the web framework that turns Python functions into HTTP endpoints). (`JSONResponse`: an HTTP response whose body is JSON.)
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`DeliveryQueue`: A queue with acknowledgments and redelivery, in a database table read with row locks.)
- `from inbox_worker.domain.events import ...`: takes names from `inbox_worker.domain.events`, this repository's own code. (`event_id_of`: The event id a receiver files a payload under; a payload that is not an event gets a stable placeholder so it can still be queued, parked....)
- `from inbox_worker.domain.signature import ...`: takes names from `inbox_worker.domain.signature`, this repository's own code. (`verify`: (ok, reason).)
- `LOGGER = logging.getLogger("inbox_worker.webhook")`: stores the result of calling `logging.getLogger("inbox_worker.webhook")`, which gets the logger named `"inbox_worker.webhook"` in `LOGGER`.

```python
def create_app(
    queue: DeliveryQueue,
    secret: bytes,
    max_bytes: int,
    ready: Callable[[], bool],
    clock: Callable[[], float] = time.time,
) -> FastAPI:
```

- Defines the function `create_app`.
- Parameters:
  - `queue`, type `DeliveryQueue`.
  - `secret`, type `bytes`.
  - `max_bytes`, type `int`.
  - `ready`, type `Callable[[], bool]`.
  - `clock`, type `Callable[[], float]`, optional (default `time.time`).
- Gives back a value of type `FastAPI`.

```python
"""Build the app. `clock` is injected so a test can send a request that is five minutes old."""
```

- The docstring (documentation kept with the code) says: *Build the app. `clock` is injected so a test can send a request that is five minutes old.*

```python
app = FastAPI(title="Inbox webhook", version="0.1.0")
```

- `app = FastAPI(title="Inbox webhook", version="0.1.0")`: stores the result of calling `FastAPI(title="Inbox webhook", version="0.1.0")`, which makes a `FastAPI` object with the named values `title`, `version` in `app`.

```python
@app.post("/webhook/email", status_code=202)
async def receive(
    request: Request,
    x_timestamp: Annotated[str | None, Header()] = None,
    x_signature: Annotated[str | None, Header()] = None,
) -> JSONResponse:
```

- Defines the async function `receive` (a coroutine: calling it makes a job for the event loop to run).
- `@app.post("/webhook/email", status_code=202)`: registers the function with the web application: it runs when a matching request arrives.
- Parameters:
  - `request`, type `Request`.
  - `x_timestamp`, type `Annotated[str | None, Header()]`, optional (default `None`).
  - `x_signature`, type `Annotated[str | None, Header()]`, optional (default `None`).
- Gives back a value of type `JSONResponse`.

> **`async def` and `await`.** An `async def` function is a coroutine: calling it does not run the body but makes an object that the event loop runs. `await` inside it pauses this function until the awaited thing is ready, and lets the loop run other work meanwhile, all on one thread.

```python
body = bytearray()
```

- `body = bytearray()`: stores the result of calling `bytearray()`, which builds a changeable byte buffer in `body`.

```python
async for chunk in request.stream():
```

- Repeats the indented lines once for each item of `request.stream()`, naming the current item `chunk`. (`async for` waits for each item.)

```python
body.extend(chunk)
```

- `body.extend(chunk)`: calling `body.extend(chunk)`, which adds every item of `chunk` to the end of `body`.

```python
if len(body) > max_bytes:
```

- Checks whether `len(body)` is greater than `max_bytes`. If so, the indented lines run.

```python
return JSONResponse({"error": f"body larger than {max_bytes} bytes"}, status_code=413)
```

- `return JSONResponse({"error": f"body larger than {max_bytes} bytes"...`: ends the function and gives back the result of calling `JSONResponse({"error": f"body larger than {max_bytes} bytes"}, status_code=413)`, which makes a `JSONResponse` object from `{"error": f"body larger than {max_bytes} bytes"}` with the named values `status_code`.

```python
payload = body.decode("utf-8", "replace")
ok, reason = verify(secret, x_timestamp or "", payload, x_signature or "", clock())
```

- `payload = body.decode("utf-8", "replace")`: stores the result of calling `body.decode("utf-8", "replace")`, which turns the bytes `body` into text in `payload`.
- `ok, reason = verify(secret, x_timestamp or "", payload, x_signature...`: unpacks the result of calling `verify(secret, x_timestamp or "", payload, x_signature or "", clock())`, which is this repository's own `verify` (in `src/inbox_worker/domain/signature.py`): (ok, reason) into the names `ok`, `reason`, one item each.

```python
if not ok:
```

- Checks whether it is not the case that `ok` is truthy (not `None`, `False`, zero or empty). If so, the indented lines run.

```python
LOGGER.warning("webhook rejected", extra={"fields": {"reason": reason}})
return JSONResponse({"error": reason}, status_code=401)
```

- `LOGGER.warning("webhook rejected", extra={"fields": {"reason": reas...`: calling `LOGGER.warning("webhook rejected", extra={"fields": {"reason": reason}})`, which writes a WARNING log line The named values are `extra`..
- `return JSONResponse({"error": reason}, status_code=401)`: ends the function and gives back the result of calling `JSONResponse({"error": reason}, status_code=401)`, which makes a `JSONResponse` object from `{"error": reason}` with the named values `status_code`.

```python
delivery_id = await run_in_threadpool(queue.put, event_id_of(payload), payload)
return JSONResponse({"delivery_id": delivery_id}, status_code=202)
```

- `delivery_id = await run_in_threadpool(queue.put, event_id_of(payloa...`: stores the answer of the result of calling `run_in_threadpool(queue.put, event_id_of(payload), payload)` once the wait is over in `delivery_id`.
- `return JSONResponse({"delivery_id": delivery_id}, status_code=202)`: ends the function and gives back the result of calling `JSONResponse({"delivery_id": delivery_id}, status_code=202)`, which makes a `JSONResponse` object from `{"delivery_id": delivery_id}` with the named values `status_code`.

```python
@app.get("/healthz")
def healthz() -> dict[str, str]:
```

- Defines the function `healthz`.
- `@app.get("/healthz")`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `dict[str, str]`.

```python
return {"status": "ok"}
```

- `return {"status": "ok"}`: ends the function and gives back a new dict with 1 entries.

```python
@app.get("/readyz")
def readyz() -> JSONResponse:
```

- Defines the function `readyz`.
- `@app.get("/readyz")`: registers the function with the web application: it runs when a matching request arrives.
- Gives back a value of type `JSONResponse`.

```python
if ready():
```

- Checks whether `ready()` is true. If so, the indented lines run.

```python
return JSONResponse({"status": "ready"})
```

- `return JSONResponse({"status": "ready"})`: ends the function and gives back the result of calling `JSONResponse({"status": "ready"})`, which makes a `JSONResponse` object from `{"status": "ready"}`.

```python
return JSONResponse({"status": "database unavailable"}, status_code=503)
```

- `return JSONResponse({"status": "database unavailable"}, status_code...`: ends the function and gives back the result of calling `JSONResponse({"status": "database unavailable"}, status_code=503)`, which makes a `JSONResponse` object from `{"status": "database unavailable"}` with the named values `status_code`.

```python
return app
```

- `return app`: ends the function and gives back the value of `app`.

#### `src/inbox_worker/interfaces/wiring.py`

```python
"""Compose the database, model, handler, worker and relay the settings ask for."""
```

- The docstring (documentation kept with the code) says: *Compose the database, model, handler, worker and relay the settings ask for.*

```python
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from inbox_worker.application.extraction import TicketExtractor
```

- `from __future__ import ...`: takes names from `__future__` (a special module whose imports switch on language behavior). (`annotations`: makes type hints be stored as text and read later, so a hint may name something defined further down.)
- `import os`: makes the module `os` available (operating-system services: environment variables, paths, processes).
- `from collections.abc import ...`: takes names from `collections.abc` (the standard library's extra container types (Counter, defaultdict, deque)). (`Callable`: the type hint for a function value.)
- `from dataclasses import ...`: takes names from `dataclasses` (writes the boring parts of a plain data class for you). (`dataclass`: the decorator that builds a data class.)
- `from pathlib import ...`: takes names from `pathlib` (file paths as objects). (`Path`: a file path object; `/` joins parts, and it has methods to read, write and test files.)
- `from inbox_worker.application.extraction import ...`: takes names from `inbox_worker.application.extraction`, this repository's own code. (`TicketExtractor`: Model-backed extraction.)

```python
from inbox_worker.application.handler import EventHandler, RetryPolicy
from inbox_worker.application.ports import ChatModel
from inbox_worker.infrastructure.cassette import RecordedModel
from inbox_worker.infrastructure.claude_model import ClaudeModel
from inbox_worker.infrastructure.clock import SystemClock
from inbox_worker.infrastructure.fake_model import FakeModel
```

- `from inbox_worker.application.handler import ...`: takes names from `inbox_worker.application.handler`, this repository's own code. (`EventHandler`: Applies each event's effects once, however often the queue delivers it.) (`RetryPolicy`: How a failing event is retried before it is parked.)
- `from inbox_worker.application.ports import ...`: takes names from `inbox_worker.application.ports`, this repository's own code. (`ChatModel`: A text model.)
- `from inbox_worker.infrastructure.cassette import ...`: takes names from `inbox_worker.infrastructure.cassette`, this repository's own code. (`RecordedModel`: Replays replies from a cassette file; a request with no recording fails loudly.)
- `from inbox_worker.infrastructure.claude_model import ...`: takes names from `inbox_worker.infrastructure.claude_model`, this repository's own code. (`ClaudeModel`: One Messages API call per request.)
- `from inbox_worker.infrastructure.clock import ...`: takes names from `inbox_worker.infrastructure.clock`, this repository's own code. (`SystemClock`: Now, in UTC.)
- `from inbox_worker.infrastructure.fake_model import ...`: takes names from `inbox_worker.infrastructure.fake_model`, this repository's own code. (`FakeModel`: Thread-safe; counts calls, rate-limit errors and injected errors.)

```python
from inbox_worker.infrastructure.postgres import (
    Database,
    FakeMailSender,
    PostgresEffects,
    PostgresOutbox,
    PostgresQueue,
    PostgresReports,
)
```

- `from inbox_worker.infrastructure.postgres import ...`: takes names from `inbox_worker.infrastructure.postgres`, this repository's own code. (`Database`: A small connection pool over one database URL.) (`FakeMailSender`: Records every send in `sent_mail`; the unique event id refuses a second send of one acknowledgment.) (`PostgresEffects`: The processed mark, the ticket and the outbox row.) (`PostgresOutbox`: The unsent acknowledgments.) (`PostgresQueue`: The delivery queue.) (`PostgresReports`: Read-only queries for the reports and the verification steps.)

```python
from inbox_worker.infrastructure.prompt_file import read_prompt
from inbox_worker.infrastructure.settings import Settings
```

- `from inbox_worker.infrastructure.prompt_file import ...`: takes names from `inbox_worker.infrastructure.prompt_file`, this repository's own code. (`read_prompt`: Read `---`, header lines, `---`, then the prompt text; both fences are required.)
- `from inbox_worker.infrastructure.settings import ...`: takes names from `inbox_worker.infrastructure.settings`, this repository's own code. (`Settings`: Everything the programs read from the environment.)

```python
@dataclass(frozen=True, slots=True)
class Components:
```

- Defines the class `Components`.
- `@dataclass(frozen=True, slots=True)`: builds `__init__`, `__repr__` and `__eq__` from the annotated fields; objects cannot be changed after creation, attributes are stored compactly.

```python
"""Everything a command needs, built once."""
```

- The docstring (documentation kept with the code) says: *Everything a command needs, built once.*

```python
settings: Settings
database: Database
queue: PostgresQueue
effects: PostgresEffects
outbox: PostgresOutbox
mail: FakeMailSender
reports: PostgresReports
```

- `settings: Settings`: a field named `settings` of type `Settings`, no default (must be given).
- `database: Database`: a field named `database` of type `Database`, no default (must be given).
- `queue: PostgresQueue`: a field named `queue` of type `PostgresQueue`, no default (must be given).
- `effects: PostgresEffects`: a field named `effects` of type `PostgresEffects`, no default (must be given).
- `outbox: PostgresOutbox`: a field named `outbox` of type `PostgresOutbox`, no default (must be given).
- `mail: FakeMailSender`: a field named `mail` of type `FakeMailSender`, no default (must be given).
- `reports: PostgresReports`: a field named `reports` of type `PostgresReports`, no default (must be given).

```python
def build_components(settings: Settings) -> Components:
```

- Defines the function `build_components`.
- Parameters:
  - `settings`, type `Settings`.
- Gives back a value of type `Components`.

```python
"""Wire the PostgreSQL adapters over one pool sized for the worker's concurrency."""
```

- The docstring (documentation kept with the code) says: *Wire the PostgreSQL adapters over one pool sized for the worker's concurrency.*

```python
database = Database(settings.database_url, max_connections=settings.concurrency + 6)
return Components(
    settings,
    database,
    PostgresQueue(database),
    PostgresEffects(database),
    PostgresOutbox(database),
    FakeMailSender(database),
    PostgresReports(database),
)
```

- `database = Database(settings.database_url, max_connections=settings...`: stores the result of calling `Database(settings.database_url, max_connections=settings.concurrency + 6)`, which is this repository's own `Database` (in `src/inbox_worker/infrastructure/postgres.py`): a small connection pool over one database URL in `database`.
- `return Components( settings, database, PostgresQueue(database), Pos...`: ends the function and gives back the result of calling `Components( settings, database, PostgresQueue(database), PostgresEffects(database), Pos...`, which is this repository's own `Components` (in `src/inbox_worker/interfaces/wiring.py`): everything a command needs, built once.

```python
def build_model(settings: Settings) -> ChatModel:
```

- Defines the function `build_model`.
- Parameters:
  - `settings`, type `Settings`.
- Gives back a value of type `ChatModel`.

```python
"""The fake model (load tests), the recorded adapter (offline smoke run), or Claude."""
```

- The docstring (documentation kept with the code) says: *The fake model (load tests), the recorded adapter (offline smoke run), or Claude.*

```python
if settings.model_adapter == "claude":
```

- Checks whether `settings.model_adapter` equals `"claude"`. If so, the indented lines run.

```python
return ClaudeModel(settings.model_id, settings.anthropic_api_key)
```

- `return ClaudeModel(settings.model_id, settings.anthropic_api_key)`: ends the function and gives back the result of calling `ClaudeModel(settings.model_id, settings.anthropic_api_key)`, which is this repository's own `ClaudeModel` (in `src/inbox_worker/infrastructure/claude_model.py`): one Messages API call per request.

```python
if settings.model_adapter == "recorded":
```

- Checks whether `settings.model_adapter` equals `"recorded"`. If so, the indented lines run.

```python
return RecordedModel(settings.root / settings.cassette)
```

- `return RecordedModel(settings.root / settings.cassette)`: ends the function and gives back the result of calling `RecordedModel(settings.root / settings.cassette)`, which is this repository's own `RecordedModel` (in `src/inbox_worker/infrastructure/cassette.py`): replays replies from a cassette file; a request with no recording fails loudly.

```python
return FakeModel(
    delay_seconds=settings.fake_delay_seconds, error_rate=settings.fake_error_rate, max_rps=settings.fake_max_rps
)
```

- `return FakeModel( delay_seconds=settings.fake_delay_seconds, error_...`: ends the function and gives back the result of calling `FakeModel( delay_seconds=settings.fake_delay_seconds, error_rate=settings.fake_error_ra...`, which is this repository's own `FakeModel` (in `src/inbox_worker/infrastructure/fake_model.py`): thread-safe; counts calls, rate-limit errors and injected errors.

```python
def retry_policy(settings: Settings) -> RetryPolicy:
```

- Defines the function `retry_policy`.
- Parameters:
  - `settings`, type `Settings`.
- Gives back a value of type `RetryPolicy`.

```python
"""The retry settings as a value."""
```

- The docstring (documentation kept with the code) says: *The retry settings as a value.*

```python
return RetryPolicy(
    settings.max_attempts,
    settings.backoff_base_seconds,
    settings.backoff_cap_seconds,
    settings.event_deadline_seconds,
)
```

- `return RetryPolicy( settings.max_attempts, settings.backoff_base_se...`: ends the function and gives back the result of calling `RetryPolicy( settings.max_attempts, settings.backoff_base_seconds, settings.backoff_cap...`, which is this repository's own `RetryPolicy` (in `src/inbox_worker/application/handler.py`): how a failing event is retried before it is parked.

```python
def crash_hook_from_environment() -> Callable[[str], None]:
```

- Defines the function `crash_hook_from_environment`.
- Gives back a value of type `Callable[[str], None]`.

```python
"""For the crash tests: `CRASH_AT=<point>` and `CRASH_AFTER=<n>` kill the process (exit code 137, as SIGKILL would)
the n-th time the handler reaches that point. Unset, it does nothing."""
```

- The docstring (documentation kept with the code) says: *For the crash tests: `CRASH_AT=<point>` and `CRASH_AFTER=<n>` kill the process (exit code 137, as SIGKILL would) the n-th time the handler reaches that point. Unset, it does nothing.*

```python
point, after = os.environ.get("CRASH_AT"), int(os.environ.get("CRASH_AFTER", "1"))
seen = {"count": 0}
```

- `point, after = os.environ.get("CRASH_AT"), int(os.environ.get("CRAS...`: unpacks a tuple of 2 items into the names `point`, `after`, one item each.
- `seen = {"count": 0}`: stores a new dict with 1 entries in `seen`.

```python
def hook(reached: str) -> None:
```

- Defines the function `hook`.
- Parameters:
  - `reached`, type `str`.
- Gives back a value of type `None`.

```python
if point and reached == point:
```

- Checks whether `point` is truthy (not `None`, `False`, zero or empty) and `reached` equals `point`. If so, the indented lines run.

```python
seen["count"] += 1
```

- `seen["count"] += 1`: adds `1` to `seen["count"]` and keeps the result there.

```python
if seen["count"] >= after:
```

- Checks whether `seen["count"]` is greater than or equal to `after`. If so, the indented lines run.

```python
os._exit(137)
```

- `os._exit(137)`: calling `os._exit(137)`.

```python
return hook
```

- `return hook`: ends the function and gives back the value of `hook`.

```python
PROMPT_FILE = Path("prompts/extract.v1.md")
```

- `PROMPT_FILE = Path("prompts/extract.v1.md")`: stores the result of calling `Path("prompts/extract.v1.md")`, which makes a `Path` object from `"prompts/extract.v1.md"` in `PROMPT_FILE`.

```python
def build_extractor(settings: Settings, model: ChatModel) -> TicketExtractor:
```

- Defines the function `build_extractor`.
- Parameters:
  - `settings`, type `Settings`.
  - `model`, type `ChatModel`.
- Gives back a value of type `TicketExtractor`.

```python
"""The extractor over the model, with the prompt text and version read from the versioned prompt file."""
```

- The docstring (documentation kept with the code) says: *The extractor over the model, with the prompt text and version read from the versioned prompt file.*

```python
prompt = read_prompt(settings.root / PROMPT_FILE)
return TicketExtractor(model, prompt.text, prompt.version)
```

- `prompt = read_prompt(settings.root / PROMPT_FILE)`: stores the result of calling `read_prompt(settings.root / PROMPT_FILE)`, which is this repository's own `read_prompt` (in `src/inbox_worker/infrastructure/prompt_file.py`): read `---`, header lines, `---`, then the prompt text; both fences are required in `prompt`.
- `return TicketExtractor(model, prompt.text, prompt.version)`: ends the function and gives back the result of calling `TicketExtractor(model, prompt.text, prompt.version)`, which is this repository's own `TicketExtractor` (in `src/inbox_worker/application/extraction.py`): model-backed extraction.

```python
def build_handler(
    components: Components, model: ChatModel, crash_at: Callable[[str], None] | None = None
) -> EventHandler:
```

- Defines the function `build_handler`.
- Parameters:
  - `components`, type `Components`.
  - `model`, type `ChatModel`.
  - `crash_at`, type `Callable[[str], None] | None`, optional (default `None`).
- Gives back a value of type `EventHandler`.

```python
"""The event handler over the components' queue and effects store."""
```

- The docstring (documentation kept with the code) says: *The event handler over the components' queue and effects store.*

```python
settings = components.settings
return EventHandler(
    components.queue,
    components.effects,
    build_extractor(settings, model),
    SystemClock(),
    retry_policy(settings),
    crash_at=crash_at or (lambda point: None),
)
```

- `settings = components.settings`: stores `components.settings` in `settings`.
- `return EventHandler( components.queue, components.effects, build_ex...`: ends the function and gives back the result of calling `EventHandler( components.queue, components.effects, build_extractor(settings, model), S...`, which is this repository's own `EventHandler` (in `src/inbox_worker/application/handler.py`): applies each event's effects once, however often the queue delivers it.

<!-- /fullwalk -->

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
