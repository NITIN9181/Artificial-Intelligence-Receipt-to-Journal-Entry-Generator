"""Prevent physical deletion of POSTED journal entries

Revision ID: 009
Revises: 008
Create Date: 2026-05-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create trigger to prevent deletion of POSTED journal entries."""
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_prevent_posted_delete()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.status = 'POSTED' THEN
                RAISE EXCEPTION 'Cannot delete posted journal entries. Use reversal instead.';
            END IF;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trg_prevent_posted_delete
        BEFORE DELETE ON journal_entries
        FOR EACH ROW EXECUTE FUNCTION fn_prevent_posted_delete();
    """)


def downgrade() -> None:
    """Remove trigger that prevents deletion of POSTED entries."""
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_posted_delete ON journal_entries;")
    op.execute("DROP FUNCTION IF EXISTS fn_prevent_posted_delete();")
