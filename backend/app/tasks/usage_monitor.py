import logging
from sqlalchemy import text
from app.database import async_session_maker
from app.models.usage import UsageSnapshot

logger = logging.getLogger(__name__)

async def check_usage():
    async with async_session_maker() as session:
        try:
            # Query current Postgres size
            db_size_query = text("SELECT pg_database_size(current_database()) / (1024.0 * 1024.0) AS size_mb")
            db_size_result = await session.execute(db_size_query)
            postgres_mb = float(db_size_result.scalar() or 0)
            
            # Query today's request count from audit_logs table
            daily_requests_query = text("SELECT COUNT(*) FROM audit_logs WHERE performed_at >= NOW() - INTERVAL '1 day'")
            daily_requests_result = await session.execute(daily_requests_query)
            daily_requests = int(daily_requests_result.scalar() or 0)
            
            # Thresholds
            postgres_limit_mb = 400.0
            daily_requests_limit = 400000
            
            threshold_hit = postgres_mb > postgres_limit_mb or daily_requests > daily_requests_limit
            
            if threshold_hit:
                logger.warning(
                    f"Threshold exceeded: Postgres: {postgres_mb:.1f}MB (> {postgres_limit_mb}MB), "
                    f"Requests: {daily_requests} (> {daily_requests_limit})"
                )
            
            # Create row in usage_snapshots table
            snapshot = UsageSnapshot(
                postgres_mb=postgres_mb,
                storage_mb=0,
                request_count_today=daily_requests,
                threshold_hit=threshold_hit,
                alert_logged=threshold_hit,
            )
            session.add(snapshot)
            await session.commit()
            logger.info("Nightly usage check completed successfully.")
        except Exception as e:
            logger.error(f"Error in nightly usage check: {e}")
            await session.rollback()
