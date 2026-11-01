"""Application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.core.request_context import request_id_var
from app.core.security import TokenVerifier, build_token_verifier
from app.database.pool import Database
from app.middleware.request_id import RequestContextMiddleware

logger = logging.getLogger(__name__)


def _envelope(
    status_code: int, code: str, message: str, details: dict[str, Any] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": request_id_var.get(),
            }
        },
    )


def _clean_message(message: str) -> str:
    message = message.removeprefix("Value error, ")
    return message if message.endswith((".", "?", "!")) else f"{message}."


def _install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return _envelope(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        if any(e["type"] == "json_invalid" for e in errors):
            return _envelope(400, "INVALID_REQUEST", "The request body is not valid JSON.")
        fields = [
            {
                "field": ".".join(str(p) for p in e["loc"][1:]) or str(e["loc"][0]),
                "message": _clean_message(str(e["msg"])),
            }
            for e in errors
        ]
        message = (
            fields[0]["message"]
            if len(fields) == 1
            else f"The request contains {len(fields)} invalid fields."
        )
        return _envelope(422, "VALIDATION_ERROR", message, {"fields": fields})

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        mapping = {
            404: ("NOT_FOUND", "The resource was not found."),
            405: ("INVALID_REQUEST", "The method is not allowed for this resource."),
            401: ("UNAUTHENTICATED", "Authentication is required."),
            403: ("FORBIDDEN", "You do not have permission to perform this action."),
        }
        code, message = mapping.get(exc.status_code, ("INVALID_REQUEST", "The request is invalid."))
        return _envelope(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # No stack trace, SQL text or configuration is ever returned to the client.
        logger.error("unhandled_exception", extra={"exc_type": type(exc).__name__}, exc_info=True)
        return _envelope(500, "INTERNAL_ERROR", "An unexpected error occurred.")


def create_app(
    settings: Settings | None = None,
    *,
    database: Database | None = None,
    verifier: TokenVerifier | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, json_output=settings.log_json)
    db = database or Database(settings)
    token_verifier = verifier or build_token_verifier(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db.open()
        try:
            db.verify_runtime_role()
        except Exception:
            db.close()
            raise
        logger.info("startup_complete", extra={"environment": settings.app_env})
        try:
            yield
        finally:
            db.close()

    docs = settings.docs_enabled
    app = FastAPI(
        title="UtsavAI API",
        version=settings.app_version,
        description="Celebration planning platform API. Phase 1: identity and private events.",
        lifespan=lifespan,
        docs_url=f"{settings.api_v1_prefix}/docs" if docs else None,
        redoc_url=None,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json" if docs else None,
    )
    app.state.settings = settings
    app.state.database = db
    app.state.verifier = token_verifier

    _install_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    if settings.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "If-Match",
                "X-Request-ID",
                "Idempotency-Key",
            ],
            expose_headers=["ETag", "X-Request-ID", "Location"],
            max_age=600,
        )
    # Outermost: request id and security headers apply to every response, including CORS and errors.
    app.add_middleware(
        RequestContextMiddleware,
        max_body_bytes=settings.max_request_body_bytes,
        hsts=settings.is_production,
        api_prefix=settings.api_v1_prefix,
    )
    return app


def app_factory() -> FastAPI:
    """Uvicorn entrypoint: `uvicorn app.main:app_factory --factory`."""
    return create_app()
