from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()

overflow = max(settings.db_pool_max - settings.db_pool_min, 0)

engine = create_async_engine(
    settings.db_url,
    pool_size=settings.db_pool_min,
    max_overflow=overflow,
    pool_pre_ping=True,
)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


async def init_models() -> None:
    from . import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Alias for compatibility
get_db = get_session
async_session = AsyncSessionFactory

