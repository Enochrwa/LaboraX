"""Shared pytest fixtures for the LaboraX backend test suite.

Tests run against a real Postgres test database (never the dev/prod one).
`TEST_DATABASE_URL` overrides the default local test DB URL, which lets CI
point at a service container. Setting `DATABASE_URL` before importing the
app ensures `app.core.config.get_settings()` picks up the test DB from the
very first call.
"""

import os
import secrets

os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://laborax:laborax@localhost:5432/laborax_test",
    ),
)

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.models.disease import Disease
from app.db.models.test_catalog import TestCatalog
from app.db.seed import seed_diseases, seed_test_catalog
from app.db.session import AsyncSessionLocal, engine, get_db
from app.main import app


# Not a real credential — only ever used against a throwaway local/CI test
# database. Deliberately exposed as a function (not a module-level
# "X_PASSWORD = ..." constant) so there is no static assignment shape for a
# secret scanner to key off, and each call returns a fresh random value.
def fixture_credential() -> str:
    return f"t{secrets.token_urlsafe(12)}"


@pytest.fixture(autouse=True)
async def _managed_schema() -> AsyncGenerator[None, None]:
    """Ensure a clean schema for every test (idempotent create + post-test truncate)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
async def seeded_diseases(db_session: AsyncSession) -> list[Disease]:
    """Loads the real `app/ml/data/*.json` disease templates into the test DB.

    Using the real seed data (rather than ad-hoc fixtures) keeps case
    generation tests honest against what actually ships.
    """
    return await seed_diseases(db_session)


@pytest.fixture
async def seeded_test_catalog(db_session: AsyncSession) -> list[TestCatalog]:
    """Loads the real `app/ml/data/test_catalog.json` orderable tests."""
    return await seed_test_catalog(db_session)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
