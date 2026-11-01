"""Budget and Expense Pydantic V2 schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.core.domain import ExpenseStatus

DecimalMoney = Annotated[Decimal, Field(max_digits=12, decimal_places=2)]


class BudgetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_limit: DecimalMoney = Field(..., ge=Decimal("0.00"), description="Total spending ceiling")


class BudgetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_limit: DecimalMoney = Field(..., ge=Decimal("0.00"), description="Total spending ceiling")


class BudgetOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    event_id: uuid.UUID
    total_limit: DecimalMoney
    currency: str
    created_at: datetime
    updated_at: datetime


class BudgetCategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_key: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=160)
    planned_amount: DecimalMoney = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    sort_order: int = Field(default=0)


class BudgetCategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    planned_amount: DecimalMoney | None = Field(default=None, ge=Decimal("0.00"))
    sort_order: int | None = None


class BudgetCategoryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    budget_id: uuid.UUID
    category_key: str
    name: str
    planned_amount: DecimalMoney
    sort_order: int
    created_at: datetime
    updated_at: datetime
    committed_amount: DecimalMoney = Decimal("0.00")
    paid_amount: DecimalMoney = Decimal("0.00")
    projected_amount: DecimalMoney = Decimal("0.00")
    remaining_amount: DecimalMoney = Decimal("0.00")
    is_over_budget: bool = False


class ExpenseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_category_id: uuid.UUID
    description: str = Field(..., min_length=1, max_length=240)
    amount: DecimalMoney = Field(..., gt=Decimal("0.00"))
    expense_date: date | None = None
    status: ExpenseStatus = ExpenseStatus.PLANNED
    vendor_id: uuid.UUID | None = None


class ExpenseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    budget_category_id: uuid.UUID | None = None
    description: str | None = Field(default=None, min_length=1, max_length=240)
    amount: DecimalMoney | None = Field(default=None, gt=Decimal("0.00"))
    expense_date: date | None = None
    status: ExpenseStatus | None = None
    vendor_id: uuid.UUID | None = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    event_id: uuid.UUID
    budget_category_id: uuid.UUID
    vendor_id: uuid.UUID | None = None
    description: str
    amount: DecimalMoney
    currency: str
    expense_date: date
    status: ExpenseStatus
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CategorySummaryItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: uuid.UUID
    category_key: str
    name: str
    planned_amount: DecimalMoney
    committed_amount: DecimalMoney
    paid_amount: DecimalMoney
    projected_amount: DecimalMoney
    remaining_amount: DecimalMoney
    is_over_budget: bool


class BudgetSummaryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    currency: str
    total_limit: DecimalMoney
    total_allocated: DecimalMoney
    unallocated_amount: DecimalMoney
    planned_expenses: DecimalMoney
    committed_expenses: DecimalMoney
    paid_expenses: DecimalMoney
    cancelled_expenses: DecimalMoney
    projected_total: DecimalMoney
    remaining_after_committed: DecimalMoney
    projected_headroom: DecimalMoney
    alerts: list[str] = []
    category_summaries: list[CategorySummaryItem] = []


# AI Budget Recommendation Schemas
class ProposedCategoryAllocation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_key: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=160)
    percentage: Decimal = Field(..., ge=Decimal("0.0"), le=Decimal("100.0"))
    suggested_amount: DecimalMoney
    notes: str = ""


class BudgetProposalPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    summary: str
    assumptions: list[str] = []
    warnings: list[str] = []
    savings_recommendations: list[str] = []
    follow_up_questions: list[str] = []
    proposed_allocations: list[ProposedCategoryAllocation] = []


class BudgetGenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(..., min_length=3, max_length=2000)


class BudgetProposalOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    event_id: uuid.UUID
    conversation_id: uuid.UUID | None
    proposal_type: str
    status: str
    base_revision: int
    payload: BudgetProposalPayload
    created_at: datetime
    accepted_at: datetime | None = None


class BudgetAcceptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_revision: int
    selected_category_keys: list[str] = Field(..., min_length=1)
