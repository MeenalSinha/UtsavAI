"""Public guest GiftCircle API router (unauthenticated, token-scoped)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import DatabaseDep
from app.modules.gifts import service as gift_service
from app.modules.gifts.schemas import (
    PublicCancelReservationRequest,
    PublicContributionConfirmationOut,
    PublicContributionRequest,
    PublicRegistryOut,
    PublicReservationConfirmationOut,
    PublicReserveRequest,
)

router = APIRouter(tags=["public_gifts"])


@router.get(
    "/public/registries/{share_token}",
    response_model=PublicRegistryOut,
    summary="Get public gift registry and wishlist without authentication",
)
def get_public_registry(
    share_token: str,
    db: DatabaseDep,
) -> PublicRegistryOut:
    return gift_service.get_public_registry(db, share_token)


@router.post(
    "/public/registries/{share_token}/items/{item_id}/reserve",
    response_model=PublicReservationConfirmationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Reserve an individual gift item (account-free)",
)
def public_reserve_item(
    share_token: str,
    item_id: uuid.UUID,
    req: PublicReserveRequest,
    db: DatabaseDep,
) -> PublicReservationConfirmationOut:
    return gift_service.public_reserve_item(db, share_token, item_id, req)


@router.post(
    "/public/registries/{share_token}/reservations/{reservation_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel reservation with one-time cancellation token",
)
def public_cancel_reservation(
    share_token: str,
    reservation_id: uuid.UUID,
    req: PublicCancelReservationRequest,
    db: DatabaseDep,
) -> None:
    gift_service.public_cancel_reservation(db, share_token, reservation_id, req)


@router.post(
    "/public/registries/{share_token}/items/{item_id}/contributions",
    response_model=PublicContributionConfirmationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Pledge a contribution towards a group gift item",
)
def public_contribute_item(
    share_token: str,
    item_id: uuid.UUID,
    req: PublicContributionRequest,
    db: DatabaseDep,
) -> PublicContributionConfirmationOut:
    return gift_service.public_contribute_item(db, share_token, item_id, req)
