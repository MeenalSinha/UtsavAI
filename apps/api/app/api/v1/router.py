from fastapi import APIRouter

from app.api.v1 import (
    ai,
    budget,
    context,
    events,
    functions,
    health,
    me,
    meta,
    preferences,
    tasks,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(meta.router)
api_router.include_router(me.router)
api_router.include_router(events.router)
api_router.include_router(context.router)
api_router.include_router(preferences.router)
api_router.include_router(functions.router)
api_router.include_router(ai.router)
api_router.include_router(budget.router)
api_router.include_router(tasks.router)
