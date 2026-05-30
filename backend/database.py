"""Async SQLAlchemy engine + session factory. Mirrors aftershoot's pattern:
the app talks async (aiomysql); Alembic/admin scripts use the sync PyMySQL URL.

Tables are created on startup via ``init_db`` (the schema is tiny — two tables —
so we don't carry an Alembic setup for it yet).
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from config.settings import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def _to_async_url(url: str) -> str:
    """Convert the sync PyMySQL URL to its async aiomysql equivalent."""
    if url.startswith("mysql+pymysql://"):
        return "mysql+aiomysql://" + url[len("mysql+pymysql://"):]
    if url.startswith("mysql://"):
        return "mysql+aiomysql://" + url[len("mysql://"):]
    return url


async_engine = create_async_engine(
    _to_async_url(settings.DATABASE_URL),
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Create tables if they don't exist. Import models first so they register."""
    import models  # noqa: F401  (populates Base.metadata)

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready")


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
