from __future__ import annotations

import os
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.core.security import TokenVerifier
from app.database.pool import Database
from app.main import create_app
from tests.conftest import RUNTIME_URL_DEFAULT, build_settings

ADMIN_URL = os.environ.get(
    "TEST_DATABASE_ADMIN_URL", "postgresql://postgres:pgadmin_local@localhost:5432/utsavai_test"
)


def _admin_available() -> bool:
    try:
        with psycopg.connect(ADMIN_URL, connect_timeout=3):
            return True
    except psycopg.Error:
        return False


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session", autouse=True)
def _require_database() -> None:
    if not _admin_available():
        if os.environ.get("CI"):
            pytest.fail("PostgreSQL is required in CI (TEST_DATABASE_ADMIN_URL)")
        pytest.skip("No PostgreSQL available: set TEST_DATABASE_ADMIN_URL / TEST_DATABASE_URL")


@pytest.fixture
def admin() -> Iterator[psycopg.Connection]:
    """Superuser connection used ONLY by tests to seed auth.users and inspect state."""
    with psycopg.connect(ADMIN_URL, autocommit=True) as conn:
        conn.execute(
            "truncate public.audit_logs, public.event_members, public.events, public.profiles cascade"
        )
        conn.execute("delete from auth.users")
        yield conn


@dataclass
class TestUser:
    __test__ = False
    id: uuid.UUID
    token: str

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


@pytest.fixture
def make_user(admin: psycopg.Connection, make_token: Callable[..., str]) -> Callable[[str], TestUser]:
    def _make(label: str = "user") -> TestUser:
        user_id = uuid.uuid4()
        admin.execute(
            "insert into auth.users (id, email) values (%s, %s)",
            (user_id, f"{label}-{user_id.hex[:8]}@example.test"),
        )
        return TestUser(user_id, make_token(user_id, email=f"{label}@example.test"))

    return _make


@pytest.fixture
def db_settings():
    return build_settings(
        database_url=os.environ.get("TEST_DATABASE_URL", RUNTIME_URL_DEFAULT),
        db_pool_min_size=1,
        db_pool_max_size=1,  # one shared connection makes identity leakage observable
    )


@pytest.fixture
def database(db_settings) -> Iterator[Database]:  # type: ignore[no-untyped-def]
    db = Database(db_settings)
    db.open()
    yield db
    db.close()


@pytest.fixture
def client(db_settings, verifier: TokenVerifier) -> Iterator[TestClient]:  # type: ignore[no-untyped-def]
    app = create_app(db_settings, verifier=verifier)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def event_payload(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "event_type": "wedding",
        "title": "Synthetic Test Wedding",
        "start_at": "2027-02-12T10:00:00+05:30",
        "end_at": "2027-02-14T22:00:00+05:30",
        "timezone": "Asia/Kolkata",
        "location": {
            "name": "Test Venue",
            "city": "Jaipur",
            "region": "Rajasthan",
            "country_code": "IN",
        },
        "expected_guest_count": 300,
        "currency": "INR",
    }
    body.update(overrides)
    return body
