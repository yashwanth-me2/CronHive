from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config import settings

# Create async engine. `echo=True` will log all SQL queries if in development mode.
engine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    future=True,
    pool_size=20,
    max_overflow=10,
)

# Async session factory
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting an async DB session."""
    async with async_session_maker() as session:
        yield session
