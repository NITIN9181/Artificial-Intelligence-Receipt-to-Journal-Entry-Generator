"""
Journal entry API endpoints — PRD §9.
Immutability rules: POSTED entries cannot be updated or deleted. Only reversals.
"""

import logging
from datetime import date as date_type
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_user_id
from app.database import get_db
from app.models.journal import EntryStatus, JournalEntry, JournalEntryLine
from app.models.receipt import Receipt
from app.schemas.journal import (
    JournalEntryLineResponse,
    JournalEntryListResponse,
    JournalEntryResponse,
    JournalEntryReverseRequest,
)
from app.services.bookkeeping import create_reversal_entry
from app.services.storage import get_signed_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/journal-entries", tags=["journal-entries"])


def _entry_to_response(entry: JournalEntry, image_url: Optional[str] = None) -> dict:
    """Convert a JournalEntry ORM object to response dict."""
    lines = []
    for line in (entry.lines or []):
        lines.append(JournalEntryLineResponse(
            id=line.id,
            account_code=line.account_code,
            account_name=line.account_name,
            debit=line.debit,
            credit=line.credit,
            description=line.description,
            line_order=line.line_order,
        ))

    return JournalEntryResponse(
        id=entry.id,
        receipt_id=entry.receipt_id,
        entry_number=entry.entry_number,
        entry_date=entry.entry_date,
        reference=entry.reference,
        description=entry.description,
        total_debit=entry.total_debit,
        total_credit=entry.total_credit,
        status=entry.status.value if isinstance(entry.status, EntryStatus) else entry.status,
        reversal_of_id=entry.reversal_of_id,
        posted_by=entry.posted_by,
        posted_at=entry.posted_at,
        created_at=entry.created_at,
        lines=lines,
        receipt_image_url=image_url,
    )


@router.get("", response_model=JournalEntryListResponse)
async def list_journal_entries(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=100),
    date_from: Optional[date_type] = None,
    date_to: Optional[date_type] = None,
    vendor: Optional[str] = None,
    category: Optional[str] = None,
    entry_status: Optional[str] = Query(default=None, alias="status"),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/journal-entries — Paginated, filterable list."""
    # Base query: only entries linked to user's receipts
    # Exclude QUARANTINED from standard list
    query = (
        select(JournalEntry)
        .join(Receipt, JournalEntry.receipt_id == Receipt.id)
        .where(Receipt.user_id == user_id)
        .where(JournalEntry.status != EntryStatus.QUARANTINED)
        .options(selectinload(JournalEntry.lines))
    )

    # Apply filters
    if date_from:
        query = query.where(JournalEntry.entry_date >= date_from)
    if date_to:
        query = query.where(JournalEntry.entry_date <= date_to)
    if vendor:
        query = query.where(JournalEntry.reference.ilike(f"%{vendor}%"))
    if entry_status:
        try:
            status_enum = EntryStatus(entry_status)
            query = query.where(JournalEntry.status == status_enum)
        except ValueError:
            pass

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    query = query.order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    entries = result.scalars().all()

    data = [_entry_to_response(entry) for entry in entries]

    return JournalEntryListResponse(
        data=data,
        pagination={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page if total > 0 else 0,
        },
    )


@router.get("/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/journal-entries/{id} — Full entry + lines + receipt image URL."""
    query = (
        select(JournalEntry)
        .join(Receipt, JournalEntry.receipt_id == Receipt.id)
        .where(JournalEntry.id == entry_id)
        .where(Receipt.user_id == user_id)
        .options(selectinload(JournalEntry.lines))
    )
    result = await db.execute(query)
    entry = result.scalars().first()

    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    # Get receipt image URL
    receipt = await db.get(Receipt, entry.receipt_id)
    image_url = None
    if receipt:
        try:
            image_url = await get_signed_url(receipt.image_url)
        except Exception:
            pass

    return _entry_to_response(entry, image_url)


@router.delete("/{entry_id}/reverse", status_code=201)
async def reverse_journal_entry(
    entry_id: UUID,
    body: JournalEntryReverseRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    DELETE /api/v1/journal-entries/{id}/reverse
    Creates a mirror entry; does NOT delete the original.
    """
    query = (
        select(JournalEntry)
        .join(Receipt, JournalEntry.receipt_id == Receipt.id)
        .where(JournalEntry.id == entry_id)
        .where(Receipt.user_id == user_id)
        .options(selectinload(JournalEntry.lines))
    )
    result = await db.execute(query)
    entry = result.scalars().first()

    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    current_status = EntryStatus(entry.status) if isinstance(entry.status, str) else entry.status

    if current_status != EntryStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Only POSTED entries can be reversed. Current status: {entry.status}",
        )

    if entry.reversal_of_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This entry is itself a reversal and cannot be reversed again",
        )

    # Check if already reversed
    check_query = select(JournalEntry).where(JournalEntry.reversal_of_id == entry_id)
    check_result = await db.execute(check_query)
    if check_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This entry has already been reversed",
        )

    reversal = await create_reversal_entry(
        db=db,
        original_entry=entry,
        user_id=UUID(user_id),
        reason=body.reason,
    )

    return _entry_to_response(reversal)
