"""Endpoints for data snapshots."""

from fastapi import APIRouter, Depends

from ..services.data_service import DataService

router = APIRouter()


def get_data_service() -> DataService:
    # dependency injection placeholder
    return DataService()


@router.get("/snapshot", summary="Current market snapshot")
async def snapshot(service: DataService = Depends(get_data_service)) -> dict:
    return await service.snapshot()
