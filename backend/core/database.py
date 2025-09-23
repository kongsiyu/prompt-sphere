"""
Core database management module.

This module provides high-level database management functions including
initialization, health monitoring, and application-level database operations.
"""

import logging
from typing import Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager

from database.connection import (
    get_engine,
    check_database_connection,
    close_database_connections,
    get_async_session
)
from database.session import (
    get_session,
    get_transaction,
    check_session_health,
    session_manager,
    execute_raw_sql
)
from database.migration_manager import MigrationManager
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    High-level database manager for the application.

    Provides a unified interface for database operations, health monitoring,
    and lifecycle management.
    """

    def __init__(self):
        self._initialized = False
        self._migration_manager = None
        self._health_check_interval = 300  # 5 minutes

    @property
    def is_initialized(self) -> bool:
        """Check if database is initialized."""
        return self._initialized

    async def initialize(self, run_migrations: bool = True) -> None:
        """
        Initialize the database system.

        Args:
            run_migrations: Whether to run pending migrations

        Raises:
            Exception: If initialization fails
        """
        try:
            logger.info("Starting database initialization...")

            # Test basic connectivity
            health_check = await check_database_connection()
            if health_check["status"] != "connected":
                raise Exception("Failed to establish database connection")

            # Initialize migration manager
            if run_migrations:
                self._migration_manager = MigrationManager()
                await self._migration_manager.initialize()

                # Run pending migrations
                pending_migrations = await self._migration_manager.get_pending_migrations()
                if pending_migrations:
                    logger.info(f"Running {len(pending_migrations)} pending migrations")
                    for migration in pending_migrations:
                        await self._migration_manager.run_migration(migration)
                        logger.info(f"Applied migration: {migration}")
                else:
                    logger.info("No pending migrations to run")

            # Create engine and tables if needed
            engine = get_engine()
            from database.models import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            # Verify system health
            health_status = await self.get_comprehensive_health()
            if health_status["overall_status"] != "healthy":
                raise Exception(f"Database health check failed: {health_status}")

            self._initialized = True
            logger.info("Database initialization completed successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def shutdown(self) -> None:
        """
        Shutdown the database system gracefully.
        """
        try:
            logger.info("Starting database shutdown...")

            # Close all managed sessions
            await session_manager.close_all_sessions()

            # Close the main database engine
            await close_database_connections()

            self._initialized = False
            logger.info("Database shutdown completed successfully")

        except Exception as e:
            logger.error(f"Error during database shutdown: {e}")
            raise

    async def reset_database(self, confirm: bool = False) -> None:
        """
        Reset the database by dropping and recreating all tables.

        Args:
            confirm: Must be True to actually perform the reset

        Raises:
            ValueError: If confirm is not True
            Exception: If reset fails
        """
        if not confirm:
            raise ValueError("Database reset requires explicit confirmation")

        try:
            logger.warning("Starting database reset - this will destroy all data!")

            # Close all sessions first
            await session_manager.close_all_sessions()

            # Drop and recreate all tables
            engine = get_engine()
            from database.models import Base
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("All tables dropped")
                await conn.run_sync(Base.metadata.create_all)
                logger.info("All tables recreated")

            # Reinitialize migration tracking if migration manager exists
            if self._migration_manager:
                await self._migration_manager.initialize()

            logger.warning("Database reset completed - all data has been lost!")

        except Exception as e:
            logger.error(f"Database reset failed: {e}")
            raise

    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """
        Get comprehensive health status of the database system.

        Returns:
            Dict with detailed health information
        """
        health_report = {
            "overall_status": "unknown",
            "connection_health": {},
            "session_health": {},
            "pool_stats": {},
            "migration_status": {},
            "timestamp": None,
            "errors": []
        }

        try:
            # Check connection health
            connection_health = await check_database_connection()
            health_report["connection_health"] = connection_health

            # Check session management health
            session_health = await check_session_health()
            health_report["session_health"] = session_health

            # Get connection pool statistics
            engine = get_engine()
            pool = engine.pool
            pool_stats = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalidated": pool.invalidated()
            }
            health_report["pool_stats"] = pool_stats

            # Check migration status if manager exists
            if self._migration_manager:
                try:
                    migration_status = await self._migration_manager.get_status()
                    health_report["migration_status"] = migration_status
                except Exception as e:
                    health_report["errors"].append(f"Migration status check failed: {e}")

            # Determine overall status
            connection_ok = connection_health.get("status") == "connected"
            session_ok = session_health.get("status") == "healthy"

            if connection_ok and session_ok:
                health_report["overall_status"] = "healthy"
            elif connection_ok or session_ok:
                health_report["overall_status"] = "degraded"
            else:
                health_report["overall_status"] = "unhealthy"

            # Add timestamp
            import datetime
            health_report["timestamp"] = datetime.datetime.utcnow().isoformat()

        except Exception as e:
            health_report["overall_status"] = "unhealthy"
            health_report["errors"].append(f"Health check failed: {e}")
            logger.error(f"Comprehensive health check failed: {e}")

        return health_report

    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get detailed database information.

        Returns:
            Dict with database configuration and status
        """
        info = {
            "configuration": {
                "database_url": settings.database_url,
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "host": settings.database_host,
                "port": settings.database_port,
                "database_name": settings.database_name,
            },
            "runtime": {
                "initialized": self._initialized,
                "active_sessions": session_manager.session_count,
                "migration_manager": self._migration_manager is not None,
            },
            "health": await self.get_comprehensive_health()
        }

        return info

    async def execute_maintenance_tasks(self) -> Dict[str, Any]:
        """
        Execute routine database maintenance tasks.

        Returns:
            Dict with maintenance task results
        """
        results = {
            "tasks_executed": [],
            "errors": [],
            "timestamp": None
        }

        try:
            logger.info("Starting database maintenance tasks...")

            # Clean up idle sessions
            try:
                initial_count = session_manager.session_count
                await session_manager.close_all_sessions()
                results["tasks_executed"].append(f"Cleaned up {initial_count} idle sessions")
            except Exception as e:
                results["errors"].append(f"Session cleanup failed: {e}")

            # Check and log pool statistics
            try:
                engine = get_engine()
                pool = engine.pool
                if pool.invalidated() > 0:
                    results["tasks_executed"].append(
                        f"Found {pool.invalidated()} invalidated connections"
                    )
            except Exception as e:
                results["errors"].append(f"Pool stats check failed: {e}")

            # Test basic connectivity
            try:
                conn_check = await check_database_connection()
                if conn_check["status"] == "connected":
                    results["tasks_executed"].append("Database connectivity verified")
                else:
                    results["errors"].append("Database connectivity test failed")
            except Exception as e:
                results["errors"].append(f"Connectivity test failed: {e}")

            import datetime
            results["timestamp"] = datetime.datetime.utcnow().isoformat()
            logger.info(f"Maintenance tasks completed. Executed: {len(results['tasks_executed'])}, Errors: {len(results['errors'])}")

        except Exception as e:
            results["errors"].append(f"Maintenance task execution failed: {e}")
            logger.error(f"Database maintenance failed: {e}")

        return results

    async def backup_database_schema(self) -> str:
        """
        Create a backup of the database schema.

        Returns:
            Schema backup as SQL string
        """
        try:
            # This is a simplified version - in production you'd want more sophisticated backup
            schema_sql = []

            async with get_async_session() as db:
                from sqlalchemy import text
                # Get table information
                tables_result = await db.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()")
                )
                tables = [row[0] for row in tables_result.fetchall()]

                for table in tables:
                    # Get CREATE TABLE statement
                    create_result = await db.execute(text(f"SHOW CREATE TABLE {table}"))
                    create_statement = create_result.fetchone()
                    if create_statement:
                        schema_sql.append(create_statement[1])

            return ";\n\n".join(schema_sql) + ";"

        except Exception as e:
            logger.error(f"Schema backup failed: {e}")
            raise

    @asynccontextmanager
    async def maintenance_mode(self):
        """
        Context manager for maintenance mode operations.

        During maintenance mode, new connections may be limited
        and existing sessions may be closed.
        """
        try:
            logger.info("Entering maintenance mode")
            # Close all managed sessions
            await session_manager.close_all_sessions()
            yield
        finally:
            logger.info("Exiting maintenance mode")


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for common operations
async def initialize_database(run_migrations: bool = True) -> None:
    """Initialize the database system."""
    await db_manager.initialize(run_migrations)


async def shutdown_database() -> None:
    """Shutdown the database system."""
    await db_manager.shutdown()


async def get_database_health() -> Dict[str, Any]:
    """Get database health status."""
    return await db_manager.get_comprehensive_health()


async def get_database_info() -> Dict[str, Any]:
    """Get database information."""
    return await db_manager.get_database_info()


async def run_maintenance() -> Dict[str, Any]:
    """Run database maintenance tasks."""
    return await db_manager.execute_maintenance_tasks()


# Database lifecycle management for FastAPI
@asynccontextmanager
async def database_lifespan():
    """
    Context manager for database lifecycle in FastAPI applications.

    Usage in FastAPI:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with database_lifespan():
                yield
    """
    try:
        # Initialize database on startup
        await initialize_database()
        logger.info("Database system ready")
        yield
    finally:
        # Cleanup on shutdown
        await shutdown_database()
        logger.info("Database system shutdown complete")


# Health check endpoint helper
async def health_check_endpoint() -> Dict[str, Any]:
    """
    Helper function for health check endpoints.

    Returns simplified health status suitable for HTTP endpoints.
    """
    try:
        health = await get_database_health()
        return {
            "status": health["overall_status"],
            "database": health["connection_health"]["status"] == "connected",
            "sessions": health["session_health"]["status"] == "healthy",
            "pool_size": health["pool_stats"]["pool_size"],
            "active_connections": health["pool_stats"]["checked_out"],
            "timestamp": health["timestamp"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": None
        }