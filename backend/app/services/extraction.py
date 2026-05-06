"""
Extraction service — orchestrates LLM call + Pydantic validation.
Handles the UPLOADED → EXTRACTING → EXTRACTED pipeline.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm_client import ExtractionParseError, llm_client
from app.models.receipt import Receipt, ReceiptStatus, validate_status_transition
from app.schemas.receipt import ReceiptExtraction

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Wraps extraction failures with context for error handling."""

    def __init__(self, receipt_id: UUID, raw_output: str = "", message: str = ""):
        self.receipt_id = receipt_id
        self.raw_output = raw_output
        super().__init__(message)


async def extract_receipt(
    db: AsyncSession,
    receipt: Receipt,
    image_bytes: bytes,
) -> Receipt:
    """
    Run LLM extraction on a receipt image and validate with Pydantic.

    State transitions:
      UPLOADED → EXTRACTING → EXTRACTED (success)
      UPLOADED → EXTRACTING → EXTRACTION_FAILED (LLM/parse failure)
      UPLOADED → EXTRACTING → VALIDATION_FAILED (Pydantic failure)
    """
    # Validate state transition
    if not validate_status_transition(
        ReceiptStatus(receipt.status), ReceiptStatus.EXTRACTING
    ):
        raise ValueError(
            f"Cannot extract receipt in status '{receipt.status}'. "
            f"Expected 'UPLOADED' or 'EXTRACTION_FAILED'."
        )

    # Transition to EXTRACTING
    receipt.status = ReceiptStatus.EXTRACTING
    await db.flush()

    raw_output = ""
    try:
        # Call LLM
        raw_output = await llm_client.extract_raw(image_bytes)
        receipt.raw_llm_output = raw_output

        # Parse JSON from LLM output
        from app.llm_client import parse_llm_output
        parsed_data = parse_llm_output(raw_output)

        # Validate with Pydantic
        extraction = ReceiptExtraction(**parsed_data)

        # Success — store validated data
        receipt.extracted_data = extraction.model_dump(mode="json")
        receipt.confidence_scores = extraction.confidence_scores.model_dump()
        receipt.status = ReceiptStatus.EXTRACTED
        receipt.extracted_at = datetime.utcnow()
        receipt.extraction_error = None

        logger.info(
            f"Receipt {receipt.id} extracted successfully. "
            f"Vendor: {extraction.vendor_name}, Total: {extraction.total_amount}"
        )

    except ExtractionParseError as e:
        # LLM output couldn't be parsed as JSON
        receipt.status = ReceiptStatus.EXTRACTION_FAILED
        receipt.raw_llm_output = e.raw_output
        receipt.extraction_error = str(e)
        logger.warning(f"Receipt {receipt.id} extraction parse failed: {e}")

    except ValueError as e:
        # Pydantic validation failed
        receipt.status = ReceiptStatus.VALIDATION_FAILED
        receipt.extraction_error = str(e)
        logger.warning(f"Receipt {receipt.id} validation failed: {e}")

    except Exception as e:
        # Network error, timeout, etc.
        receipt.status = ReceiptStatus.EXTRACTION_FAILED
        receipt.raw_llm_output = raw_output
        receipt.extraction_error = f"Extraction error: {type(e).__name__}: {str(e)}"
        logger.error(f"Receipt {receipt.id} extraction error: {e}", exc_info=True)

    return receipt
