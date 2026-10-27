# Threads and thread pools (threading, concurrent.futures)

## What it is

A *thread* is a separate line of execution inside one program. A *thread pool* is a fixed group of threads that take jobs from a queue. They let a program wait for several slow things (a model call, a database call) at the same time.

## Why this repository uses it

The worker handles several events at once on a pool of threads, and the model call and the database calls are all waiting on other programs. A fixed-size pool bounds how much runs at once, which is the concurrency limit the burst measurement varies.

## Where it appears

| File | What it does with Threads and thread pools (threading, concurrent.futures) |
| --- | --- |
| `src/inbox_worker/application/worker.py` | `Worker` and its `ThreadPoolExecutor` |
| `src/inbox_worker/infrastructure/fake_model.py` | a lock around the token bucket |
| `src/inbox_worker/infrastructure/shutdown.py` | a `threading.Event` for a graceful stop |
| `src/inbox_worker/interfaces/measure.py` | the burst's feeder and sampler threads |

## How it works underneath

`ThreadPoolExecutor(max_workers=N)` starts up to N threads. `executor.submit(function, args)` returns a *future*, an object for a result that is not ready yet; `future.result(timeout=...)` waits and raises `TimeoutError` if too slow. `executor.map(function, items)` runs the function on each item and returns results in order. A `threading.Lock` lets only one thread at a time run a protected block; `threading.Event` lets one thread signal others (used for 'stop now').

In CPython only one thread runs Python code at a time (the *global interpreter lock*), but threads that wait for input and output do not hold it, so a pool works well for waiting on networks and databases. A thread cannot be killed from outside: a call that never returns keeps its thread busy until its own timeout, which is why callers set timeouts. Shared state needs a lock, or each thread must work on its own data.

## Walkthrough of this repository's use

From `src/inbox_worker/application/worker.py`:

```python
class Worker:
    """Pulls batches from the queue. A shutdown request finishes the deliveries in flight and then returns."""
```

- `class Worker:`: The loop that claims deliveries and handles them.
- `"""Pulls batches from the queue. A shutdown request finishes the deliveries in flight and then returns."""`: The docstring: a shutdown request finishes the deliveries in flight and then returns.

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
        self._queue = queue
        self._handler = handler
        self._concurrency = concurrency
        self._lease = lease_seconds
        self._stop = stop_requested
        self._wait = wait
        self._idle = idle_poll_seconds
```

- `def __init__(`: The constructor; its parameters follow.
- `self,`: The object itself.
- `queue: DeliveryQueue,`: A collaborator passed in (the queue, the handler).
- `handler: EventHandler,`: A collaborator passed in (the queue, the handler).
- `*,`: Everything after this must be passed by name.
- `concurrency: int,`: A setting: how many events at once, and how long a claim lasts.
- `lease_seconds: float,`: A setting: how many events at once, and how long a claim lasts.
- `stop_requested: Callable[[], bool],`: Functions passed in so tests can fake the stop signal and the waiting.
- `wait: Callable[[float], bool],`: Functions passed in so tests can fake the stop signal and the waiting.
- `idle_poll_seconds: float = 0.2,`: How long to wait when the queue is empty.
- `) -> None:`: Closes the parameter list.
- `self._queue = queue`: Keeps `queue`.
- `self._handler = handler`: Keeps `handler`.
- `self._concurrency = concurrency`: Keeps `concurrency`.
- `self._lease = lease_seconds`: Keeps `lease_seconds`.
- `self._stop = stop_requested`: Keeps `stop_requested`.
- `self._wait = wait`: Keeps `wait`.
- `self._idle = idle_poll_seconds`: Keeps `idle_poll_seconds`.

```python
    def _handle_safely(self, delivery: Delivery) -> str:
        """A failure the handler did not classify is logged and left to the lease: the delivery comes back."""
        try:
            return self._handler.handle(delivery)
        except Exception:
            LOGGER.exception("delivery failed unexpectedly", extra={"fields": {"delivery_id": delivery.delivery_id}})
            return "error"
```

- `def _handle_safely(self, delivery: Delivery) -> str:`: Runs the handler for one delivery and never lets an unexpected error escape the pool thread.
- `"""A failure the handler did not classify is logged and left to the lease: the delivery comes back."""`: The docstring: it is logged and left to the lease, so the delivery comes back.
- `try:`: Guards the handler call.
- `return self._handler.handle(delivery)`: Handles it and returns the outcome.
- `except Exception:`: Any error nobody expected.
- `LOGGER.exception("delivery failed unexpectedly", extra={"fields": {"delivery_id": delivery.delivery_id}})`: Logs the error with its traceback and the delivery id.
- `return "error"`: Reports an `error` outcome. The delivery is not acknowledged; when its lease expires it is claimed again.

```python
    def run(self, *, until_idle: bool = False) -> Counter[str]:
        """Process deliveries until a stop is requested (or, with `until_idle`, until the queue is empty)."""
        outcomes: Counter[str] = Counter()
        with ThreadPoolExecutor(max_workers=self._concurrency, thread_name_prefix="handle") as pool:
            failures = 0
            while not self._stop():
                try:
                    batch = self._queue.claim(self._concurrency, self._lease)
                    if not batch and until_idle and self._queue.depth() == 0:
                        break
                except Exception:
                    # The queue is unreachable (database restart, failover). Nothing is lost: claimed rows come
                    # back when their lease expires. Wait with a growing pause and try again.
                    failures += 1
                    LOGGER.exception("queue unavailable", extra={"fields": {"consecutive_failures": failures}})
                    outcomes["queue_error"] += 1
                    self._wait(min(self._idle * 2**failures, MAX_BACKOFF_SECONDS))
                    continue
                failures = 0
                if not batch:
                    self._wait(self._idle)
                    continue
                for outcome in pool.map(self._handle_safely, batch):
                    outcomes[outcome] += 1
        LOGGER.info("worker stopped", extra={"fields": dict(outcomes)})
        return outcomes
```

- `def run(self, *, until_idle: bool = False) -> Counter[str]:`: The main loop. With `until_idle` it ends when the queue is empty.
- `` """Process deliveries until a stop is requested (or, with `until_idle`, until the queue is empty).""" ``: The docstring.
- `outcomes: Counter[str] = Counter()`: A `Counter` is a dict that counts: `outcomes['processed'] += 1`.
- `with ThreadPoolExecutor(max_workers=self._concurrency, thread_name_prefix="handle") as pool:`: Creates the pool of worker threads for the whole run; leaving the `with` block waits for the running jobs and shuts it down.
- `failures = 0`: Counts consecutive failures to reach the queue.
- `while not self._stop():`: Repeats until a stop was requested.
- `try:`: Guards the handler call.
- `batch = self._queue.claim(self._concurrency, self._lease)`: Claims up to `concurrency` deliveries.
- `if not batch and until_idle and self._queue.depth() == 0:`: Nothing was claimed, `until_idle` is on, and nothing is queued or in flight: done.
- `break`: Leaves the loop.
- `except Exception:`: Any error nobody expected.
- `# The queue is unreachable (database restart, failover). Nothing is lost: claimed rows come`: A comment.
- `# back when their lease expires. Wait with a growing pause and try again.`: A comment.
- `failures += 1`: One more failure in a row.
- `LOGGER.exception("queue unavailable", extra={"fields": {"consecutive_failures": failures}})`: Logs it.
- `outcomes["queue_error"] += 1`: Counts it.
- `self._wait(min(self._idle * 2**failures, MAX_BACKOFF_SECONDS))`: Waits longer after each failure (doubling), up to a cap of ten seconds. Because the wait is the injected function, a stop request wakes it.
- `continue`: Goes back to the top of the loop and tries the queue again.
- `failures = 0`: Counts consecutive failures to reach the queue.
- `if not batch:`: The queue was empty.
- `self._wait(self._idle)`: Wait a little before asking again.
- `continue`: Goes back to the top of the loop and tries the queue again.
- `for outcome in pool.map(self._handle_safely, batch):`: `pool.map(function, items)` runs the function on every item on the pool's threads at the same time and gives back the results in order. The loop waits until the whole batch is done.
- `outcomes[outcome] += 1`: Counts the outcome.
- `LOGGER.info("worker stopped", extra={"fields": dict(outcomes)})`: Logs the totals when the loop ends.
- `return outcomes`: Returns them.

### Graceful stop

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
.venv/bin/pytest tests/unit/application -q -k worker
```

Runs the worker tests, including 'waits and retries when the queue is unreachable'.

```bash
make burst
```

Runs the worker at two concurrency limits and prints the throughput table.

```bash
make worker
```

Processes whatever is queued and exits when the queue is empty.

## Mistakes people make

- Sharing a mutable object between threads without a lock.
- Waiting for a thread without a timeout.
- Assuming a deadline stops the work. The caller stops waiting; the worker thread ends when its own call times out.
- Creating too many threads; the pool size is fixed by a setting.
- Calling thread-unsafe code from several threads.

## Check yourself

1. What is a thread pool?
   *Answer:* A fixed group of threads that run submitted jobs.
2. What is a future?
   *Answer:* An object representing a result that will be ready later.
3. What does `future.result(timeout=2)` do if the job takes longer?
   *Answer:* Raises `TimeoutError`; the job itself may still be running.
4. What does a `Lock` do?
   *Answer:* Allows only one thread at a time into a protected block.
5. Why do threads help for network waits?
   *Answer:* A waiting thread does not hold the interpreter lock, so other threads run.

## Further reading

- [concurrent.futures](https://docs.python.org/3.12/library/concurrent.futures.html)
- [threading](https://docs.python.org/3.12/library/threading.html)
