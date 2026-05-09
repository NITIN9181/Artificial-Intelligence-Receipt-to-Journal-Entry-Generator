"""
Role-based access control tests for Phase 3.
Tests that PREPARER, REVIEWER, and ADMIN roles have correct permissions.
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4

from app.models.user import UserRole
from app.models.receipt import ReceiptStatus

pytestmark = pytest.mark.asyncio


class TestRoleAccess:
    """Verify role-based access control on all endpoints."""
    
    async def test_preparer_can_upload(self, client: AsyncClient, preparer_token: str):
        """PREPARER can upload receipts."""
        # This would require multipart upload setup
        # For now, just verify the endpoint exists and requires auth
        resp = await client.post(
            "/api/v1/receipts/upload",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        # Should fail with 422 (missing file) not 403 (forbidden)
        assert resp.status_code != 403
    
    async def test_preparer_cannot_approve(
        self, client: AsyncClient, preparer_token: str, pending_receipt_id: str
    ):
        """PREPARER gets 403 on approve endpoint."""
        resp = await client.post(
            f"/api/v1/receipts/{pending_receipt_id}/approve",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 403
        detail = resp.json().get("detail", "")
        assert "REVIEWER" in detail or "ADMIN" in detail or "Requires one of" in detail
    
    async def test_reviewer_can_approve(
        self, client: AsyncClient, reviewer_token: str, pending_receipt_id: str
    ):
        """REVIEWER can approve PENDING_REVIEW receipts."""
        resp = await client.post(
            f"/api/v1/receipts/{pending_receipt_id}/approve",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "REVIEWED"
    
    async def test_reviewer_can_see_all_pending(
        self, client: AsyncClient, reviewer_token: str, other_user_pending_id: str
    ):
        """REVIEWER sees PENDING_REVIEW from other users."""
        resp = await client.get(
            "/api/v1/receipts/pending-review",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", data)  # Handle both formats
        assert len(items) >= 1
        assert any(r["id"] == other_user_pending_id for r in items)
    
    async def test_reviewer_cannot_see_non_pending_from_others(
        self, client: AsyncClient, reviewer_token: str, other_user_uploaded_id: str
    ):
        """REVIEWER cannot see non-PENDING_REVIEW receipts from others."""
        resp = await client.get(
            f"/api/v1/receipts/{other_user_uploaded_id}",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        # Should be 404 (not found) or 403 (forbidden)
        assert resp.status_code in [403, 404]
    
    async def test_admin_can_change_roles(
        self, client: AsyncClient, admin_token: str, preparer_user_id: str
    ):
        """ADMIN can change user roles."""
        resp = await client.put(
            f"/api/v1/admin/users/{preparer_user_id}/role",
            json={"role": "REVIEWER"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "REVIEWER"
    
    async def test_non_admin_cannot_change_roles(
        self, client: AsyncClient, preparer_token: str, other_user_id: str
    ):
        """PREPARER gets 403 on role change."""
        resp = await client.put(
            f"/api/v1/admin/users/{other_user_id}/role",
            json={"role": "ADMIN"},
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 403
    
    async def test_admin_can_list_all_users(
        self, client: AsyncClient, admin_token: str
    ):
        """ADMIN can list all users."""
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert len(data["users"]) >= 1
    
    async def test_preparer_cannot_list_all_users(
        self, client: AsyncClient, preparer_token: str
    ):
        """PREPARER gets 403 on user list."""
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 403
    
    async def test_preparer_can_only_submit_own_receipts(
        self, client: AsyncClient, preparer_token: str, other_user_reviewed_id: str
    ):
        """PREPARER cannot submit another user's receipt."""
        resp = await client.post(
            f"/api/v1/receipts/{other_user_reviewed_id}/submit",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 403
    
    async def test_admin_has_all_permissions(
        self, client: AsyncClient, admin_token: str, pending_receipt_id: str
    ):
        """ADMIN can perform all actions."""
        # Can approve
        resp = await client.post(
            f"/api/v1/receipts/{pending_receipt_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
        
        # Can list users
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert resp.status_code == 200
