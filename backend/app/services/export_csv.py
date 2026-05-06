import csv
import io
from typing import AsyncGenerator
from datetime import date as date_type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi.responses import StreamingResponse

from app.models.journal import JournalEntry
from app.models.receipt import Receipt


async def stream_journal_lines(filters: dict, db: AsyncSession, user_id: str) -> AsyncGenerator[list, None]:
    """Yields rows for the CSV export one by one."""
    
    query = (
        select(JournalEntry)
        .join(Receipt, JournalEntry.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .options(selectinload(JournalEntry.lines))
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
    )
    
    if filters.get("date_from"):
        query = query.where(JournalEntry.entry_date >= filters["date_from"])
    if filters.get("date_to"):
        query = query.where(JournalEntry.entry_date <= filters["date_to"])
    if filters.get("vendor"):
        query = query.where(JournalEntry.reference.ilike(f"%{filters['vendor']}%"))
    if filters.get("status"):
        query = query.where(JournalEntry.status == filters["status"])

    # We yield results row by row
    result = await db.stream(query)
    async for row in result.scalars():
        entry: JournalEntry = row
        status_str = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
        posted_at_str = entry.posted_at.isoformat() if entry.posted_at else ""
        
        for line in (entry.lines or []):
            yield [
                entry.entry_number,
                entry.entry_date.isoformat() if entry.entry_date else "",
                entry.reference or "",
                entry.reference or "",  # Vendor name is often the reference
                "Operating Expense",    # Category is not natively on JournalEntry, would need mapping or pull from receipt
                line.account_code,
                line.account_name,
                f"{line.debit:.2f}" if line.debit else "0.00",
                f"{line.credit:.2f}" if line.credit else "0.00",
                status_str,
                str(entry.posted_by) if entry.posted_by else "",
                posted_at_str,
            ]


async def generate_csv_stream(filters: dict, db: AsyncSession, user_id: str):
    async def iter_rows():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "Entry Number", "Date", "Reference", "Vendor",
            "Category", "Account Code", "Account Name",
            "Debit", "Credit", "Status", "Posted By", "Posted At"
        ])
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        async for line_row in stream_journal_lines(filters, db, user_id):
            writer.writerow(line_row)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        iter_rows(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=journal_entries.csv"}
    )
