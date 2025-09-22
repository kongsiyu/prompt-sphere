"""Database connection and session management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy import text, event

from app.core.config import settings
from database.models import Base


# Configure logging
logger = logging.getLogger(__name__)

# Create async engine with MySQL optimizations
engine = create_async_engine(
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
    },
)

# Add connection event listeners for monitoring
@event.listens_for(engine.sync_engine, "connect")
def receive_connect(dbapi_connection, connection_record):
    """Handle new database connections."""
    logger.info(f"New database connection established: {connection_record.info}")

@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """Handle connection checkout from pool."""
    logger.debug("Connection checked out from pool")

@event.listens_for(engine.sync_engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """Handle connection checkin to pool."""
    logger.debug("Connection checked in to pool")

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session with proper error handling and logging.

    Yields:
        AsyncSession: Database session
    """
    session = AsyncSessionLocal()
    try:
        logger.debug("Creating new database session")
        yield session
        await session.commit()
        logger.debug("Database session committed successfully")
    except Exception as e:
        logger.error(f"Database session error: {e}")
        await session.rollback()
        logger.debug("Database session rolled back")
        raise
    finally:
        await session.close()
        logger.debug("Database session closed")

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Alternative context manager for database sessions.

    Usage:
        async with get_db_session() as session:
            # Use session here
    """
    session = AsyncSessionLocal()
    try:
        logger.debug("Creating database session context")
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f"Database session context error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()
        logger.debug("Database session context closed")


async def create_database_tables() -> None:
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_database_tables() -> None:
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def close_database() -> None:
    """Close database engine."""
    logger.info("Closing database engine")
    await engine.dispose()
    logger.info("Database engine closed")


async def check_database_health() -> dict:
    """
    Check database connection health.

    Returns:
        Dict with health status information
    """
    health_status = {
        "status": "unknown",
        "connection_pool": {},
        "database_info": {},
        "error": None
    }

    try:
        async with engine.begin() as conn:
            # Test basic connectivity
            result = await conn.execute(text("SELECT 1 as health_check"))
            health_check = result.scalar()

            if health_check == 1:
                health_status["status"] = "healthy"

                # Get database version and info
                db_version = await conn.execute(text("SELECT VERSION() as version"))
                version_info = db_version.scalar()
                health_status["database_info"]["version"] = version_info

                # Get current timestamp
                timestamp_result = await conn.execute(text("SELECT NOW() as current_time"))
                current_time = timestamp_result.scalar()
                health_status["database_info"]["current_time"] = str(current_time)

                # Connection pool information
                pool = engine.pool
                health_status["connection_pool"] = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalidated": pool.invalidated()
                }

                logger.info("Database health check passed")
            else:
                health_status["status"] = "unhealthy"
                health_status["error"] = "Health check query failed"

    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        logger.error(f"Database health check failed: {e}")

    return health_status


async def get_connection_pool_stats() -> dict:
    """
    Get detailed connection pool statistics.

    Returns:
        Dict with connection pool statistics
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in_connections": pool.checkedin(),
        "checked_out_connections": pool.checkedout(),
        "overflow_connections": pool.overflow(),
        "invalidated_connections": pool.invalidated(),
        "total_connections": pool.size() + pool.overflow(),
        "available_connections": pool.checkedin(),
    }


async def test_database_connection() -> bool:
    """
    Test database connection without creating a session.

    Returns:
        True if connection is successful, False otherwise
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


async def init_database() -> None:
    """
    Initialize database with all required tables and configurations.
    """
    try:
        logger.info("Initializing database...")

        # Test connection first
        if not await test_database_connection():
            raise Exception("Cannot establish database connection")

        # Create all tables
        await create_database_tables()

        # Verify initialization
        health = await check_database_health()
        if health["status"] != "healthy":
            raise Exception(f"Database initialization failed: {health.get('error', 'Unknown error')}")

        logger.info("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise