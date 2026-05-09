"""Add PENDING_REVIEW status to receipt_status enum

Revision ID: 011
Revises: 010
Create Date: 2024-01-15 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL doesn't support ALTER TYPE ... ADD VALUE in a transaction
    # We need to use a raw connection
    op.execute("ALTER TYPE receipt_status ADD VALUE 'PENDING_REVIEW'")


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # We need to recreate the enum type without PENDING_REVIEW
    
    # Create new enum without PENDING_REVIEW
    op.execute("""
        CREATE TYPE receipt_status_new AS ENUM (
            'UPLOADED', 'EXTRACTING', 'EXTRACTED', 'EXTRACTION_FAILED',
            'VALIDATION_FAILED', 'REVIEWED', 'POSTED', 'REJECTED', 'QUARANTINED'
        )
    """)
    
    # Update any PENDING_REVIEW receipts to REVIEWED (safe fallback)
    op.execute("UPDATE receipts SET status = 'REVIEWED' WHERE status = 'PENDING_REVIEW'")
    
    # Alter column to use new enum
    op.execute("ALTER TABLE receipts ALTER COLUMN status TYPE receipt_status_new USING status::text::receipt_status_new")
    
    # Drop old enum and rename new one
    op.execute("DROP TYPE receipt_status")
    op.execute("ALTER TYPE receipt_status_new RENAME TO receipt_status")
