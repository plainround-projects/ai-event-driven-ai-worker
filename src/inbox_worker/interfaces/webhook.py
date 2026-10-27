"""The webhook: verify the signature, queue the event, answer 202. The model is nowhere on this path."""

import logging
import time
from collections.abc import Callable
from typing import Annotated

from fastapi import FastAPI, Header, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from inbox_worker.application.ports import DeliveryQueue
from inbox_worker.domain.events import event_id_of
from inbox_worker.domain.signature import verify

LOGGER = logging.getLogger("inbox_worker.webhook")


def create_app(
    queue: DeliveryQueue,
    secret: bytes,
    max_bytes: int,
    ready: Callable[[], bool],
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    """Build the app. `clock` is injected so a test can send a request that is five minutes old."""
    app = FastAPI(title="Inbox webhook", version="0.1.0")

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

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz")
    def readyz() -> JSONResponse:
        if ready():
            return JSONResponse({"status": "ready"})
        return JSONResponse({"status": "database unavailable"}, status_code=503)

    return app
