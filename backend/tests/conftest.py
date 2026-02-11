"""Shared test fixtures for the Q-Logic backend test suite.

Uses an in-process SQLite database so tests run without PostgreSQL.
For integration tests requiring PG-specific features (FOR UPDATE SKIP LOCKED,
ENUM types, etc.), set TEST_DATABASE_URL to a real PostgreSQL instance.
"""

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.auth import Role, create_access_token, hash_password
from app.core.database import Base, get_db
from app.main import app

# Use SQLite for unit tests by default; override with TEST_DATABASE_URL for PG
TEST_DB_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///")

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    """Provide a clean database session for direct service-layer testing."""
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for route-level testing (no auth)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def admin_token():
    """Generate a valid JWT for an admin user."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "admin@test.com", Role.ADMIN)
    return token.access_token


@pytest_asyncio.fixture
async def agent_token():
    """Generate a valid JWT for an agent user."""
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "agent@test.com", Role.AGENT)
    return token.access_token


@pytest_asyncio.fixture
async def auth_client(client, admin_token):
    """HTTP client with admin Authorization header pre-set."""
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client
