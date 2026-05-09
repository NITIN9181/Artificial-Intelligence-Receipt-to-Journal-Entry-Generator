"""
Supabase JWT verification middleware.
Verifies the Bearer token from the Authorization header using local JWT verification.
Uses JWKS caching for performance. Rejects 401 on missing or invalid tokens.
"""

import time
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
import httpx
from supabase import create_client

from app.config import settings

security = HTTPBearer()

# Supabase JWT settings
SUPABASE_JWT_SECRET = settings.supabase_jwt_secret
ALGORITHM = "HS256"
AUDIENCE = "authenticated"
ISSUER = f"{settings.supabase_url}/auth/v1"

# JWKS cache (for RS256 if needed in future)
_jwks_cache: Optional[dict] = None
_jwks_cache_time: float = 0
JWKS_CACHE_TTL = 3600  # 1 hour
supabase_client = create_client(settings.supabase_url, settings.supabase_anon_key)


async def _get_jwks() -> dict:
    """Fetch and cache Supabase JWKS public keys."""
    global _jwks_cache, _jwks_cache_time
    
    current_time = time.time()
    if _jwks_cache and (current_time - _jwks_cache_time) < JWKS_CACHE_TTL:
        return _jwks_cache
    
    # Fetch JWKS from Supabase
    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        _jwks_cache = response.json()
        _jwks_cache_time = current_time
        return _jwks_cache


def _decode_token(token: str) -> dict:
    """
    Validate a Supabase JWT token locally using the JWT secret.
    Falls back to Supabase API verification if local verification fails.
    """
    try:
        # First, try local JWT verification (fast path)
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            issuer=ISSUER,
        )
        return payload
    except JWTError as e:
        # If local verification fails, fall back to Supabase API (slow path)
        # This handles edge cases like key rotation
        try:
            response = supabase_client.auth.get_user(token)
            if not response or not response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return {
                "sub": response.user.id,
                "email": response.user.email,
            }
        except Exception as fallback_error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency — extracts and validates the Supabase JWT.
    Returns the decoded token payload containing user info.

    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            user_id = user["sub"]
    """
    payload = _decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a valid user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

async def get_current_user_id(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Convenience dependency — returns just the user UUID string and ensures they exist in local DB."""
    user_id = user["sub"]
    
    # Auto-upsert to sync Cloud Supabase Auth with Local Postgres
    from sqlalchemy import text
    try:
        await db.execute(
            text("INSERT INTO users (id, full_name, company_name) VALUES (:id, 'Test User', 'Test Corp') ON CONFLICT (id) DO NOTHING"),
            {"id": user_id}
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        
    return user_id


from app.models.user import User, UserRole

async def require_admin(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """FastAPI dependency — requires the current user to be an admin."""
    user = await db.get(User, current_user["sub"])
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_role(*roles: UserRole):
    """
    Factory function to create role-checking dependencies.
    
    Usage:
        require_reviewer = require_role(UserRole.REVIEWER, UserRole.ADMIN)
        
        @router.get("/approval-queue")
        async def get_queue(user: User = Depends(require_reviewer)):
            ...
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        user = await db.get(User, current_user["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in database"
            )
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {[r.value for r in roles]}"
            )
        return user
    return role_checker


# Convenience dependencies for common role checks
require_authenticated = require_role(UserRole.PREPARER, UserRole.REVIEWER, UserRole.ADMIN)  # Any authenticated user
require_preparer = require_role(UserRole.PREPARER, UserRole.REVIEWER, UserRole.ADMIN)  # Alias for backward compatibility
require_reviewer = require_role(UserRole.REVIEWER, UserRole.ADMIN)
require_admin_role = require_role(UserRole.ADMIN)



async def get_optional_user(
    request: Request,
) -> Optional[dict]:
    """
    Optional auth dependency — returns None if no valid token is present.
    Used for public endpoints that optionally accept auth (e.g., health check).
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        return _decode_token(token)
    except HTTPException:
        return None


def create_test_token(user_id: str, role: str = "PREPARER") -> str:
    """
    Create a test JWT token for testing purposes.
    
    Args:
        user_id: User UUID as string
        role: User role (PREPARER, REVIEWER, or ADMIN)
        
    Returns:
        JWT token string (without "Bearer " prefix)
    """
    from datetime import datetime, timedelta, timezone
    
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": str(user_id),
        "id": str(user_id),
        "email": f"test-{user_id}@example.com",
        "aud": "authenticated",
        "iss": f"{settings.supabase_url}/auth/v1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "role": role
    }
    return jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm=ALGORITHM)
