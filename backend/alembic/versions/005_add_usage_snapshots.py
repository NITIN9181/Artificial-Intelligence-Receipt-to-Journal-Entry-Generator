"""add_usage_snapshots

Revision ID: 005
Revises: 004
Create Date: 2026-05-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("""
        CREATE TABLE usage_snapshots (
          id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          checked_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          postgres_mb          NUMERIC(10,2),
          storage_mb           NUMERIC(10,2),
          request_count_today  INTEGER,
          threshold_hit        BOOLEAN NOT NULL DEFAULT FALSE,
          alert_logged         BOOLEAN NOT NULL DEFAULT FALSE
        );
    """)
    op.execute("""
        CREATE INDEX idx_usage_snapshots_checked_at ON usage_snapshots(checked_at DESC);
    """)

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_usage_snapshots_checked_at;")
    op.execute("DROP TABLE IF EXISTS usage_snapshots;")
