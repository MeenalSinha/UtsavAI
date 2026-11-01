"""Task and Timeline Pydantic V2 schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.domain import TaskOrigin, TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=4000)
    due_at: datetime | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    function_id: uuid.UUID | None = None
    assigned_user_id: uuid.UUID | None = None
    sort_order: int = Field(default=0)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=4000)
    due_at: datetime | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    function_id: uuid.UUID | None = None
    assigned_user_id: uuid.UUID | None = None
    sort_order: int | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    event_id: uuid.UUID
    function_id: uuid.UUID | None = None
    title: str
    description: str | None = None
    due_at: datetime | None = None
    status: TaskStatus
    priority: TaskPriority
    assigned_user_id: uuid.UUID | None = None
    origin: TaskOrigin
    sort_order: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    depends_on_task_ids: list[uuid.UUID] = []


class TaskDependencyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    depends_on_task_id: uuid.UUID


class TaskDependencyOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: uuid.UUID
    depends_on_task_id: uuid.UUID
    created_at: datetime


class TimelineSummaryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    blocked_tasks: int
    cancelled_tasks: int
    overdue_tasks: int
    upcoming_tasks: int
    unscheduled_tasks: int
    high_priority_tasks: int
    completion_percentage: float


# AI Timeline Schedule Generation Schemas
class ProposedTaskItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_ref: str = Field(..., min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=180)
    description: str | None = None
    due_at: datetime | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    function_ref: str | None = None
    depends_on: list[str] = []


class TimelineProposalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    summary: str
    assumptions: list[str] = []
    warnings: list[str] = []
    follow_up_questions: list[str] = []
    proposed_tasks: list[ProposedTaskItem] = []


class TimelineGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., min_length=3, max_length=2000)


class TimelineProposalOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    event_id: uuid.UUID
    conversation_id: uuid.UUID | None
    proposal_type: str
    status: str
    base_revision: int
    payload: TimelineProposalPayload
    created_at: datetime
    accepted_at: datetime | None = None


class TimelineAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_revision: int
    selected_task_refs: list[str] = Field(..., min_length=1)
