"""
Admin-only endpoints for usage monitoring and system management.
Requires is_admin = TRUE in users table (migration 004).
"""

import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.database import get_db
from app.models.user import User
from app.models.receipt import Receipt
from app.models.usage import UsageSnapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/usage", status_code=200)
async def get_usage_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/v1/admin/usage
    
    Returns current usage statistics for monitoring free tier limits.
    Requires admin privileges.
    
    Free Tier Limits (Supabase):
    - Postgres: 500 MB
    - Daily requests: ~50K (estimated from audit_logs)
    
    Returns:
    - postgres_mb: Current database size in MB
    - daily_requests: Request count in last 24 hours
    - threshold_percent: Percentage of limit used (max of postgres and requests)
    - usage_threshold_flag: True if > 80% of any limit
    """
    
    # Query database size
    db_size_query = text("""
        SELECT pg_database_size(current_database()) / (1024.0 * 1024.0) AS size_mb
    """)
    db_size_result = await db.execute(db_size_query)
    postgres_mb = float(db_size_result.scalar() or 0)
    
    # Query daily request count (approximate from audit_logs)
    yesterday = datetime.now() - timedelta(days=1)
    daily_requests_query = select(func.count()).select_from(
        text("audit_logs")
    ).where(
        text("performed_at >= :yesterday")
    ).params(yesterday=yesterday)
    
    try:
        daily_requests_result = await db.execute(
            text("SELECT COUNT(*) FROM audit_logs WHERE performed_at >= :yesterday"),
            {"yesterday": yesterday}
        )
        daily_requests = int(daily_requests_result.scalar() or 0)
    except Exception as e:
        logger.warning(f"Could not query audit_logs for daily requests: {e}")
        daily_requests = 0
    
    # Calculate threshold percentages
    postgres_limit_mb = 500.0  # Supabase free tier
    daily_requests_limit = 50000  # Estimated safe limit
    
    postgres_percent = (postgres_mb / postgres_limit_mb) * 100
    requests_percent = (daily_requests / daily_requests_limit) * 100
    
    threshold_percent = max(postgres_percent, requests_percent)
    usage_threshold_flag = threshold_percent >= 80.0
    
    # Log warning if threshold exceeded
    if usage_threshold_flag:
        logger.warning(
            f"Usage threshold exceeded: {threshold_percent:.1f}% "
            f"(Postgres: {postgres_mb:.1f}MB / {postgres_limit_mb}MB, "
            f"Requests: {daily_requests} / {daily_requests_limit})"
        )
    
    return {
        "postgres_mb": round(postgres_mb, 2),
        "postgres_limit_mb": postgres_limit_mb,
        "postgres_percent": round(postgres_percent, 2),
        "daily_requests": daily_requests,
        "daily_requests_limit": daily_requests_limit,
        "requests_percent": round(requests_percent, 2),
        "threshold_percent": round(threshold_percent, 2),
        "usage_threshold_flag": usage_threshold_flag,
        "checked_at": datetime.now().isoformat(),
    }


@router.post("/usage/snapshot", status_code=201)
async def create_usage_snapshot(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /api/v1/admin/usage/snapshot
    
    Manually trigger a usage snapshot (normally done by nightly cron).
    Stores current usage stats in usage_snapshots table.
    """
    # Get current usage stats
    usage_stats = await get_usage_stats(admin_user, db)
    
    # Create snapshot
    snapshot = UsageSnapshot(
        postgres_mb=usage_stats["postgres_mb"],
        storage_mb=0,  # Not tracking storage separately yet
        request_count_today=usage_stats["daily_requests"],
        threshold_hit=usage_stats["usage_threshold_flag"],
        alert_logged=False,
    )
    
    db.add(snapshot)
    await db.commit()
    await db.refresh(snapshot)
    
    return {
        "id": str(snapshot.id),
        "checked_at": snapshot.checked_at.isoformat() if snapshot.checked_at else None,
        "postgres_mb": float(snapshot.postgres_mb) if snapshot.postgres_mb else 0,
        "request_count_today": snapshot.request_count_today,
        "threshold_hit": snapshot.threshold_hit,
    }


@router.get("/usage/history", status_code=200)
async def get_usage_history(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    days: int = 30,
):
    """
    GET /api/v1/admin/usage/history?days=30
    
    Returns historical usage snapshots for trend analysis.
    """
    cutoff_date = datetime.now() - timedelta(days=days)
    
    query = (
        select(UsageSnapshot)
        .where(UsageSnapshot.checked_at >= cutoff_date)
        .order_by(UsageSnapshot.checked_at.desc())
    )
    
    result = await db.execute(query)
    snapshots = result.scalars().all()
    
    return {
        "snapshots": [
            {
                "id": str(s.id),
                "checked_at": s.checked_at.isoformat() if s.checked_at else None,
                "postgres_mb": float(s.postgres_mb) if s.postgres_mb else 0,
                "request_count_today": s.request_count_today,
                "threshold_hit": s.threshold_hit,
                "alert_logged": s.alert_logged,
            }
            for s in snapshots
        ],
        "total": len(snapshots),
        "days": days,
    }


@router.get("/stats", status_code=200)
async def get_admin_stats(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    GET /api/v1/admin/stats
    
    Returns system-wide statistics for admin dashboard.
    """
    # Total users
    total_users_query = select(func.count()).select_from(User)
    total_users_result = await db.execute(total_users_query)
    total_users = total_users_result.scalar() or 0
    
    # Total receipts
    total_receipts_query = select(func.count()).select_from(Receipt)
    total_receipts_result = await db.execute(total_receipts_query)
    total_receipts = total_receipts_result.scalar() or 0
    
    # Receipts by status
    status_query = select(
        Receipt.status,
        func.count(Receipt.id).label("count")
    ).group_by(Receipt.status)
    status_result = await db.execute(status_query)
    status_counts = {row[0]: row[1] for row in status_result.all()}
    
    return {
        "total_users": total_users,
        "total_receipts": total_receipts,
        "receipts_by_status": status_counts,
        "generated_at": datetime.now().isoformat(),
    }
