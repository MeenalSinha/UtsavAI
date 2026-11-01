"""Integration tests for Phase 5: GiftCircle module."""

from __future__ import annotations

import uuid
from decimal import Decimal

from tests.integration.conftest import event_payload

BASE = "/api/v1"


def test_giftcircle_full_lifecycle(client, make_user):
    host = make_user("host")
    other = make_user("other")

    # 1. Create celebration event
    res = client.post(f"{BASE}/events", json=event_payload(), headers=host.headers)
    assert res.status_code == 201
    event_id = res.json()["id"]

    # 2. Host creates registry
    reg_res = client.post(
        f"{BASE}/events/{event_id}/gift-registry",
        json={
            "title": "Aarav & Meera Wedding Wishlist",
            "welcome_message": "Thank you for celebrating with us!",
            "delivery_address": "123 Heritage Lane, Jaipur",
            "allow_group_gifting": True,
        },
        headers=host.headers,
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["title"] == "Aarav & Meera Wedding Wishlist"
    assert reg_data["allow_group_gifting"] is True

    # 3. Non-member cannot access private host registry
    forbidden_res = client.get(f"{BASE}/events/{event_id}/gift-registry", headers=other.headers)
    assert forbidden_res.status_code == 404

    # 4. Generate share link
    link_res = client.post(
        f"{BASE}/events/{event_id}/gift-registry/share-link",
        headers=host.headers,
    )
    assert link_res.status_code == 201
    share_token = link_res.json()["share_token"]
    assert len(share_token) > 20

    # 5. Add Individual Gift Item
    item1_res = client.post(
        f"{BASE}/events/{event_id}/gift-registry/items",
        json={
            "name": "Espresso Machine",
            "description": "Compact dual-boiler coffee maker",
            "item_type": "physical",
            "gift_mode": "individual",
            "target_amount": 45000.0,
            "currency": "INR",
            "priority": "high",
        },
        headers=host.headers,
    )
    assert item1_res.status_code == 201
    item1 = item1_res.json()
    assert item1["gift_mode"] == "individual"
    item1_id = item1["id"]

    # 6. Add Group Gift Item
    item2_res = client.post(
        f"{BASE}/events/{event_id}/gift-registry/items",
        json={
            "name": "Udaipur Honeymoon Stay",
            "description": "3 nights at Lake Palace",
            "item_type": "experience",
            "gift_mode": "group",
            "target_amount": 100000.0,
            "currency": "INR",
            "priority": "high",
        },
        headers=host.headers,
    )
    assert item2_res.status_code == 201
    item2 = item2_res.json()
    assert item2["gift_mode"] == "group"
    item2_id = item2["id"]

    # 7. Public guest reads registry (no auth headers!)
    public_res = client.get(f"{BASE}/public/registries/{share_token}")
    assert public_res.status_code == 200
    pub_data = public_res.json()
    assert pub_data["registry_title"] == "Aarav & Meera Wedding Wishlist"
    assert pub_data["delivery_address"] == "123 Heritage Lane, Jaipur"
    assert len(pub_data["items"]) == 2

    # 8. Public guest reserves individual gift
    idempotency_key_1 = str(uuid.uuid4())
    reserve_res = client.post(
        f"{BASE}/public/registries/{share_token}/items/{item1_id}/reserve",
        json={
            "idempotency_key": idempotency_key_1,
            "guest_alias": "Sunil Uncle",
            "notes": "Looking forward to celebrating!",
        },
    )
    assert reserve_res.status_code == 201
    reserve_data = reserve_res.json()
    res_id = reserve_data["reservation_id"]
    cancel_token = reserve_data["cancellation_token"]

    # Verify item is no longer available to other guests
    pub_check = client.get(f"{BASE}/public/registries/{share_token}")
    item1_pub = next(it for it in pub_check.json()["items"] if it["id"] == item1_id)
    assert item1_pub["is_available"] is False
    assert item1_pub["reservation_status"] == "reserved"

    # 9. Duplicate reservation attempt fails
    dup_reserve = client.post(
        f"{BASE}/public/registries/{share_token}/items/{item1_id}/reserve",
        json={
            "idempotency_key": str(uuid.uuid4()),
            "guest_alias": "Other Guest",
        },
    )
    assert dup_reserve.status_code == 409

    # 10. Public guest cancels reservation using cancellation token
    cancel_res = client.post(
        f"{BASE}/public/registries/{share_token}/reservations/{res_id}/cancel",
        json={"cancellation_token": cancel_token},
    )
    assert cancel_res.status_code == 204

    # Verify item is available again
    pub_check2 = client.get(f"{BASE}/public/registries/{share_token}")
    item1_pub2 = next(it for it in pub_check2.json()["items"] if it["id"] == item1_id)
    assert item1_pub2["is_available"] is True
    assert item1_pub2["reservation_status"] is None

    # 11. Public guest contributes to group gift
    pledge_key = str(uuid.uuid4())
    pledge_res = client.post(
        f"{BASE}/public/registries/{share_token}/items/{item2_id}/contribute",
        json={
            "idempotency_key": pledge_key,
            "guest_alias": "Priya & Friends",
            "amount": 40000.0,
            "currency": "INR",
        },
    )
    assert pledge_res.status_code == 201
    pledge_data = pledge_res.json()
    contrib_id = pledge_data["contribution_id"]
    assert Decimal(pledge_data["amount"]) == Decimal("40000.00")

    # Idempotent re-submission returns cached response
    pledge_replay = client.post(
        f"{BASE}/public/registries/{share_token}/items/{item2_id}/contribute",
        json={
            "idempotency_key": pledge_key,
            "guest_alias": "Priya & Friends",
            "amount": 40000.0,
            "currency": "INR",
        },
    )
    assert pledge_replay.status_code == 201
    assert pledge_replay.json()["contribution_id"] == contrib_id

    # 12. Attempt to pledge beyond remaining target fails (Remaining is 60,000)
    over_pledge = client.post(
        f"{BASE}/public/registries/{share_token}/items/{item2_id}/contribute",
        json={
            "idempotency_key": str(uuid.uuid4()),
            "guest_alias": "Generous Donor",
            "amount": 70000.0,
            "currency": "INR",
        },
    )
    assert over_pledge.status_code == 409

    # 13. Host views contributions and verifies offline receipt
    contribs_res = client.get(
        f"{BASE}/events/{event_id}/gift-registry/contributions",
        headers=host.headers,
    )
    assert contribs_res.status_code == 200
    contribs = contribs_res.json()
    assert len(contribs) == 1
    assert contribs[0]["status"] == "pledged"

    verify_res = client.post(
        f"{BASE}/events/{event_id}/gift-registry/contributions/{contrib_id}/verify",
        json={
            "verification_method": "offline_cash",
            "verification_notes": "Received cash envelope at wedding reception",
        },
        headers=host.headers,
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["status"] == "verified"

    # 14. Host overview shows accurate totals
    overview_res = client.get(
        f"{BASE}/events/{event_id}/gift-registry/overview",
        headers=host.headers,
    )
    assert overview_res.status_code == 200
    ov = overview_res.json()
    assert ov["total_items"] == 2
    assert Decimal(ov["total_verified"]) == Decimal("40000.00")
    assert Decimal(ov["total_pledged"]) == Decimal("0.00")

    # 15. Shared event context includes gift summary
    ctx_res = client.get(f"{BASE}/events/{event_id}/context", headers=host.headers)
    assert ctx_res.status_code == 200
    gift_sum = ctx_res.json()["gift_summary"]
    assert gift_sum is not None
    assert gift_sum["total_items"] == 2
    assert Decimal(gift_sum["total_contributed"]) == Decimal("40000.00")

    # 16. Revoke share link
    revoke_res = client.delete(
        f"{BASE}/events/{event_id}/gift-registry/share-link",
        headers=host.headers,
    )
    assert revoke_res.status_code == 204

    # Public access with old token returns 404
    expired_res = client.get(f"{BASE}/public/registries/{share_token}")
    assert expired_res.status_code == 404
