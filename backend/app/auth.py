"""
Auth module — authentication bypassed, all requests run as a fixed anonymous user.
No JWT or login required.
"""

import time
from typing import Optional
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# Fixed anonymous user ID used for all requests
ANONYMOUS_USER_ID = "00000000-0000-0000-0000-000000000001"
ANONYMOUS_USER = {
    "sub": ANONYMOUS_USER_ID,
    "id": ANONYMOUS_USER_ID,
    "email": "user@localhost",
    "aud": "authenticated",
}

# Stub supabase_client so imports in main.py don't break
from supabase import create_client
supabase_client = create_client(settings.supabase_url, settings.supabase_anon_key)


async def get_current_user(request: Request = None) -> dict:
    """Returns the fixed anonymous user — no token required."""
    return ANONYMOUS_USER


from app.database import get_db

async def get_current_user_id(
    db: AsyncSession = Depends(get_db),
) -> str:
    """Returns the fixed anonymous user ID and ensures the user row exists in the DB."""
    from sqlalchemy import text
    try:
        await db.execute(
            text("INSERT INTO users (id) VALUES (:id) ON CONFLICT (id) DO NOTHING"),
            {"id": ANONYMOUS_USER_ID}
        )
        await db.commit()
    except Exception:
        await db.rollback()
    return ANONYMOUS_USER_ID


from app.models.user import User, UserRole


async def require_admin(db: AsyncSession = Depends(get_db)) -> User:
    """Returns the anonymous user as admin — no auth check."""
    user = await db.get(User, UUID(ANONYMOUS_USER_ID))
    if not user:
        user = User(id=UUID(ANONYMOUS_USER_ID), role=UserRole.ADMIN)
    return user


def require_role(*roles: UserRole):
    """Always passes — returns the anonymous user with ADMIN role."""
    async def role_checker(db: AsyncSession = Depends(get_db)) -> User:
        user = await db.get(User, UUID(ANONYMOUS_USER_ID))
        if not user:
            user = User(id=UUID(ANONYMOUS_USER_ID), role=UserRole.ADMIN)
        return user
    return role_checker


# Convenience role dependencies — all pass through
require_authenticated = require_role(UserRole.PREPARER)
require_preparer = require_role(UserRole.PREPARER)
require_reviewer = require_role(UserRole.REVIEWER)
require_admin_role = require_role(UserRole.ADMIN)


async def get_optional_user(request: Request) -> Optional[dict]:
    """Always returns the anonymous user."""
    return ANONYMOUS_USER


def create_test_token(user_id: str, role: str = "PREPARER") -> str:
    """Kept for test compatibility — generates a JWT using the configured secret."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt

    SUPABASE_JWT_SECRET = settings.supabase_jwt_secret
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user_id),
        "id": str(user_id),
        "email": f"test-{user_id}@example.com",
        "aud": "authenticated",
        "iss": f"{settings.supabase_url}/auth/v1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "role": role,
    }
    return jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")
