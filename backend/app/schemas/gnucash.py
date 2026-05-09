"""
Pydantic schemas for GnuCash export (Phase 3).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


# Export format type
ExportFormat = Literal["xml", "csv", "sqlite"]


class GnuCashMappingCreate(BaseModel):
    """Schema for creating a new GnuCash account mapping."""
    internal_account_code: str = Field(..., min_length=1, max_length=50)
    gnucash_account_path: str = Field(..., min_length=1, max_length=255)


class GnuCashMappingUpdate(BaseModel):
    """Schema for updating a GnuCash account mapping."""
    gnucash_account_path: str = Field(..., min_length=1, max_length=255)


class GnuCashMappingResponse(BaseModel):
    """Schema for GnuCash mapping response."""
    id: UUID
    user_id: UUID
    internal_account_code: str
    gnucash_account_path: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExportRequest(BaseModel):
    """Schema for exporting journal entries."""
    entry_ids: list[UUID] = Field(..., min_items=1)
    format: ExportFormat = "xml"
