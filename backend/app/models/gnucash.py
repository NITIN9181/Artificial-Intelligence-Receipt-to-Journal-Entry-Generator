"""
SQLAlchemy ORM model for GnuCash account mappings (Phase 3).
Maps internal chart of account codes to GnuCash account paths.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class GnuCashMapping(Base):
    """
    Maps internal account codes to GnuCash account paths for export.
    Example: EXPENSE_OFFICE → Expenses:Office Supplies
    """
    __tablename__ = "gnucash_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    internal_account_code = Column(String(50), nullable=False)
    gnucash_account_path = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'internal_account_code', name='uq_user_internal_code'),
    )
