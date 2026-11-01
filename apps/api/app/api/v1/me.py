from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import IdentityServiceDep, PrincipalDep, RequestIdDep
from app.modules.identity.schemas import ProfileOut, ProfileUpdate
from app.schemas.common import ErrorEnvelope

router = APIRouter(prefix="/me", tags=["identity"], responses={401: {"model": ErrorEnvelope}})


@router.get("", response_model=ProfileOut, summary="Current user's profile")
def get_me(principal: PrincipalDep, service: IdentityServiceDep, request_id: RequestIdDep) -> ProfileOut:
    return service.get_me(principal, request_id)


@router.patch(
    "",
    response_model=ProfileOut,
    summary="Update display name, locale or time zone",
    responses={422: {"model": ErrorEnvelope}},
)
def patch_me(
    payload: ProfileUpdate,
    principal: PrincipalDep,
    service: IdentityServiceDep,
    request_id: RequestIdDep,
) -> ProfileOut:
    return service.update_me(principal, payload, request_id)
