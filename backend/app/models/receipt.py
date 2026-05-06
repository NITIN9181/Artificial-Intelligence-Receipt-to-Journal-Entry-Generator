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
    POSTED = "POSTED"
    REJECTED = "REJECTED"


# Valid state transitions per PRD §FR-5
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
        ReceiptStatus.POSTED,
        ReceiptStatus.REJECTED,
    },
    ReceiptStatus.POSTED: set(),       # terminal — immutable
    ReceiptStatus.REJECTED: set(),     # terminal
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
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    # Relationships
    journal_entries = relationship("JournalEntry", back_populates="receipt")
