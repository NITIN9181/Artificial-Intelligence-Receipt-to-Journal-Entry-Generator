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

from app.auth import get_current_user_id, require_preparer, require_reviewer
from app.config import settings
from app.database import get_db
from app.llm_client import llm_client
from app.models.receipt import Receipt, ReceiptStatus, validate_status_transition, ReviewComment
from app.models.user import User
from app.schemas.receipt import (
    JournalizeRequest,
    ReceiptCorrectRequest,
    ReceiptExtraction,
    ReceiptExtractResponse,
    ReceiptResponse,
    ReceiptUploadResponse,
    RejectReceiptRequest,
    ReviewCommentResponse,
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


@router.post("/bulk-upload", status_code=202)
async def bulk_upload_receipts(
    files: list[UploadFile] = File(...),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/receipts/bulk-upload — Upload up to 20 receipt images/PDFs."""
    if len(files) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 20 files allowed per bulk upload.",
        )

    # Validate file sizes and types first
    file_data_list = []
    for file in files:
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type for {file.filename}: {file.content_type}.",
            )
        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File {file.filename} exceeds {settings.max_upload_size_mb} MB limit.",
            )
        file_data_list.append((file, file_bytes))

    # Check daily limit
    today_start = datetime.combine(date.today(), datetime.min.time())
    count_query = select(func.count()).where(
        Receipt.user_id == user_id,
        Receipt.created_at >= today_start,
    )
    result = await db.execute(count_query)
    today_count = result.scalar() or 0

    if today_count + len(files) > settings.max_receipts_per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily receipt limit reached. You can only upload {settings.max_receipts_per_day - today_count} more today.",
        )

    batch_id = uuid4()
    
    # Upload to Supabase Storage in parallel
    import asyncio
    upload_tasks = []
    receipt_ids = []
    
    for file, file_bytes in file_data_list:
        receipt_id = uuid4()
        receipt_ids.append(receipt_id)
        filename = f"{receipt_id}_{file.filename}"
        upload_tasks.append(
            upload_receipt_image(
                file_bytes=file_bytes,
                filename=filename,
                user_id=UUID(user_id),
                content_type=file.content_type,
            )
        )
        
    storage_paths = await asyncio.gather(*upload_tasks)
    
    # Create receipt records
    receipt_responses = []
    for (file, file_bytes), receipt_id, storage_path in zip(file_data_list, receipt_ids, storage_paths):
        receipt = Receipt(
            id=receipt_id,
            user_id=UUID(user_id),
            image_url=storage_path,
            original_filename=file.filename,
            mime_type=file.content_type,
            file_size_bytes=len(file_bytes),
            status=ReceiptStatus.UPLOADED,
            batch_id=batch_id,
        )
        db.add(receipt)
        receipt_responses.append({
            "id": str(receipt_id),
            "filename": file.filename,
            "status": "UPLOADED"
        })
        
    await db.flush()
    await db.commit()

    return {
        "batch_id": str(batch_id),
        "receipts": receipt_responses,
        "total": len(files),
        "message": f"{len(files)} receipts uploaded. Trigger extraction on each receipt individually or use /bulk-extract."
    }


from pydantic import BaseModel

class BulkExtractRequest(BaseModel):
    batch_id: str

@router.post("/bulk-extract", status_code=202)
async def bulk_extract_receipts(
    body: BulkExtractRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """POST /api/v1/receipts/bulk-extract — Trigger sequential extraction for a batch."""
    from app.services.bulk_processor import get_receipts_by_batch, process_batch_sequentially
    
    receipts = await get_receipts_by_batch(body.batch_id, db)
    if not receipts:
        raise HTTPException(status_code=404, detail="Batch not found or empty")
        
    # Verify ownership
    if str(receipts[0].user_id) != user_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    # The background task will need its own DB session or we need to ensure the session stays open
    # Instead, background tasks running SQLAlchemy need a new session context. 
    # For now, we will pass the batch_id and create a new session inside the task if needed,
    # but process_batch_sequentially can just use the provided session if we manage it carefully.
    # Actually, background_tasks in FastAPI close the injected session. We must instantiate a new one.
    from app.database import async_session_maker
    
    async def process_with_session(b_id: str):
        async with async_session_maker() as session:
            await process_batch_sequentially(b_id, session)
            
    background_tasks.add_task(process_with_session, body.batch_id)
    return {"message": "Bulk extraction started"}


@router.get("/batch/{batch_id}", status_code=200)
async def get_batch_status(
    batch_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """GET /api/v1/receipts/batch/{batch_id} — Get aggregated batch status."""
    from app.services.bulk_processor import get_receipts_by_batch
    receipts = await get_receipts_by_batch(batch_id, db)
    if not receipts:
        raise HTTPException(status_code=404, detail="Batch not found")
        
    if str(receipts[0].user_id) != user_id:
        raise HTTPException(status_code=404, detail="Batch not found")

    status_counts = {
        "UPLOADED": 0,
        "EXTRACTING": 0,
        "EXTRACTED": 0,
        "EXTRACTION_FAILED": 0,
        "POSTED": 0,
        "VALIDATION_FAILED": 0,
        "REVIEWED": 0,
        "REJECTED": 0,
    }
    
    for r in receipts:
        status_val = r.status.value if isinstance(r.status, ReceiptStatus) else r.status
        if status_val in status_counts:
            status_counts[status_val] += 1
            
    return {
        "batch_id": batch_id,
        "total": len(receipts),
        "uploaded": status_counts["UPLOADED"],
        "extracting": status_counts["EXTRACTING"],
        "extracted": status_counts["EXTRACTED"] + status_counts["VALIDATION_FAILED"] + status_counts["REVIEWED"],
        "failed": status_counts["EXTRACTION_FAILED"],
        "posted": status_counts["POSTED"]
    }



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

    # Download image before returning (fast — from Supabase storage)
    image_bytes = await download_receipt_image(receipt.image_url)

    # Mark as EXTRACTING immediately so the UI shows progress
    receipt.status = ReceiptStatus.EXTRACTING
    await db.commit()  # ✅ Commit the status change so it's visible to other requests

    # Run LLM extraction in background with its own DB session
    from app.database import async_session_maker

    async def run_extraction(r_id: UUID, img_bytes: bytes):
        async with async_session_maker() as session:
            r = await session.get(Receipt, r_id)
            if r:
                try:
                    await extract_receipt(session, r, img_bytes)
                    await session.commit()
                    logger.info(f"Background extraction completed for receipt {r_id}")
                except Exception as e:
                    logger.error(f"Background extraction failed for receipt {r_id}: {e}", exc_info=True)
                    r.status = ReceiptStatus.EXTRACTION_FAILED
                    r.extraction_error = f"Extraction error: {type(e).__name__}: {str(e)}"
                    await session.commit()

    background_tasks.add_task(run_extraction, receipt_id, image_bytes)

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
        # QUARANTINE — never post unbalanced entries (PRD §FR-4, §FR-5)
        logger.error(f"Bookkeeping assertion failure for receipt {receipt_id}: {e}")
        
        # Set receipt status to QUARANTINED
        old_status = receipt.status.value if isinstance(receipt.status, ReceiptStatus) else receipt.status
        receipt.status = ReceiptStatus.QUARANTINED
        
        # Write to audit_logs table
        from sqlalchemy import text
        audit_query = text("""
            INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values, performed_by)
            VALUES ('receipts', :record_id, 'UPDATE', :old_values, :new_values, :performed_by)
        """)
        
        await db.execute(
            audit_query,
            {
                "record_id": str(receipt_id),
                "old_values": {"status": old_status},
                "new_values": {
                    "status": "QUARANTINED",
                    "error": f"Bookkeeping assertion failed: debits ({e.total_debit}) != credits ({e.total_credit})",
                    "details": e.details
                },
                "performed_by": user_id,
            }
        )
        
        await db.commit()
        
        # Return HTTP 422 with detailed error
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Bookkeeping assertion failed",
                "message": "This receipt has been quarantined and will not enter the ledger. Contact an administrator.",
                "receipt_id": str(receipt_id),
                "status": "QUARANTINED",
                "total_debit": str(e.total_debit),
                "total_credit": str(e.total_credit),
            },
        )


# --- Phase 3: Approval Workflow Endpoints ---

@router.post("/{receipt_id}/submit", response_model=ReceiptResponse)
async def submit_for_review(
    receipt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_preparer)
):
    """
    POST /api/v1/receipts/{id}/submit — Submit receipt for reviewer approval.
    
    Transition: REVIEWED → PENDING_REVIEW
    Role: PREPARER (own receipts only)
    """
    receipt = await db.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Verify ownership
    if receipt.user_id != user.id:
        raise HTTPException(status_code=403, detail="Can only submit your own receipts")
    
    # Validate state transition
    current_status = ReceiptStatus(receipt.status)
    if not validate_status_transition(current_status, ReceiptStatus.PENDING_REVIEW):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot submit receipt in status '{receipt.status}'. Must be REVIEWED."
        )
    
    # Update status
    old_status = receipt.status.value if isinstance(receipt.status, ReceiptStatus) else receipt.status
    receipt.status = ReceiptStatus.PENDING_REVIEW
    
    # Audit log
    from sqlalchemy import text
    audit_query = text("""
        INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values, performed_by)
        VALUES ('receipts', :record_id, 'UPDATE', :old_values, :new_values, :performed_by)
    """)
    await db.execute(
        audit_query,
        {
            "record_id": str(receipt_id),
            "old_values": {"status": old_status},
            "new_values": {"status": "PENDING_REVIEW"},
            "performed_by": str(user.id),
        }
    )
    
    await db.commit()
    
    # Return response
    signed_url = await get_signed_url(receipt.image_url)
    return ReceiptResponse(
        id=receipt.id,
        status=receipt.status.value,
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


@router.post("/{receipt_id}/approve", response_model=ReceiptResponse)
async def approve_receipt(
    receipt_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_reviewer)
):
    """
    POST /api/v1/receipts/{id}/approve — Approve receipt (reviewer).
    
    Transition: PENDING_REVIEW → REVIEWED
    Role: REVIEWER or ADMIN
    """
    receipt = await db.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Validate state transition
    current_status = ReceiptStatus(receipt.status)
    if not validate_status_transition(current_status, ReceiptStatus.REVIEWED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot approve receipt in status '{receipt.status}'. Must be PENDING_REVIEW."
        )
    
    # Update status
    old_status = receipt.status.value if isinstance(receipt.status, ReceiptStatus) else receipt.status
    receipt.status = ReceiptStatus.REVIEWED
    
    # Add review comment
    comment = ReviewComment(
        receipt_id=receipt.id,
        reviewer_id=user.id,
        comment="Approved",
        action="APPROVED"
    )
    db.add(comment)
    
    # Audit log
    from sqlalchemy import text
    audit_query = text("""
        INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values, performed_by)
        VALUES ('receipts', :record_id, 'UPDATE', :old_values, :new_values, :performed_by)
    """)
    await db.execute(
        audit_query,
        {
            "record_id": str(receipt_id),
            "old_values": {"status": old_status},
            "new_values": {"status": "REVIEWED", "action": "APPROVED"},
            "performed_by": str(user.id),
        }
    )
    
    await db.commit()
    
    # Return response
    signed_url = await get_signed_url(receipt.image_url)
    return ReceiptResponse(
        id=receipt.id,
        status=receipt.status.value,
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


@router.post("/{receipt_id}/reject", response_model=ReceiptResponse)
async def reject_receipt(
    receipt_id: UUID,
    data: RejectReceiptRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_reviewer)
):
    """
    POST /api/v1/receipts/{id}/reject — Reject receipt with comment (reviewer).
    
    Transition: PENDING_REVIEW → REJECTED
    Role: REVIEWER or ADMIN
    """
    receipt = await db.get(Receipt, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Validate state transition
    current_status = ReceiptStatus(receipt.status)
    if not validate_status_transition(current_status, ReceiptStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reject receipt in status '{receipt.status}'. Must be PENDING_REVIEW."
        )
    
    # Update status
    old_status = receipt.status.value if isinstance(receipt.status, ReceiptStatus) else receipt.status
    receipt.status = ReceiptStatus.REJECTED
    
    # Add review comment
    comment = ReviewComment(
        receipt_id=receipt.id,
        reviewer_id=user.id,
        comment=data.comment,
        action="REJECTED"
    )
    db.add(comment)
    
    # Audit log
    from sqlalchemy import text
    audit_query = text("""
        INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values, performed_by)
        VALUES ('receipts', :record_id, 'UPDATE', :old_values, :new_values, :performed_by)
    """)
    await db.execute(
        audit_query,
        {
            "record_id": str(receipt_id),
            "old_values": {"status": old_status},
            "new_values": {"status": "REJECTED", "comment": data.comment, "action": "REJECTED"},
            "performed_by": str(user.id),
        }
    )
    
    await db.commit()
    
    # Return response
    signed_url = await get_signed_url(receipt.image_url)
    return ReceiptResponse(
        id=receipt.id,
        status=receipt.status.value,
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


@router.get("/pending-review", status_code=200)
async def list_pending_review(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_reviewer),
    skip: int = 0,
    limit: int = 25
):
    """
    GET /api/v1/receipts/pending-review — List all receipts awaiting review.
    
    Returns: All receipts with status = PENDING_REVIEW (any user)
    Role: REVIEWER or ADMIN
    """
    result = await db.execute(
        select(Receipt)
        .where(Receipt.status == ReceiptStatus.PENDING_REVIEW)
        .order_by(Receipt.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    receipts = result.scalars().all()
    
    items = []
    for r in receipts:
        signed_url = await get_signed_url(r.image_url)
        items.append({
            "id": str(r.id),
            "user_id": str(r.user_id),
            "status": r.status.value if isinstance(r.status, ReceiptStatus) else r.status,
            "image_url": signed_url,
            "original_filename": r.original_filename,
            "extracted_data": r.extracted_data,
            "confidence_scores": r.confidence_scores,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })
    
    return {"items": items, "total": len(items)}


@router.get("/{receipt_id}/comments", response_model=list[ReviewCommentResponse])
async def get_review_comments(
    receipt_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    GET /api/v1/receipts/{id}/comments — Get all review comments for a receipt.
    
    Returns: List of review comments with reviewer info
    """
    # Verify receipt exists and user has access
    receipt = await db.get(Receipt, receipt_id)
    if not receipt or str(receipt.user_id) != user_id:
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    # Fetch comments
    result = await db.execute(
        select(ReviewComment)
        .where(ReviewComment.receipt_id == receipt_id)
        .order_by(ReviewComment.created_at.desc())
    )
    comments = result.scalars().all()
    
    return comments
