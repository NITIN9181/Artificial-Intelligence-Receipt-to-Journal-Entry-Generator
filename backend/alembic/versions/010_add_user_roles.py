"""Add user roles

Revision ID: 010
Revises: 009
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_role enum
    user_role_enum = postgresql.ENUM('PREPARER', 'REVIEWER', 'ADMIN', name='user_role')
    user_role_enum.create(op.get_bind())
    
    # Add role column with default PREPARER
    op.add_column('users', sa.Column('role', sa.Enum('PREPARER', 'REVIEWER', 'ADMIN', name='user_role'), nullable=False, server_default='PREPARER'))
    
    # Migrate existing data: is_admin = TRUE → role = 'ADMIN'
    op.execute("UPDATE users SET role = 'ADMIN' WHERE is_admin = TRUE")
    op.execute("UPDATE users SET role = 'PREPARER' WHERE is_admin = FALSE OR is_admin IS NULL")
    
    # Drop is_admin column
    op.drop_column('users', 'is_admin')


def downgrade() -> None:
    # Add back is_admin column
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    
    # Migrate data back: role = 'ADMIN' → is_admin = TRUE
    op.execute("UPDATE users SET is_admin = TRUE WHERE role = 'ADMIN'")
    op.execute("UPDATE users SET is_admin = FALSE WHERE role != 'ADMIN'")
    
    # Drop role column
    op.drop_column('users', 'role')
    
    # Drop user_role enum
    user_role_enum = postgresql.ENUM('PREPARER', 'REVIEWER', 'ADMIN', name='user_role')
    user_role_enum.drop(op.get_bind())
