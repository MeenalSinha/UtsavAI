"""Tasks and Timeline API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import AIProviderDep, DatabaseDep, PrincipalDep
from app.modules.tasks import ai_service as timeline_ai
from app.modules.tasks import service as task_service
from app.modules.tasks.schemas import (
    TaskCreate,
    TaskDependencyCreate,
    TaskDependencyOut,
    TaskOut,
    TaskUpdate,
    TimelineAcceptRequest,
    TimelineGenerateRequest,
    TimelineProposalOut,
    TimelineSummaryOut,
)

router = APIRouter(tags=["tasks"])


@router.get(
    "/events/{event_id}/tasks",
    response_model=list[TaskOut],
    summary="List event tasks with filtering",
)
def list_tasks(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    function_id: uuid.UUID | None = Query(default=None),
    assigned_user_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None),
) -> list[TaskOut]:
    return task_service.list_tasks(
        db, principal, event_id, status, priority, function_id, assigned_user_id, search
    )


@router.post(
    "/events/{event_id}/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    event_id: uuid.UUID,
    body: TaskCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> TaskOut:
    return task_service.create_task(db, principal, event_id, body)


@router.get(
    "/events/{event_id}/tasks/{task_id}",
    response_model=TaskOut,
    summary="Get task details",
)
def get_task(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> TaskOut:
    return task_service.get_task(db, principal, event_id, task_id)


@router.patch(
    "/events/{event_id}/tasks/{task_id}",
    response_model=TaskOut,
    summary="Update task title, due date, status, or priority",
)
def update_task(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    body: TaskUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> TaskOut:
    return task_service.update_task(db, principal, event_id, task_id, body)


@router.delete(
    "/events/{event_id}/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel a task",
)
def delete_task(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> None:
    task_service.delete_task(db, principal, event_id, task_id)


@router.post(
    "/events/{event_id}/tasks/{task_id}/dependencies",
    response_model=TaskDependencyOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a directed prerequisite dependency between tasks",
)
def add_dependency(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    body: TaskDependencyCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> TaskDependencyOut:
    return task_service.add_dependency(db, principal, event_id, task_id, body.depends_on_task_id)


@router.delete(
    "/events/{event_id}/tasks/{task_id}/dependencies/{depends_on_task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a task dependency",
)
def remove_dependency(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    depends_on_task_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> None:
    task_service.remove_dependency(db, principal, event_id, task_id, depends_on_task_id)


@router.get(
    "/events/{event_id}/timeline/summary",
    response_model=TimelineSummaryOut,
    summary="Get timeline progress summary and milestone metrics",
)
@router.get(
    "/events/{event_id}/tasks/summary",
    response_model=TimelineSummaryOut,
    include_in_schema=False,
)
def get_timeline_summary(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> TimelineSummaryOut:
    return task_service.calculate_timeline_summary(db, principal, event_id)


@router.post(
    "/events/{event_id}/timeline/ai/generate",
    response_model=TimelineProposalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI schedule and task preparation proposals",
)
@router.post(
    "/events/{event_id}/tasks/ai/generate",
    response_model=TimelineProposalOut,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def generate_timeline_proposal(
    event_id: uuid.UUID,
    body: TimelineGenerateRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
    ai_provider: AIProviderDep,
) -> TimelineProposalOut:
    return await timeline_ai.generate_timeline_proposal(db, ai_provider, principal, event_id, body.prompt)


@router.post(
    "/events/{event_id}/timeline/ai/proposals/{proposal_id}/accept",
    response_model=TimelineProposalOut,
    summary="Accept selected timeline tasks and dependencies",
)
@router.post(
    "/events/{event_id}/tasks/ai/proposals/{proposal_id}/accept",
    response_model=TimelineProposalOut,
    include_in_schema=False,
)
def accept_timeline_proposal(
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    body: TimelineAcceptRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> TimelineProposalOut:
    return timeline_ai.accept_timeline_proposal(db, principal, event_id, proposal_id, body)
