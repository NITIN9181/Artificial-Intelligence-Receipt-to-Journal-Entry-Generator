"""Fix audit log trigger to populate performed_by with auth.uid()

Revision ID: 008
Revises: 007
Create Date: 2026-05-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update fn_audit_log() to populate performed_by with auth.uid()."""
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_audit_log()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                INSERT INTO audit_logs (table_name, record_id, action, old_values, performed_by)
                VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD), auth.uid());
                RETURN OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values, performed_by)
                VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW), auth.uid());
                RETURN NEW;
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO audit_logs (table_name, record_id, action, new_values, performed_by)
                VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW), auth.uid());
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)


def downgrade() -> None:
    """Revert to original fn_audit_log() without performed_by."""
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_audit_log()
        RETURNS TRIGGER AS $$
        BEGIN
            IF (TG_OP = 'DELETE') THEN
                INSERT INTO audit_logs (table_name, record_id, action, old_values)
                VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
                RETURN OLD;
            ELSIF (TG_OP = 'UPDATE') THEN
                INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values)
                VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
                RETURN NEW;
            ELSIF (TG_OP = 'INSERT') THEN
                INSERT INTO audit_logs (table_name, record_id, action, new_values)
                VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)
