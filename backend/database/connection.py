"""Database connection and session management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncEngine
from sqlalchemy.pool import QueuePool
from sqlalchemy import text, event

from app.core.config import settings
from database.models import Base


# Configure logging
logger = logging.getLogger(__name__)

# Global engine instance
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine lazily."""
    global _engine
    if _engine is None:
        logger.info(f"Creating database engine with URL: {settings.database_url}")

        # Create async engine with MySQL optimizations
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            echo=settings.debug,  # Log SQL queries in debug mode
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,  # Recycle connections every hour
            pool_timeout=30,  # Connection timeout
            poolclass=QueuePool,  # Use QueuePool for better concurrency
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False,
                "server_side_cursors": True,
            } if settings.database_url.startswith('mysql') else {}
        )

        # Add connection event listeners for monitoring
        @event.listens_for(_engine.sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Handle new database connections."""
            logger.info(f"New database connection established: {connection_record.info}")

        @event.listens_for(_engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Handle connection checkout from pool."""
            logger.debug("Connection checked out from pool")

        @event.listens_for(_engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Handle connection checkin to pool."""
            logger.debug("Connection checked in to pool")

    return _engine


def get_session_factory() -> async_sessionmaker:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )
    return _session_factory


# Backward compatibility
def get_async_session_local() -> async_sessionmaker:
    """Get the async session factory (backward compatibility)."""
    return get_session_factory()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.

    This context manager ensures proper session lifecycle management.

    Usage:
        async with get_async_session() as session:
            # Use session here
            result = await session.execute(select(User))
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_database_connection() -> dict:
    """
    Check database connection and return status information.

    Returns:
        dict: Connection status and database information
    """
    try:
        async with get_async_session() as session:
            # Execute a simple query to test connection
            result = await session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()

            # Get database version if possible
            try:
                version_result = await session.execute(text("SELECT VERSION()"))
                db_version = version_result.scalar()
            except:
                db_version = "Unknown"

            return {
                "status": "connected",
                "test_query": test_value == 1,
                "database_version": db_version,
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow
            }
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return {
            "status": "disconnected",
            "error": str(e),
            "test_query": False
        }


async def close_database_connections():
    """Close all database connections."""
    global _engine
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")


# Backward compatibility aliases
engine = property(get_engine)
AsyncSessionLocal = get_session_factory