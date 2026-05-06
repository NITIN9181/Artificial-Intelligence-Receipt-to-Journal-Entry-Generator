import asyncio
import logging
from typing import List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt import Receipt, ReceiptStatus
from app.services.extraction import extract_receipt
from app.llm_client import llm_client

logger = logging.getLogger(__name__)


async def get_receipts_by_batch(batch_id: str, db: AsyncSession) -> List[Receipt]:
    query = select(Receipt).where(Receipt.batch_id == UUID(batch_id)).order_by(Receipt.created_at.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def trigger_single_extraction(receipt_id: UUID, db: AsyncSession):
    """Trigger single extraction, mimicking the regular extract endpoint logic."""
    from app.services.storage import download_receipt_image
    
    receipt = await db.get(Receipt, receipt_id)
    if not receipt:
        return
        
    current_status = ReceiptStatus(receipt.status)
    if current_status not in [ReceiptStatus.UPLOADED, ReceiptStatus.EXTRACTION_FAILED]:
        return

    try:
        image_bytes = await download_receipt_image(receipt.image_url)
        await extract_receipt(db, receipt, image_bytes)
        await db.commit()
    except Exception as e:
        logger.error(f"Failed to extract receipt {receipt_id} in batch: {e}")
        receipt.status = ReceiptStatus.EXTRACTION_FAILED
        receipt.extraction_error = str(e)
        await db.commit()


async def process_batch_sequentially(batch_id: str, db: AsyncSession):
    """
    Background task to process all receipts in a batch sequentially.
    """
    logger.info(f"Starting sequential processing for batch {batch_id}")
    receipts = await get_receipts_by_batch(batch_id, db)
    
    for receipt in receipts:
        await trigger_single_extraction(receipt.id, db)
        
    logger.info(f"Completed sequential processing for batch {batch_id}")
