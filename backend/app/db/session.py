"""Database session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings

# Create async engine
db_url = settings.database_url
if db_url.startswith("sqlite"):
    # SQLite async setup - ensure proper format
    if "sqlite+aiosqlite" not in db_url:
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(
        db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.environment == "development",
    )
elif db_url.startswith("postgresql"):
    # PostgreSQL async setup
    if "postgresql+asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(
        db_url,
        echo=settings.environment == "development",
        pool_pre_ping=True,
    )
else:
    raise ValueError(f"Unsupported database URL: {db_url}")

# Create async session factory
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for all database models
Base = declarative_base()


async def init_db() -> None:
    """Initialize database and create all tables."""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered
        from app.db.models import Job  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()