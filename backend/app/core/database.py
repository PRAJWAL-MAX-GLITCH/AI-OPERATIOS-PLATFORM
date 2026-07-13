from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import get_settings
import structlog

logger = structlog.get_logger(__name__)
settings = get_settings()

# Create the async engine
# pool_pre_ping=True: Health check connection before use to avoid 'server closed the connection unexpectedly'
# pool_recycle=3600: Recycle connections after 1 hour
# pool_size=20, max_overflow=10: Handles burst traffic up to 30 concurrent connections
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=20,
    max_overflow=10,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to provide a database session for requests.
    Closes the session after the request is finished.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error("db_session_error", error=str(e))
            await session.rollback()
            raise
        finally:
            await session.close()
