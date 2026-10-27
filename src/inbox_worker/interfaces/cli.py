"""The `inbox-worker` command: database, events, webhook, worker, relay, redrive, measurements."""

import argparse
import json
import logging
import os
import socket
import sys
import threading
import time
from collections.abc import Sequence

import httpx

from inbox_worker.application.generate_events import generate_events
from inbox_worker.application.outbox import OutboxRelay
from inbox_worker.application.worker import Worker
from inbox_worker.domain.signature import sign, verify
from inbox_worker.domain.stats import percentile
from inbox_worker.infrastructure.cassette import MissingRecordingError
from inbox_worker.infrastructure.environment import ConfigurationError
from inbox_worker.infrastructure.logging import configure_logging
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

LOGGER = logging.getLogger("inbox_worker")


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


def _status(components: Components) -> int:
    counts = components.reports.counts()
    print("counts:", counts)
    for dead_id, event_id, reason, attempts, error, digest in components.reports.dead_events():
        print(f"dead letter {dead_id}: {event_id} reason={reason} attempts={attempts} hash={digest} error={error[:80]}")
    ids = components.reports.ticket_event_ids()
    print(f"tickets: {len(ids)}; distinct events with a ticket: {len(set(ids))}")
    return 0


def _webhook_demo(settings: Settings) -> int:
    secret = settings.webhook_secret
    now = time.time()
    body = '{"event_id": "e-001", "body": "Please cancel order 4417"}'
    signature = sign(secret, now, body)
    print("valid request:", verify(secret, str(now), body, signature, now))
    print("tampered body:", verify(secret, str(now), body.replace("4417", "9999"), signature, now))
    print("replayed old request:", verify(secret, str(now - 400), body, sign(secret, now - 400, body), now))
    return 0


def _free_port() -> int:
    """A port nothing is listening on (the benchmark must not collide with a service already on the machine)."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _bench_webhook(components: Components) -> int:
    import uvicorn

    settings = components.settings
    app = create_app(components.queue, settings.webhook_secret, settings.max_webhook_bytes, components.database.ping)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    wait_for_port(base + "/healthz")
    reset_tables(components.database, settings.root / "sql")
    timings = []
    with httpx.Client(base_url=base) as client:
        for number in range(500):
            body = json.dumps({"event_id": f"e-{number:04d}", "body": "Please cancel order 4417."})
            now = time.time()
            headers = {"X-Timestamp": str(now), "X-Signature": sign(settings.webhook_secret, now, body)}
            started = time.perf_counter()
            response = client.post("/webhook/email", content=body, headers=headers)
            timings.append((time.perf_counter() - started) * 1000)
            assert response.status_code == 202, response.text
        tampered = client.post("/webhook/email", content=body.replace("4417", "9999"), headers=headers)
        old = str(time.time() - 400)
        replayed = client.post(
            "/webhook/email",
            content=body,
            headers={"X-Timestamp": old, "X-Signature": sign(settings.webhook_secret, float(old), body)},
        )
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
    print(f"p95 budget {budget:.0f} ms: {'met' if percentile(timings, 0.95) < budget else 'NOT met'}")
    return 0 if percentile(timings, 0.95) < budget else 1


def _worker(components: Components, until_idle: bool) -> int:
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
    outcomes = worker.run(until_idle=until_idle)
    print("outcomes:", dict(outcomes))
    return 0


def _relay(components: Components, once: bool) -> int:
    shutdown = ShutdownSignal()
    shutdown.install()
    relay = OutboxRelay(components.outbox, components.mail)
    total = 0
    while not shutdown.requested:
        try:
            sent = relay.run_once()
        except Exception:
            LOGGER.exception("outbox unavailable, retrying")
            shutdown.wait(2.0)
            continue
        total += sent
        if once and sent == 0:
            break
        if sent == 0:
            shutdown.wait(0.5)
    print(f"acknowledgments sent: {total}")
    return 0


def _burst(components: Components, arguments: argparse.Namespace) -> int:
    print(
        "| Concurrency | Throughput (events/s) | Peak queue depth | p95 event to ticket (s) | Rate-limit errors | Tickets | Dead letters | Drained |"
    )
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for concurrency in arguments.concurrency:
        result = run_burst(
            components,
            events=arguments.events,
            seconds=arguments.seconds,
            concurrency=concurrency,
            delay=arguments.delay,
            max_rps=arguments.max_rps,
        )
        print(
            f"| {result.concurrency} | {result.throughput_per_second:.1f} | {result.peak_queue_depth} | "
            f"{result.p95_event_to_ticket_seconds:.2f} | {result.rate_limit_errors} | {result.tickets} | {result.dead_letters} | {result.drained} |"
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run one subcommand; returns the process exit code."""
    arguments = _parser().parse_args(argv)
    try:
        settings = Settings.from_environ(os.environ)
    except ConfigurationError as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return 2
    configure_logging(settings.log_level)
    if arguments.command == "webhook-demo":
        return _webhook_demo(settings)
    components = build_components(settings)
    try:
        if arguments.command == "db":
            print("applied " + ", ".join(apply_scripts(components.database, settings.root / "sql")))
        elif arguments.command == "reset":
            reset_tables(components.database, settings.root / "sql")
            print("tables emptied")
        elif arguments.command == "check":
            return 0 if components.database.ping() else 1
        elif arguments.command == "status":
            return _status(components)
        elif arguments.command == "enqueue":
            inbox = generate_events(arguments.events, 2610)
            components.queue.put_many(list(inbox.deliveries))
            print(
                f"queued {len(inbox.deliveries)} deliveries of {arguments.events} events ({len(inbox.duplicates)} delivered twice, {len(inbox.poison)} poison)"
            )
        elif arguments.command == "serve-webhook":
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
        elif arguments.command == "worker":
            return _worker(components, arguments.until_idle)
        elif arguments.command == "relay":
            return _relay(components, arguments.once)
        elif arguments.command == "redrive":
            new = components.queue.redrive(arguments.dead_id)
            print(
                f"redriven as delivery {new}"
                if new
                else f"dead letter {arguments.dead_id} not found or already redriven"
            )
            return 0 if new else 1
        elif arguments.command == "bench-webhook":
            return _bench_webhook(components)
        elif arguments.command == "burst":
            return _burst(components, arguments)
        elif arguments.command == "crash-test":
            codes, sent, ticketed = run_crash_test(components, arguments.at)
            print(dict(codes))
            print(
                f"event ids sent: {len(set(sent))}; tickets: {len(ticketed)}; distinct events with a ticket: {len(set(ticketed))}"
            )
            lost, duplicated = sorted(set(sent) - set(ticketed)), len(ticketed) - len(set(ticketed))
            print(f"lost: {lost}; duplicated tickets: {duplicated}")
            return 0 if not lost and not duplicated else 1
        return 0
    except MissingRecordingError as error:
        LOGGER.error("%s", error)
        return 1
    finally:
        components.database.close()


if __name__ == "__main__":
    raise SystemExit(main())
