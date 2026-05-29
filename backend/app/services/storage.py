"""
Local filesystem storage service — replaces Supabase Storage.
Files are saved to backend/uploads/ and served via a static route.
"""

import logging
import os
from pathlib import Path
from uuid import UUID

logger = logging.getLogger(__name__)

# Directory where uploaded files are stored
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Base URL the frontend uses to reach the backend
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


async def upload_receipt_image(
    file_bytes: bytes,
    filename: str,
    user_id: UUID,
    content_type: str = "image/jpeg",
) -> str:
    """
    Save a receipt image to local disk.
    Returns the storage path used as the image_url in the DB.
    """
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_dir / filename
    file_path.write_bytes(file_bytes)

    storage_path = f"{user_id}/{filename}"
    logger.info(f"Saved receipt image locally: {storage_path}")
    return storage_path


async def get_signed_url(storage_path: str) -> str:
    """
    Return a direct URL to the locally stored file.
    No expiry — files are served by the FastAPI static files mount.
    """
    return f"{BACKEND_URL}/uploads/{storage_path}"


async def download_receipt_image(storage_path: str) -> bytes:
    """Read a receipt image from local disk."""
    file_path = UPLOAD_DIR / storage_path
    if not file_path.exists():
        raise FileNotFoundError(f"Receipt image not found: {storage_path}")
    return file_path.read_bytes()


async def delete_receipt_image(storage_path: str) -> None:
    """Delete a receipt image from local disk."""
    file_path = UPLOAD_DIR / storage_path
    if file_path.exists():
        file_path.unlink()
        logger.info(f"Deleted receipt image: {storage_path}")
