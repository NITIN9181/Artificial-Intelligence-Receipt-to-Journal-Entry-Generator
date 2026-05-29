"""
SQLAlchemy ORM models for journal_entries and journal_entry_lines tables.
Uses dialect-agnostic types for SQLite + PostgreSQL compatibility.
"""

import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.receipt import GUID


class EntryStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    QUARANTINED = "QUARANTINED"


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(GUID, primary_key=True, default=uuid4)
    receipt_id = Column(GUID, ForeignKey("receipts.id"), nullable=False)
    entry_number = Column(String(14), nullable=False, unique=True)
    entry_date = Column(Date, nullable=False)
    reference = Column(Text)
    description = Column(Text)
    total_debit = Column(Numeric(15, 2), nullable=False)
    total_credit = Column(Numeric(15, 2), nullable=False)
    status = Column(
        Enum(EntryStatus, name="entry_status", create_type=False),
        nullable=False,
        default=EntryStatus.DRAFT,
    )
    reversal_of_id = Column(GUID, ForeignKey("journal_entries.id"))
    posted_by = Column(GUID, ForeignKey("users.id"))
    posted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    receipt = relationship("Receipt", back_populates="journal_entries")
    lines = relationship(
        "JournalEntryLine",
        back_populates="journal_entry",
        cascade="all, delete-orphan",
        order_by="JournalEntryLine.line_order",
    )
    reversal_of = relationship("JournalEntry", remote_side="JournalEntry.id")


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"

    id = Column(GUID, primary_key=True, default=uuid4)
    journal_entry_id = Column(GUID, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_code = Column(String(10), nullable=False)
    account_name = Column(Text, nullable=False)
    debit = Column(Numeric(15, 2), nullable=False, default=0)
    credit = Column(Numeric(15, 2), nullable=False, default=0)
    description = Column(Text)
    line_order = Column(SmallInteger, nullable=False)

    journal_entry = relationship("JournalEntry", back_populates="lines")
