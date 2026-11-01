"""Supabase JWT verification. Nothing here trusts unverified claims."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient

from app.core.config import Settings
from app.core.errors import DependencyUnavailableError, UnauthenticatedError

logger = logging.getLogger(__name__)

ASYMMETRIC_ALGORITHMS = ("ES256", "RS256", "EdDSA")
SYMMETRIC_ALGORITHMS = ("HS256",)


@dataclass(frozen=True, slots=True)
class Principal:
    """The authenticated caller, derived exclusively from verified JWT claims."""

    user_id: uuid.UUID
    email: str | None
    display_name_hint: str | None


class KeyResolver(Protocol):
    algorithms: tuple[str, ...]

    def resolve(self, token: str) -> Any: ...


class JWKSKeyResolver:
    """Fetches and caches Supabase signing keys; re-fetches on unknown `kid` (rotation)."""

    algorithms: tuple[str, ...] = ASYMMETRIC_ALGORITHMS

    def __init__(self, jwks_url: str, cache_seconds: int) -> None:
        self._client = PyJWKClient(
            jwks_url, cache_keys=True, lifespan=cache_seconds, timeout=5, cache_jwk_set=True
        )

    def resolve(self, token: str) -> Any:
        try:
            return self._client.get_signing_key_from_jwt(token).key
        except jwt.exceptions.PyJWKClientConnectionError as exc:
            logger.error("jwks_unavailable")
            raise DependencyUnavailableError("Identity provider keys are unavailable.") from exc
        except jwt.exceptions.PyJWKClientError as exc:
            raise UnauthenticatedError("Invalid access token.") from exc


class SharedSecretResolver:
    algorithms: tuple[str, ...] = SYMMETRIC_ALGORITHMS

    def __init__(self, secret: str) -> None:
        self._secret = secret

    def resolve(self, token: str) -> Any:  # noqa: ARG002
        return self._secret


class StaticKeyResolver:
    """Fixed public key. Used by tests and by deployments that pin a key."""

    def __init__(self, key: Any, algorithms: tuple[str, ...]) -> None:
        self._key = key
        self.algorithms = algorithms

    def resolve(self, token: str) -> Any:  # noqa: ARG002
        return self._key


class TokenVerifier:
    def __init__(self, *, resolver: KeyResolver, issuer: str, audience: str, leeway: int) -> None:
        self._resolver = resolver
        self._issuer = issuer
        self._audience = audience
        self._leeway = leeway

    def verify(self, token: str) -> Principal:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.exceptions.DecodeError as exc:
            raise UnauthenticatedError("Invalid access token.") from exc
        # The algorithm comes from our allow-list, never from the token ("alg" confusion).
        if header.get("alg") not in self._resolver.algorithms:
            raise UnauthenticatedError("Invalid access token.")

        key = self._resolver.resolve(token)
        try:
            claims = jwt.decode(
                token,
                key=key,
                algorithms=list(self._resolver.algorithms),
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._leeway,
                options={"require": ["exp", "iat", "sub", "iss", "aud"], "verify_signature": True},
            )
        except jwt.ExpiredSignatureError as exc:
            raise UnauthenticatedError("The access token has expired.") from exc
        except jwt.InvalidTokenError as exc:
            raise UnauthenticatedError("Invalid access token.") from exc

        if claims.get("role") != "authenticated":
            raise UnauthenticatedError("Invalid access token.")
        try:
            user_id = uuid.UUID(str(claims["sub"]))
        except ValueError as exc:
            raise UnauthenticatedError("Invalid access token.") from exc

        meta = claims.get("user_metadata")
        hint = None
        if isinstance(meta, dict):
            raw = meta.get("display_name") or meta.get("full_name") or meta.get("name")
            if isinstance(raw, str) and raw.strip():
                hint = raw.strip()[:80]
        email = claims.get("email")
        return Principal(
            user_id=user_id,
            email=email if isinstance(email, str) else None,
            display_name_hint=hint,
        )


def build_token_verifier(settings: Settings) -> TokenVerifier:
    secret = settings.supabase_jwt_secret.get_secret_value()
    resolver: KeyResolver
    if secret and not settings.supabase_jwks_url:
        resolver = SharedSecretResolver(secret)
    else:
        resolver = JWKSKeyResolver(settings.supabase_jwks_url, settings.jwks_cache_seconds)
    return TokenVerifier(
        resolver=resolver,
        issuer=settings.supabase_jwt_issuer,
        audience=settings.supabase_jwt_audience,
        leeway=settings.jwt_leeway_seconds,
    )
