"""
Async SQLAlchemy engine and session factory.
Supports both PostgreSQL (via asyncpg) and SQLite (via aiosqlite).
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")
_is_postgres = not _is_sqlite

engine_kwargs: dict = {
    "echo": False,
    "pool_pre_ping": True,
}

if _is_postgres:
    engine_kwargs["pool_size"] = 5
    engine_kwargs["max_overflow"] = 10
    # Disable prepared statement cache — required when using PgBouncer
    # in transaction/statement pooling mode (Supabase, Render, Railway, etc.)
    engine_kwargs["connect_args"] = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }
else:
    # SQLite requires check_same_thread=False for async use
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.validated_database_url, **engine_kwargs)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Alias for background tasks / bulk processor imports
async_session_maker = async_session


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Health check — verify database connectivity."""
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        return True
    except Exception:
        return False
