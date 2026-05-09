"""Create review_comments table

Revision ID: 013
Revises: 012
Create Date: 2024-01-15 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'review_comments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('receipt_id', UUID(as_uuid=True), sa.ForeignKey('receipts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reviewer_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('comment', sa.Text, nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.CheckConstraint("action IN ('APPROVED', 'REJECTED', 'RETURNED')", name='check_review_action')
    )
    
    # Create indexes for faster lookups
    op.create_index('idx_review_comments_receipt_id', 'review_comments', ['receipt_id'])
    op.create_index('idx_review_comments_reviewer_id', 'review_comments', ['reviewer_id'])


def downgrade() -> None:
    op.drop_index('idx_review_comments_reviewer_id', table_name='review_comments')
    op.drop_index('idx_review_comments_receipt_id', table_name='review_comments')
    op.drop_table('review_comments')
