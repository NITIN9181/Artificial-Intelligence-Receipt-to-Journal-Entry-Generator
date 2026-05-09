"""Seed defaults — COA and vendor mappings

Revision ID: 002
Revises: 001
Create Date: 2026-05-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- CHART OF ACCOUNTS SEED ---
    op.execute("""
        INSERT INTO chart_of_accounts (user_id, code, name, type, normal_balance, is_default) VALUES
        (NULL, '1010', 'Cash',                     'ASSET',     'DEBIT',  TRUE),
        (NULL, '1020', 'Checking Account',          'ASSET',     'DEBIT',  TRUE),
        (NULL, '1030', 'Credit Card Receivable',    'ASSET',     'DEBIT',  TRUE),
        (NULL, '2000', 'Accounts Payable',          'LIABILITY', 'CREDIT', TRUE),
        (NULL, '2010', 'Credit Card Liability',     'LIABILITY', 'CREDIT', TRUE),
        (NULL, '2100', 'Sales Tax Payable',         'LIABILITY', 'CREDIT', TRUE),
        (NULL, '3000', 'Owner''s Equity',           'EQUITY',    'CREDIT', TRUE),
        (NULL, '3100', 'Retained Earnings',         'EQUITY',    'CREDIT', TRUE),
        (NULL, '5000', 'Travel & Entertainment',    'EXPENSE',   'DEBIT',  TRUE),
        (NULL, '5100', 'Office Supplies',           'EXPENSE',   'DEBIT',  TRUE),
        (NULL, '5200', 'Software & Subscriptions',  'EXPENSE',   'DEBIT',  TRUE),
        (NULL, '5300', 'Meals & Entertainment',     'EXPENSE',   'DEBIT',  TRUE),
        (NULL, '5400', 'Professional Services',     'EXPENSE',   'DEBIT',  TRUE),
        (NULL, '5500', 'Utilities',                 'EXPENSE',   'DEBIT',  TRUE),
        (NULL, '5600', 'Marketing & Advertising',   'EXPENSE',   'DEBIT',  TRUE),
        (NULL, '5999', 'Miscellaneous Expense',     'EXPENSE',   'DEBIT',  TRUE),
        (NULL, '6000', 'Service Revenue',           'REVENUE',   'CREDIT', TRUE),
        (NULL, '6100', 'Product Sales',             'REVENUE',   'CREDIT', TRUE);
    """)

    # --- VENDOR CATEGORY MAPPINGS SEED ---
    op.execute("""
        INSERT INTO vendor_category_mappings (user_id, vendor_name_pattern, account_code, is_default) VALUES
        (NULL, 'united airlines',  '5000', TRUE),
        (NULL, 'delta',            '5000', TRUE),
        (NULL, 'american airlines','5000', TRUE),
        (NULL, 'southwest',        '5000', TRUE),
        (NULL, 'uber',             '5000', TRUE),
        (NULL, 'lyft',             '5000', TRUE),
        (NULL, 'staples',          '5100', TRUE),
        (NULL, 'office depot',     '5100', TRUE),
        (NULL, 'amazon',           '5100', TRUE),
        (NULL, 'github',           '5200', TRUE),
        (NULL, 'aws',              '5200', TRUE),
        (NULL, 'openai',           '5200', TRUE),
        (NULL, 'stripe',           '5200', TRUE),
        (NULL, 'vercel',           '5200', TRUE),
        (NULL, 'starbucks',        '5300', TRUE),
        (NULL, 'mcdonalds',        '5300', TRUE),
        (NULL, 'ups',              '5600', TRUE),
        (NULL, 'fedex',            '5600', TRUE),
        (NULL, 'google ads',       '5600', TRUE),
        (NULL, 'facebook',         '5600', TRUE);
    """)


def downgrade() -> None:
    op.execute("DELETE FROM vendor_category_mappings WHERE user_id IS NULL;")
    op.execute("DELETE FROM chart_of_accounts WHERE user_id IS NULL;")
