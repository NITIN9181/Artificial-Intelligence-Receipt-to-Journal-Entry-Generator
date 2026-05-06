"""add_batch_id

Revision ID: 006
Revises: 005
Create Date: 2026-05-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('receipts', sa.Column('batch_id', UUID(as_uuid=True), nullable=True))
    op.create_index('idx_receipts_batch_id', 'receipts', ['batch_id'])

def downgrade() -> None:
    op.drop_index('idx_receipts_batch_id', table_name='receipts')
    op.drop_column('receipts', 'batch_id')
