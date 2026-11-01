import hashlib
import secrets
from decimal import Decimal

from app.modules.gifts.service import _hash_token


def test_token_generation_and_hashing():
    raw_token = secrets.token_urlsafe(32)
    assert len(raw_token) > 30
    token_hash = _hash_token(raw_token)

    # Hash should be 64 characters hex
    assert len(token_hash) == 64
    assert token_hash != raw_token
    # Hashing should be deterministic
    assert _hash_token(raw_token) == token_hash

    expected_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    assert token_hash == expected_hash


def test_group_gifting_remaining_capacity():
    target = Decimal("100000.00")
    pledged = Decimal("40000.00")
    verified = Decimal("25000.00")
    total_contributed = pledged + verified

    remaining = max(Decimal("0.00"), target - total_contributed)
    assert remaining == Decimal("35000.00")

    # If new pledge is within capacity
    new_pledge = Decimal("30000.00")
    assert new_pledge <= remaining

    # If new pledge exceeds capacity
    excess_pledge = Decimal("40000.00")
    assert excess_pledge > remaining


def test_capacity_floor_at_zero():
    target = Decimal("50000.00")
    total_contributed = Decimal("60000.00")
    remaining = max(Decimal("0.00"), target - total_contributed)
    assert remaining == Decimal("0.00")


def test_idempotency_payload_hashing():
    alias1 = "Sunil Uncle"
    amount1 = Decimal("10000.00")
    currency1 = "INR"

    raw_payload_1 = f"{alias1}:{amount1}:{currency1}"
    hash_1 = hashlib.sha256(raw_payload_1.encode()).hexdigest()

    # Identical parameters produce identical hash
    assert hashlib.sha256(raw_payload_1.encode()).hexdigest() == hash_1

    # Differing parameters produce differing hash
    raw_payload_2 = f"{alias1}:{Decimal('15000.00')}:{currency1}"
    hash_2 = hashlib.sha256(raw_payload_2.encode()).hexdigest()
    assert hash_1 != hash_2
