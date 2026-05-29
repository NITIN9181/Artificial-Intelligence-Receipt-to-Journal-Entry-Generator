"""
SQLAlchemy ORM model for receipts table.
Uses dialect-agnostic types for SQLite + PostgreSQL compatibility.
"""

import enum
import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
    TypeDecorator,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Compatibility types
# ---------------------------------------------------------------------------

class GUID(TypeDecorator):
    """UUID stored as TEXT in SQLite, native UUID in Postgres."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        import uuid
        return uuid.UUID(str(value))


class JSONType(TypeDecorator):
    """JSON stored as TEXT in SQLite, native JSONB in Postgres."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        return json.loads(value)


# ---------------------------------------------------------------------------
# Enums & state machine
# ---------------------------------------------------------------------------

class ReceiptStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    REVIEWED = "REVIEWED"
    PENDING_REVIEW = "PENDING_REVIEW"
    POSTED = "POSTED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


VALID_TRANSITIONS: dict[ReceiptStatus, set[ReceiptStatus]] = {
    ReceiptStatus.UPLOADED: {ReceiptStatus.EXTRACTING},
    ReceiptStatus.EXTRACTING: {ReceiptStatus.EXTRACTED, ReceiptStatus.EXTRACTION_FAILED},
    ReceiptStatus.EXTRACTED: {ReceiptStatus.REVIEWED, ReceiptStatus.VALIDATION_FAILED},
    ReceiptStatus.EXTRACTION_FAILED: {ReceiptStatus.EXTRACTING},
    ReceiptStatus.VALIDATION_FAILED: {ReceiptStatus.REVIEWED},
    ReceiptStatus.REVIEWED: {
        ReceiptStatus.PENDING_REVIEW,
        ReceiptStatus.POSTED,
        ReceiptStatus.REJECTED,
        ReceiptStatus.QUARANTINED,
    },
    ReceiptStatus.PENDING_REVIEW: {ReceiptStatus.REVIEWED, ReceiptStatus.REJECTED},
    ReceiptStatus.POSTED: set(),
    ReceiptStatus.REJECTED: set(),
    ReceiptStatus.QUARANTINED: set(),
}


def validate_status_transition(current: ReceiptStatus, target: ReceiptStatus) -> bool:
    return target in VALID_TRANSITIONS.get(current, set())


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(GUID, primary_key=True, default=uuid4)
    user_id = Column(GUID, nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    original_filename = Column(Text)
    mime_type = Column(Text)
    file_size_bytes = Column(Integer)
    status = Column(
        Enum(ReceiptStatus, name="receipt_status", create_type=False),
        nullable=False,
        default=ReceiptStatus.UPLOADED,
    )
    extracted_data = Column(JSONType)
    confidence_scores = Column(JSONType)
    raw_llm_output = Column(Text)
    extraction_error = Column(Text)
    extracted_at = Column(DateTime(timezone=True))
    reviewed_at = Column(DateTime(timezone=True))
    batch_id = Column(GUID, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    journal_entries = relationship("JournalEntry", back_populates="receipt")
    review_comments = relationship("ReviewComment", back_populates="receipt", cascade="all, delete-orphan")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(GUID, primary_key=True, default=uuid4)
    receipt_id = Column(GUID, ForeignKey("receipts.id"), nullable=False, index=True)
    reviewer_id = Column(GUID, nullable=True, index=True)
    comment = Column(Text, nullable=False)
    action = Column(String(20), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    receipt = relationship("Receipt", back_populates="review_comments")
