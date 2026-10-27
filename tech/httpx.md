# HTTPX

## What it is

HTTPX is a Python library for making HTTP requests: it is the 'browser' side, where FastAPI and Uvicorn are the 'server' side. It has a synchronous client and an asynchronous one, and it can also call a Python web application directly in memory, which is how FastAPI's test client works.

## Why this repository uses it

The benchmark and the tests talk to the webhook the way a sender would. HTTPX is the client: the benchmark opens a real connection to a server in the same process; the unit tests use the in-memory transport.

## Where it appears

| File | What it does with HTTPX |
| --- | --- |
| `src/inbox_worker/interfaces/cli.py` | `_bench_webhook` sends 500 signed requests |
| `src/inbox_worker/interfaces/measure.py` | `wait_for_port` |
| `tests/` | `TestClient` (built on HTTPX) |

## How it works underneath

`httpx.get(url)` or `client.post(url, json=...)` opens a connection, sends the request, and returns a response with `.status_code`, `.headers`, `.text` and `.json()`. A streaming call (`client.stream(...)`) yields the body in pieces as it arrives, which this repository uses to read server-sent events. A `timeout` limits how long to wait. With `httpx.ASGITransport(app=app)` the client skips the network and runs the ASGI app in the same process, so tests need no open port.

In this repository HTTPX appears in tests (calling the apps), in the demo and measurement code (calling real servers on a free port), and as a declared dependency of FastAPI's test tools.

## Walkthrough of this repository's use

The loop that times 500 requests (the first lines of the benchmark's `with httpx.Client(...)` block):

From `src/inbox_worker/interfaces/cli.py`:

```python
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
```

- `with httpx.Client(base_url=base) as client:`: Another line of the function (a statement or a continuation of the one above).
- `for number in range(500):`: Repeats the block below for each item of `range(500)`.
- `body = json.dumps({"event_id": f"e-{number:04d}", "body": "Please cancel order 4417."})`: Stores `json.dumps({"event_id": f"e-{number:04d}", "body": "Please cancel order 4417."})` in the name `body`.
- `now = time.time()`: Stores `time.time()` in the name `now`.
- `headers = {"X-Timestamp": str(now), "X-Signature": sign(settings.webhook_secret, now, body)}`: Stores `{"X-Timestamp": str(now), "X-Signature": sign(settings.webhook_secret, now, body)}` in the name `headers`.
- `started = time.perf_counter()`: Stores `time.perf_counter()` in the name `started`.
- `response = client.post("/webhook/email", content=body, headers=headers)`: Stores `client.post("/webhook/email", content=body, headers=headers)` in the name `response`.
- `timings.append((time.perf_counter() - started) * 1000)`: Calls `timings.append`.
- `assert response.status_code == 202, response.text`: Another line of the function (a statement or a continuation of the one above).
- `tampered = client.post("/webhook/email", content=body.replace("4417", "9999"), headers=headers)`: Stores `client.post("/webhook/email", content=body.replace("4417", "9999"), headers=headers)` in the name `tampered`.
- `old = str(time.time() - 400)`: Stores `str(time.time() - 400)` in the name `old`.
- `replayed = client.post(`: Stores `client.post(` in the name `replayed`.

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
.venv/bin/python -c "import httpx; print(httpx.__version__)"
```

Prints the pinned version.

```bash
make bench-webhook
```

Prints `500 requests: p50 ... ms, p95 ... ms` and the two rejection lines.

```bash
WEBHOOK_P95_BUDGET_MS=500 make bench-webhook
```

Changes the bar the command checks (default 100 ms). Pending capacity: the 100 ms bar was not met on the loaded build machine.

## Mistakes people make

- No timeout; a hung server then hangs the caller forever.
- Reading a streamed response twice. A stream can be consumed once; the code reads it to the end in one loop.
- Not closing responses and clients; the code uses `with` / `async with` blocks.
- Testing against a fixed port that another program may already hold.
- Assuming the in-memory transport behaves exactly like the network (it skips real sockets).

## Check yourself

1. What does `response.status_code` hold?
   *Answer:* The HTTP status number, such as 200 or 404.
2. How can tests call an app without opening a port?
   *Answer:* With `httpx.ASGITransport(app=app)`.
3. What is a streamed response?
   *Answer:* One whose body is read in pieces as it arrives.
4. Why set a timeout?
   *Answer:* So a hung server cannot hang the caller.
5. Can you read a streamed response body twice?
   *Answer:* No.

## Further reading

- [HTTPX documentation (pinned version 0.28.1)](https://www.python-httpx.org/)
- [Async support](https://www.python-httpx.org/async/)
- [Calling the app directly](https://www.python-httpx.org/advanced/transports/)
