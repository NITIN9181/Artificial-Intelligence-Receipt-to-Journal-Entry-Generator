"""
Supabase Storage service — upload receipt images and generate signed URLs.
Uses signed URLs with 1-hour expiry per PRD §12 PII protection rules.
"""

import logging
from typing import Optional
from uuid import UUID

from app.config import settings

logger = logging.getLogger(__name__)

BUCKET_NAME = "receipts"
SIGNED_URL_EXPIRY = 3600  # 1 hour in seconds


async def upload_receipt_image(
    file_bytes: bytes,
    filename: str,
    user_id: UUID,
    content_type: str = "image/jpeg",
) -> str:
    """
    Upload a receipt image to Supabase Storage.
    Returns the storage path (not a public URL — use get_signed_url for access).
    """
    from supabase import create_client

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )

    # Organize by user ID
    storage_path = f"{user_id}/{filename}"

    try:
        supabase.storage.from_(BUCKET_NAME).upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": content_type,
                "upsert": "true",
            },
        )
        logger.info(f"Uploaded receipt image: {storage_path}")
        return storage_path

    except Exception as e:
        logger.error(f"Failed to upload receipt image: {e}")
        raise


async def get_signed_url(storage_path: str) -> str:
    """
    Generate a signed URL for a receipt image with 1-hour expiry.
    Per PRD §12: "Supabase Storage URLs must use signed URLs with 1-hour expiry."
    """
    from supabase import create_client

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )

    try:
        response = supabase.storage.from_(BUCKET_NAME).create_signed_url(
            path=storage_path,
            expires_in=SIGNED_URL_EXPIRY,
        )
        return response["signedURL"]

    except Exception as e:
        logger.error(f"Failed to generate signed URL for {storage_path}: {e}")
        raise


async def download_receipt_image(storage_path: str) -> bytes:
    """Download a receipt image from Supabase Storage."""
    from supabase import create_client

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )

    try:
        response = supabase.storage.from_(BUCKET_NAME).download(storage_path)
        return response

    except Exception as e:
        logger.error(f"Failed to download receipt image {storage_path}: {e}")
        raise


async def delete_receipt_image(storage_path: str) -> None:
    """Delete a receipt image from Supabase Storage."""
    from supabase import create_client

    supabase = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )

    try:
        supabase.storage.from_(BUCKET_NAME).remove([storage_path])
        logger.info(f"Deleted receipt image: {storage_path}")

    except Exception as e:
        logger.error(f"Failed to delete receipt image {storage_path}: {e}")
        raise
