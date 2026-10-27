# FastAPI

## What it is

FastAPI is a Python framework for building web servers that speak HTTP (the language of the web). You write ordinary functions and mark them with a *route*, such as `@app.post("/ask")`; FastAPI turns them into URLs that other programs can call, checks the incoming data, and turns your return values into JSON responses.

## Why this repository uses it

The webhook must verify, enqueue and answer 202 at once, with no model call on its path. FastAPI gives that in a screenful of code, reads the body in chunks so an oversized request is refused without being buffered, and runs the one blocking database call in a thread.

## Where it appears

| File | What it does with FastAPI |
| --- | --- |
| `src/inbox_worker/interfaces/webhook.py` | `create_app`: `POST /webhook/email`, `/healthz`, `/readyz` |
| `tests/unit/interfaces/` | tests the webhook with `TestClient` |

## How it works underneath

A web server is a program that waits for *requests* and answers with *responses*. A request has a *method* (`GET` to read, `POST` to send), a path (`/ask`), headers (name-value pairs such as `Authorization`), and sometimes a body. A response has a status code (200 OK, 401 not signed in, 404 not found, 413 too large, 422 invalid data, 504 gateway timeout) and a body.

FastAPI is built on Starlette (the part that handles the HTTP details) and Pydantic (the part that validates data). `@app.get("/healthz")` registers a route. Function parameters named in the path (`/runs/{run_id}`) are filled from the URL; a parameter typed as a Pydantic model is filled from the JSON body and rejected with status 422 if invalid; `Header()` reads a header. `Depends(function)` runs another function first and passes its result in: the code uses this for authentication.

`def` handlers run in a thread pool; `async def` handlers run on the event loop (see the notes on `asyncio` where they are used). FastAPI itself is only an application object; a separate server program (Uvicorn) accepts network connections and hands each request to it. Tests call the application in-process with an HTTP client, without opening a port.

One detail to know in this code base: in the modules that build routes inside a function, `from __future__ import annotations` is not used, because FastAPI reads the real type objects of parameters and the delayed form breaks nested dependencies.

## Walkthrough of this repository's use

The whole webhook application. The signature is in two headers (`X-Timestamp`, `X-Signature`), declared as parameters of type `Annotated[str | None, Header()]`: FastAPI turns `x_timestamp` into the header `X-Timestamp`. The body is read with `request.stream()` so the size limit is applied while reading. The database insert is the only blocking call, so it runs with `run_in_threadpool`.

From `src/inbox_worker/interfaces/webhook.py`:

```python
def create_app(
    queue: DeliveryQueue,
    secret: bytes,
    max_bytes: int,
    ready: Callable[[], bool],
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    """Build the app. `clock` is injected so a test can send a request that is five minutes old."""
    app = FastAPI(title="Inbox webhook", version="0.1.0")
```

- `def create_app(`: Builds the web application. The parameters (the collaborators) follow, so tests can supply fakes.
- `queue: DeliveryQueue,`: The field `queue`, type `DeliveryQueue,`.
- `secret: bytes,`: The field `secret`, type `bytes,`.
- `max_bytes: int,`: The field `max_bytes`, type `int,`.
- `ready: Callable[[], bool],`: The field `ready`, type `Callable[[], bool],`.
- `clock: Callable[[], float] = time.time,`: The field `clock`, type `Callable[[], float]`, default `time.time,`.
- `) -> FastAPI:`: Closes the parameter list: the function returns a `FastAPI` application.
- `` """Build the app. `clock` is injected so a test can send a request that is five minutes old.""" ``: The docstring: says what the function is for.
- `app = FastAPI(title="Inbox webhook", version="0.1.0")`: Creates the application object; everything below registers routes on it.

```python
    @app.post("/webhook/email", status_code=202)
    async def receive(
        request: Request,
        x_timestamp: Annotated[str | None, Header()] = None,
        x_signature: Annotated[str | None, Header()] = None,
    ) -> JSONResponse:
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > max_bytes:
                return JSONResponse({"error": f"body larger than {max_bytes} bytes"}, status_code=413)
        payload = body.decode("utf-8", "replace")
        ok, reason = verify(secret, x_timestamp or "", payload, x_signature or "", clock())
        if not ok:
            LOGGER.warning("webhook rejected", extra={"fields": {"reason": reason}})
            return JSONResponse({"error": reason}, status_code=401)
        delivery_id = await run_in_threadpool(queue.put, event_id_of(payload), payload)
        return JSONResponse({"delivery_id": delivery_id}, status_code=202)
```

- `@app.post("/webhook/email", status_code=202)`: A *decorator* that registers the function below as the handler for `POST /webhook/email` (extra settings: `status_code=202`).
- `async def receive(`: Another line of the function (a statement or a continuation of the one above).
- `request: Request,`: The field `request`, type `Request,`.
- `x_timestamp: Annotated[str | None, Header()] = None,`: The field `x_timestamp`, type `Annotated[str | None, Header()]`, default `None,`.
- `x_signature: Annotated[str | None, Header()] = None,`: The field `x_signature`, type `Annotated[str | None, Header()]`, default `None,`.
- `) -> JSONResponse:`: Another line of the function (a statement or a continuation of the one above).
- `body = bytearray()`: Stores `bytearray()` in the name `body`.
- `async for chunk in request.stream():`: Repeats the block below for each item the asynchronous iterator `request.stream()` produces, waiting for each.
- `body.extend(chunk)`: Calls `body.extend`.
- `if len(body) > max_bytes:`: Runs the block below only when `len(body) > max_bytes`.
- `return JSONResponse({"error": f"body larger than {max_bytes} bytes"}, status_code=413)`: Builds the response by hand so the status code and body are exactly as written.
- `payload = body.decode("utf-8", "replace")`: Stores `body.decode("utf-8", "replace")` in the name `payload`.
- `ok, reason = verify(secret, x_timestamp or "", payload, x_signature or "", clock())`: Stores `verify(secret, x_timestamp or "", payload, x_signature or "", clock())` in `ok, reason`.
- `if not ok:`: Runs the block below only when `not ok`.
- `LOGGER.warning("webhook rejected", extra={"fields": {"reason": reason}})`: Calls `LOGGER.warning`.
- `return JSONResponse({"error": reason}, status_code=401)`: Builds the response by hand so the status code and body are exactly as written.
- `delivery_id = await run_in_threadpool(queue.put, event_id_of(payload), payload)`: Stores `await run_in_threadpool(queue.put, event_id_of(payload), payload)` in the name `delivery_id`.
- `return JSONResponse({"delivery_id": delivery_id}, status_code=202)`: Builds the response by hand so the status code and body are exactly as written.

```python
    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}
```

- `@app.get("/healthz")`: A *decorator* that registers the function below as the handler for `GET /healthz`.
- `def healthz() -> dict[str, str]:`: The function `healthz`, returning `dict[str, str]`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `return {"status": "ok"}`: Returns a dict; FastAPI turns it into a JSON response with status 200 unless the decorator says otherwise.

```python
    @app.get("/readyz")
    def readyz() -> JSONResponse:
        if ready():
            return JSONResponse({"status": "ready"})
        return JSONResponse({"status": "database unavailable"}, status_code=503)
```

- `@app.get("/readyz")`: A *decorator* that registers the function below as the handler for `GET /readyz`.
- `def readyz() -> JSONResponse:`: The function `readyz`, returning `JSONResponse`. If a decorator on the line above registers it as a route, FastAPI fills each parameter from the request (a name in the path comes from the URL, a parameter typed as a model comes from the JSON body, `Header()` reads a header, `Depends(...)` runs another function first) and turns the return value into the response. Otherwise it is an ordinary function.
- `if ready():`: Runs the block below only when `ready()`.
- `return JSONResponse({"status": "ready"})`: Builds the response by hand so the status code and body are exactly as written.
- `return JSONResponse({"status": "database unavailable"}, status_code=503)`: Builds the response by hand so the status code and body are exactly as written.

```python
    return app
```

- `return app`: Hands the finished application to the caller (Uvicorn or a test client).

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
make db && make serve-webhook   # in one terminal
```

Starts the webhook on http://127.0.0.1:8090.

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8090/webhook/email -d '{}'
```

`401`: no signature.

```bash
make bench-webhook
```

Sends 500 signed requests through a real server and prints p50, p95 and the 401 results.

```bash
curl -s localhost:8090/readyz
```

`{"status":"ready"}` when the database answers, 503 otherwise.

## Mistakes people make

- Trusting data in the request body without a model. Every body here is a Pydantic model or checked by hand.
- Doing slow blocking work inside an `async def` handler, which freezes every other request. Blocking calls are moved to a thread (`run_in_threadpool`, `asyncio.to_thread`).
- Returning internal errors to callers. The handlers return typed errors with a stable code and message.
- Forgetting authentication on an administrative route. Reviewer-only routes depend on a role check.
- Using string annotations (`from __future__ import annotations`) in modules that define handlers with `Depends` inside functions.

## Check yourself

1. What is a route?
   *Answer:* A URL path and method bound to a function, created with a decorator like `@app.get("/healthz")`.
2. What status code means 'invalid data'?
   *Answer:* 422.
3. What does `Depends` do?
   *Answer:* Runs another function before the handler and passes its result in.
4. What accepts the network connections for a FastAPI app?
   *Answer:* A separate server program, Uvicorn.
5. Why not run blocking code in an `async def` handler?
   *Answer:* It blocks the event loop, so no other request is served meanwhile.

## Further reading

- [FastAPI documentation (pinned version 0.162.0)](https://fastapi.tiangolo.com/)
- [Tutorial - User guide](https://fastapi.tiangolo.com/tutorial/)
- [Starlette](https://www.starlette.io/)
