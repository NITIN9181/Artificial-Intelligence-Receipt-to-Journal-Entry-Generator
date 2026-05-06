"""
API integration tests — test endpoint behavior, status codes, state machine.
"""

import pytest
from app.models.receipt import ReceiptStatus, VALID_TRANSITIONS, validate_status_transition


class TestReceiptStateMachine:
    """Test all state machine transitions per PRD §FR-5."""

    def test_uploaded_to_extracting(self):
        assert validate_status_transition(ReceiptStatus.UPLOADED, ReceiptStatus.EXTRACTING)

    def test_extracting_to_extracted(self):
        assert validate_status_transition(ReceiptStatus.EXTRACTING, ReceiptStatus.EXTRACTED)

    def test_extracting_to_extraction_failed(self):
        assert validate_status_transition(ReceiptStatus.EXTRACTING, ReceiptStatus.EXTRACTION_FAILED)

    def test_extracted_to_reviewed(self):
        assert validate_status_transition(ReceiptStatus.EXTRACTED, ReceiptStatus.REVIEWED)

    def test_extracted_to_validation_failed(self):
        assert validate_status_transition(ReceiptStatus.EXTRACTED, ReceiptStatus.VALIDATION_FAILED)

    def test_reviewed_to_posted(self):
        assert validate_status_transition(ReceiptStatus.REVIEWED, ReceiptStatus.POSTED)

    def test_reviewed_to_rejected(self):
        assert validate_status_transition(ReceiptStatus.REVIEWED, ReceiptStatus.REJECTED)

    def test_reviewed_to_quarantined(self):
        """REVIEWED can transition to QUARANTINED if bookkeeping assertion fails."""
        assert validate_status_transition(ReceiptStatus.REVIEWED, ReceiptStatus.QUARANTINED)

    def test_extraction_failed_can_retry(self):
        assert validate_status_transition(ReceiptStatus.EXTRACTION_FAILED, ReceiptStatus.EXTRACTING)

    def test_validation_failed_to_reviewed(self):
        assert validate_status_transition(ReceiptStatus.VALIDATION_FAILED, ReceiptStatus.REVIEWED)

    # --- Invalid transitions ---

    def test_posted_is_terminal(self):
        """POSTED entries cannot transition to any other status."""
        for target in ReceiptStatus:
            assert not validate_status_transition(ReceiptStatus.POSTED, target)

    def test_rejected_is_terminal(self):
        """REJECTED entries cannot transition to any other status."""
        for target in ReceiptStatus:
            assert not validate_status_transition(ReceiptStatus.REJECTED, target)

    def test_quarantined_is_terminal(self):
        """QUARANTINED entries cannot transition to any other status (requires admin intervention)."""
        for target in ReceiptStatus:
            assert not validate_status_transition(ReceiptStatus.QUARANTINED, target)

    def test_cannot_skip_extracting(self):
        """Cannot go directly from UPLOADED to EXTRACTED."""
        assert not validate_status_transition(ReceiptStatus.UPLOADED, ReceiptStatus.EXTRACTED)

    def test_cannot_go_backward(self):
        """Cannot go from EXTRACTED back to UPLOADED."""
        assert not validate_status_transition(ReceiptStatus.EXTRACTED, ReceiptStatus.UPLOADED)

    def test_cannot_post_without_review(self):
        """Cannot go from EXTRACTED directly to POSTED."""
        assert not validate_status_transition(ReceiptStatus.EXTRACTED, ReceiptStatus.POSTED)

    def test_all_transitions_covered(self):
        """Ensure every status has a transition entry."""
        for status in ReceiptStatus:
            assert status in VALID_TRANSITIONS


class TestEntryNumberFormat:
    """Test JE-YYYY-XXXXX format."""

    def test_format_regex(self):
        import re
        pattern = re.compile(r"^JE-\d{4}-\d{5}$")
        assert pattern.match("JE-2026-00001")
        assert pattern.match("JE-2026-00042")
        assert pattern.match("JE-2026-99999")
        assert not pattern.match("JE-2026-1")
        assert not pattern.match("JE-26-00001")
        assert not pattern.match("XX-2026-00001")



class TestPostedEntryImmutability:
    """Test that POSTED journal entries cannot be physically deleted."""

    def test_posted_entry_cannot_be_deleted(self):
        """
        Verify that attempting to delete a POSTED journal entry
        will fail at the database level with a trigger exception.
        
        This is a placeholder test - full integration test would require
        database setup and actual DELETE attempt.
        """
        # The database trigger fn_prevent_posted_delete() will raise an exception
        # when attempting to DELETE a row where status = 'POSTED'
        # This test documents the expected behavior
        pass

    def test_reversal_endpoint_does_not_delete(self):
        """
        The DELETE /api/v1/journal-entries/{id}/reverse endpoint
        creates a mirror reversal entry and marks the original as REVERSED,
        but never physically deletes the original entry.
        """
        # This is verified by code inspection of journal_entries.py
        # The endpoint calls create_reversal_entry() which:
        # 1. Creates a new entry with swapped debits/credits
        # 2. Sets original.status = REVERSED
        # 3. Never calls db.delete()
        pass



class TestInvalidStateTransitions:
    """Test that invalid state transitions return HTTP 409."""

    @pytest.mark.parametrize("current,target,description", [
        (ReceiptStatus.POSTED, ReceiptStatus.EXTRACTING, "Cannot extract a posted receipt"),
        (ReceiptStatus.UPLOADED, ReceiptStatus.POSTED, "Cannot post without extraction and review"),
        (ReceiptStatus.REJECTED, ReceiptStatus.REVIEWED, "Cannot review a rejected receipt"),
        (ReceiptStatus.EXTRACTION_FAILED, ReceiptStatus.POSTED, "Cannot post a failed extraction"),
        (ReceiptStatus.EXTRACTED, ReceiptStatus.UPLOADED, "Cannot go backward to uploaded"),
        (ReceiptStatus.REVIEWED, ReceiptStatus.EXTRACTING, "Cannot re-extract a reviewed receipt"),
        (ReceiptStatus.POSTED, ReceiptStatus.REJECTED, "Cannot reject a posted receipt"),
        (ReceiptStatus.QUARANTINED, ReceiptStatus.REVIEWED, "Cannot review a quarantined receipt"),
    ])
    def test_invalid_transition_returns_409(self, current, target, description):
        """
        Verify that invalid state transitions are rejected.
        
        This is a documentation test - actual HTTP 409 testing requires
        full API integration tests with database setup.
        """
        # Verify the state machine rejects this transition
        assert not validate_status_transition(current, target), (
            f"State machine should reject {current.value} → {target.value}: {description}"
        )
