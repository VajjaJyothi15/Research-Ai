import pytest_asyncio
from app.core.config import settings
from app.db.base import Base
from app.db.session import async_engine


@pytest_asyncio.fixture(autouse=True, scope="session")
async def setup_test_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
