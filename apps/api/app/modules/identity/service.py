from __future__ import annotations

from app.core.security import Principal
from app.database.pool import Database
from app.modules.identity import repository
from app.modules.identity.schemas import ProfileOut, ProfileUpdate


class IdentityService:
    def __init__(self, db: Database) -> None:
        self._db = db

    def get_me(self, principal: Principal, request_id: str) -> ProfileOut:
        with self._db.transaction(principal.user_id, request_id) as conn:
            row = repository.ensure_profile(conn, principal.user_id, principal.display_name_hint)
        return self._to_out(row, principal)

    def update_me(self, principal: Principal, payload: ProfileUpdate, request_id: str) -> ProfileOut:
        fields = {name: getattr(payload, name) for name in payload.model_fields_set}
        with self._db.transaction(principal.user_id, request_id) as conn:
            repository.ensure_profile(conn, principal.user_id, principal.display_name_hint)
            row = repository.update_profile(conn, principal.user_id, fields)
        return self._to_out(row, principal)

    @staticmethod
    def _to_out(row: dict[str, object], principal: Principal) -> ProfileOut:
        return ProfileOut(
            user_id=str(row["user_id"]),
            display_name=row["display_name"],
            preferred_locale=str(row["preferred_locale"]),
            timezone=row["timezone"],
            email=principal.email,
        )
