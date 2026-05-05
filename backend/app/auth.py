"""
Supabase JWT verification middleware.
Verifies the Bearer token from the Authorization header against Supabase's JWKS.
Rejects 401 on missing or invalid tokens.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

security = HTTPBearer()

# Supabase JWT settings
SUPABASE_JWT_SECRET = settings.supabase_anon_key  # Supabase uses anon key as JWT secret
ALGORITHM = "HS256"
AUDIENCE = "authenticated"


from supabase import create_client, Client

# Initialize a Supabase client for auth verification
supabase_client: Client = create_client(
    settings.supabase_url, 
    settings.supabase_anon_key
)

def _decode_token(token: str) -> dict:
    """Validate a Supabase JWT token by calling the Supabase Auth API."""
    try:
        # get_user automatically verifies the JWT against the Supabase Auth server
        response = supabase_client.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Return a payload that matches what the rest of the app expects (needs "sub")
        return {
            "sub": response.user.id,
            "email": response.user.email,
        }
    except Exception as e:
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
