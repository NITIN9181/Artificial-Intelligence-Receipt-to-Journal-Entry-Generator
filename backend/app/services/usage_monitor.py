import logging
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import create_client, Client

from app.config import settings
from app.models.usage import UsageSnapshot

logger = logging.getLogger(__name__)

async def query_postgres_size(db: AsyncSession) -> float:
    from sqlalchemy import text
    query = text("SELECT pg_database_size(current_database()) / 1048576.0")
    result = await db.execute(query)
    return float(result.scalar() or 0.0)

async def query_storage_usage(supabase_admin_client: Client) -> float:
    # Storage API doesn't expose usage directly to the client easily, 
    # but we can list buckets and sum file sizes. This is an approximation.
    # A true usage would require Supabase Management API which is paid.
    try:
        total_size = 0.0
        # Supabase python client doesn't expose list_all, so we do a simple list
        res = supabase_admin_client.storage.from_("receipts").list()
        for item in res:
            if hasattr(item, "metadata") and getattr(item, "metadata", None):
                total_size += item.metadata.get("size", 0)
            elif isinstance(item, dict) and "metadata" in item:
                total_size += item["metadata"].get("size", 0)
        return total_size / 1048576.0
    except Exception as e:
        logger.error(f"Failed to query storage usage: {e}")
        return 0.0

async def query_daily_request_count(db: AsyncSession) -> int:
    """Query daily request count from audit_logs table."""
    from sqlalchemy import text
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    try:
        result = await db.execute(
            text("SELECT COUNT(*) FROM audit_logs WHERE performed_at >= :yesterday"),
            {"yesterday": yesterday}
        )
        return int(result.scalar() or 0)
    except Exception as e:
        logger.warning(f"Could not query audit_logs for daily request count: {e}")
        return 0

async def run_usage_check(db: AsyncSession, supabase_admin_client: Client):
    postgres_mb = await query_postgres_size(db)
    storage_mb = await query_storage_usage(supabase_admin_client)
    request_count = await query_daily_request_count(db)

    threshold_hit = (
        postgres_mb > 400 or
        storage_mb > 800 or
        request_count > 400_000
    )

    snapshot = UsageSnapshot(
        postgres_mb=postgres_mb,
        storage_mb=storage_mb,
        request_count_today=request_count,
        threshold_hit=threshold_hit,
        alert_logged=False
    )
    db.add(snapshot)
    await db.commit()

    if threshold_hit:
        logger.warning(
            f"USAGE ALERT: postgres={postgres_mb}MB, "
            f"storage={storage_mb}MB, requests={request_count}/day"
        )
