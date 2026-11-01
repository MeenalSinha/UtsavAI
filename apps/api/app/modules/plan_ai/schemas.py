"""Pydantic schemas and domain validators for PlanAI."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import AIValidationError
from app.modules.events.context import SharedEventContext


class ProposedFunction(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    client_ref: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    location_name: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=1000)
    sort_order: int = Field(default=0, ge=-1000, le=1000)


class ProposedTask(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    client_ref: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=1000)
    due_at: datetime | None = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    function_ref: str | None = Field(default=None, max_length=40)
    depends_on: list[str] = Field(default_factory=list, max_length=20)


class PlanProposalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    schema_version: Literal[1] = 1
    summary: str = Field(min_length=1, max_length=2000)
    assumptions: list[str] = Field(default_factory=list, max_length=20)
    warnings: list[str] = Field(default_factory=list, max_length=20)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=10)
    theme_suggestions: list[str] = Field(default_factory=list, max_length=10)
    proposed_functions: list[ProposedFunction] = Field(default_factory=list, max_length=50)
    proposed_tasks: list[ProposedTask] = Field(default_factory=list, max_length=100)
    planning_notes: list[str] = Field(default_factory=list, max_length=20)


class PlanGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    request: str = Field(min_length=3, max_length=2000)
    include: list[str] = Field(
        default_factory=lambda: ["functions", "tasks", "themes", "planning_notes"],
        max_length=10,
    )
    base_revision: int = Field(ge=1)
    conversation_id: uuid.UUID | None = None


class PlanAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    base_revision: int = Field(ge=1)
    selected_function_refs: list[str] = Field(default_factory=list, max_length=50)
    selected_task_refs: list[str] = Field(default_factory=list, max_length=100)


class PlanProposalOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: uuid.UUID
    event_id: uuid.UUID
    conversation_id: uuid.UUID | None
    base_revision: int
    status: str
    schema_version: int
    payload: PlanProposalPayload
    created_at: datetime
    accepted_at: datetime | None
    model_metadata: dict[str, Any] = Field(default_factory=dict)


class PlanAcceptResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: uuid.UUID
    status: str
    new_revision: int
    accepted_functions_count: int
    accepted_tasks_count: int
    created_function_ids: list[uuid.UUID]
    created_task_ids: list[uuid.UUID]


def validate_plan_proposal_domain(payload: PlanProposalPayload, context: SharedEventContext) -> None:
    """Deterministic domain validation on AI-generated proposals."""
    # 1. Unique function client_refs
    fn_refs = [f.client_ref for f in payload.proposed_functions]
    if len(fn_refs) != len(set(fn_refs)):
        raise AIValidationError("Proposal contains duplicate function client_ref values.")

    # 2. Unique task client_refs
    task_refs = [t.client_ref for t in payload.proposed_tasks]
    if len(task_refs) != len(set(task_refs)):
        raise AIValidationError("Proposal contains duplicate task client_ref values.")

    fn_set = set(fn_refs)
    task_set = set(task_refs)

    # 3. Function time range validity
    for fn in payload.proposed_functions:
        if fn.starts_at and fn.ends_at and fn.ends_at < fn.starts_at:
            raise AIValidationError(f"Proposed function '{fn.name}' has ends_at before starts_at.")

    # 4. Task references validation
    for task in payload.proposed_tasks:
        if task.function_ref and task.function_ref not in fn_set:
            raise AIValidationError(
                f"Task '{task.title}' references non-existent function_ref '{task.function_ref}'."
            )
        for dep in task.depends_on:
            if dep not in task_set:
                raise AIValidationError(f"Task '{task.title}' depends on non-existent task_ref '{dep}'.")
            if dep == task.client_ref:
                raise AIValidationError(f"Task '{task.title}' cannot depend on itself.")

    # 5. Cycle detection in task dependency graph (DFS)
    adj: dict[str, list[str]] = {t.client_ref: list(t.depends_on) for t in payload.proposed_tasks}
    visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

    def has_cycle(u: str) -> bool:
        visited[u] = 1
        for v in adj.get(u, []):
            if visited.get(v, 0) == 1:
                return True
            if visited.get(v, 0) == 0 and has_cycle(v):
                return True
        visited[u] = 2
        return False

    for node in task_set:
        if visited.get(node, 0) == 0 and has_cycle(node):
            raise AIValidationError("Task dependency graph contains a cycle.")
