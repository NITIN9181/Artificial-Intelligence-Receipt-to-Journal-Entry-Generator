"""
Pydantic v2 schemas for journal entries and journal entry lines.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JournalEntryLineResponse(BaseModel):
    """A single journal entry line (debit or credit)."""
    id: UUID
    account_code: str
    account_name: str
    debit: Decimal = Field(default=Decimal("0"))
    credit: Decimal = Field(default=Decimal("0"))
    description: Optional[str] = None
    line_order: int


class JournalEntryResponse(BaseModel):
    """Full journal entry response."""
    id: UUID
    receipt_id: UUID
    entry_number: str
    entry_date: date
    reference: Optional[str] = None
    description: Optional[str] = None
    total_debit: Decimal
    total_credit: Decimal
    status: str
    reversal_of_id: Optional[UUID] = None
    posted_by: Optional[UUID] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
    lines: list[JournalEntryLineResponse] = Field(default_factory=list)
    receipt_image_url: Optional[str] = None


class JournalEntryListResponse(BaseModel):
    """Paginated list of journal entries."""
    data: list[JournalEntryResponse]
    pagination: dict


class JournalEntryCreateResponse(BaseModel):
    """Response for POST /api/v1/receipts/{id}/journalize"""
    journal_entry_id: UUID
    entry_number: str
    status: str
    total_debit: Decimal
    total_credit: Decimal


class JournalEntryReverseRequest(BaseModel):
    """Request for DELETE /api/v1/journal-entries/{id}/reverse"""
    reason: str = Field(..., min_length=1, max_length=500)
