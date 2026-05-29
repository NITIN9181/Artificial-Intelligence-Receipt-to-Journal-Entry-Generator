"""
SQLAlchemy ORM model for GnuCash account mappings.
Uses dialect-agnostic types for SQLite + PostgreSQL compatibility.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint

from app.database import Base
from app.models.receipt import GUID


class GnuCashMapping(Base):
    __tablename__ = "gnucash_mappings"

    id = Column(GUID, primary_key=True, default=uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    internal_account_code = Column(String(50), nullable=False)
    gnucash_account_path = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'internal_account_code', name='uq_user_internal_code'),
    )
