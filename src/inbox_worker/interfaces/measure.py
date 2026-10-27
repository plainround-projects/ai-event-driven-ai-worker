"""Measurements that need threads and a database: the burst, the crash recovery and the webhook latency."""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from collections import Counter
from dataclasses import dataclass, replace

from inbox_worker.application.generate_events import generate_events
from inbox_worker.application.handler import EventHandler, RetryPolicy
from inbox_worker.application.worker import Worker
from inbox_worker.domain.stats import percentile
from inbox_worker.infrastructure.clock import SystemClock
from inbox_worker.infrastructure.fake_model import FakeModel
from inbox_worker.infrastructure.postgres import reset_tables
from inbox_worker.interfaces.wiring import Components, build_extractor


@dataclass(frozen=True, slots=True)
class BurstResult:
    """What one burst measured."""

    concurrency: int
    events: int
    seconds_to_drain: float
    throughput_per_second: float
    peak_queue_depth: int
    p95_event_to_ticket_seconds: float
    rate_limit_errors: int
    tickets: int
    dead_letters: int
    drained: bool


def run_burst(
    components: Components, *, events: int, seconds: float, concurrency: int, delay: float, max_rps: float
) -> BurstResult:
    """Send `events` events over `seconds` to a worker with `concurrency` threads, against a fake model with a rate limit.

    Throughput is tickets over the time from the first event to an empty queue. The queue depth is sampled every 50 ms.
    """
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
    inbox = generate_events(events, duplicate_rate=0.0, poison_rate=0.0)
    depths: list[int] = []
    sampling = threading.Event()

    def sample() -> None:
        while not sampling.is_set():
            depths.append(components.queue.depth())
            sampling.wait(0.05)

    runner = threading.Thread(target=worker.run, daemon=True)
    sampler = threading.Thread(target=sample, daemon=True)
    started = time.monotonic()
    runner.start()
    sampler.start()
    interval = seconds / events
    for index, (event_id, payload) in enumerate(inbox.deliveries):
        components.queue.put(event_id, payload)
        pause = started + (index + 1) * interval - time.monotonic()
        if pause > 0:
            time.sleep(pause)
    deadline = time.monotonic() + 120
    while components.queue.depth() > 0 and time.monotonic() < deadline:
        time.sleep(0.05)
    elapsed = time.monotonic() - started
    stop.set()
    sampling.set()
    runner.join(timeout=10)
    counts = components.reports.counts()
    latencies = components.reports.event_to_ticket_seconds()
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


def run_crash_test(components: Components, point: str, events: int = 30) -> tuple[Counter[str], list[str], list[str]]:
    """Kill the worker process at `point` (after the model call, or after the commit), restart it, and return the exit
    codes, the event ids sent and the event ids that have tickets."""
    root = components.settings.root
    reset_tables(components.database, root / "sql")
    inbox = generate_events(events, duplicate_rate=0.0, poison_rate=0.0)
    components.queue.put_many(list(inbox.deliveries))
    base = {**os.environ, "CONCURRENCY": "1", "LEASE_SECONDS": "2", "MODEL_ADAPTER": "fake", "PROJECT_ROOT": str(root)}
    command = [sys.executable, "-m", "inbox_worker.interfaces.cli", "worker", "--until-idle"]
    crashed = subprocess.run(command, env={**base, "CRASH_AT": point, "CRASH_AFTER": "7"}, cwd=root, check=False)
    mid = components.reports.counts()
    restarted = subprocess.run(command, env=base, cwd=root, check=False)
    codes: Counter[str] = Counter(
        {f"crash run exit {crashed.returncode}": 1, f"restart exit {restarted.returncode}": 1}
    )
    codes[f"tickets after the crash: {mid['tickets']}"] = 1
    return codes, [event_id for event_id, _ in inbox.deliveries], components.reports.ticket_event_ids()


def wait_for_port(url_ready: str, attempts: int = 100) -> None:
    """Poll a URL until it answers 200."""
    import urllib.error
    import urllib.request

    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url_ready, timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(0.1)
    raise RuntimeError(f"{url_ready} did not become ready")
