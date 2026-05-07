import os
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure app settings can load in test runs without production env.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SUPABASE_URL", "http://localhost:54321")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
os.environ.setdefault("NVIDIA_NIM_API_KEY", "test-nvidia-key")

from app.auth import get_current_user
from app.database import Base, get_db
from app.main import app

# Import all models so Base.metadata has every table.
import app.models.journal  # noqa: F401
import app.models.receipt  # noqa: F401
import app.models.usage  # noqa: F401
import app.models.user  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
TEST_SECRET = "test-secret"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture
async def db_session() -> AsyncSession:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_user_token() -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "aud": "authenticated",
        "iss": "http://localhost:54321/auth/v1",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


@pytest.fixture
async def async_client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    async def override_get_current_user():
        return {
            "id": "00000000-0000-0000-0000-000000000001",
            "sub": "00000000-0000-0000-0000-000000000001",
            "email": "test@example.com",
        }

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
