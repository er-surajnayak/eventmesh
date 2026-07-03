"""System health endpoints (mounted at the root, outside /api/v1).

- ``/health``       overall status (kept for the Render health check; DB-free).
- ``/health/live``  liveness: the process is up. Never touches the DB.
- ``/health/ready`` readiness: can we serve traffic? Probes the database.
"""

import asyncio

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["system"])

_READY_TIMEOUT_SECONDS = 5


@router.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": settings.version,
        "environment": settings.environment,
    }


@router.get("/health/live")
async def live() -> dict[str, str]:
    return {"status": "alive"}


@router.get("/health/ready")
async def ready(response: Response) -> dict[str, str]:
    async def _probe() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    try:
        await asyncio.wait_for(_probe(), timeout=_READY_TIMEOUT_SECONDS)
        return {"status": "ready", "database": "up"}
    except Exception as exc:  # noqa: BLE001 - any failure means not ready
        logger.warning("readiness_check_failed", error=str(exc))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "database": "down"}
