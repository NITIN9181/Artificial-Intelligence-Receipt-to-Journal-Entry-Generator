"""Initial schema — all tables, types, and indexes

Revision ID: 001
Revises: None
Create Date: 2026-05-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- ENUM TYPES ---
    op.execute("CREATE TYPE receipt_status AS ENUM ('UPLOADED','EXTRACTING','EXTRACTED','EXTRACTION_FAILED','VALIDATION_FAILED','REVIEWED','POSTED','REJECTED');")
    op.execute("CREATE TYPE account_type AS ENUM ('ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE');")
    op.execute("CREATE TYPE normal_balance AS ENUM ('DEBIT','CREDIT');")
    op.execute("CREATE TYPE entry_status AS ENUM ('DRAFT','POSTED','REVERSED','QUARANTINED');")

    # --- TABLES ---
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            full_name TEXT,
            company_name TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    op.execute("""
        CREATE TABLE receipts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            image_url TEXT NOT NULL,
            original_filename TEXT,
            mime_type TEXT,
            file_size_bytes INTEGER,
            status receipt_status NOT NULL DEFAULT 'UPLOADED',
            extracted_data JSONB,
            confidence_scores JSONB,
            raw_llm_output TEXT,
            extraction_error TEXT,
            extracted_at TIMESTAMPTZ,
            reviewed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX idx_receipts_user_id ON receipts(user_id);")
    op.execute("CREATE INDEX idx_receipts_status ON receipts(status);")
    op.execute("CREATE INDEX idx_receipts_created_at ON receipts(created_at DESC);")

    op.execute("""
        CREATE TABLE chart_of_accounts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            code VARCHAR(10) NOT NULL,
            name TEXT NOT NULL,
            type account_type NOT NULL,
            normal_balance normal_balance NOT NULL,
            is_default BOOLEAN NOT NULL DEFAULT FALSE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(user_id, code)
        );
    """)
    op.execute("CREATE INDEX idx_coa_user_id ON chart_of_accounts(user_id);")

    op.execute("""
        CREATE TABLE vendor_category_mappings (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            vendor_name_pattern TEXT NOT NULL,
            account_code VARCHAR(10) NOT NULL,
            is_default BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX idx_vcm_user_id ON vendor_category_mappings(user_id);")

    op.execute("""
        CREATE TABLE journal_entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            receipt_id UUID NOT NULL REFERENCES receipts(id),
            entry_number VARCHAR(14) NOT NULL UNIQUE,
            entry_date DATE NOT NULL,
            reference TEXT,
            description TEXT,
            total_debit NUMERIC(15,2) NOT NULL,
            total_credit NUMERIC(15,2) NOT NULL,
            status entry_status NOT NULL DEFAULT 'DRAFT',
            reversal_of_id UUID REFERENCES journal_entries(id),
            posted_by UUID REFERENCES users(id),
            posted_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT chk_balanced CHECK (total_debit = total_credit),
            CONSTRAINT chk_positive_totals CHECK (total_debit >= 0 AND total_credit >= 0)
        );
    """)
    op.execute("CREATE INDEX idx_je_receipt_id ON journal_entries(receipt_id);")
    op.execute("CREATE INDEX idx_je_entry_date ON journal_entries(entry_date DESC);")
    op.execute("CREATE INDEX idx_je_status ON journal_entries(status);")
    op.execute("CREATE INDEX idx_je_posted_by ON journal_entries(posted_by);")

    op.execute("""
        CREATE TABLE journal_entry_lines (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            journal_entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
            account_code VARCHAR(10) NOT NULL,
            account_name TEXT NOT NULL,
            debit NUMERIC(15,2) NOT NULL DEFAULT 0 CHECK (debit >= 0),
            credit NUMERIC(15,2) NOT NULL DEFAULT 0 CHECK (credit >= 0),
            description TEXT,
            line_order SMALLINT NOT NULL,
            CONSTRAINT chk_debit_or_credit CHECK (
                (debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)
            )
        );
    """)
    op.execute("CREATE INDEX idx_jel_entry_id ON journal_entry_lines(journal_entry_id);")

    op.execute("""
        CREATE TABLE audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            table_name TEXT NOT NULL,
            record_id UUID NOT NULL,
            action TEXT NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
            old_values JSONB,
            new_values JSONB,
            performed_by UUID REFERENCES users(id),
            performed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX idx_audit_table_record ON audit_logs(table_name, record_id);")
    op.execute("CREATE INDEX idx_audit_performed_at ON audit_logs(performed_at DESC);")


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.execute("DROP TABLE IF EXISTS audit_logs CASCADE;")
    op.execute("DROP TABLE IF EXISTS journal_entry_lines CASCADE;")
    op.execute("DROP TABLE IF EXISTS journal_entries CASCADE;")
    op.execute("DROP TABLE IF EXISTS vendor_category_mappings CASCADE;")
    op.execute("DROP TABLE IF EXISTS chart_of_accounts CASCADE;")
    op.execute("DROP TABLE IF EXISTS receipts CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS entry_status;")
    op.execute("DROP TYPE IF EXISTS normal_balance;")
    op.execute("DROP TYPE IF EXISTS account_type;")
    op.execute("DROP TYPE IF EXISTS receipt_status;")
