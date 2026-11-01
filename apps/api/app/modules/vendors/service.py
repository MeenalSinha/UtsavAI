"""Business logic and service orchestration for VendorConnect."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from app.core.domain import ExpenseStatus, MemberRole, Permission, QuoteStatus, VendorStatus
from app.core.errors import ConflictError, ForbiddenError, InvalidRequestError, NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.audit import repository as audit
from app.modules.budget import repository as budget_repo
from app.modules.budget.schemas import ExpenseOut
from app.modules.events import repository as events_repo
from app.modules.events.permissions import require_permission
from app.modules.vendors import comparison
from app.modules.vendors import repository as repo
from app.modules.vendors.schemas import (
    QuotationComparisonOut,
    VendorCreate,
    VendorDetailOut,
    VendorOut,
    VendorQuoteCreate,
    VendorQuoteOut,
    VendorQuoteUpdate,
    VendorSummaryOut,
    VendorUpdate,
)

# Valid vendor status transitions
_VALID_VENDOR_TRANSITIONS: dict[VendorStatus, set[VendorStatus]] = {
    VendorStatus.IDENTIFIED: {
        VendorStatus.IDENTIFIED,
        VendorStatus.CONTACTED,
        VendorStatus.QUOTED,
        VendorStatus.SHORTLISTED,
        VendorStatus.DECLINED,
    },
    VendorStatus.CONTACTED: {
        VendorStatus.CONTACTED,
        VendorStatus.QUOTED,
        VendorStatus.SHORTLISTED,
        VendorStatus.DECLINED,
    },
    VendorStatus.QUOTED: {
        VendorStatus.QUOTED,
        VendorStatus.SHORTLISTED,
        VendorStatus.BOOKED,
        VendorStatus.DECLINED,
    },
    VendorStatus.SHORTLISTED: {
        VendorStatus.SHORTLISTED,
        VendorStatus.BOOKED,
        VendorStatus.QUOTED,  # Allow reconsideration
        VendorStatus.DECLINED,
    },
    VendorStatus.BOOKED: {
        VendorStatus.BOOKED,
        VendorStatus.SHORTLISTED,  # If contract falls through
        VendorStatus.DECLINED,
    },
    VendorStatus.DECLINED: {
        VendorStatus.DECLINED,
        VendorStatus.IDENTIFIED,
        VendorStatus.CONTACTED,
        VendorStatus.QUOTED,  # Allow restoring
    },
}


def _require_active_event(event: dict[str, Any]) -> None:
    if event["status"] == "archived":
        raise ForbiddenError("Archived events are read-only.")


def list_vendors(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    category: str | None = None,
    status: str | None = None,
    search: str | None = None,
    include_archived: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> list[VendorOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_READ)

        vendor_rows = repo.list_vendors(
            conn,
            event_id,
            category=category,
            status=status,
            search=search,
            include_archived=include_archived,
            limit=limit,
            offset=offset,
        )
        expense_stats = repo.get_vendor_expense_stats(conn, event_id)
        latest_quotes = repo.get_vendor_latest_quotes(conn, event_id)

        # Count quotes per vendor
        all_quotes = repo.list_all_event_quotes(conn, event_id)
        quote_counts: dict[uuid.UUID, int] = {}
        for q in all_quotes:
            vid = q["vendor_id"]
            quote_counts[vid] = quote_counts.get(vid, 0) + 1

        result: list[VendorOut] = []
        for r in vendor_rows:
            vid = r["id"]
            exp_info = expense_stats.get(vid, {"count": 0, "total": Decimal("0.00")})
            quote_info = latest_quotes.get(vid)

            result.append(
                VendorOut(
                    id=r["id"],
                    event_id=r["event_id"],
                    category=r["category"],
                    name=r["name"],
                    contact_name=r["contact_name"],
                    email=r["email"],
                    phone=r["phone"],
                    website_url=r["website_url"],
                    notes=r["notes"],
                    status=VendorStatus(r["status"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    archived_at=r["archived_at"],
                    quotes_count=quote_counts.get(vid, 0),
                    latest_quote_amount=quote_info["amount"] if quote_info else None,
                    latest_quote_currency=quote_info["currency"] if quote_info else None,
                    associated_expenses_count=exp_info["count"],
                    total_spent_amount=exp_info["total"],
                )
            )
        return result


def get_vendor(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
) -> VendorDetailOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_READ)

        v = repo.get_vendor(conn, event_id, vendor_id, include_archived=True)
        if v is None:
            raise NotFoundError("Vendor not found.")

        quote_rows = repo.list_quotes_for_vendor(conn, vendor_id)
        expense_rows = budget_repo.list_expenses(conn, event_id)
        vendor_expenses = [e for e in expense_rows if e["vendor_id"] == vendor_id]

        expense_stats = repo.get_vendor_expense_stats(conn, event_id)
        exp_info = expense_stats.get(vendor_id, {"count": 0, "total": Decimal("0.00")})
        latest_quotes = repo.get_vendor_latest_quotes(conn, event_id)
        quote_info = latest_quotes.get(vendor_id)

        quotes_out = [
            VendorQuoteOut(
                id=q["id"],
                vendor_id=q["vendor_id"],
                amount=Decimal(str(q["amount"])),
                currency=q["currency"],
                scope_summary=q["scope_summary"],
                valid_until=q["valid_until"],
                notes=q["notes"],
                status=QuoteStatus(q["status"]),
                created_at=q["created_at"],
                updated_at=q["updated_at"],
            )
            for q in quote_rows
        ]

        expenses_out = [
            ExpenseOut(
                id=e["id"],
                event_id=e["event_id"],
                budget_category_id=e["budget_category_id"],
                vendor_id=e["vendor_id"],
                description=e["description"],
                amount=Decimal(str(e["amount"])),
                currency=e["currency"],
                expense_date=e["expense_date"],
                status=ExpenseStatus(e["status"]),
                created_by=e["created_by"],
                created_at=e["created_at"],
                updated_at=e["updated_at"],
            )
            for e in vendor_expenses
        ]

        return VendorDetailOut(
            id=v["id"],
            event_id=v["event_id"],
            category=v["category"],
            name=v["name"],
            contact_name=v["contact_name"],
            email=v["email"],
            phone=v["phone"],
            website_url=v["website_url"],
            notes=v["notes"],
            status=VendorStatus(v["status"]),
            created_at=v["created_at"],
            updated_at=v["updated_at"],
            archived_at=v["archived_at"],
            quotes_count=len(quotes_out),
            latest_quote_amount=quote_info["amount"] if quote_info else None,
            latest_quote_currency=quote_info["currency"] if quote_info else None,
            associated_expenses_count=exp_info["count"],
            total_spent_amount=exp_info["total"],
            quotes=quotes_out,
            associated_expenses=expenses_out,
        )


def create_vendor(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    req: VendorCreate,
) -> VendorOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_MANAGE)

        row = repo.create_vendor(
            conn,
            event_id=event_id,
            category=req.category,
            name=req.name,
            contact_name=req.contact_name,
            email=req.email,
            phone=req.phone,
            website_url=req.website_url,
            notes=req.notes,
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="vendor.created",
            entity_type="event_vendors",
            entity_id=row["id"],
            request_id=request_id,
            metadata={"name": req.name, "category": req.category},
        )

        return VendorOut(
            id=row["id"],
            event_id=row["event_id"],
            category=row["category"],
            name=row["name"],
            contact_name=row["contact_name"],
            email=row["email"],
            phone=row["phone"],
            website_url=row["website_url"],
            notes=row["notes"],
            status=VendorStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            archived_at=row["archived_at"],
            quotes_count=0,
            latest_quote_amount=None,
            latest_quote_currency=None,
            associated_expenses_count=0,
            total_spent_amount=Decimal("0.00"),
        )


def update_vendor(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    req: VendorUpdate,
) -> VendorOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_MANAGE)

        existing = repo.get_vendor(conn, event_id, vendor_id, include_archived=True)
        if existing is None:
            raise NotFoundError("Vendor not found.")

        current_status = VendorStatus(existing["status"])

        # Validate status transitions if status is updated
        if req.status is not None and req.status != current_status:
            valid_targets = _VALID_VENDOR_TRANSITIONS.get(current_status, set())
            if req.status not in valid_targets:
                raise ConflictError(
                    f"Cannot transition vendor from '{current_status.value}' to '{req.status.value}'."
                )

        row = repo.update_vendor(
            conn,
            event_id=event_id,
            vendor_id=vendor_id,
            category=req.category,
            name=req.name,
            contact_name=req.contact_name,
            email=req.email,
            phone=req.phone,
            website_url=req.website_url,
            notes=req.notes,
            status=req.status.value if req.status else None,
        )
        assert row is not None

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="vendor.updated",
            entity_type="event_vendors",
            entity_id=vendor_id,
            request_id=request_id,
            metadata={
                "status": req.status.value if req.status else current_status.value,
                "name": row["name"],
            },
        )

        expense_stats = repo.get_vendor_expense_stats(conn, event_id)
        latest_quotes = repo.get_vendor_latest_quotes(conn, event_id)
        quote_info = latest_quotes.get(vendor_id)
        exp_info = expense_stats.get(vendor_id, {"count": 0, "total": Decimal("0.00")})
        quote_rows = repo.list_quotes_for_vendor(conn, vendor_id)

        return VendorOut(
            id=row["id"],
            event_id=row["event_id"],
            category=row["category"],
            name=row["name"],
            contact_name=row["contact_name"],
            email=row["email"],
            phone=row["phone"],
            website_url=row["website_url"],
            notes=row["notes"],
            status=VendorStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            archived_at=row["archived_at"],
            quotes_count=len(quote_rows),
            latest_quote_amount=quote_info["amount"] if quote_info else None,
            latest_quote_currency=quote_info["currency"] if quote_info else None,
            associated_expenses_count=exp_info["count"],
            total_spent_amount=exp_info["total"],
        )


def archive_vendor(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_MANAGE)

        existing = repo.get_vendor(conn, event_id, vendor_id, include_archived=False)
        if existing is None:
            raise NotFoundError("Vendor not found or already archived.")

        ok = repo.archive_vendor(conn, event_id, vendor_id)
        if not ok:
            raise NotFoundError("Vendor not found or already archived.")

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="vendor.archived",
            entity_type="event_vendors",
            entity_id=vendor_id,
            request_id=request_id,
            metadata={"name": existing["name"]},
        )


# ------------------------------------------------------------------ Quotation Service Methods
def list_quotes(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
) -> list[VendorQuoteOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_READ)

        v = repo.get_vendor(conn, event_id, vendor_id, include_archived=True)
        if v is None:
            raise NotFoundError("Vendor not found.")

        rows = repo.list_quotes_for_vendor(conn, vendor_id)
        return [
            VendorQuoteOut(
                id=r["id"],
                vendor_id=r["vendor_id"],
                amount=Decimal(str(r["amount"])),
                currency=r["currency"],
                scope_summary=r["scope_summary"],
                valid_until=r["valid_until"],
                notes=r["notes"],
                status=QuoteStatus(r["status"]),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]


def create_quote(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    req: VendorQuoteCreate,
) -> VendorQuoteOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_MANAGE)

        v = repo.get_vendor(conn, event_id, vendor_id, include_archived=True)
        if v is None:
            raise NotFoundError("Vendor not found.")
        if v["archived_at"] is not None:
            raise ForbiddenError("Cannot add quotations to an archived vendor.")

        if req.currency != event["currency"]:
            raise InvalidRequestError(
                f"Quotation currency '{req.currency}' does not match event currency '{event['currency']}'."
            )

        row = repo.create_quote(
            conn,
            vendor_id=vendor_id,
            amount=req.amount,
            currency=req.currency,
            scope_summary=req.scope_summary,
            valid_until=req.valid_until,
            notes=req.notes,
        )

        # Advance vendor status to 'quoted' if currently 'identified' or 'contacted'
        if v["status"] in (VendorStatus.IDENTIFIED.value, VendorStatus.CONTACTED.value):
            repo.update_vendor(conn, event_id, vendor_id, status=VendorStatus.QUOTED.value)

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="vendor.quote_created",
            entity_type="vendor_quotes",
            entity_id=row["id"],
            request_id=request_id,
            metadata={"amount": str(req.amount), "vendor_id": str(vendor_id)},
        )

        return VendorQuoteOut(
            id=row["id"],
            vendor_id=row["vendor_id"],
            amount=Decimal(str(row["amount"])),
            currency=row["currency"],
            scope_summary=row["scope_summary"],
            valid_until=row["valid_until"],
            notes=row["notes"],
            status=QuoteStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def update_quote(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    quote_id: uuid.UUID,
    req: VendorQuoteUpdate,
) -> VendorQuoteOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_MANAGE)

        v = repo.get_vendor(conn, event_id, vendor_id, include_archived=True)
        if v is None:
            raise NotFoundError("Vendor not found.")

        quote = repo.get_quote(conn, vendor_id, quote_id)
        if quote is None:
            raise NotFoundError("Quotation not found.")

        if req.currency is not None and req.currency != event["currency"]:
            raise InvalidRequestError(
                f"Quotation currency '{req.currency}' does not match event currency '{event['currency']}'."
            )

        row = repo.update_quote(
            conn,
            vendor_id=vendor_id,
            quote_id=quote_id,
            amount=req.amount,
            currency=req.currency,
            scope_summary=req.scope_summary,
            valid_until=req.valid_until,
            notes=req.notes,
            status=req.status.value if req.status else None,
        )
        assert row is not None

        # Synchronize vendor status if quotation status moves to shortlisted or accepted
        if req.status == QuoteStatus.SHORTLISTED and v["status"] not in (
            VendorStatus.BOOKED.value,
            VendorStatus.SHORTLISTED.value,
        ):
            repo.update_vendor(conn, event_id, vendor_id, status=VendorStatus.SHORTLISTED.value)
        elif req.status == QuoteStatus.ACCEPTED and v["status"] != VendorStatus.BOOKED.value:
            repo.update_vendor(conn, event_id, vendor_id, status=VendorStatus.BOOKED.value)

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="vendor.quote_updated",
            entity_type="vendor_quotes",
            entity_id=quote_id,
            request_id=request_id,
            metadata={
                "status": req.status.value if req.status else quote["status"],
                "amount": str(row["amount"]),
            },
        )

        return VendorQuoteOut(
            id=row["id"],
            vendor_id=row["vendor_id"],
            amount=Decimal(str(row["amount"])),
            currency=row["currency"],
            scope_summary=row["scope_summary"],
            valid_until=row["valid_until"],
            notes=row["notes"],
            status=QuoteStatus(row["status"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def get_quotation_comparison(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
) -> QuotationComparisonOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_READ)

        raw_quotes = repo.list_all_event_quotes(conn, event_id)
        return comparison.generate_quotation_comparison(
            event_id=event_id,
            event_currency=event["currency"],
            raw_quotes=raw_quotes,
        )


def get_vendor_summary(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
) -> VendorSummaryOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.VENDOR_READ)

        metrics = repo.get_vendor_metrics(conn, event_id)
        return VendorSummaryOut(**metrics)
