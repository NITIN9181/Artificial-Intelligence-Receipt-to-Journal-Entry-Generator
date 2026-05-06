"""
Receipt API endpoints — PRD §9.
All endpoints require authentication except where noted.
State machine enforcement per PRD §FR-5.
"""

import logging
from datetime import datetime, date, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_id
from app.config import settings
from app.database import get_db
from app.llm_client import llm_client
from app.models.receipt import Receipt, ReceiptStatus, validate_status_transition
from app.schemas.receipt import (
    JournalizeRequest,
    ReceiptCorrectRequest,
    ReceiptExtraction,
    ReceiptExtractResponse,
    ReceiptResponse,
    ReceiptUploadResponse,
)
from app.services.extraction import extract_receipt
from app.services.storage import download_receipt_image, get_signed_url, upload_receipt_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/receipts", tags=["receipts"])

ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/heic", "image/heif",
    "application/pdf",
}
MAX_FILE_SIZE = settings.max_upload_size_mb * 1024 * 1024


@router.post("/upload", response_model=ReceiptUploadResponse, status_code=201)
async def upload_receipt(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/receipts/upload — Upload a receipt image or PDF."""
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Allowed: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    # Read and validate file size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {len(file_bytes)} bytes. Maximum: {MAX_FILE_SIZE} bytes ({settings.max_upload_size_mb} MB)",
        )

    # Check daily limit
    today_start = datetime.combine(date.today(), datetime.min.time())
    count_query = select(func.count()).where(
        Receipt.user_id == user_id,
        Receipt.created_at >= today_start,
    )
    result = await db.execute(count_query)
    today_count = result.scalar() or 0

    if today_count >= settings.max_receipts_per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily receipt limit reached ({settings.max_receipts_per_day}). Try again tomorrow.",
        )

    # Upload to Supabase Storage
    receipt_id = uuid4()
    filename = f"{receipt_id}_{file.filename}"
    storage_path = await upload_receipt_image(
        file_bytes=file_bytes,
        filename=filename,
        user_id=UUID(user_id),
        content_type=file.content_type,
    )

    # Create receipt record
    receipt = Receipt(
        id=receipt_id,
        user_id=UUID(user_id),
        image_url=storage_path,
        original_filename=file.filename,
        mime_type=file.content_type,
        file_size_bytes=len(file_bytes),
        status=ReceiptStatus.UPLOADED,
    )
    db.add(receipt)
    await db.flush()

    # Generate signed URL for response
    signed_url = await get_signed_url(storage_path)

    return ReceiptUploadResponse(
        id=receipt.id,
        status=receipt.status.value,
        image_url=signed_url,
        created_at=receipt.created_at,
    )


@router.get("", status_code=200)
async def list_receipts(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """GET /api/v1/receipts — List all receipts for the current user."""
    query = select(Receipt).where(Receipt.user_id == user_id).order_by(Receipt.created_at.desc())

    if status_filter:
        query = query.where(Receipt.status == status_filter)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    receipts = result.scalars().all()

    items = []
    for r in receipts:
        signed_url = await get_signed_url(r.image_url)
        items.append({
            "id": str(r.id),
            "status": r.status.value if isinstance(r.status, ReceiptStatus) else r.status,
            "image_url": signed_url,
            "original_filename": r.original_filename,
            "extracted_data": r.extracted_data,
            "confidence_scores": r.confidence_scores,
            "extraction_error": r.extraction_error,
            "extracted_at": r.extracted_at.isoformat() if r.extracted_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })

    return {"items": items, "total": len(items)}

@router.post("/{receipt_id}/extract", response_model=ReceiptExtractResponse, status_code=202)
async def trigger_extraction(
    receipt_id: UUID,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/receipts/{id}/extract — Trigger async LLM extraction."""
    receipt = await db.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    if str(receipt.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Validate state transition
    current_status = ReceiptStatus(receipt.status)
    if current_status == ReceiptStatus.EXTRACTING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Extraction already in progress",
        )

    if not validate_status_transition(current_status, ReceiptStatus.EXTRACTING):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot extract receipt in status '{receipt.status}'. Expected 'UPLOADED' or 'EXTRACTION_FAILED'.",
        )

    # Download image and trigger extraction in background
    image_bytes = await download_receipt_image(receipt.image_url)

    # Run extraction (using background task for async processing)
    await extract_receipt(db, receipt, image_bytes)
    await db.flush()

    return ReceiptExtractResponse(
        id=receipt.id,
        status=receipt.status.value if isinstance(receipt.status, ReceiptStatus) else receipt.status,
        queue_position=llm_client.queue_position,
    )


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/receipts/{id} — Retrieve receipt with extracted data."""
    receipt = await db.get(Receipt, receipt_id)
    if not receipt or str(receipt.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Generate fresh signed URL
    signed_url = await get_signed_url(receipt.image_url)

    return ReceiptResponse(
        id=receipt.id,
        status=receipt.status.value if isinstance(receipt.status, ReceiptStatus) else receipt.status,
        image_url=signed_url,
        original_filename=receipt.original_filename,
        mime_type=receipt.mime_type,
        file_size_bytes=receipt.file_size_bytes,
        extracted_data=receipt.extracted_data,
        confidence_scores=receipt.confidence_scores,
        extraction_error=receipt.extraction_error,
        extracted_at=receipt.extracted_at,
        reviewed_at=receipt.reviewed_at,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
    )


@router.put("/{receipt_id}/correct", response_model=ReceiptResponse)
async def correct_receipt(
    receipt_id: UUID,
    corrections: ReceiptCorrectRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """PUT /api/v1/receipts/{id}/correct — Submit human corrections."""
    receipt = await db.get(Receipt, receipt_id)
    if not receipt or str(receipt.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Receipt not found")

    current_status = ReceiptStatus(receipt.status)
    if current_status == ReceiptStatus.POSTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot correct a posted receipt",
        )

    # Merge corrections into extracted_data
    current_data = receipt.extracted_data or {}
    correction_dict = corrections.model_dump(exclude_none=True)
    current_data.update(correction_dict)

    # Re-validate with Pydantic
    try:
        validated = ReceiptExtraction(**current_data)
        receipt.extracted_data = validated.model_dump(mode="json")
        receipt.confidence_scores = validated.confidence_scores.model_dump()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed after correction: {str(e)}",
        )

    # Transition to REVIEWED
    if current_status in (ReceiptStatus.EXTRACTED, ReceiptStatus.VALIDATION_FAILED):
        receipt.status = ReceiptStatus.REVIEWED
        receipt.reviewed_at = datetime.now(timezone.utc)

    signed_url = await get_signed_url(receipt.image_url)

    return ReceiptResponse(
        id=receipt.id,
        status=receipt.status.value if isinstance(receipt.status, ReceiptStatus) else receipt.status,
        image_url=signed_url,
        original_filename=receipt.original_filename,
        mime_type=receipt.mime_type,
        file_size_bytes=receipt.file_size_bytes,
        extracted_data=receipt.extracted_data,
        confidence_scores=receipt.confidence_scores,
        extraction_error=receipt.extraction_error,
        extracted_at=receipt.extracted_at,
        reviewed_at=receipt.reviewed_at,
        created_at=receipt.created_at,
        updated_at=receipt.updated_at,
    )


@router.post("/{receipt_id}/journalize", status_code=201)
async def journalize_receipt(
    receipt_id: UUID,
    body: JournalizeRequest = JournalizeRequest(),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/receipts/{id}/journalize — Create journal entry from receipt."""
    from app.services.bookkeeping import (
        BookkeepingAssertionError,
        create_journal_entry,
    )

    receipt = await db.get(Receipt, receipt_id)
    if not receipt or str(receipt.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Receipt not found")

    current_status = ReceiptStatus(receipt.status)

    # Must be REVIEWED to journalize
    if current_status != ReceiptStatus.REVIEWED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Receipt must be in REVIEWED status to journalize. Current: {receipt.status}",
        )

    # Check if already journalized
    from sqlalchemy import exists
    already_exists = await db.execute(
        select(exists().where(
            __import__("app.models.journal", fromlist=["JournalEntry"]).JournalEntry.receipt_id == receipt_id
        ))
    )
    # Simpler approach:
    from app.models.journal import JournalEntry
    existing = await db.execute(
        select(JournalEntry).where(JournalEntry.receipt_id == receipt_id)
    )
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Receipt already has a journal entry",
        )

    try:
        journal_entry = await create_journal_entry(
            db=db,
            receipt_id=receipt_id,
            user_id=UUID(user_id),
            extracted_data=receipt.extracted_data,
            account_overrides=body.account_overrides,
        )

        # Transition receipt to POSTED
        receipt.status = ReceiptStatus.POSTED

        return {
            "journal_entry_id": str(journal_entry.id),
            "entry_number": journal_entry.entry_number,
            "status": journal_entry.status.value,
            "total_debit": float(journal_entry.total_debit),
            "total_credit": float(journal_entry.total_credit),
        }

    except BookkeepingAssertionError as e:
        # QUARANTINE — never post unbalanced entries
        from app.models.journal import EntryStatus
        logger.error(f"Bookkeeping assertion failure for receipt {receipt_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Journal entry balance assertion failed: {str(e)}",
        )
