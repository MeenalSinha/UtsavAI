"""Private host GiftCircle API router."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, status

from app.api.deps import DatabaseDep, PrincipalDep
from app.modules.gifts import service as gift_service
from app.modules.gifts.schemas import (
    GiftContributionOut,
    GiftItemCreate,
    GiftItemOut,
    GiftItemUpdate,
    GiftRegistryOut,
    GiftRegistryUpdate,
    GiftReservationOut,
    GiftReservationUpdate,
    HostConfirmationRequest,
    ShareLinkOut,
)

router = APIRouter(tags=["gifts"])


@router.get(
    "/events/{event_id}/gift-registry",
    response_model=GiftRegistryOut,
    summary="Get event gift registry and private metrics",
)
def get_registry(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> GiftRegistryOut:
    return gift_service.get_registry(db, principal, event_id)


@router.put(
    "/events/{event_id}/gift-registry",
    response_model=GiftRegistryOut,
    summary="Create or update event gift registry settings",
)
def update_registry(
    event_id: uuid.UUID,
    req: GiftRegistryUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> GiftRegistryOut:
    return gift_service.update_registry(db, principal, event_id, req)


@router.post(
    "/events/{event_id}/gift-registry/share-link",
    response_model=ShareLinkOut,
    summary="Generate or rotate public share token for gift registry",
)
def generate_share_link(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> ShareLinkOut:
    return gift_service.generate_share_link(db, principal, event_id)


@router.delete(
    "/events/{event_id}/gift-registry/share-link",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke current public share link",
)
def revoke_share_link(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> None:
    gift_service.revoke_share_link(db, principal, event_id)


@router.get(
    "/events/{event_id}/gift-registry/items",
    response_model=list[GiftItemOut],
    summary="List all gift wishlist items",
)
def list_items(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> list[GiftItemOut]:
    return gift_service.list_items(db, principal, event_id)


@router.post(
    "/events/{event_id}/gift-registry/items",
    response_model=GiftItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new gift wishlist item",
)
def create_item(
    event_id: uuid.UUID,
    req: GiftItemCreate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> GiftItemOut:
    return gift_service.create_item(db, principal, event_id, req)


@router.patch(
    "/events/{event_id}/gift-registry/items/{item_id}",
    response_model=GiftItemOut,
    summary="Update a gift wishlist item",
)
def update_item(
    event_id: uuid.UUID,
    item_id: uuid.UUID,
    req: GiftItemUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> GiftItemOut:
    return gift_service.update_item(db, principal, event_id, item_id, req)


@router.delete(
    "/events/{event_id}/gift-registry/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate a gift wishlist item",
)
def deactivate_item(
    event_id: uuid.UUID,
    item_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> None:
    gift_service.deactivate_item(db, principal, event_id, item_id)


@router.get(
    "/events/{event_id}/gift-reservations",
    response_model=list[GiftReservationOut],
    summary="List guest reservations for the event",
)
def list_reservations(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> list[GiftReservationOut]:
    return gift_service.list_reservations(db, principal, event_id)


@router.patch(
    "/events/{event_id}/gift-reservations/{reservation_id}",
    response_model=GiftReservationOut,
    summary="Update reservation status (e.g. fulfilled or cancelled)",
)
def update_reservation(
    event_id: uuid.UUID,
    reservation_id: uuid.UUID,
    req: GiftReservationUpdate,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> GiftReservationOut:
    return gift_service.update_reservation(db, principal, event_id, reservation_id, req)


@router.get(
    "/events/{event_id}/gift-contributions",
    response_model=list[GiftContributionOut],
    summary="List all group gift contributions for reconciliation",
)
def list_contributions(
    event_id: uuid.UUID,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> list[GiftContributionOut]:
    return gift_service.list_contributions(db, principal, event_id)


@router.post(
    "/events/{event_id}/gift-contributions/{contribution_id}/confirm",
    response_model=GiftContributionOut,
    summary="Host manually confirms receipt of an offline group contribution",
)
def confirm_contribution(
    event_id: uuid.UUID,
    contribution_id: uuid.UUID,
    req: HostConfirmationRequest,
    principal: PrincipalDep,
    db: DatabaseDep,
) -> GiftContributionOut:
    return gift_service.confirm_contribution(db, principal, event_id, contribution_id, req)
