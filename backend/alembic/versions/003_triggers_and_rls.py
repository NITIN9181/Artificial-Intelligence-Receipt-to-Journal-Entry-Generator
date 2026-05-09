"""Triggers and RLS policies

Revision ID: 003
Revises: 002
Create Date: 2026-05-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- MOCK SUPABASE AUTH FOR LOCAL POSTGRES ---
    op.execute("CREATE SCHEMA IF NOT EXISTS auth;")
    op.execute("""
        CREATE OR REPLACE FUNCTION auth.uid() RETURNS uuid AS $$
        BEGIN
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # --- TRIGGER FUNCTIONS ---
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

    op.execute("""
        CREATE TRIGGER trg_receipts_audit
        AFTER INSERT OR UPDATE OR DELETE ON receipts
        FOR EACH ROW EXECUTE FUNCTION fn_audit_log();
    """)
    
    op.execute("""
        CREATE TRIGGER trg_journal_entries_audit
        AFTER INSERT OR UPDATE OR DELETE ON journal_entries
        FOR EACH ROW EXECUTE FUNCTION fn_audit_log();
    """)

    op.execute("""
        CREATE OR REPLACE FUNCTION fn_set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER trg_receipts_updated_at
        BEFORE UPDATE ON receipts
        FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();
    """)

    # --- ROW LEVEL SECURITY POLICIES ---
    op.execute("ALTER TABLE receipts ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chart_of_accounts ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE vendor_category_mappings ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE journal_entry_lines ENABLE ROW LEVEL SECURITY;")

    op.execute("""
        CREATE POLICY "user_receipts_isolation" ON receipts
        FOR ALL USING (user_id = auth.uid());
    """)

    op.execute("""
        CREATE POLICY "user_coa_isolation" ON chart_of_accounts
        FOR ALL USING (user_id = auth.uid() OR user_id IS NULL);
    """)

    op.execute("""
        CREATE POLICY "user_vcm_isolation" ON vendor_category_mappings
        FOR ALL USING (user_id = auth.uid() OR user_id IS NULL);
    """)

    op.execute("""
        CREATE POLICY "user_je_isolation" ON journal_entries
        FOR ALL USING (
            EXISTS (SELECT 1 FROM receipts WHERE receipts.id = journal_entries.receipt_id AND receipts.user_id = auth.uid())
        );
    """)

    op.execute("""
        CREATE POLICY "user_jel_isolation" ON journal_entry_lines
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM journal_entries 
                JOIN receipts ON receipts.id = journal_entries.receipt_id 
                WHERE journal_entries.id = journal_entry_lines.journal_entry_id 
                AND receipts.user_id = auth.uid()
            )
        );
    """)


def downgrade() -> None:
    # Drop policies
    op.execute("DROP POLICY IF EXISTS user_jel_isolation ON journal_entry_lines;")
    op.execute("DROP POLICY IF EXISTS user_je_isolation ON journal_entries;")
    op.execute("DROP POLICY IF EXISTS user_vcm_isolation ON vendor_category_mappings;")
    op.execute("DROP POLICY IF EXISTS user_coa_isolation ON chart_of_accounts;")
    op.execute("DROP POLICY IF EXISTS user_receipts_isolation ON receipts;")

    # Disable RLS
    op.execute("ALTER TABLE journal_entry_lines DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE journal_entries DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE vendor_category_mappings DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE chart_of_accounts DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE receipts DISABLE ROW LEVEL SECURITY;")

    # Drop triggers and functions
    op.execute("DROP TRIGGER IF EXISTS trg_receipts_updated_at ON receipts;")
    op.execute("DROP FUNCTION IF EXISTS fn_set_updated_at();")
    op.execute("DROP TRIGGER IF EXISTS trg_journal_entries_audit ON journal_entries;")
    op.execute("DROP TRIGGER IF EXISTS trg_receipts_audit ON receipts;")
    op.execute("DROP FUNCTION IF EXISTS fn_audit_log();")
