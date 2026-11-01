import pytest
from pydantic import ValidationError

from app.core.config import Settings

BASE = {
    "database_url": "postgresql://utsavai_app:x@db.internal:5432/app",
    "supabase_url": "https://abc.supabase.co",
}


def make(**kw):
    return Settings(_env_file=None, **{**BASE, **kw})


def test_derives_issuer_and_jwks_from_supabase_url():
    s = make()
    assert s.supabase_jwt_issuer == "https://abc.supabase.co/auth/v1"
    assert s.supabase_jwks_url == "https://abc.supabase.co/auth/v1/.well-known/jwks.json"
    assert s.supabase_jwt_audience == "authenticated"


def test_missing_database_url_fails_clearly():
    with pytest.raises(ValidationError, match="DATABASE_URL is required"):
        Settings(_env_file=None, supabase_url="https://abc.supabase.co")


def test_missing_supabase_url_fails_clearly():
    with pytest.raises(ValidationError, match="SUPABASE_URL is required"):
        Settings(_env_file=None, database_url=BASE["database_url"])


@pytest.mark.parametrize("user", ["postgres", "postgres.projectref", "supabase_admin", "service_role"])
def test_privileged_database_users_are_rejected(user):
    with pytest.raises(ValidationError, match="dedicated runtime role"):
        make(database_url=f"postgresql://{user}:x@db.internal:5432/app")


def test_wildcard_cors_rejected():
    with pytest.raises(ValidationError, match="explicit origins"):
        make(cors_allowed_origins="*")


def test_production_requires_https_cors_and_ssl():
    with pytest.raises(ValidationError) as exc:
        make(app_env="production", cors_allowed_origins="http://example.com")
    text = str(exc.value)
    assert "https" in text and "sslmode" in text


def test_production_valid_configuration_and_docs_disabled():
    s = make(
        app_env="production",
        database_url="postgresql://utsavai_app:x@db.internal:5432/app?sslmode=require",
        cors_allowed_origins="https://app.example.com/",
    )
    assert s.cors_origins_list == ["https://app.example.com"]
    assert s.docs_enabled is False and s.is_production


def test_pool_bounds_validated():
    with pytest.raises(ValidationError, match="DB_POOL_MIN_SIZE"):
        make(db_pool_min_size=5, db_pool_max_size=2)
