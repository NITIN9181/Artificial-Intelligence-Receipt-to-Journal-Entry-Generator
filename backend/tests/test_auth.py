"""
Auth middleware tests — mock Supabase verification.
"""

import pytest
from fastapi import HTTPException, status
from app.auth import get_current_user
from unittest.mock import MagicMock, patch

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """Verify that a valid token returns the user payload."""
    mock_creds = MagicMock()
    mock_creds.credentials = "valid_token"
    
    mock_payload = {"sub": "123-456", "email": "test@example.com"}
    
    with patch("app.auth._decode_token", return_value=mock_payload):
        user = await get_current_user(mock_creds)
        assert user["sub"] == "123-456"
        assert user["email"] == "test@example.com"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Verify that an invalid token raises 401."""
    mock_creds = MagicMock()
    mock_creds.credentials = "invalid_token"
    
    with patch("app.auth._decode_token", side_effect=HTTPException(status_code=401, detail="Invalid token")):
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(mock_creds)
        assert excinfo.value.status_code == 401
        assert "Invalid token" in excinfo.value.detail

@pytest.mark.asyncio
async def test_get_current_user_missing_sub():
    """Verify that a token without 'sub' raises 401."""
    mock_creds = MagicMock()
    mock_creds.credentials = "no_sub_token"
    
    # Missing "sub" key in return
    with patch("app.auth._decode_token", return_value={"email": "test@example.com"}):
        with pytest.raises(HTTPException) as excinfo:
            await get_current_user(mock_creds)
        assert excinfo.value.status_code == 401
        assert "valid user identifier" in excinfo.value.detail
