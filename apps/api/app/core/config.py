"""Typed, validated settings. Loaded once at startup; fails loudly when invalid."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlparse

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_PRIVILEGED_DB_USERS = {"postgres", "supabase_admin", "service_role", "supabase_auth_admin"}


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or unsafe."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_ignore_empty=True,
    )

    # Application
    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "utsavai-api"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = True
    enable_docs: bool | None = None  # default: on outside production
    max_request_body_bytes: int = Field(default=64 * 1024, ge=1024, le=5 * 1024 * 1024)

    # Database: runtime role only (NOBYPASSRLS). Never a superuser or service-role key.
    database_url: SecretStr = Field(default=SecretStr(""))
    db_pool_min_size: int = Field(default=1, ge=1)
    db_pool_max_size: int = Field(default=10, ge=1)
    db_pool_timeout_seconds: float = Field(default=10.0, gt=0)
    db_statement_timeout_ms: int = Field(default=15_000, ge=100)

    # Supabase Auth / JWT verification
    supabase_url: str = ""
    supabase_jwt_issuer: str = ""  # default: <supabase_url>/auth/v1
    supabase_jwt_audience: str = "authenticated"
    supabase_jwks_url: str = ""  # default: <issuer>/.well-known/jwks.json
    # Legacy projects that still sign with a shared HS256 secret. Optional.
    supabase_jwt_secret: SecretStr = Field(default=SecretStr(""))
    jwt_leeway_seconds: int = Field(default=10, ge=0, le=120)
    jwks_cache_seconds: int = Field(default=600, ge=30)

    # CORS (explicit origins only, never "*")
    cors_allowed_origins: str = ""

    # AI / Gemini (Phase 2)
    gemini_api_key: SecretStr = Field(default=SecretStr(""))
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = Field(default=30.0, gt=0)
    gemini_max_output_tokens: int = Field(default=4096, ge=256, le=16384)
    gemini_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    gemini_retries: int = Field(default=2, ge=0, le=5)
    ai_feature_enabled: bool = True
    ai_rate_limit_per_minute: int = Field(default=30, ge=1)

    def _validate_database_config(self, errors: list[str]) -> None:
        if not self.database_url.get_secret_value():
            errors.append("DATABASE_URL is required (runtime role connection string)")
        else:
            parsed = urlparse(self.database_url.get_secret_value())
            if parsed.scheme not in {"postgresql", "postgres"}:
                errors.append("DATABASE_URL must be a postgresql:// URL")
            user = (parsed.username or "").split(".")[0].lower()
            if user in _PRIVILEGED_DB_USERS:
                errors.append(
                    "DATABASE_URL must use the dedicated runtime role (utsavai_app), "
                    "not a privileged database user"
                )

        if self.db_pool_min_size > self.db_pool_max_size:
            errors.append("DB_POOL_MIN_SIZE must be <= DB_POOL_MAX_SIZE")

    def _validate_supabase_config(self, errors: list[str]) -> None:
        if not self.supabase_url:
            errors.append("SUPABASE_URL is required")
        else:
            base = self.supabase_url.rstrip("/")
            if not self.supabase_jwt_issuer:
                self.supabase_jwt_issuer = f"{base}/auth/v1"
            if not self.supabase_jwks_url:
                self.supabase_jwks_url = f"{self.supabase_jwt_issuer}/.well-known/jwks.json"

    def _validate_production_and_cors(self, errors: list[str]) -> None:
        if self.cors_origins_list and "*" in self.cors_origins_list:
            errors.append("CORS_ALLOWED_ORIGINS must list explicit origins, not '*'")

        if self.app_env == "production":
            if not self.supabase_url.startswith("https://"):
                errors.append("SUPABASE_URL must use https in production")
            if not self.cors_origins_list:
                errors.append("CORS_ALLOWED_ORIGINS is required in production")
            if any(not o.startswith("https://") for o in self.cors_origins_list):
                errors.append("CORS_ALLOWED_ORIGINS must be https in production")
            db_url = self.database_url.get_secret_value()
            if db_url and "sslmode=" not in db_url:
                errors.append("DATABASE_URL must set sslmode=require (or verify-full) in production")

    @model_validator(mode="after")
    def _derive_and_validate(self) -> Self:
        errors: list[str] = []
        self._validate_database_config(errors)
        self._validate_supabase_config(errors)
        self._validate_production_and_cors(errors)

        if errors:
            raise ValueError("; ".join(errors))
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_allowed_origins.split(",") if o.strip()]

    @property
    def docs_enabled(self) -> bool:
        return self.enable_docs if self.enable_docs is not None else self.app_env != "production"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except ValueError as exc:  # pydantic ValidationError subclasses ValueError
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc
