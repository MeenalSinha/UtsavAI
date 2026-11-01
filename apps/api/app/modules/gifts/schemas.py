"""Pydantic schemas and DTOs for GiftCircle."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.domain import (
    DEFAULT_CURRENCY,
    SUPPORTED_CURRENCIES,
    GiftContributionStatus,
    GiftItemPriority,
    GiftItemType,
    GiftMode,
    GiftReservationStatus,
    VerificationMethod,
)


class GiftRegistryBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    is_public: bool = False
    allow_group_gifting: bool = True
    expires_at: datetime | None = None


class GiftRegistryUpdate(GiftRegistryBase):
    pass


class GiftRegistryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_id: uuid.UUID
    title: str
    is_public: bool
    has_share_token: bool
    allow_group_gifting: bool
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    total_items: int = 0
    available_items: int = 0
    reserved_items: int = 0
    group_gift_items: int = 0
    total_pledged_amount: Decimal = Decimal("0.00")
    total_confirmed_amount: Decimal = Decimal("0.00")
    currency: str = DEFAULT_CURRENCY


class ShareLinkOut(BaseModel):
    share_url: str
    raw_token: str
    expires_at: datetime | None = None


# ------------------------------------------------------------------ Gift Items
class GiftItemCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    item_type: GiftItemType = GiftItemType.PRODUCT
    gift_mode: GiftMode = GiftMode.INDIVIDUAL
    product_url: str | None = Field(default=None, max_length=1000)
    target_amount: Decimal | None = None
    currency: str = DEFAULT_CURRENCY
    priority: GiftItemPriority = GiftItemPriority.IMPORTANT
    display_order: int = 0

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Currency '{v}' is not supported.")
        return v

    @field_validator("target_amount")
    @classmethod
    def validate_target(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0.00"):
            raise ValueError("Target amount must be strictly positive.")
        return v


class GiftItemUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    item_type: GiftItemType | None = None
    gift_mode: GiftMode | None = None
    product_url: str | None = Field(default=None, max_length=1000)
    target_amount: Decimal | None = None
    currency: str | None = None
    priority: GiftItemPriority | None = None
    display_order: int | None = None
    is_active: bool | None = None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is not None and v not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Currency '{v}' is not supported.")
        return v

    @field_validator("target_amount")
    @classmethod
    def validate_target(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= Decimal("0.00"):
            raise ValueError("Target amount must be strictly positive.")
        return v


class GiftItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    registry_id: uuid.UUID
    title: str
    description: str | None = None
    item_type: GiftItemType
    gift_mode: GiftMode
    product_url: str | None = None
    target_amount: Decimal | None = None
    currency: str
    priority: GiftItemPriority
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    # Aggregated metrics for host view
    active_reservation_status: GiftReservationStatus | None = None
    active_reservation_alias: str | None = None
    pledged_amount: Decimal = Decimal("0.00")
    confirmed_amount: Decimal = Decimal("0.00")
    remaining_amount: Decimal | None = None


# ------------------------------------------------------------------ Reservations
class GiftReservationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: GiftReservationStatus


class GiftReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    gift_item_id: uuid.UUID
    gift_item_title: str | None = None
    guest_alias: str | None = None
    status: GiftReservationStatus
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------------ Contributions
class HostConfirmationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmation_note: str | None = Field(default=None, max_length=2000)
    verification_method: VerificationMethod = VerificationMethod.HOST_MANUAL_CONFIRMATION


class GiftContributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    gift_item_id: uuid.UUID
    gift_item_title: str | None = None
    guest_alias: str | None = None
    amount: Decimal
    currency: str
    status: GiftContributionStatus
    verification_method: VerificationMethod | None = None
    verified_at: datetime | None = None
    verified_by: uuid.UUID | None = None
    confirmation_note: str | None = None
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------------ Public Guest DTOs
class PublicGiftItemOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None = None
    item_type: GiftItemType
    gift_mode: GiftMode
    product_url: str | None = None
    target_amount: Decimal | None = None
    currency: str
    priority: GiftItemPriority
    pledged_amount: Decimal
    confirmed_amount: Decimal
    remaining_amount: Decimal | None = None
    status: str  # "available" | "reserved" | "fulfilled" | "target_reached"


class PublicRegistryOut(BaseModel):
    title: str
    event_label: str
    items: list[PublicGiftItemOut]
    allow_group_gifting: bool
    currency: str


class PublicReserveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    guest_alias: str | None = Field(default=None, max_length=80)
    idempotency_key: str = Field(min_length=1, max_length=128)


class PublicReservationConfirmationOut(BaseModel):
    reservation_id: uuid.UUID
    gift_item_id: uuid.UUID
    cancellation_token: str | None = None
    message: str


class PublicCancelReservationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cancellation_token: str = Field(min_length=1, max_length=256)


class PublicContributionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    guest_alias: str | None = Field(default=None, max_length=80)
    amount: Decimal = Field(gt=Decimal("0.00"))
    currency: str = DEFAULT_CURRENCY
    idempotency_key: str = Field(min_length=1, max_length=128)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v not in SUPPORTED_CURRENCIES:
            raise ValueError(f"Currency '{v}' is not supported.")
        return v


class PublicContributionConfirmationOut(BaseModel):
    contribution_id: uuid.UUID
    gift_item_id: uuid.UUID
    amount: Decimal
    currency: str
    message: str


# ------------------------------------------------------------------ Shared Event Context Gift Summary
class ContextGiftSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registry_exists: bool = False
    is_public: bool = False
    total_items: int = 0
    available_items: int = 0
    reserved_items: int = 0
    group_gift_items: int = 0
    active_group_pledges: Decimal = Decimal("0.00")
    host_confirmed_amount: Decimal = Decimal("0.00")
    currency: str = DEFAULT_CURRENCY
