"""Pydantic schemas and DTOs for the Adaptive Planning Engine."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.domain import ChangeProposalStatus


class EventChangeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_guest_count: int | None = Field(default=None, ge=1, le=100_000)
    start_at: datetime | None = None
    end_at: datetime | None = None
    timezone: str | None = None
    location_name: str | None = Field(default=None, max_length=160)
    city: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    country_code: str | None = Field(default=None, max_length=2)


class BudgetChangeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_limit: Decimal | None = Field(default=None, ge=Decimal("0.00"), decimal_places=2)


class FunctionChangeItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["add", "update", "archive"]
    function_id: uuid.UUID | None = None
    name: str | None = Field(default=None, max_length=160)
    function_type: str | None = Field(default=None, max_length=80)
    start_at: datetime | None = None
    end_at: datetime | None = None
    expected_guest_count: int | None = Field(default=None, ge=1, le=100_000)


class TypedChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    base_revision: int = Field(ge=1)
    request_text: str = Field(min_length=1, max_length=4000)
    event_changes: EventChangeItem | None = None
    budget_changes: BudgetChangeItem | None = None
    function_changes: list[FunctionChangeItem] = Field(default_factory=list)


class AffectedRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    module: str
    entity_type: str
    entity_id: str | None = None
    entity_name: str
    change_nature: str
    details: str | None = None


class CalculationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric: str
    before_value: str
    after_value: str
    delta: str
    unit: str = ""


class WarningItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    severity: Literal["low", "medium", "high", "critical"]
    recommended_action: str


class ProposedOperation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op_code: str
    target_module: str
    description: str
    payload: dict[str, Any] = Field(default_factory=dict)


class SuggestedOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    operations: list[ProposedOperation] = Field(default_factory=list)
    selected_by_default: bool = True


class ImpactResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules_version: str = "1.0.0"
    severity: Literal["low", "medium", "high", "critical"]
    affected_modules: list[str] = Field(default_factory=list)
    affected_records: list[AffectedRecord] = Field(default_factory=list)
    calculations: list[CalculationItem] = Field(default_factory=list)
    warnings: list[WarningItem] = Field(default_factory=list)
    suggested_options: list[SuggestedOption] = Field(default_factory=list)


class ChangeProposalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_revision: int = Field(ge=1)
    request_text: str = Field(min_length=1, max_length=4000)
    event_changes: EventChangeItem | None = None
    budget_changes: BudgetChangeItem | None = None
    function_changes: list[FunctionChangeItem] = Field(default_factory=list)


class ChangeProposalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    created_by: uuid.UUID
    base_revision: int
    request_text: str
    requested_changes: dict[str, Any]
    impact_result: ImpactResult
    ai_explanation: str | None = None
    status: ChangeProposalStatus
    accepted_at: datetime | None = None
    accepted_revision: int | None = None
    rules_version: str = "1.0.0"
    schema_version: int = 1
    created_at: datetime
    updated_at: datetime


class ProposalAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected_option_ids: list[str] = Field(default_factory=list)


class ProposalRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, max_length=1000)


class InterpretRequestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=2, max_length=4000)


class InterpretedChangeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    candidate_request: ChangeProposalCreate
