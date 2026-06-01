from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        # statement_cache_size=0 only needed for Supabase pgBouncer (port 6543)
        connect_args = {"statement_cache_size": 0} if "6543" in settings.database_url else {}
        _engine = create_async_engine(
            settings.database_url,
            connect_args=connect_args,
            echo=False,
        )
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    AsyncSessionLocal = sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session
