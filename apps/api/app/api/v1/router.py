from fastapi import APIRouter

from app.api.v1 import (
    adaptive,
    ai,
    budget,
    context,
    events,
    functions,
    gifts,
    health,
    me,
    meta,
    preferences,
    public_gifts,
    tasks,
    vendors,
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
api_router.include_router(vendors.router)
api_router.include_router(gifts.router)
api_router.include_router(public_gifts.router)
api_router.include_router(adaptive.router)
