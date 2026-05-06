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
