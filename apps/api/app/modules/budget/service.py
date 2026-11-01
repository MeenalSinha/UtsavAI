"""Authoritative, deterministic Budget and Expense service using Python Decimal."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from app.core.domain import ExpenseStatus, MemberRole, Permission
from app.core.errors import ConflictError, ForbiddenError, InvalidRequestError, NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.audit import repository as audit
from app.modules.budget import repository as repo
from app.modules.budget.schemas import (
    BudgetCategoryCreate,
    BudgetCategoryOut,
    BudgetCategoryUpdate,
    BudgetCreate,
    BudgetOut,
    BudgetSummaryOut,
    BudgetUpdate,
    CategorySummaryItem,
    ExpenseCreate,
    ExpenseOut,
    ExpenseUpdate,
)
from app.modules.events import repository as events_repo
from app.modules.events.permissions import require_permission
from app.modules.vendors import repository as vendors_repo


def _require_active_event(event: dict[str, Any]) -> None:
    if event["status"] == "archived":
        raise ForbiddenError("Archived events are read-only.")


def get_or_create_budget(
    db: Database, principal: Principal, event_id: uuid.UUID, create_req: BudgetCreate | None = None
) -> BudgetOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_READ)

        row = repo.get_budget(conn, event_id)
        if row is not None:
            return BudgetOut(**row)

        # Create new budget
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_MANAGE)
        _require_active_event(event)

        total_limit = create_req.total_limit if create_req else Decimal("0.00")
        row = repo.create_budget(conn, event_id, total_limit, event["currency"])
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="budget.created",
            entity_type="budgets",
            entity_id=row["id"],
            request_id=request_id,
            metadata={"total_limit": str(total_limit), "currency": event["currency"]},
        )
        return BudgetOut(**row)


def get_budget(db: Database, principal: Principal, event_id: uuid.UUID) -> BudgetOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_READ)

        row = repo.get_budget(conn, event_id)
        if row is None:
            raise NotFoundError("Budget not found for this event. Initialize it first.")
        return BudgetOut(**row)


def update_budget(db: Database, principal: Principal, event_id: uuid.UUID, req: BudgetUpdate) -> BudgetOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_MANAGE)

        row = repo.get_budget(conn, event_id)
        if row is None:
            # Create if not exists
            row = repo.create_budget(conn, event_id, req.total_limit, event["currency"])
        else:
            row = repo.update_budget(conn, event_id, req.total_limit)
        assert row is not None

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="budget.updated",
            entity_type="budgets",
            entity_id=row["id"],
            request_id=request_id,
            metadata={"total_limit": str(req.total_limit)},
        )
        return BudgetOut(**row)


def list_categories(db: Database, principal: Principal, event_id: uuid.UUID) -> list[BudgetCategoryOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_READ)

        budget = repo.get_budget(conn, event_id)
        if budget is None:
            return []

        cat_rows = repo.list_categories(conn, budget["id"])
        expenses = repo.list_expenses(conn, event_id)

        # Aggregate category spending
        cat_map: dict[uuid.UUID, dict[str, Decimal]] = {}
        for c in cat_rows:
            cat_map[c["id"]] = {
                "committed": Decimal("0.00"),
                "paid": Decimal("0.00"),
                "planned": Decimal("0.00"),
            }

        for exp in expenses:
            c_id = exp["budget_category_id"]
            if c_id in cat_map:
                amt = Decimal(str(exp["amount"]))
                st = exp["status"]
                if st == ExpenseStatus.COMMITTED.value:
                    cat_map[c_id]["committed"] += amt
                elif st == ExpenseStatus.PAID.value:
                    cat_map[c_id]["paid"] += amt
                elif st == ExpenseStatus.PLANNED.value:
                    cat_map[c_id]["planned"] += amt

        result: list[BudgetCategoryOut] = []
        for c in cat_rows:
            stats = cat_map[c["id"]]
            planned = Decimal(str(c["planned_amount"]))
            committed = stats["committed"]
            paid = stats["paid"]
            projected = committed + paid + stats["planned"]
            remaining = planned - (committed + paid)
            is_over = (committed + paid) > planned

            result.append(
                BudgetCategoryOut(
                    id=c["id"],
                    budget_id=c["budget_id"],
                    category_key=c["category_key"],
                    name=c["name"],
                    planned_amount=planned,
                    sort_order=c["sort_order"],
                    created_at=c["created_at"],
                    updated_at=c["updated_at"],
                    committed_amount=committed,
                    paid_amount=paid,
                    projected_amount=projected,
                    remaining_amount=remaining,
                    is_over_budget=is_over,
                )
            )
        return result


def create_category(
    db: Database, principal: Principal, event_id: uuid.UUID, req: BudgetCategoryCreate
) -> BudgetCategoryOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_MANAGE)

        budget = repo.get_budget(conn, event_id)
        if budget is None:
            budget = repo.create_budget(conn, event_id, Decimal("0.00"), event["currency"])

        existing = repo.get_category_by_key(conn, budget["id"], req.category_key)
        if existing is not None:
            raise ConflictError(f"Category with key '{req.category_key}' already exists.")

        cat_row = repo.create_category(
            conn,
            budget["id"],
            req.category_key,
            req.name,
            req.planned_amount,
            req.sort_order,
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="budget.category_created",
            entity_type="budget_categories",
            entity_id=cat_row["id"],
            request_id=request_id,
            metadata={"category_key": req.category_key, "name": req.name},
        )
        return BudgetCategoryOut(
            id=cat_row["id"],
            budget_id=cat_row["budget_id"],
            category_key=cat_row["category_key"],
            name=cat_row["name"],
            planned_amount=Decimal(str(cat_row["planned_amount"])),
            sort_order=cat_row["sort_order"],
            created_at=cat_row["created_at"],
            updated_at=cat_row["updated_at"],
        )


def update_category(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    category_id: uuid.UUID,
    req: BudgetCategoryUpdate,
) -> BudgetCategoryOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_MANAGE)

        cat = repo.get_category(conn, category_id)
        if cat is None:
            raise NotFoundError("Category not found.")

        updated = repo.update_category(conn, category_id, req.name, req.planned_amount, req.sort_order)
        assert updated is not None

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="budget.category_updated",
            entity_type="budget_categories",
            entity_id=category_id,
            request_id=request_id,
            metadata={"name": req.name, "planned_amount": str(req.planned_amount)},
        )
        return BudgetCategoryOut(
            id=updated["id"],
            budget_id=updated["budget_id"],
            category_key=updated["category_key"],
            name=updated["name"],
            planned_amount=Decimal(str(updated["planned_amount"])),
            sort_order=updated["sort_order"],
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
        )


def delete_category(db: Database, principal: Principal, event_id: uuid.UUID, category_id: uuid.UUID) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_MANAGE)

        cat = repo.get_category(conn, category_id)
        if cat is None:
            raise NotFoundError("Category not found.")

        active_expenses = repo.count_active_expenses_for_category(conn, category_id)
        if active_expenses > 0:
            raise ConflictError(
                f"Cannot delete category with {active_expenses} active expense(s). "
                "Reassign or cancel expenses first."
            )

        repo.delete_category(conn, category_id)
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="budget.category_deleted",
            entity_type="budget_categories",
            entity_id=category_id,
            request_id=request_id,
            metadata={},
        )


def list_expenses(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    category_id: uuid.UUID | None = None,
    status: str | None = None,
    search: str | None = None,
) -> list[ExpenseOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.EXPENSE_READ)

        rows = repo.list_expenses(conn, event_id, category_id, status, search)
        return [
            ExpenseOut(
                id=r["id"],
                event_id=r["event_id"],
                budget_category_id=r["budget_category_id"],
                vendor_id=r["vendor_id"],
                description=r["description"],
                amount=Decimal(str(r["amount"])),
                currency=r["currency"],
                expense_date=r["expense_date"],
                status=ExpenseStatus(r["status"]),
                created_by=r["created_by"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]


def create_expense(db: Database, principal: Principal, event_id: uuid.UUID, req: ExpenseCreate) -> ExpenseOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.EXPENSE_MANAGE)

        cat = repo.get_category(conn, req.budget_category_id)
        if cat is None:
            raise NotFoundError("Budget category not found.")

        # Ensure category belongs to event budget
        budget = repo.get_budget(conn, event_id)
        if budget is None or cat["budget_id"] != budget["id"]:
            raise InvalidRequestError("Category does not belong to this event's budget.")

        if req.vendor_id is not None:
            vendor = vendors_repo.get_vendor(conn, event_id, req.vendor_id)
            if vendor is None:
                raise InvalidRequestError("Vendor does not belong to this event.")

        expense_date = req.expense_date or date.today()
        row = repo.create_expense(
            conn,
            event_id=event_id,
            budget_category_id=req.budget_category_id,
            description=req.description,
            amount=req.amount,
            currency=event["currency"],
            expense_date=expense_date,
            status=req.status.value,
            created_by=principal.user_id,
            vendor_id=req.vendor_id,
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="expense.created",
            entity_type="expenses",
            entity_id=row["id"],
            request_id=request_id,
            metadata={"amount": str(req.amount), "status": req.status.value},
        )
        return ExpenseOut(
            id=row["id"],
            event_id=row["event_id"],
            budget_category_id=row["budget_category_id"],
            vendor_id=row["vendor_id"],
            description=row["description"],
            amount=Decimal(str(row["amount"])),
            currency=row["currency"],
            expense_date=row["expense_date"],
            status=ExpenseStatus(row["status"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def update_expense(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    expense_id: uuid.UUID,
    req: ExpenseUpdate,
) -> ExpenseOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.EXPENSE_MANAGE)

        current = repo.get_expense(conn, event_id, expense_id)
        if current is None:
            raise NotFoundError("Expense not found.")

        if req.budget_category_id is not None:
            cat = repo.get_category(conn, req.budget_category_id)
            if cat is None:
                raise NotFoundError("Budget category not found.")
            budget = repo.get_budget(conn, event_id)
            if budget is None or cat["budget_id"] != budget["id"]:
                raise InvalidRequestError("Category does not belong to this event's budget.")

        if req.vendor_id is not None:
            vendor = vendors_repo.get_vendor(conn, event_id, req.vendor_id)
            if vendor is None:
                raise InvalidRequestError("Vendor does not belong to this event.")

        status_val = req.status.value if req.status is not None else None
        updated = repo.update_expense(
            conn,
            event_id=event_id,
            expense_id=expense_id,
            budget_category_id=req.budget_category_id,
            description=req.description,
            amount=req.amount,
            expense_date=req.expense_date,
            status=status_val,
            vendor_id=req.vendor_id,
        )
        assert updated is not None

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="expense.updated",
            entity_type="expenses",
            entity_id=expense_id,
            request_id=request_id,
            metadata={"status": status_val},
        )
        return ExpenseOut(
            id=updated["id"],
            event_id=updated["event_id"],
            budget_category_id=updated["budget_category_id"],
            vendor_id=updated["vendor_id"],
            description=updated["description"],
            amount=Decimal(str(updated["amount"])),
            currency=updated["currency"],
            expense_date=updated["expense_date"],
            status=ExpenseStatus(updated["status"]),
            created_by=updated["created_by"],
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
        )


def delete_expense(db: Database, principal: Principal, event_id: uuid.UUID, expense_id: uuid.UUID) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.EXPENSE_MANAGE)

        current = repo.get_expense(conn, event_id, expense_id)
        if current is None:
            raise NotFoundError("Expense not found.")

        repo.delete_expense(conn, event_id, expense_id)
        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="expense.deleted",
            entity_type="expenses",
            entity_id=expense_id,
            request_id=request_id,
            metadata={},
        )


def calculate_budget_summary(db: Database, principal: Principal, event_id: uuid.UUID) -> BudgetSummaryOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.BUDGET_READ)

        budget = repo.get_budget(conn, event_id)
        total_limit = Decimal(str(budget["total_limit"])) if budget else Decimal("0.00")
        currency = budget["currency"] if budget else event["currency"]

        cat_rows = repo.list_categories(conn, budget["id"]) if budget else []
        expenses = repo.list_expenses(conn, event_id)

        # Totals by category and overall
        total_allocated = Decimal("0.00")
        cat_stats: dict[uuid.UUID, dict[str, Decimal]] = {}
        for c in cat_rows:
            planned = Decimal(str(c["planned_amount"]))
            total_allocated += planned
            cat_stats[c["id"]] = {
                "committed": Decimal("0.00"),
                "paid": Decimal("0.00"),
                "planned": Decimal("0.00"),
            }

        planned_exp = Decimal("0.00")
        committed_exp = Decimal("0.00")
        paid_exp = Decimal("0.00")
        cancelled_exp = Decimal("0.00")

        for exp in expenses:
            amt = Decimal(str(exp["amount"]))
            st = exp["status"]
            c_id = exp["budget_category_id"]

            if st == ExpenseStatus.PLANNED.value:
                planned_exp += amt
                if c_id in cat_stats:
                    cat_stats[c_id]["planned"] += amt
            elif st == ExpenseStatus.COMMITTED.value:
                committed_exp += amt
                if c_id in cat_stats:
                    cat_stats[c_id]["committed"] += amt
            elif st == ExpenseStatus.PAID.value:
                paid_exp += amt
                if c_id in cat_stats:
                    cat_stats[c_id]["paid"] += amt
            elif st == ExpenseStatus.CANCELLED.value:
                cancelled_exp += amt

        unallocated_amount = total_limit - total_allocated
        projected_total = planned_exp + committed_exp + paid_exp
        remaining_after_committed = total_limit - (committed_exp + paid_exp)
        projected_headroom = total_limit - projected_total

        # Build alerts and category items
        alerts: list[str] = []
        if projected_headroom < Decimal("0.00"):
            alerts.append(
                f"Projected total expenses ({currency} {projected_total:.2f}) "
                f"exceed overall budget ceiling by {currency} {abs(projected_headroom):.2f}."
            )
        if remaining_after_committed < Decimal("0.00"):
            alerts.append(
                f"Committed and paid expenses ({currency} {committed_exp + paid_exp:.2f}) "
                f"exceed budget ceiling by {currency} {abs(remaining_after_committed):.2f}."
            )
        if unallocated_amount > Decimal("0.00"):
            alerts.append(f"You have {currency} {unallocated_amount:.2f} of unallocated budget remaining.")

        category_summaries: list[CategorySummaryItem] = []
        for c in cat_rows:
            c_id = c["id"]
            stats = cat_stats[c_id]
            planned = Decimal(str(c["planned_amount"]))
            c_committed = stats["committed"]
            c_paid = stats["paid"]
            c_projected = c_committed + c_paid + stats["planned"]
            c_remaining = planned - (c_committed + c_paid)
            is_over = (c_committed + c_paid) > planned

            if is_over:
                alerts.append(
                    f"Category '{c['name']}' has exceeded its planned allocation by "
                    f"{currency} {abs(c_remaining):.2f}."
                )

            category_summaries.append(
                CategorySummaryItem(
                    category_id=c_id,
                    category_key=c["category_key"],
                    name=c["name"],
                    planned_amount=planned,
                    committed_amount=c_committed,
                    paid_amount=c_paid,
                    projected_amount=c_projected,
                    remaining_amount=c_remaining,
                    is_over_budget=is_over,
                )
            )

        return BudgetSummaryOut(
            currency=currency,
            total_limit=total_limit,
            total_allocated=total_allocated,
            unallocated_amount=unallocated_amount,
            planned_expenses=planned_exp,
            committed_expenses=committed_exp,
            paid_expenses=paid_exp,
            cancelled_expenses=cancelled_exp,
            projected_total=projected_total,
            remaining_after_committed=remaining_after_committed,
            projected_headroom=projected_headroom,
            alerts=alerts,
            category_summaries=category_summaries,
        )
