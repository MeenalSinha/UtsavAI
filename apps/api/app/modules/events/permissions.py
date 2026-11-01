from __future__ import annotations

from app.core.domain import MemberRole, Permission, role_allows
from app.core.errors import ForbiddenError


def require_permission(role: MemberRole, permission: Permission) -> None:
    if not role_allows(role, permission):
        raise ForbiddenError("You do not have permission to perform this action.")
