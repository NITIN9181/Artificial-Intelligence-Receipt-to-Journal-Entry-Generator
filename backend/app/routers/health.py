"""
Health check endpoint — public, no auth required.
Returns db + llm_provider status per PRD §9.

Also provides /auth/me for the frontend AuthProvider.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.database import check_db_connection, get_db
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


@router.get("/auth/me", tags=["auth"])
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/v1/auth/me — Returns the current authenticated user's profile.
    Used by the frontend AuthProvider to populate user context and role-based navigation.
    """
    from app.models.user import User, UserRole

    user_id = current_user.get("sub")
    db_user = await db.get(User, user_id)

    return {
        "id": user_id,
        "email": current_user.get("email"),
        "full_name": db_user.full_name if db_user else None,
        "company_name": db_user.company_name if db_user else None,
        "role": (db_user.role.value if isinstance(db_user.role, UserRole) else db_user.role)
                if db_user else UserRole.PREPARER.value,
        "created_at": db_user.created_at.isoformat() if db_user and db_user.created_at else None,
    }
