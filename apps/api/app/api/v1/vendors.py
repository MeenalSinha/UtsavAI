"""VendorConnect API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query, status

from app.api.deps import DatabaseDep, PrincipalDep
from app.modules.vendors import service as vendor_service
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

router = APIRouter(tags=["vendors"])


@router.get(
    "/events/{event_id}/vendors",
    response_model=list[VendorOut],
    summary="List event vendors with optional filtering",
)
def list_vendors(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[VendorOut]:
    return vendor_service.list_vendors(
        db,
        principal,
        event_id,
        category=category,
        status=status,
        search=search,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/events/{event_id}/vendors",
    response_model=VendorOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new vendor record",
)
def create_vendor(
    event_id: uuid.UUID,
    body: VendorCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> VendorOut:
    return vendor_service.create_vendor(db, principal, event_id, body)


@router.get(
    "/events/{event_id}/vendors/summary",
    response_model=VendorSummaryOut,
    summary="Get vendor status summary and category metrics",
)
def get_vendor_summary(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> VendorSummaryOut:
    return vendor_service.get_vendor_summary(db, principal, event_id)


@router.get(
    "/events/{event_id}/vendors/{vendor_id}",
    response_model=VendorDetailOut,
    summary="Get vendor details including recorded quotations and linked expenses",
)
def get_vendor(
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> VendorDetailOut:
    return vendor_service.get_vendor(db, principal, event_id, vendor_id)


@router.patch(
    "/events/{event_id}/vendors/{vendor_id}",
    response_model=VendorOut,
    summary="Update vendor details or lifecycle status",
)
def update_vendor(
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    body: VendorUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> VendorOut:
    return vendor_service.update_vendor(db, principal, event_id, vendor_id, body)


@router.delete(
    "/events/{event_id}/vendors/{vendor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-archive a vendor record",
)
def archive_vendor(
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> None:
    vendor_service.archive_vendor(db, principal, event_id, vendor_id)


# ------------------------------------------------------------------ Quotations
@router.get(
    "/events/{event_id}/vendors/{vendor_id}/quotes",
    response_model=list[VendorQuoteOut],
    summary="List recorded quotations for a vendor",
)
def list_quotes(
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> list[VendorQuoteOut]:
    return vendor_service.list_quotes(db, principal, event_id, vendor_id)


@router.post(
    "/events/{event_id}/vendors/{vendor_id}/quotes",
    response_model=VendorQuoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new quotation from a vendor",
)
def create_quote(
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    body: VendorQuoteCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> VendorQuoteOut:
    return vendor_service.create_quote(db, principal, event_id, vendor_id, body)


@router.patch(
    "/events/{event_id}/vendors/{vendor_id}/quotes/{quote_id}",
    response_model=VendorQuoteOut,
    summary="Update quotation details or acceptance/shortlist status",
)
def update_quote(
    event_id: uuid.UUID,
    vendor_id: uuid.UUID,
    quote_id: uuid.UUID,
    body: VendorQuoteUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> VendorQuoteOut:
    return vendor_service.update_quote(db, principal, event_id, vendor_id, quote_id, body)


# ------------------------------------------------------------------ Intelligent Comparison
@router.get(
    "/events/{event_id}/vendor-quote-comparison",
    response_model=QuotationComparisonOut,
    summary="Deterministic quotation comparison grouped by category",
)
def get_quotation_comparison(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> QuotationComparisonOut:
    return vendor_service.get_quotation_comparison(db, principal, event_id)
