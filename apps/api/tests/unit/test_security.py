import time
import uuid

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.core.errors import UnauthenticatedError
from app.core.security import StaticKeyResolver, TokenVerifier
from tests.conftest import AUDIENCE, ISSUER


def test_valid_token_yields_principal(make_token, verifier):
    uid = uuid.uuid4()
    principal = verifier.verify(
        make_token(uid, email="a@example.test", user_metadata={"full_name": "Asha Test"})
    )
    assert principal.user_id == uid
    assert principal.email == "a@example.test"
    assert principal.display_name_hint == "Asha Test"


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": int(time.time()) - 60},
        {"aud": "someone-else"},
        {"iss": "https://evil.example/auth/v1"},
        {"sub": "not-a-uuid"},
        {"role": "anon"},
        {"sub": None},
        {"exp": None},
    ],
)
def test_invalid_claims_rejected(make_token, verifier, overrides):
    with pytest.raises(UnauthenticatedError):
        verifier.verify(make_token(**overrides))


def test_wrong_signing_key_rejected(verifier):
    other = ec.generate_private_key(ec.SECP256R1())
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + 60,
            "role": "authenticated",
        },
        other,
        algorithm="ES256",
    )
    with pytest.raises(UnauthenticatedError):
        verifier.verify(token)


def test_alg_none_rejected(verifier):
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + 60,
            "role": "authenticated",
        },
        key=None,  # type: ignore[arg-type]
        algorithm="none",
    )
    with pytest.raises(UnauthenticatedError):
        verifier.verify(token)


def test_hs256_token_signed_with_public_key_is_rejected(signing_key, verifier):
    """Classic algorithm-confusion attack: HS256 using the public key material as secret."""
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + 60,
            "role": "authenticated",
        },
        "public-key-as-secret-0123456789abcdef",
        algorithm="HS256",
    )
    with pytest.raises(UnauthenticatedError):
        verifier.verify(token)


def test_garbage_token_rejected(verifier):
    with pytest.raises(UnauthenticatedError):
        verifier.verify("not.a.jwt")


def test_shared_secret_verifier_for_legacy_projects():
    secret = "x" * 48
    v = TokenVerifier(
        resolver=StaticKeyResolver(secret, ("HS256",)), issuer=ISSUER, audience=AUDIENCE, leeway=0
    )
    now = int(time.time())
    uid = uuid.uuid4()
    token = jwt.encode(
        {
            "sub": str(uid),
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + 60,
            "role": "authenticated",
        },
        secret,
        algorithm="HS256",
    )
    assert v.verify(token).user_id == uid
