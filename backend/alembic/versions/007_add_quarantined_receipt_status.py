"""Add QUARANTINED status to receipt_status enum

Revision ID: 007
Revises: 006
Create Date: 2026-05-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add QUARANTINED status to receipt_status enum for unbalanced entries."""
    # PostgreSQL doesn't support ALTER TYPE ... ADD VALUE in a transaction by default
    # We need to use a raw connection to execute this outside a transaction block
    op.execute("ALTER TYPE receipt_status ADD VALUE IF NOT EXISTS 'QUARANTINED'")


def downgrade() -> None:
    """
    Removing enum values is complex in PostgreSQL.
    We would need to:
    1. Create a new enum without QUARANTINED
    2. Alter the column to use the new enum
    3. Drop the old enum
    
    For safety, we'll just document that downgrade is not supported.
    """
    # Note: Downgrading enum values in PostgreSQL requires recreating the enum
    # This is intentionally left as a no-op for safety
    pass
