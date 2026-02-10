"""Database session management with async SQLAlchemy."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..config import settings

# Convert postgresql:// to postgresql+asyncpg:// for async support
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine compatible with Supabase PgBouncer (transaction mode)
# NullPool is required because PgBouncer handles connection pooling externally
engine = create_async_engine(
    database_url,
    echo=settings.app_env == "development",
    poolclass=NullPool,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    },
)

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Yields async session and handles commit/rollback automatically.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
