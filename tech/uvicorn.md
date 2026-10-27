# Uvicorn

## What it is

Uvicorn is a web server for Python programs. It listens on a network *port*, accepts connections, reads each HTTP request, hands it to the application (here a FastAPI app) through a standard interface called ASGI, and sends the answer back.

## Why this repository uses it

The webhook needs a real HTTP server; the benchmark needs one on a port that is certainly free.

## Where it appears

| File | What it does with Uvicorn |
| --- | --- |
| `src/inbox_worker/interfaces/cli.py` | `serve-webhook` calls `uvicorn.run`; `bench-webhook` runs a server in a thread on a free port |
| `Dockerfile` | `CMD ["inbox-worker", "serve-webhook"]` |

## How it works underneath

A *port* is a number (0 to 65535) that identifies one listening program on a machine; the pair *host* and port, for example `127.0.0.1:8080`, is an address. `127.0.0.1` means 'this machine only'; `0.0.0.0` means 'every network interface', needed inside a container so the published port can reach the server.

ASGI (Asynchronous Server Gateway Interface) is the contract between the server and the app: the app is an `async` function that receives the request as a dictionary plus two channels for incoming and outgoing messages. Uvicorn runs an event loop, so one process can keep thousands of connections open at once, which is what makes streaming responses possible.

`uvicorn.run(app, host=..., port=...)` starts it from Python. It installs signal handlers: on SIGTERM or SIGINT (the polite 'please stop' signals) it stops accepting new connections, lets running requests finish (up to `timeout_graceful_shutdown`), and exits. When the signal came from the outside, Uvicorn re-raises it at the end, so the process may report an exit status of -15 (killed by signal 15, SIGTERM) even though the shutdown was clean.

## Walkthrough of this repository's use

Asking the operating system for a free port (the benchmark must not collide with a service already on the machine): binding to port 0 lets the system pick one.

From `src/inbox_worker/interfaces/cli.py`:

```python
def _free_port() -> int:
    """A port nothing is listening on (the benchmark must not collide with a service already on the machine)."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])
```

- `def _free_port() -> int:`: The function `_free_port`, returning `int`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `"""A port nothing is listening on (the benchmark must not collide with a service already on the machine)."""`: The docstring: says what the function is for.
- `with socket.socket() as probe:`: Another line of the function (a statement or a continuation of the one above).
- `probe.bind(("127.0.0.1", 0))`: Calls `probe.bind`.
- `return int(probe.getsockname()[1])`: Gives back `int(probe.getsockname()[1])`.

```python
def _bench_webhook(components: Components) -> int:
```

- `def _bench_webhook(components: Components) -> int:`: The function `_bench_webhook`, returning `int`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.

The benchmark starts the same application in a thread:

From `src/inbox_worker/interfaces/cli.py`:

```python
def _bench_webhook(components: Components) -> int:
    import uvicorn
```

- `def _bench_webhook(components: Components) -> int:`: The function `_bench_webhook`, returning `int`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `import uvicorn`: Another line of the function (a statement or a continuation of the one above).

```python
    settings = components.settings
    app = create_app(components.queue, settings.webhook_secret, settings.max_webhook_bytes, components.database.ping)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"
    wait_for_port(base + "/healthz")
```

- `settings = components.settings`: Stores `components.settings` in the name `settings`.
- `app = create_app(components.queue, settings.webhook_secret, settings.max_webhook_bytes, components.database.ping)`: Stores `create_app(components.queue, settings.webhook_secret, settings.max_webhook_bytes, components.database.ping)` in the name `app`.
- `port = _free_port()`: Stores `_free_port()` in the name `port`.
- `server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))`: Stores `uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))` in the name `server`.
- `thread = threading.Thread(target=server.run, daemon=True)`: Stores `threading.Thread(target=server.run, daemon=True)` in the name `thread`.
- `thread.start()`: Calls `thread.start`.
- `base = f"http://127.0.0.1:{port}"`: Stores `f"http://127.0.0.1:{port}"` in the name `base`.
- `wait_for_port(base + "/healthz")`: Another line of the function (a statement or a continuation of the one above).

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make serve-webhook
```

Prints `Uvicorn running on http://127.0.0.1:8090`.

```bash
WEBHOOK_PORT=8191 make serve-webhook
```

The same on another port.

```bash
lsof -nP -iTCP:8090 -sTCP:LISTEN
```

Shows which process holds port 8090 (another program on a shared machine may).

## Mistakes people make

- Binding to `127.0.0.1` inside a container; the published port then cannot reach it.
- A port that is already taken by another program on the machine. The measurement code asks the operating system for a free port instead of a fixed one.
- Treating exit status -15 as a crash. After a polite SIGTERM it is the normal result.
- Running with auto-reload in production. Not used here.
- Killing the server with SIGKILL, which gives no chance to finish requests.

## Check yourself

1. What is a port?
   *Answer:* A number that identifies which listening program on a machine should get a connection.
2. What does host `0.0.0.0` mean?
   *Answer:* Listen on every network interface.
3. What is ASGI?
   *Answer:* The standard interface between an async Python web server and an application.
4. What does the server do on SIGTERM?
   *Answer:* Stops accepting connections, lets in-flight requests finish, and exits.
5. Why can one process hold many connections?
   *Answer:* It runs an event loop, switching between connections whenever one waits.

## Further reading

- [Uvicorn documentation (pinned version 0.54.0)](https://www.uvicorn.org/)
- [ASGI specification](https://asgi.readthedocs.io/en/latest/)
