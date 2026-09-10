"""Test fixtures.

The suite runs against an in-memory SQLite database (via aiosqlite) so it needs
no Docker. The ORM models are deliberately backend-agnostic; PostgreSQL-specific
behaviour (concurrent index creation, etc.) lives only in Alembic migrations,
which are exercised separately against the compose stack.
"""

import contextlib

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app import database
from app.database import Base
from app.limiter import limiter
from app.main import app


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    with contextlib.suppress(Exception):
        limiter.reset()
    yield


@pytest.fixture
async def _db(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)

    monkeypatch.setattr(database, "_engine", engine)
    monkeypatch.setattr(database, "_sessionmaker", sessionmaker)
    yield sessionmaker
    await engine.dispose()


@pytest.fixture
async def client(_db) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def session(_db):
    async with _db() as s:
        yield s
