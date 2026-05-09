"""
FastAPI application entry point.
CORS, startup, error handling, router registration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import health, journal_entries, receipts, admin, gnucash

# Configure logging — NEVER log secrets
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.usage_monitor import run_usage_check
from app.database import async_session_maker
from app.auth import supabase_client

scheduler = AsyncIOScheduler()

async def scheduled_usage_check():
    async with async_session_maker() as db:
        await run_usage_check(db, supabase_client)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting AI Receipt Journal Entry Generator")
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Database configured: {'yes' if settings.database_url else 'no'}")
    
    scheduler.add_job(scheduled_usage_check, 'cron', hour=2, minute=0)
    scheduler.start()
    
    yield
    logger.info("Shutting down...")
    scheduler.shutdown()


app = FastAPI(
    title="AI Receipt to Journal Entry Generator",
    description="Transform receipt images into validated double-entry journal entries",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(health.router)
app.include_router(receipts.router)
app.include_router(journal_entries.router)
app.include_router(admin.router)
app.include_router(gnucash.router)  # Phase 3: GnuCash export


# --- Global Error Handler (Task B7) ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch all unhandled exceptions.
    Return structured error response — NO stack traces in production.
    """
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
    )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "detail": "The requested resource was not found.",
        },
    )
