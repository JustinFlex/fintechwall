"""Health and service metadata endpoints."""

from fastapi import APIRouter

from ..core.cache import cache
from ..core.settings import settings

router = APIRouter()


@router.get("/live", summary="Liveness probe")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
def ready() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "data_mode": settings.data_mode,
        "cache_enabled": cache.enabled,
    }
