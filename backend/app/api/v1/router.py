"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from backend.app.api.v1.analyze import router as analyze_router
from backend.app.api.v1.history import router as history_router
from backend.app.api.v1.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(analyze_router)
api_router.include_router(history_router)
