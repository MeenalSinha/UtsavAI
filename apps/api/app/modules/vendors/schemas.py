"""VendorConnect schemas and validation models."""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.core.domain import QuoteStatus, VendorStatus
from app.modules.budget.schemas import DecimalMoney, ExpenseOut

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CategoryStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
ContactNameStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]


class VendorCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category: CategoryStr
    name: NameStr
    contact_name: ContactNameStr | None = None
    email: str | None = None
    phone: str | None = None
    website_url: str | None = None
    notes: str | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format.")
        return v

    @field_validator("website_url")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", v, re.IGNORECASE):
            raise ValueError("Website must be a valid HTTP/HTTPS URL.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^\+?[\d\s\-()]{7,25}$", v):
            raise ValueError("Invalid telephone number format.")
        return v


class VendorUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    category: CategoryStr | None = None
    name: NameStr | None = None
    contact_name: ContactNameStr | None = None
    email: str | None = None
    phone: str | None = None
    website_url: str | None = None
    notes: str | None = None
    status: VendorStatus | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", v):
            raise ValueError("Invalid email format.")
        return v

    @field_validator("website_url")
    @classmethod
    def validate_website(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^https?://[^\s/$.?#].[^\s]*$", v, re.IGNORECASE):
            raise ValueError("Website must be a valid HTTP/HTTPS URL.")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not re.match(r"^\+?[\d\s\-()]{7,25}$", v):
            raise ValueError("Invalid telephone number format.")
        return v


class VendorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: uuid.UUID
    category: str
    name: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    website_url: str | None = None
    notes: str | None = None
    status: VendorStatus
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None

    quotes_count: int = 0
    latest_quote_amount: DecimalMoney | None = None
    latest_quote_currency: str | None = None
    associated_expenses_count: int = 0
    total_spent_amount: DecimalMoney = Decimal("0.00")


class VendorQuoteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: DecimalMoney
    currency: str = Field(default="INR", min_length=3, max_length=3)
    scope_summary: NonEmptyStr
    valid_until: date | None = None
    notes: str | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v < Decimal("0.00"):
            raise ValueError("Quotation amount cannot be negative.")
        return v.quantize(Decimal("0.01"))

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("Currency code must be 3 uppercase letters.")
        return v


class VendorQuoteUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    amount: DecimalMoney | None = None
    currency: str | None = None
    scope_summary: NonEmptyStr | None = None
    valid_until: date | None = None
    notes: str | None = None
    status: QuoteStatus | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal | None) -> Decimal | None:
        if v is None:
            return None
        if v < Decimal("0.00"):
            raise ValueError("Quotation amount cannot be negative.")
        return v.quantize(Decimal("0.01"))

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip().upper()
        if not re.match(r"^[A-Z]{3}$", v):
            raise ValueError("Currency code must be 3 uppercase letters.")
        return v


class VendorQuoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_id: uuid.UUID
    amount: DecimalMoney
    currency: str
    scope_summary: str
    valid_until: date | None = None
    notes: str | None = None
    status: QuoteStatus
    created_at: datetime
    updated_at: datetime


class VendorDetailOut(VendorOut):
    quotes: list[VendorQuoteOut] = Field(default_factory=list)
    associated_expenses: list[ExpenseOut] = Field(default_factory=list)


# ------------------------------------------------------------------ Quotation Comparison Schemas
class QuotationComparisonItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_id: uuid.UUID
    vendor_name: str
    vendor_status: VendorStatus
    quote_id: uuid.UUID
    amount: DecimalMoney
    currency: str
    scope_summary: str
    valid_until: date | None = None
    status: QuoteStatus
    missing_fields: list[str] = Field(default_factory=list)
    comparison_warnings: list[str] = Field(default_factory=list)
    updated_at: datetime


class QuotationComparisonGroup(BaseModel):
    category: str
    quotes: list[QuotationComparisonItem] = Field(default_factory=list)
    category_warnings: list[str] = Field(default_factory=list)
    price_range_min: DecimalMoney | None = None
    price_range_max: DecimalMoney | None = None


class QuotationComparisonOut(BaseModel):
    event_id: uuid.UUID
    currency: str
    groups: list[QuotationComparisonGroup] = Field(default_factory=list)
    total_quotes_compared: int = 0


# ------------------------------------------------------------------ Vendor Dashboard & Context Schemas
class VendorCategorySummary(BaseModel):
    category: str
    vendor_count: int = 0
    quoted_count: int = 0
    shortlisted_count: int = 0
    booked_count: int = 0


class VendorSummaryOut(BaseModel):
    total_vendors: int = 0
    identified_count: int = 0
    contacted_count: int = 0
    quoted_count: int = 0
    shortlisted_count: int = 0
    booked_count: int = 0
    declined_count: int = 0
    categories: list[VendorCategorySummary] = Field(default_factory=list)
    quote_count: int = 0
    pending_decisions: int = 0
