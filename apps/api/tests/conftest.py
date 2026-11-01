from __future__ import annotations

import os
import time
import uuid
from collections.abc import Callable, Iterator
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.security import StaticKeyResolver, TokenVerifier
from app.main import create_app

ISSUER = "https://test-project.supabase.co/auth/v1"
AUDIENCE = "authenticated"
RUNTIME_URL_DEFAULT = "postgresql://utsavai_app:utsavai_local_only@localhost:5432/utsavai_test"


@pytest.fixture(scope="session")
def signing_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="session")
def make_token(signing_key: ec.EllipticCurvePrivateKey) -> Callable[..., str]:
    def _make(user_id: uuid.UUID | str | None = None, **overrides: Any) -> str:
        now = int(time.time())
        claims: dict[str, Any] = {
            "sub": str(user_id or uuid.uuid4()),
            "iss": ISSUER,
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + 3600,
            "role": "authenticated",
            "email": "synthetic@example.test",
        }
        claims.update(overrides)
        claims = {k: v for k, v in claims.items() if v is not None}
        return jwt.encode(claims, signing_key, algorithm="ES256", headers={"kid": "test-key"})

    return _make


@pytest.fixture(scope="session")
def verifier(signing_key: ec.EllipticCurvePrivateKey) -> TokenVerifier:
    return TokenVerifier(
        resolver=StaticKeyResolver(signing_key.public_key(), ("ES256",)),
        issuer=ISSUER,
        audience=AUDIENCE,
        leeway=0,
    )


def build_settings(**overrides: Any) -> Settings:
    values: dict[str, Any] = {
        "app_env": "test",
        "database_url": os.environ.get("TEST_DATABASE_URL", RUNTIME_URL_DEFAULT),
        "supabase_url": "https://test-project.supabase.co",
        "log_json": False,
        "log_level": "WARNING",
        "cors_allowed_origins": "http://localhost:3000",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def settings() -> Settings:
    return build_settings()


class _OfflineDatabase:
    """Stub database for offline tests that validates no SQL is executed."""

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    def verify_runtime_role(self) -> None:
        pass


@pytest.fixture
def offline_client(settings: Settings, verifier: TokenVerifier) -> Iterator[TestClient]:
    """App without a running database: for auth/validation paths that never reach SQL."""
    app = create_app(settings, database=_OfflineDatabase(), verifier=verifier)  # type: ignore[arg-type]
    yield TestClient(app, raise_server_exceptions=False)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
