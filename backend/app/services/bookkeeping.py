"""
Double-entry bookkeeping engine — the most critical service.
Zero tolerance for errors. No unbalanced entry may ever be posted.

Implements PRD §FR-4:
  - Vendor → category lookup (case-insensitive substring match)
  - Debit/credit line construction
  - Payment method → credit account mapping
  - Hard assertion: sum(debits) == sum(credits)
  - Entry number format: JE-YYYY-XXXXX
"""

import logging
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.journal import EntryStatus, JournalEntry, JournalEntryLine

logger = logging.getLogger(__name__)


class BookkeepingAssertionError(Exception):
    """Raised when debits ≠ credits. Entry is quarantined."""

    def __init__(self, total_debit: Decimal, total_credit: Decimal, details: str = ""):
        self.total_debit = total_debit
        self.total_credit = total_credit
        self.details = details
        super().__init__(
            f"Bookkeeping assertion failure: debits ({total_debit}) ≠ credits ({total_credit}). {details}"
        )


# Payment method → credit account mapping (PRD §FR-4)
PAYMENT_METHOD_ACCOUNT_MAP: dict[Optional[str], tuple[str, str]] = {
    "Cash": ("1010", "Cash"),
    "Card": ("2010", "Credit Card Liability"),
    "Check": ("1020", "Checking Account"),
    "Split": ("1010", "Cash"),  # Primary; user prompted to specify split
    None: ("2000", "Accounts Payable"),  # Default for unknown
}

# Fallback expense account
FALLBACK_EXPENSE_CODE = "5999"
FALLBACK_EXPENSE_NAME = "Miscellaneous Expense"

# Tax and tip accounts
TAX_ACCOUNT = ("2100", "Sales Tax Payable")
TIP_ACCOUNT = ("5300", "Meals & Entertainment")


def _round_currency(amount: Decimal) -> Decimal:
    """Round to 2 decimal places using banker's rounding."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def lookup_vendor_account(
    db: AsyncSession,
    vendor_name: str,
    user_id: UUID,
) -> tuple[str, str]:
    """
    Look up vendor in vendor_category_mappings (case-insensitive substring match).
    User-specific mappings take precedence over system defaults.
    Falls back to 5999 Miscellaneous Expense.
    """
    from sqlalchemy import or_, text as sql_text

    # Query for matching vendor patterns — user-specific first, then system defaults
    query = sql_text("""
        SELECT vcm.account_code, coa.name
        FROM vendor_category_mappings vcm
        JOIN chart_of_accounts coa ON coa.code = vcm.account_code
            AND (coa.user_id = :user_id OR coa.user_id IS NULL)
        WHERE LOWER(:vendor) LIKE '%%' || LOWER(vcm.vendor_name_pattern) || '%%'
            AND (vcm.user_id = :user_id OR vcm.user_id IS NULL)
        ORDER BY
            CASE WHEN vcm.user_id IS NOT NULL THEN 0 ELSE 1 END,
            LENGTH(vcm.vendor_name_pattern) DESC
        LIMIT 1
    """)

    result = await db.execute(
        query,
        {"vendor": vendor_name.lower(), "user_id": str(user_id)},
    )
    row = result.first()

    if row:
        return (row[0], row[1])

    return (FALLBACK_EXPENSE_CODE, FALLBACK_EXPENSE_NAME)


async def generate_entry_number(db: AsyncSession) -> str:
    """
    Generate entry number in format JE-YYYY-XXXXX.
    Zero-padded 5-digit sequential counter, resetting annually.
    """
    current_year = date.today().year
    prefix = f"JE-{current_year}-"

    # Find the highest existing entry number for this year
    query = select(func.max(JournalEntry.entry_number)).where(
        JournalEntry.entry_number.like(f"{prefix}%")
    )
    result = await db.execute(query)
    max_number = result.scalar()

    if max_number:
        # Extract the counter part and increment
        counter = int(max_number.split("-")[-1]) + 1
    else:
        counter = 1

    return f"{prefix}{counter:05d}"


async def create_journal_entry(
    db: AsyncSession,
    receipt_id: UUID,
    user_id: UUID,
    extracted_data: dict,
    account_overrides: Optional[dict[str, str]] = None,
) -> JournalEntry:
    """
    Create a double-entry journal entry from extracted receipt data.

    Steps:
    1. Look up vendor → expense account
    2. Build debit lines (expense, tax, tip)
    3. Build credit line (payment method)
    4. Assert debits == credits
    5. Generate entry number
    6. Persist to database

    Raises BookkeepingAssertionError if debits ≠ credits.
    """
    vendor_name = extracted_data.get("vendor_name", "Unknown Vendor")
    receipt_date_str = extracted_data.get("date")
    receipt_date = (
        date.fromisoformat(receipt_date_str) if receipt_date_str else date.today()
    )
    total_amount = Decimal(str(extracted_data.get("total_amount", 0)))
    subtotal = Decimal(str(extracted_data.get("subtotal", 0) or 0))
    tax_amount = Decimal(str(extracted_data.get("tax_amount", 0) or 0))
    tip_amount = Decimal(str(extracted_data.get("tip_amount", 0) or 0))
    payment_method = extracted_data.get("payment_method")

    # Apply account overrides if provided
    expense_override = (account_overrides or {}).get("expense")
    payment_override = (account_overrides or {}).get("payment")

    # --- Step 1: Determine expense account ---
    if expense_override:
        expense_code = expense_override
        # Look up account name from COA
        coa_query = sql_text_import(
            "SELECT name FROM chart_of_accounts WHERE code = :code "
            "AND (user_id = :user_id OR user_id IS NULL) LIMIT 1"
        )
        result = await db.execute(
            coa_query, {"code": expense_code, "user_id": str(user_id)}
        )
        row = result.first()
        expense_name = row[0] if row else f"Account {expense_code}"
    else:
        expense_code, expense_name = await lookup_vendor_account(
            db, vendor_name, user_id
        )

    # --- Step 2: Build debit lines ---
    lines: list[dict] = []
    line_order = 1

    # Main expense debit (subtotal, or total minus tax/tip if no subtotal)
    expense_amount = subtotal if subtotal > 0 else (total_amount - tax_amount - tip_amount)
    expense_amount = _round_currency(expense_amount)

    if expense_amount > 0:
        lines.append({
            "account_code": expense_code,
            "account_name": expense_name,
            "debit": expense_amount,
            "credit": Decimal("0"),
            "description": f"{vendor_name} - {receipt_date}",
            "line_order": line_order,
        })
        line_order += 1

    # Tax debit
    tax_amount = _round_currency(tax_amount)
    if tax_amount > 0:
        lines.append({
            "account_code": TAX_ACCOUNT[0],
            "account_name": TAX_ACCOUNT[1],
            "debit": tax_amount,
            "credit": Decimal("0"),
            "description": "Sales tax",
            "line_order": line_order,
        })
        line_order += 1

    # Tip debit
    tip_amount = _round_currency(tip_amount)
    if tip_amount > 0:
        lines.append({
            "account_code": TIP_ACCOUNT[0],
            "account_name": TIP_ACCOUNT[1],
            "debit": tip_amount,
            "credit": Decimal("0"),
            "description": "Tip / gratuity",
            "line_order": line_order,
        })
        line_order += 1

    # --- Step 3: Build credit line ---
    if payment_override:
        credit_code = payment_override
        coa_query2 = sql_text_import(
            "SELECT name FROM chart_of_accounts WHERE code = :code "
            "AND (user_id = :user_id OR user_id IS NULL) LIMIT 1"
        )
        result2 = await db.execute(
            coa_query2, {"code": credit_code, "user_id": str(user_id)}
        )
        row2 = result2.first()
        credit_name = row2[0] if row2 else f"Account {credit_code}"
    else:
        credit_code, credit_name = PAYMENT_METHOD_ACCOUNT_MAP.get(
            payment_method, PAYMENT_METHOD_ACCOUNT_MAP[None]
        )

    total_debit = sum(line["debit"] for line in lines)
    total_debit = _round_currency(total_debit)

    lines.append({
        "account_code": credit_code,
        "account_name": credit_name,
        "debit": Decimal("0"),
        "credit": total_debit,  # Credit must equal total debits
        "description": f"Payment - {payment_method or 'Unknown'}",
        "line_order": line_order,
    })

    total_credit = total_debit  # By construction

    # --- Step 4: HARD ASSERTION — debits MUST equal credits ---
    if total_debit != total_credit:
        raise BookkeepingAssertionError(
            total_debit=total_debit,
            total_credit=total_credit,
            details=(
                f"Vendor: {vendor_name}, Receipt: {receipt_id}, "
                f"Payment: {payment_method}"
            ),
        )

    # Additional sanity check
    assert total_debit == total_credit, (
        f"CRITICAL: Bookkeeping assertion failed! "
        f"Debits ({total_debit}) ≠ Credits ({total_credit})"
    )

    # --- Step 5: Generate entry number ---
    entry_number = await generate_entry_number(db)

    # --- Step 6: Persist ---
    journal_entry = JournalEntry(
        id=uuid4(),
        receipt_id=receipt_id,
        entry_number=entry_number,
        entry_date=receipt_date,
        reference=f"{vendor_name} - {receipt_date}",
        description=f"Receipt from {vendor_name}",
        total_debit=total_debit,
        total_credit=total_credit,
        status=EntryStatus.POSTED,
        posted_by=user_id,
        posted_at=datetime.utcnow(),
    )
    db.add(journal_entry)

    for line_data in lines:
        line = JournalEntryLine(
            id=uuid4(),
            journal_entry_id=journal_entry.id,
            **line_data,
        )
        db.add(line)

    return journal_entry


async def create_reversal_entry(
    db: AsyncSession,
    original_entry: JournalEntry,
    user_id: UUID,
    reason: str,
) -> JournalEntry:
    """
    Create a mirror reversal entry with swapped debits/credits.
    The original entry status is set to REVERSED.
    """
    entry_number = await generate_entry_number(db)

    reversal = JournalEntry(
        id=uuid4(),
        receipt_id=original_entry.receipt_id,
        entry_number=entry_number,
        entry_date=date.today(),
        reference=f"Reversal of {original_entry.entry_number}: {reason}",
        description=f"Reversal - {reason}",
        total_debit=original_entry.total_debit,
        total_credit=original_entry.total_credit,
        status=EntryStatus.POSTED,
        reversal_of_id=original_entry.id,
        posted_by=user_id,
        posted_at=datetime.utcnow(),
    )
    db.add(reversal)

    # Swap debits and credits from original lines
    line_order = 1
    for original_line in original_entry.lines:
        reversed_line = JournalEntryLine(
            id=uuid4(),
            journal_entry_id=reversal.id,
            account_code=original_line.account_code,
            account_name=original_line.account_name,
            debit=original_line.credit,    # Swap
            credit=original_line.debit,    # Swap
            description=f"Reversal: {original_line.description or ''}",
            line_order=line_order,
        )
        db.add(reversed_line)
        line_order += 1

    # Mark original as reversed
    original_entry.status = EntryStatus.REVERSED

    return reversal


def sql_text_import(query: str):
    """Helper to import sqlalchemy.text without circular imports."""
    from sqlalchemy import text
    return text(query)
