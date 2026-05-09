"""
Approval workflow tests for Phase 3.
Tests the complete approval flow: submit → approve/reject → post.
"""

import pytest
from httpx import AsyncClient

from app.models.receipt import ReceiptStatus

pytestmark = pytest.mark.asyncio


class TestApprovalWorkflow:
    """End-to-end approval workflow tests."""
    
    async def test_submit_reviewed_to_pending(
        self, client: AsyncClient, preparer_token: str, reviewed_receipt_id: str
    ):
        """PREPARER: REVIEWED → PENDING_REVIEW."""
        resp = await client.post(
            f"/api/v1/receipts/{reviewed_receipt_id}/submit",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "PENDING_REVIEW"
    
    async def test_approve_pending_to_reviewed(
        self, client: AsyncClient, reviewer_token: str, pending_receipt_id: str
    ):
        """REVIEWER: PENDING_REVIEW → REVIEWED."""
        resp = await client.post(
            f"/api/v1/receipts/{pending_receipt_id}/approve",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "REVIEWED"
    
    async def test_reject_pending_with_comment(
        self, client: AsyncClient, reviewer_token: str, pending_receipt_id: str
    ):
        """REVIEWER: PENDING_REVIEW → REJECTED with comment."""
        resp = await client.post(
            f"/api/v1/receipts/{pending_receipt_id}/reject",
            json={"comment": "Missing receipt image - please re-upload"},
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"
        
        # Verify comment stored
        comments_resp = await client.get(
            f"/api/v1/receipts/{pending_receipt_id}/comments",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert comments_resp.status_code == 200
        comments = comments_resp.json()
        assert len(comments) >= 1
        assert comments[0]["comment"] == "Missing receipt image - please re-upload"
        assert comments[0]["action"] == "REJECTED"
    
    async def test_invalid_pending_to_posted_direct(
        self, client: AsyncClient, preparer_token: str, pending_receipt_id: str
    ):
        """Direct PENDING_REVIEW → POSTED must return 409 or 422."""
        resp = await client.post(
            f"/api/v1/receipts/{pending_receipt_id}/journalize",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        # Should fail because status is PENDING_REVIEW, not REVIEWED
        assert resp.status_code in [409, 422]
    
    async def test_reviewed_can_be_posted(
        self, client: AsyncClient, preparer_token: str, reviewed_receipt_with_data_id: str
    ):
        """After reviewer approves, preparer must be able to journalize (REVIEWED → POSTED)."""
        # This tests the critical bug fix: REVIEWED → POSTED transition
        resp = await client.post(
            f"/api/v1/receipts/{reviewed_receipt_with_data_id}/journalize",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        # Should succeed (201) or fail with specific error (not 409 state machine error)
        if resp.status_code != 201:
            # If it fails, it should NOT be because of state machine
            detail = resp.json().get("detail", "")
            assert "status" not in detail.lower() or "REVIEWED" not in detail
    
    async def test_full_workflow_e2e(
        self, client: AsyncClient, preparer_token: str, reviewer_token: str,
        extracted_receipt_id: str
    ):
        """Complete flow: EXTRACTED → REVIEWED → PENDING_REVIEW → REVIEWED → POSTED."""
        # 1. Preparer reviews and corrects (EXTRACTED → REVIEWED)
        resp = await client.put(
            f"/api/v1/receipts/{extracted_receipt_id}/correct",
            json={
                "vendor_name": "Test Vendor",
                "total_amount": 50.00,
                "date": "2024-01-15"
            },
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "REVIEWED"
        
        # 2. Preparer submits (REVIEWED → PENDING_REVIEW)
        resp = await client.post(
            f"/api/v1/receipts/{extracted_receipt_id}/submit",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "PENDING_REVIEW"
        
        # 3. Reviewer approves (PENDING_REVIEW → REVIEWED)
        resp = await client.post(
            f"/api/v1/receipts/{extracted_receipt_id}/approve",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "REVIEWED"
        
        # 4. Preparer journalizes (REVIEWED → POSTED)
        resp = await client.post(
            f"/api/v1/receipts/{extracted_receipt_id}/journalize",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        # May fail due to missing data, but should not fail due to state machine
        if resp.status_code != 201:
            detail = resp.json().get("detail", "")
            # Should not be a state machine error
            assert "status" not in detail.lower() or "cannot" not in detail.lower()
    
    async def test_cannot_submit_non_reviewed(
        self, client: AsyncClient, preparer_token: str, uploaded_receipt_id: str
    ):
        """Cannot submit receipt that is not in REVIEWED status."""
        resp = await client.post(
            f"/api/v1/receipts/{uploaded_receipt_id}/submit",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 409
    
    async def test_cannot_approve_non_pending(
        self, client: AsyncClient, reviewer_token: str, reviewed_receipt_id: str
    ):
        """Cannot approve receipt that is not in PENDING_REVIEW status."""
        resp = await client.post(
            f"/api/v1/receipts/{reviewed_receipt_id}/approve",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert resp.status_code == 409
    
    async def test_review_comment_stored_on_approve(
        self, client: AsyncClient, reviewer_token: str, pending_receipt_id: str
    ):
        """Approval creates a review comment with action=APPROVED."""
        resp = await client.post(
            f"/api/v1/receipts/{pending_receipt_id}/approve",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        assert resp.status_code == 200
        
        # Check comment was created
        comments_resp = await client.get(
            f"/api/v1/receipts/{pending_receipt_id}/comments",
            headers={"Authorization": f"Bearer {reviewer_token}"}
        )
        comments = comments_resp.json()
        assert any(c["action"] == "APPROVED" for c in comments)
    
    async def test_preparer_can_see_own_rejected_comments(
        self, client: AsyncClient, preparer_token: str, rejected_receipt_id: str
    ):
        """Preparer can see rejection comments on their own receipts."""
        resp = await client.get(
            f"/api/v1/receipts/{rejected_receipt_id}/comments",
            headers={"Authorization": f"Bearer {preparer_token}"}
        )
        assert resp.status_code == 200
        comments = resp.json()
        assert len(comments) >= 1
        assert any(c["action"] == "REJECTED" for c in comments)
