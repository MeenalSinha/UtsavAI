from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Query, Response, status

from app.api.deps import EventServiceDep, PrincipalDep, RequestIdDep
from app.core.domain import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, EventSort, EventStatus
from app.modules.events.preconditions import etag, parse_if_match
from app.modules.events.schemas import EventCreate, EventOut, EventPage, EventUpdate
from app.schemas.common import ErrorEnvelope

router = APIRouter(
    prefix="/events",
    tags=["events"],
    responses={
        401: {"model": ErrorEnvelope},
        403: {"model": ErrorEnvelope},
        404: {"model": ErrorEnvelope},
    },
)


@router.post(
    "",
    response_model=EventOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event; the caller becomes its owner",
    responses={422: {"model": ErrorEnvelope}},
)
def create_event(
    payload: EventCreate,
    response: Response,
    principal: PrincipalDep,
    service: EventServiceDep,
    request_id: RequestIdDep,
) -> EventOut:
    event = service.create(principal, payload, request_id)
    response.headers["ETag"] = etag(event.revision)
    response.headers["Location"] = f"/api/v1/events/{event.id}"
    return event


@router.get("", response_model=EventPage, summary="List events the caller can access")
def list_events(
    principal: PrincipalDep,
    service: EventServiceDep,
    request_id: RequestIdDep,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
    status_filter: Annotated[list[EventStatus] | None, Query(alias="status")] = None,
    include_archived: bool = False,
    sort: EventSort = EventSort.START_ASC,
) -> EventPage:
    return service.list(
        principal,
        statuses=status_filter,
        include_archived=include_archived,
        sort=sort,
        limit=limit,
        cursor=cursor,
        request_id=request_id,
    )


@router.get("/{event_id}", response_model=EventOut, summary="Get one event")
def get_event(
    event_id: uuid.UUID,
    response: Response,
    principal: PrincipalDep,
    service: EventServiceDep,
    request_id: RequestIdDep,
) -> EventOut:
    event = service.get(principal, event_id, request_id)
    response.headers["ETag"] = etag(event.revision)
    return event


@router.patch(
    "/{event_id}",
    response_model=EventOut,
    summary="Update an event (requires If-Match with the current revision)",
    responses={
        409: {"model": ErrorEnvelope},
        422: {"model": ErrorEnvelope},
        428: {"model": ErrorEnvelope},
    },
)
def update_event(
    event_id: uuid.UUID,
    payload: EventUpdate,
    response: Response,
    principal: PrincipalDep,
    service: EventServiceDep,
    request_id: RequestIdDep,
    if_match: Annotated[str | None, Header()] = None,
) -> EventOut:
    revision = parse_if_match(if_match)
    event = service.update(principal, event_id, payload, revision, request_id)
    response.headers["ETag"] = etag(event.revision)
    return event


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive an event (soft delete; owner only)",
)
def archive_event(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    service: EventServiceDep,
    request_id: RequestIdDep,
) -> Response:
    service.archive(principal, event_id, request_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
