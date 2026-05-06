"""add_admin_flag

Revision ID: 004
Revises: 003
Create Date: 2026-05-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('idx_users_is_admin', 'users', ['id'], postgresql_where=sa.text('is_admin = TRUE'))

def downgrade() -> None:
    op.drop_index('idx_users_is_admin', table_name='users')
    op.drop_column('users', 'is_admin')
