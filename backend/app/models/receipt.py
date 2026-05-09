"""
SQLAlchemy ORM model for receipts table.
Maps to the schema defined in PRD §6.
"""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ReceiptStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    REVIEWED = "REVIEWED"
    PENDING_REVIEW = "PENDING_REVIEW"  # Phase 3: Awaiting reviewer approval
    POSTED = "POSTED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"  # Unbalanced entries that failed bookkeeping assertion


# Valid state transitions per PRD §FR-5 + Phase 3 approval workflow
VALID_TRANSITIONS: dict[ReceiptStatus, set[ReceiptStatus]] = {
    ReceiptStatus.UPLOADED: {ReceiptStatus.EXTRACTING},
    ReceiptStatus.EXTRACTING: {
        ReceiptStatus.EXTRACTED,
        ReceiptStatus.EXTRACTION_FAILED,
    },
    ReceiptStatus.EXTRACTED: {
        ReceiptStatus.REVIEWED,
        ReceiptStatus.VALIDATION_FAILED,
    },
    ReceiptStatus.EXTRACTION_FAILED: {ReceiptStatus.EXTRACTING},  # retry
    ReceiptStatus.VALIDATION_FAILED: {ReceiptStatus.REVIEWED},     # manual fix
    ReceiptStatus.REVIEWED: {
        ReceiptStatus.PENDING_REVIEW,  # Phase 3: Preparer submits for approval
        ReceiptStatus.POSTED,
        ReceiptStatus.REJECTED,
        ReceiptStatus.QUARANTINED,  # Can transition to QUARANTINED if bookkeeping fails
    },
    ReceiptStatus.PENDING_REVIEW: {
        ReceiptStatus.REVIEWED,  # Reviewer approves or returns for edits
        ReceiptStatus.REJECTED,  # Reviewer rejects
    },
    ReceiptStatus.POSTED: set(),       # terminal — immutable
    ReceiptStatus.REJECTED: set(),     # terminal
    ReceiptStatus.QUARANTINED: set(),  # terminal — requires admin intervention
}


def validate_status_transition(
    current: ReceiptStatus, target: ReceiptStatus
) -> bool:
    """Check if a status transition is valid per the PRD state machine."""
    return target in VALID_TRANSITIONS.get(current, set())


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    original_filename = Column(Text)
    mime_type = Column(Text)
    file_size_bytes = Column(Integer)
    status = Column(
        Enum(ReceiptStatus, name="receipt_status", create_type=False),
        nullable=False,
        default=ReceiptStatus.UPLOADED,
    )
    extracted_data = Column(JSONB)
    confidence_scores = Column(JSONB)
    raw_llm_output = Column(Text)
    extraction_error = Column(Text)
    extracted_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    # Relationships
    journal_entries = relationship("JournalEntry", back_populates="receipt")
    review_comments = relationship("ReviewComment", back_populates="receipt", cascade="all, delete-orphan")


class ReviewComment(Base):
    """Review comments for approval workflow (Phase 3)."""
    __tablename__ = "review_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    receipt_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    comment = Column(Text, nullable=False)
    action = Column(String(20), nullable=False)  # APPROVED, REJECTED, RETURNED
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    # Relationships
    receipt = relationship("Receipt", back_populates="review_comments")
