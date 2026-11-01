from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app.api.deps import DatabaseDep

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


class HealthOut(BaseModel):
    status: Literal["ok"]
    service: str
    version: str


class ReadinessOut(BaseModel):
    status: Literal["ready", "unavailable"]
    database: Literal["ok", "unavailable"]


@router.get("/health", response_model=HealthOut, summary="Liveness and version")
def health(request: Request) -> HealthOut:
    settings = request.app.state.settings
    return HealthOut(status="ok", service=settings.app_name, version=settings.app_version)


@router.get(
    "/health/ready",
    response_model=ReadinessOut,
    responses={503: {"model": ReadinessOut}},
    summary="Readiness (verifies the database connection and runtime role)",
)
def ready(db: DatabaseDep, response: Response) -> ReadinessOut:
    try:
        db.verify_runtime_role()  # real round trip plus least-privilege check
    except Exception:
        logger.warning("readiness_failed")
        response.status_code = 503
        return ReadinessOut(status="unavailable", database="unavailable")
    return ReadinessOut(status="ready", database="ok")
