"""
Health check endpoint — public, no auth required.
Returns db + llm_provider status per PRD §9.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.database import check_db_connection
from app.llm_client import llm_client

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health_check():
    """
    GET /api/v1/health — public endpoint for UptimeRobot pinging.
    Returns service health status.
    """
    db_connected = await check_db_connection()
    llm_healthy = await llm_client.check_health()

    return {
        "status": "ok" if db_connected else "degraded",
        "db": "connected" if db_connected else "disconnected",
        "llm_provider": settings.llm_provider,
        "llm_healthy": llm_healthy,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
