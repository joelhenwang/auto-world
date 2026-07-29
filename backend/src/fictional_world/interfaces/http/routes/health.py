"""Health endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from fictional_world.interfaces.http.dependencies import EngineDep
from fictional_world.interfaces.http.dto import HealthLiveResponse, HealthReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=HealthLiveResponse)
async def health_live() -> HealthLiveResponse:
    return HealthLiveResponse()


@router.get("/health/ready", response_model=HealthReadyResponse)
async def health_ready(engine: EngineDep) -> HealthReadyResponse:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        return HealthReadyResponse(status="not_ready", database="down", detail=str(exc))
    return HealthReadyResponse(status="ready", database="up")
