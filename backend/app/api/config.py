"""Administrative endpoints for runtime configuration."""

from fastapi import APIRouter, HTTPException

from ..core.settings import settings

router = APIRouter()

_current_config = {
    "data_mode": settings.data_mode,
}


@router.get("", summary="Fetch current configuration")
async def get_config() -> dict:
    return _current_config


@router.post("", summary="Update configuration")
async def update_config(payload: dict) -> dict:
    data_mode = payload.get("data_mode")
    if data_mode not in {"wind", "open", "mock"}:
        raise HTTPException(status_code=400, detail="Invalid data_mode")
    _current_config["data_mode"] = data_mode
    return _current_config
