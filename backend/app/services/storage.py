"""
Storage service — uses Supabase Storage for persistence.
Falls back to local filesystem if Supabase is not configured.
"""

import logging
import os
from pathlib import Path
from uuid import UUID

logger = logging.getLogger(__name__)

BUCKET_NAME = "receipts"
SIGNED_URL_EXPIRY = 3600  # 1 hour

# Local fallback directory
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def _supabase_client():
    """Create a Supabase client using service role key."""
    from app.config import settings
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def _use_supabase() -> bool:
    """Return True if Supabase storage is properly configured."""
    from app.config import settings
    key = (settings.supabase_service_role_key or "").strip()
    url = (settings.supabase_url or "").strip()
    is_placeholder = key in ("", "dummy-not-used", "<YOUR_SUPABASE_SERVICE_ROLE_KEY>")
    result = bool(url) and not is_placeholder
    logger.info(f"Storage backend: {'supabase' if result else 'local'} (url={'set' if url else 'missing'}, key={'set' if not is_placeholder else 'placeholder'})")
    return result


async def upload_receipt_image(
    file_bytes: bytes,
    filename: str,
    user_id: UUID,
    content_type: str = "image/jpeg",
) -> str:
    """Upload receipt image. Returns storage path."""
    storage_path = f"{user_id}/{filename}"

    if _use_supabase():
        try:
            supabase = _supabase_client()
            supabase.storage.from_(BUCKET_NAME).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            logger.info(f"Uploaded to Supabase Storage: {storage_path}")
            return storage_path
        except Exception as e:
            logger.warning(f"Supabase upload failed, falling back to local: {e}")

    # Local filesystem fallback
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / filename).write_bytes(file_bytes)
    logger.info(f"Saved receipt image locally: {storage_path}")
    return storage_path


async def get_signed_url(storage_path: str) -> str:
    """Return a URL to access the stored file."""
    if _use_supabase():
        try:
            supabase = _supabase_client()
            response = supabase.storage.from_(BUCKET_NAME).create_signed_url(
                path=storage_path,
                expires_in=SIGNED_URL_EXPIRY,
            )
            url = response["signedURL"]
            logger.info(f"Signed URL generated: {url[:80]}...")
            return url
        except Exception as e:
            logger.warning(f"Supabase signed URL failed: {e}")

    url = f"{BACKEND_URL}/uploads/{storage_path}"
    logger.info(f"Local URL: {url}")
    return url


async def download_receipt_image(storage_path: str) -> bytes:
    """Download receipt image bytes."""
    if _use_supabase():
        try:
            supabase = _supabase_client()
            return supabase.storage.from_(BUCKET_NAME).download(storage_path)
        except Exception as e:
            logger.warning(f"Supabase download failed, trying local: {e}")

    file_path = UPLOAD_DIR / storage_path
    if file_path.exists():
        return file_path.read_bytes()
    raise FileNotFoundError(f"Receipt image not found: {storage_path}")


async def delete_receipt_image(storage_path: str) -> None:
    """Delete receipt image."""
    if _use_supabase():
        try:
            supabase = _supabase_client()
            supabase.storage.from_(BUCKET_NAME).remove([storage_path])
            logger.info(f"Deleted from Supabase Storage: {storage_path}")
            return
        except Exception as e:
            logger.warning(f"Supabase delete failed: {e}")

    file_path = UPLOAD_DIR / storage_path
    if file_path.exists():
        file_path.unlink()
