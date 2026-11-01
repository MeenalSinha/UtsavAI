"""Pure ASGI middleware: correlation id, size limit, security headers, request log."""

from __future__ import annotations

import json
import logging
import re
import time
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.request_context import actor_id_var, request_id_var

logger = logging.getLogger("app.request")
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def new_request_id() -> str:
    return f"req_{uuid.uuid4().hex}"


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp, *, max_body_bytes: int, hsts: bool, api_prefix: str) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes
        self.hsts = hsts
        self.api_prefix = api_prefix

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        supplied = headers.get("x-request-id", "")
        request_id = supplied if _VALID_REQUEST_ID.match(supplied) else new_request_id()
        token = request_id_var.set(request_id)
        actor_token = actor_id_var.set("-")
        scope.setdefault("state", {})["request_id"] = request_id

        started = time.perf_counter()
        status_holder = {"status": 500}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = message["status"]
                raw = list(message.get("headers", []))
                extra = {
                    "x-request-id": request_id,
                    "x-content-type-options": "nosniff",
                    "referrer-policy": "no-referrer",
                    "x-frame-options": "DENY",
                    "content-security-policy": "default-src 'none'; frame-ancestors 'none'",
                }
                if scope["path"].startswith(self.api_prefix):
                    extra["cache-control"] = "no-store"
                if self.hsts:
                    extra["strict-transport-security"] = "max-age=63072000; includeSubDomains"
                existing = {k.lower() for k, _ in raw}
                for name, value in extra.items():
                    if name.encode() not in existing:
                        raw.append((name.encode(), value.encode()))
                message = {**message, "headers": raw}
            await send(message)

        try:
            declared = headers.get("content-length")
            if declared is not None and declared.isdigit() and int(declared) > self.max_body_bytes:
                body = json.dumps(
                    {
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": "The request body is too large.",
                            "details": {},
                            "request_id": request_id,
                        }
                    }
                ).encode()
                await send_wrapper(
                    {
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode()),
                        ],
                    }
                )
                await send_wrapper({"type": "http.response.body", "body": body})
                return

            received = 0

            async def limited_receive() -> Message:
                nonlocal received
                message = await receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if received > self.max_body_bytes:
                        raise _BodyTooLargeError
                return message

            try:
                await self.app(scope, limited_receive, send_wrapper)
            except _BodyTooLargeError:
                body = json.dumps(
                    {
                        "error": {
                            "code": "PAYLOAD_TOO_LARGE",
                            "message": "The request body is too large.",
                            "details": {},
                            "request_id": request_id,
                        }
                    }
                ).encode()
                await send_wrapper(
                    {
                        "type": "http.response.start",
                        "status": 413,
                        "headers": [
                            (b"content-type", b"application/json"),
                            (b"content-length", str(len(body)).encode()),
                        ],
                    }
                )
                await send_wrapper({"type": "http.response.body", "body": body})
        finally:
            logger.info(
                "request",
                extra={
                    "method": scope["method"],
                    "route": scope.get("route").path  # type: ignore[union-attr]
                    if scope.get("route") is not None
                    else "-",
                    "status": status_holder["status"],
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id_var.reset(token)
            actor_id_var.reset(actor_token)


class _BodyTooLargeError(Exception):
    pass
