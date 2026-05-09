"""Create gnucash_mappings table

Revision ID: 012
Revises: 011
Create Date: 2024-01-15 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'gnucash_mappings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('internal_account_code', sa.String(50), nullable=False),
        sa.Column('gnucash_account_path', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.UniqueConstraint('user_id', 'internal_account_code', name='uq_user_internal_code')
    )
    
    # Create index on user_id for faster lookups
    op.create_index('idx_gnucash_mappings_user_id', 'gnucash_mappings', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_gnucash_mappings_user_id', table_name='gnucash_mappings')
    op.drop_table('gnucash_mappings')
