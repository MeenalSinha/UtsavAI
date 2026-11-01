"""Budget and Expense API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import AIProviderDep, DatabaseDep, PrincipalDep
from app.modules.budget import ai_service as budget_ai
from app.modules.budget import service as budget_service
from app.modules.budget.schemas import (
    BudgetAcceptRequest,
    BudgetCategoryCreate,
    BudgetCategoryOut,
    BudgetCategoryUpdate,
    BudgetCreate,
    BudgetGenerateRequest,
    BudgetOut,
    BudgetProposalOut,
    BudgetSummaryOut,
    BudgetUpdate,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
)

router = APIRouter(tags=["budget"])


@router.post(
    "/events/{event_id}/budget",
    response_model=BudgetOut,
    status_code=status.HTTP_201_CREATED,
    summary="Initialize or get budget for an event",
)
def create_budget(
    event_id: uuid.UUID,
    body: BudgetCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> BudgetOut:
    return budget_service.get_or_create_budget(db, principal, event_id, body)


@router.get(
    "/events/{event_id}/budget",
    response_model=BudgetOut,
    summary="Get budget for an event",
)
def get_budget(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> BudgetOut:
    return budget_service.get_budget(db, principal, event_id)


@router.patch(
    "/events/{event_id}/budget",
    response_model=BudgetOut,
    summary="Update event budget total limit",
)
def update_budget(
    event_id: uuid.UUID,
    body: BudgetUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> BudgetOut:
    return budget_service.update_budget(db, principal, event_id, body)


@router.get(
    "/events/{event_id}/budget/categories",
    response_model=list[BudgetCategoryOut],
    summary="List budget categories with spending breakdowns",
)
def list_categories(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> list[BudgetCategoryOut]:
    return budget_service.list_categories(db, principal, event_id)


@router.post(
    "/events/{event_id}/budget/categories",
    response_model=BudgetCategoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom budget category",
)
def create_category(
    event_id: uuid.UUID,
    body: BudgetCategoryCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> BudgetCategoryOut:
    return budget_service.create_category(db, principal, event_id, body)


@router.patch(
    "/events/{event_id}/budget/categories/{category_id}",
    response_model=BudgetCategoryOut,
    summary="Update category planned allocation or name",
)
def update_category(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    body: BudgetCategoryUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> BudgetCategoryOut:
    return budget_service.update_category(db, principal, event_id, category_id, body)


@router.delete(
    "/events/{event_id}/budget/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a budget category without expenses",
)
def delete_category(
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> None:
    budget_service.delete_category(db, principal, event_id, category_id)


@router.get(
    "/events/{event_id}/expenses",
    response_model=list[ExpenseOut],
    summary="List event expenses with optional filtering",
)
def list_expenses(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
    category_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
) -> list[ExpenseOut]:
    return budget_service.list_expenses(db, principal, event_id, category_id, status, search)


@router.post(
    "/events/{event_id}/expenses",
    response_model=ExpenseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new expense",
)
def create_expense(
    event_id: uuid.UUID,
    body: ExpenseCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> ExpenseOut:
    return budget_service.create_expense(db, principal, event_id, body)


@router.patch(
    "/events/{event_id}/expenses/{expense_id}",
    response_model=ExpenseOut,
    summary="Update expense amount, status, or details",
)
def update_expense(
    event_id: uuid.UUID,
    expense_id: uuid.UUID,
    body: ExpenseUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> ExpenseOut:
    return budget_service.update_expense(db, principal, event_id, expense_id, body)


@router.delete(
    "/events/{event_id}/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete an expense",
)
def delete_expense(
    event_id: uuid.UUID,
    expense_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> None:
    budget_service.delete_expense(db, principal, event_id, expense_id)


@router.get(
    "/events/{event_id}/budget/summary",
    response_model=BudgetSummaryOut,
    summary="Get authoritative financial summaries and alerts",
)
def get_budget_summary(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> BudgetSummaryOut:
    return budget_service.calculate_budget_summary(db, principal, event_id)


@router.post(
    "/events/{event_id}/budget/ai/generate",
    response_model=BudgetProposalOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate AI budget recommendations",
)
async def generate_budget_proposal(
    event_id: uuid.UUID,
    body: BudgetGenerateRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
    ai_provider: AIProviderDep,
) -> BudgetProposalOut:
    return await budget_ai.generate_budget_proposal(db, ai_provider, principal, event_id, body.prompt)


@router.post(
    "/events/{event_id}/budget/ai/proposals/{proposal_id}/accept",
    response_model=BudgetProposalOut,
    summary="Accept selected budget allocation recommendations",
)
def accept_budget_proposal(
    event_id: uuid.UUID,
    proposal_id: uuid.UUID,
    body: BudgetAcceptRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> BudgetProposalOut:
    return budget_ai.accept_budget_proposal(db, principal, event_id, proposal_id, body)
