"""Business logic and service orchestration for GiftCircle."""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from decimal import Decimal
from typing import Any

from app.core.config import get_settings
from app.core.domain import (
    DEFAULT_CURRENCY,
    GiftContributionStatus,
    GiftItemPriority,
    GiftItemType,
    GiftMode,
    GiftReservationStatus,
    MemberRole,
    Permission,
    VerificationMethod,
)
from app.core.errors import ConflictError, ForbiddenError, InvalidRequestError, NotFoundError
from app.core.request_context import request_id_var
from app.core.security import Principal
from app.database.pool import Database
from app.modules.audit import repository as audit
from app.modules.events import repository as events_repo
from app.modules.events.permissions import require_permission
from app.modules.gifts import repository as repo
from app.modules.gifts.schemas import (
    ContextGiftSummary,
    GiftContributionOut,
    GiftItemCreate,
    GiftItemOut,
    GiftItemUpdate,
    GiftRegistryOut,
    GiftRegistryUpdate,
    GiftReservationOut,
    GiftReservationUpdate,
    HostConfirmationRequest,
    PublicCancelReservationRequest,
    PublicContributionConfirmationOut,
    PublicContributionRequest,
    PublicGiftItemOut,
    PublicRegistryOut,
    PublicReservationConfirmationOut,
    PublicReserveRequest,
    ShareLinkOut,
)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def _require_active_event(event: dict[str, Any]) -> None:
    if event["status"] == "archived":
        raise ForbiddenError("Archived events are read-only.")


# ------------------------------------------------------------------ Host Registry Management
def get_registry(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
) -> GiftRegistryOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_READ)

        reg = repo.get_registry_by_event(conn, event_id)
        if reg is None:
            # Auto-provision a default registry record if none exists
            require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)
            _require_active_event(event)
            reg = repo.upsert_registry(
                conn,
                event_id=event_id,
                title=f"{event['title']} Wishlist",
                is_public=False,
                allow_group_gifting=True,
                expires_at=None,
            )

        metrics = repo.get_registry_metrics(conn, reg["id"])
        return GiftRegistryOut(
            id=reg["id"],
            event_id=reg["event_id"],
            title=reg["title"],
            is_public=reg["is_public"],
            has_share_token=reg["share_token_hash"] is not None and reg["revoked_at"] is None,
            allow_group_gifting=reg["allow_group_gifting"],
            expires_at=reg["expires_at"],
            revoked_at=reg["revoked_at"],
            created_at=reg["created_at"],
            updated_at=reg["updated_at"],
            total_items=metrics["total_items"],
            available_items=metrics["available_items"],
            reserved_items=metrics["reserved_items"],
            group_gift_items=metrics["group_gift_items"],
            total_pledged_amount=metrics["total_pledged_amount"],
            total_confirmed_amount=metrics["total_confirmed_amount"],
            currency=event["currency"] or DEFAULT_CURRENCY,
        )


def update_registry(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    req: GiftRegistryUpdate,
) -> GiftRegistryOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)

        reg = repo.upsert_registry(
            conn,
            event_id=event_id,
            title=req.title.strip(),
            is_public=req.is_public,
            allow_group_gifting=req.allow_group_gifting,
            expires_at=req.expires_at,
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="gift_registry.updated",
            entity_type="gift_registries",
            entity_id=reg["id"],
            request_id=request_id,
            metadata={"title": req.title, "is_public": req.is_public},
        )

        metrics = repo.get_registry_metrics(conn, reg["id"])
        return GiftRegistryOut(
            id=reg["id"],
            event_id=reg["event_id"],
            title=reg["title"],
            is_public=reg["is_public"],
            has_share_token=reg["share_token_hash"] is not None and reg["revoked_at"] is None,
            allow_group_gifting=reg["allow_group_gifting"],
            expires_at=reg["expires_at"],
            revoked_at=reg["revoked_at"],
            created_at=reg["created_at"],
            updated_at=reg["updated_at"],
            total_items=metrics["total_items"],
            available_items=metrics["available_items"],
            reserved_items=metrics["reserved_items"],
            group_gift_items=metrics["group_gift_items"],
            total_pledged_amount=metrics["total_pledged_amount"],
            total_confirmed_amount=metrics["total_confirmed_amount"],
            currency=event["currency"] or DEFAULT_CURRENCY,
        )


def generate_share_link(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
) -> ShareLinkOut:
    request_id = request_id_var.get()
    settings = get_settings()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)

        reg = repo.get_registry_by_event(conn, event_id)
        if reg is None:
            reg = repo.upsert_registry(
                conn,
                event_id=event_id,
                title=f"{event['title']} Wishlist",
                is_public=True,
                allow_group_gifting=True,
                expires_at=None,
            )

        raw_token = secrets.token_urlsafe(32)
        token_hash = _hash_token(raw_token)

        repo.set_share_token_hash(conn, event_id=event_id, token_hash=token_hash, is_public=True)

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="gift_registry.share_link_generated",
            entity_type="gift_registries",
            entity_id=reg["id"],
            request_id=request_id,
            metadata={"status": "public_link_created"},
        )

        # Derive share URL based on public origin
        base_origin = settings.cors_allowed_origins.split(",")[0].strip() or "http://localhost:3000"
        share_url = f"{base_origin}/g/{raw_token}"

        return ShareLinkOut(
            share_url=share_url,
            raw_token=raw_token,
            expires_at=reg["expires_at"],
        )


def revoke_share_link(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)

        reg = repo.get_registry_by_event(conn, event_id)
        if reg is None:
            raise NotFoundError("Registry not found.")

        ok = repo.revoke_share_token(conn, event_id)
        if not ok:
            raise InvalidRequestError("Share link is already inactive or revoked.")

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="gift_registry.share_link_revoked",
            entity_type="gift_registries",
            entity_id=reg["id"],
            request_id=request_id,
            metadata={"status": "revoked"},
        )


# ------------------------------------------------------------------ Host Item Management
def list_items(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
) -> list[GiftItemOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_READ)

        reg = repo.get_registry_by_event(conn, event_id)
        if reg is None:
            return []

        items = repo.list_items(conn, reg["id"], include_inactive=False)
        result: list[GiftItemOut] = []
        for it in items:
            item_id = it["id"]
            res = repo.get_active_reservation(conn, item_id)
            accounting = repo.get_contribution_accounting(conn, item_id)

            remaining: Decimal | None = None
            if it["target_amount"] is not None:
                remaining = max(Decimal("0.00"), Decimal(str(it["target_amount"])) - accounting["total"])

            result.append(
                GiftItemOut(
                    id=it["id"],
                    registry_id=it["registry_id"],
                    title=it["title"],
                    description=it["description"],
                    item_type=GiftItemType(it["item_type"]),
                    gift_mode=GiftMode(it["gift_mode"]),
                    product_url=it["product_url"],
                    target_amount=(
                        Decimal(str(it["target_amount"])) if it["target_amount"] is not None else None
                    ),
                    currency=it["currency"],
                    priority=GiftItemPriority(it["priority"]),
                    display_order=it["display_order"],
                    is_active=it["is_active"],
                    created_at=it["created_at"],
                    updated_at=it["updated_at"],
                    active_reservation_status=GiftReservationStatus(res["status"]) if res else None,
                    active_reservation_alias=res["guest_alias"] if res else None,
                    pledged_amount=accounting["pledged"],
                    confirmed_amount=accounting["verified"],
                    remaining_amount=remaining,
                )
            )
        return result


def create_item(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    req: GiftItemCreate,
) -> GiftItemOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)

        reg = repo.get_registry_by_event(conn, event_id)
        if reg is None:
            reg = repo.upsert_registry(
                conn,
                event_id=event_id,
                title=f"{event['title']} Wishlist",
                is_public=False,
                allow_group_gifting=True,
                expires_at=None,
            )

        if req.gift_mode == GiftMode.GROUP:
            if not reg["allow_group_gifting"]:
                raise InvalidRequestError("Group gifting is disabled for this registry.")
            if req.target_amount is None or req.target_amount <= Decimal("0.00"):
                raise InvalidRequestError("Group gifts require a positive target amount.")

        if req.currency != event["currency"]:
            raise InvalidRequestError(
                f"Gift currency '{req.currency}' does not match event currency '{event['currency']}'."
            )

        row = repo.create_item(
            conn,
            registry_id=reg["id"],
            title=req.title.strip(),
            description=req.description.strip() if req.description else None,
            item_type=req.item_type.value,
            gift_mode=req.gift_mode.value,
            product_url=req.product_url.strip() if req.product_url else None,
            target_amount=req.target_amount,
            currency=req.currency,
            priority=req.priority.value,
            display_order=req.display_order,
        )

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="gift_item.created",
            entity_type="gift_items",
            entity_id=row["id"],
            request_id=request_id,
            metadata={"title": row["title"], "gift_mode": row["gift_mode"]},
        )

        return GiftItemOut(
            id=row["id"],
            registry_id=row["registry_id"],
            title=row["title"],
            description=row["description"],
            item_type=GiftItemType(row["item_type"]),
            gift_mode=GiftMode(row["gift_mode"]),
            product_url=row["product_url"],
            target_amount=Decimal(str(row["target_amount"])) if row["target_amount"] is not None else None,
            currency=row["currency"],
            priority=GiftItemPriority(row["priority"]),
            display_order=row["display_order"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            remaining_amount=req.target_amount,
        )


def update_item(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    item_id: uuid.UUID,
    req: GiftItemUpdate,
) -> GiftItemOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)

        reg = repo.get_registry_by_event(conn, event_id)
        if reg is None:
            raise NotFoundError("Registry not found.")

        item = repo.get_item(conn, reg["id"], item_id)
        if item is None:
            raise NotFoundError("Gift item not found.")

        # Mutation rules check
        active_res = repo.get_active_reservation(conn, item_id)
        accounting = repo.get_contribution_accounting(conn, item_id)

        if req.gift_mode is not None and req.gift_mode != item["gift_mode"]:
            if item["gift_mode"] == "individual" and active_res is not None:
                raise ConflictError("Cannot switch to group gifting while an active reservation exists.")
            if item["gift_mode"] == "group" and accounting["total"] > Decimal("0.00"):
                raise ConflictError("Cannot switch to individual gifting while contributions exist.")

        if req.target_amount is not None and req.target_amount < accounting["total"]:
            raise InvalidRequestError(
                f"Target amount cannot be reduced below current contributions (₹{accounting['total']:.2f})."
            )

        if req.currency is not None and req.currency != item["currency"]:
            if accounting["total"] > Decimal("0.00"):
                raise ConflictError("Cannot change currency for an item with existing contributions.")
            if req.currency != event["currency"]:
                raise InvalidRequestError("Gift currency must match celebration currency.")

        row = repo.update_item(
            conn,
            registry_id=reg["id"],
            item_id=item_id,
            title=req.title.strip() if req.title else None,
            description=req.description.strip() if req.description is not None else None,
            item_type=req.item_type.value if req.item_type else None,
            gift_mode=req.gift_mode.value if req.gift_mode else None,
            product_url=req.product_url.strip() if req.product_url is not None else None,
            target_amount=req.target_amount,
            currency=req.currency,
            priority=req.priority.value if req.priority else None,
            display_order=req.display_order,
            is_active=req.is_active,
        )
        assert row is not None

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="gift_item.updated",
            entity_type="gift_items",
            entity_id=item_id,
            request_id=request_id,
            metadata={"title": row["title"]},
        )

        remaining: Decimal | None = None
        if row["target_amount"] is not None:
            remaining = max(Decimal("0.00"), Decimal(str(row["target_amount"])) - accounting["total"])

        return GiftItemOut(
            id=row["id"],
            registry_id=row["registry_id"],
            title=row["title"],
            description=row["description"],
            item_type=GiftItemType(row["item_type"]),
            gift_mode=GiftMode(row["gift_mode"]),
            product_url=row["product_url"],
            target_amount=Decimal(str(row["target_amount"])) if row["target_amount"] is not None else None,
            currency=row["currency"],
            priority=GiftItemPriority(row["priority"]),
            display_order=row["display_order"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            active_reservation_status=GiftReservationStatus(active_res["status"]) if active_res else None,
            active_reservation_alias=active_res["guest_alias"] if active_res else None,
            pledged_amount=accounting["pledged"],
            confirmed_amount=accounting["verified"],
            remaining_amount=remaining,
        )


def deactivate_item(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    item_id: uuid.UUID,
) -> None:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)

        reg = repo.get_registry_by_event(conn, event_id)
        if reg is None:
            raise NotFoundError("Registry not found.")

        ok = repo.deactivate_item(conn, reg["id"], item_id)
        if not ok:
            raise NotFoundError("Gift item not found.")

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="gift_item.deactivated",
            entity_type="gift_items",
            entity_id=item_id,
            request_id=request_id,
            metadata={"status": "deactivated"},
        )


# -------------------------------------------------- Host Reservation & Contribution Operations
def list_reservations(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
) -> list[GiftReservationOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_READ)

        rows = repo.list_reservations_for_event(conn, event_id)
        return [
            GiftReservationOut(
                id=r["id"],
                gift_item_id=r["gift_item_id"],
                gift_item_title=r["gift_item_title"],
                guest_alias=r["guest_alias"],
                status=GiftReservationStatus(r["status"]),
                expires_at=r["expires_at"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]


def update_reservation(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    reservation_id: uuid.UUID,
    req: GiftReservationUpdate,
) -> GiftReservationOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)

        row = repo.update_reservation_status(conn, reservation_id, req.status.value)
        if row is None:
            raise NotFoundError("Reservation not found.")

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="gift_reservation.updated",
            entity_type="gift_reservations",
            entity_id=reservation_id,
            request_id=request_id,
            metadata={"status": req.status.value},
        )

        return GiftReservationOut(
            id=row["id"],
            gift_item_id=row["gift_item_id"],
            guest_alias=row["guest_alias"],
            status=GiftReservationStatus(row["status"]),
            expires_at=row["expires_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def list_contributions(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
) -> list[GiftContributionOut]:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_READ)

        rows = repo.list_contributions_for_event(conn, event_id)
        return [
            GiftContributionOut(
                id=r["id"],
                gift_item_id=r["gift_item_id"],
                gift_item_title=r["gift_item_title"],
                guest_alias=r["guest_alias"],
                amount=Decimal(str(r["amount"])),
                currency=r["currency"],
                status=GiftContributionStatus(r["status"]),
                verification_method=(
                    VerificationMethod(r["verification_method"]) if r["verification_method"] else None
                ),
                verified_at=r["verified_at"],
                verified_by=r["verified_by"],
                confirmation_note=r["confirmation_note"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]


def confirm_contribution(
    db: Database,
    principal: Principal,
    event_id: uuid.UUID,
    contribution_id: uuid.UUID,
    req: HostConfirmationRequest,
) -> GiftContributionOut:
    request_id = request_id_var.get()
    with db.transaction(principal.user_id, request_id) as conn:
        event = events_repo.get_event(conn, event_id)
        if event is None:
            raise NotFoundError("Event not found.")
        _require_active_event(event)
        require_permission(MemberRole(event["my_role"]), Permission.GIFT_REGISTRY_MANAGE)

        contrib = repo.get_contribution(conn, contribution_id)
        if contrib is None or contrib["event_id"] != event_id:
            raise NotFoundError("Contribution not found for this event.")

        if contrib["status"] != "pledged":
            raise ConflictError(f"Contribution is already '{contrib['status']}'.")

        row = repo.verify_contribution(
            conn,
            contribution_id=contribution_id,
            verified_by=principal.user_id,
            confirmation_note=req.confirmation_note.strip() if req.confirmation_note else None,
            verification_method=req.verification_method.value,
        )
        if row is None:
            raise ConflictError("Failed to verify contribution.")

        audit.record(
            conn,
            event_id=event_id,
            actor_user_id=principal.user_id,
            action="gift_contribution.confirmed",
            entity_type="gift_contributions",
            entity_id=contribution_id,
            request_id=request_id,
            metadata={
                "amount": str(row["amount"]),
                "verification_method": req.verification_method.value,
            },
        )

        return GiftContributionOut(
            id=row["id"],
            gift_item_id=row["gift_item_id"],
            guest_alias=row["guest_alias"],
            amount=Decimal(str(row["amount"])),
            currency=row["currency"],
            status=GiftContributionStatus(row["status"]),
            verification_method=VerificationMethod(row["verification_method"]),
            verified_at=row["verified_at"],
            verified_by=row["verified_by"],
            confirmation_note=row["confirmation_note"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


# ------------------------------------------------------------------ Public Guest Registry Experience
def get_public_registry(
    db: Database,
    share_token: str,
) -> PublicRegistryOut:
    request_id = request_id_var.get()
    token_hash = _hash_token(share_token)

    with db.public_transaction(token_hash, request_id) as conn:
        reg = repo.get_public_registry_by_token_hash(conn, token_hash)
        if reg is None:
            raise NotFoundError("Gift registry was not found or link has expired.")

        event = events_repo.get_event(conn, reg["event_id"])
        event_label = event["title"] if event else "Celebration Wishlist"
        currency = event["currency"] if event else DEFAULT_CURRENCY

        items = repo.list_items(conn, reg["id"], include_inactive=False)
        public_items: list[PublicGiftItemOut] = []

        for it in items:
            item_id = it["id"]
            if it["gift_mode"] == "individual":
                res = repo.get_active_reservation(conn, item_id)
                status = "reserved" if res else "available"
                public_items.append(
                    PublicGiftItemOut(
                        id=it["id"],
                        title=it["title"],
                        description=it["description"],
                        item_type=GiftItemType(it["item_type"]),
                        gift_mode=GiftMode(it["gift_mode"]),
                        product_url=it["product_url"],
                        target_amount=(
                            Decimal(str(it["target_amount"])) if it["target_amount"] is not None else None
                        ),
                        currency=it["currency"],
                        priority=GiftItemPriority(it["priority"]),
                        pledged_amount=Decimal("0.00"),
                        confirmed_amount=Decimal("0.00"),
                        remaining_amount=None,
                        status=status,
                    )
                )
            else:
                accounting = repo.get_contribution_accounting(conn, item_id)
                target = (
                    Decimal(str(it["target_amount"])) if it["target_amount"] is not None else Decimal("0.00")
                )
                remaining = max(Decimal("0.00"), target - accounting["total"])
                status = "target_reached" if remaining == Decimal("0.00") else "available"

                public_items.append(
                    PublicGiftItemOut(
                        id=it["id"],
                        title=it["title"],
                        description=it["description"],
                        item_type=GiftItemType(it["item_type"]),
                        gift_mode=GiftMode(it["gift_mode"]),
                        product_url=it["product_url"],
                        target_amount=target if target > Decimal("0.00") else None,
                        currency=it["currency"],
                        priority=GiftItemPriority(it["priority"]),
                        pledged_amount=accounting["pledged"],
                        confirmed_amount=accounting["verified"],
                        remaining_amount=remaining,
                        status=status,
                    )
                )

        return PublicRegistryOut(
            title=reg["title"],
            event_label=event_label,
            items=public_items,
            allow_group_gifting=reg["allow_group_gifting"],
            currency=currency,
        )


def public_reserve_item(
    db: Database,
    share_token: str,
    item_id: uuid.UUID,
    req: PublicReserveRequest,
) -> PublicReservationConfirmationOut:
    request_id = request_id_var.get()
    token_hash = _hash_token(share_token)
    scope = f"reserve:{item_id}"
    req_hash = hashlib.sha256(f"{req.guest_alias or ''}".encode()).hexdigest()

    with db.public_transaction(token_hash, request_id) as conn:
        # 1. Check idempotency record
        existing_rec = repo.get_idempotency_record(conn, scope, req.idempotency_key)
        if existing_rec:
            if existing_rec["request_hash"] != req_hash:
                raise ConflictError("Idempotency key reused with differing parameters.")
            return PublicReservationConfirmationOut(**json.loads(existing_rec["response_body"]))

        # 2. Validate registry
        reg = repo.get_public_registry_by_token_hash(conn, token_hash)
        if reg is None:
            raise NotFoundError("Gift registry was not found or link has expired.")

        # 3. Validate item
        item = repo.get_item(conn, reg["id"], item_id)
        if item is None or not item["is_active"]:
            raise NotFoundError("Gift item is unavailable or inactive.")

        if item["gift_mode"] != "individual":
            raise InvalidRequestError("Only individual gifts can be reserved.")

        # 4. Expire any stale reservation transactionally before checking active reservation
        repo.expire_stale_reservations(conn, item_id)

        # 5. Check if currently active reservation exists
        active_res = repo.get_active_reservation(conn, item_id)
        if active_res:
            raise ConflictError("This gift has already been reserved.")

        # 6. Generate cancellation token
        raw_cancellation = secrets.token_urlsafe(32)
        cancel_hash = _hash_token(raw_cancellation)

        res_row = repo.create_reservation(
            conn,
            gift_item_id=item_id,
            guest_alias=req.guest_alias.strip() if req.guest_alias else None,
            cancellation_token_hash=cancel_hash,
            expires_at=None,
            idempotency_key=req.idempotency_key,
        )

        audit.record(
            conn,
            event_id=reg["event_id"],
            actor_user_id=None,
            actor_type="public_guest",
            action="gift_reservation.created",
            entity_type="gift_reservations",
            entity_id=res_row["id"],
            request_id=request_id,
            metadata={"gift_item_id": str(item_id)},
        )

        response = PublicReservationConfirmationOut(
            reservation_id=res_row["id"],
            gift_item_id=item_id,
            cancellation_token=raw_cancellation,
            message="Your reservation has been recorded! Thank you for coordinating with the couple.",
        )

        # 7. Persist idempotency record
        repo.save_idempotency_record(
            conn,
            scope=scope,
            idempotency_key=req.idempotency_key,
            request_hash=req_hash,
            response_code=201,
            response_body=response.model_dump(mode="json"),
        )

        return response


def public_cancel_reservation(
    db: Database,
    share_token: str,
    reservation_id: uuid.UUID,
    req: PublicCancelReservationRequest,
) -> None:
    request_id = request_id_var.get()
    token_hash = _hash_token(share_token)
    cancel_hash = _hash_token(req.cancellation_token)

    with db.public_transaction(token_hash, request_id) as conn:
        reg = repo.get_public_registry_by_token_hash(conn, token_hash)
        if reg is None:
            raise NotFoundError("Gift registry was not found or link has expired.")

        res = repo.get_reservation_by_cancel_token(conn, cancel_hash)
        if res is None or res["id"] != reservation_id:
            raise NotFoundError("Active reservation not found or invalid cancellation token.")

        if res["status"] != "reserved":
            raise ConflictError("Reservation is no longer active or cannot be cancelled.")

        repo.update_reservation_status(conn, reservation_id, "cancelled")

        audit.record(
            conn,
            event_id=reg["event_id"],
            actor_user_id=None,
            actor_type="public_guest",
            action="gift_reservation.cancelled",
            entity_type="gift_reservations",
            entity_id=reservation_id,
            request_id=request_id,
            metadata={"gift_item_id": str(res["gift_item_id"])},
        )


def public_contribute_item(
    db: Database,
    share_token: str,
    item_id: uuid.UUID,
    req: PublicContributionRequest,
) -> PublicContributionConfirmationOut:
    request_id = request_id_var.get()
    token_hash = _hash_token(share_token)
    scope = f"pledge:{item_id}"
    raw_payload = f"{req.guest_alias or ''}:{req.amount}:{req.currency}"
    req_hash = hashlib.sha256(raw_payload.encode()).hexdigest()

    with db.public_transaction(token_hash, request_id) as conn:
        # 1. Idempotency check
        existing_rec = repo.get_idempotency_record(conn, scope, req.idempotency_key)
        if existing_rec:
            if existing_rec["request_hash"] != req_hash:
                raise ConflictError("Idempotency key reused with differing parameters.")
            return PublicContributionConfirmationOut(**json.loads(existing_rec["response_body"]))

        # 2. Validate registry
        reg = repo.get_public_registry_by_token_hash(conn, token_hash)
        if reg is None:
            raise NotFoundError("Gift registry was not found or link has expired.")

        if not reg["allow_group_gifting"]:
            raise InvalidRequestError("Group gifting is not enabled for this registry.")

        # 3. Lock item row for update to serialize concurrent pledges
        item = repo.lock_item_for_update(conn, item_id)
        if item is None or not item["is_active"]:
            raise NotFoundError("Gift item is unavailable or inactive.")

        if item["gift_mode"] != "group":
            raise InvalidRequestError("Contributions are only accepted for group gifts.")

        if req.currency != item["currency"]:
            raise InvalidRequestError(f"Pledge currency must match gift currency '{item['currency']}'.")

        target = Decimal(str(item["target_amount"])) if item["target_amount"] is not None else Decimal("0.00")
        accounting = repo.get_contribution_accounting(conn, item_id)
        remaining = max(Decimal("0.00"), target - accounting["total"])

        if req.amount > remaining:
            raise ConflictError(
                f"Your pledge of ₹{req.amount:.2f} exceeds the remaining target capacity of ₹{remaining:.2f}."
            )

        contrib = repo.create_contribution(
            conn,
            gift_item_id=item_id,
            guest_alias=req.guest_alias.strip() if req.guest_alias else None,
            amount=req.amount,
            currency=req.currency,
            idempotency_key=req.idempotency_key,
        )

        audit.record(
            conn,
            event_id=reg["event_id"],
            actor_user_id=None,
            actor_type="public_guest",
            action="gift_contribution.pledged",
            entity_type="gift_contributions",
            entity_id=contrib["id"],
            request_id=request_id,
            metadata={"amount": str(req.amount), "gift_item_id": str(item_id)},
        )

        response = PublicContributionConfirmationOut(
            contribution_id=contrib["id"],
            gift_item_id=item_id,
            amount=req.amount,
            currency=req.currency,
            message="Your contribution pledge has been recorded. UtsavAI has not collected any money.",
        )

        repo.save_idempotency_record(
            conn,
            scope=scope,
            idempotency_key=req.idempotency_key,
            request_hash=req_hash,
            response_code=201,
            response_body=response.model_dump(mode="json"),
        )

        return response


# ------------------------------------------------------------------ Shared Event Context Integration
def get_event_gift_summary(
    conn: Any,
    event_id: uuid.UUID,
) -> ContextGiftSummary:
    reg = repo.get_registry_by_event(conn, event_id)
    if reg is None:
        return ContextGiftSummary(registry_exists=False)

    metrics = repo.get_registry_metrics(conn, reg["id"])
    return ContextGiftSummary(
        registry_exists=True,
        is_public=reg["is_public"] and reg["revoked_at"] is None,
        total_items=metrics["total_items"],
        available_items=metrics["available_items"],
        reserved_items=metrics["reserved_items"],
        group_gift_items=metrics["group_gift_items"],
        active_group_pledges=metrics["total_pledged_amount"],
        host_confirmed_amount=metrics["total_confirmed_amount"],
        currency=DEFAULT_CURRENCY,
    )
