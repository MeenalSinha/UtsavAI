"""FastAPI dependencies: verified principal, database, request id, services."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import UnauthenticatedError
from app.core.request_context import actor_id_var, request_id_var
from app.core.security import Principal, TokenVerifier
from app.database.pool import Database
from app.modules.events.service import EventService
from app.modules.identity.service import IdentityService

_bearer = HTTPBearer(auto_error=False, description="Supabase access token (forwarded by the BFF)")


def get_database(request: Request) -> Database:
    return request.app.state.database  # type: ignore[no-any-return]


def get_verifier(request: Request) -> TokenVerifier:
    return request.app.state.verifier  # type: ignore[no-any-return]


def get_request_id() -> str:
    return request_id_var.get()


async def get_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    verifier: Annotated[TokenVerifier, Depends(get_verifier)],
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise UnauthenticatedError("Authentication is required.")
    # JWKS fetches are blocking I/O: keep them off the event loop.
    principal = await run_in_threadpool(verifier.verify, credentials.credentials)
    actor_id_var.set(str(principal.user_id))
    return principal


PrincipalDep = Annotated[Principal, Depends(get_principal)]
RequestIdDep = Annotated[str, Depends(get_request_id)]
DatabaseDep = Annotated[Database, Depends(get_database)]


def get_event_service(db: DatabaseDep) -> EventService:
    return EventService(db)


def get_identity_service(db: DatabaseDep) -> IdentityService:
    return IdentityService(db)


EventServiceDep = Annotated[EventService, Depends(get_event_service)]
IdentityServiceDep = Annotated[IdentityService, Depends(get_identity_service)]
