from fastapi import APIRouter

from app.api.v1 import events, health, me, meta

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(meta.router)
api_router.include_router(me.router)
api_router.include_router(events.router)
