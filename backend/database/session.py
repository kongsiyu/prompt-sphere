"""
Database session management and utilities.

This module provides advanced session management capabilities including
transaction handling, retry logic, and session lifecycle management.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any, Callable, Optional, TypeVar, Generic
import asyncio
from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError
from sqlalchemy import text

from .connection import get_session_factory, get_engine

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for generic session management
T = TypeVar('T')


class DatabaseSession:
    """
    Advanced database session manager with retry logic and error handling.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._closed = False

    async def execute_with_retry(
        self,
        query_func: Callable[[AsyncSession], Any],
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> Any:
        """
        Execute a database operation with retry logic.

        Args:
            query_func: Function that takes a session and returns a result
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds

        Returns:
            Result of the query function

        Raises:
            SQLAlchemyError: If all retries are exhausted
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                result = await query_func(self.session)
                logger.debug(f"Query executed successfully on attempt {attempt + 1}")
                return result

            except (DisconnectionError, TimeoutError) as e:
                last_exception = e
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")

                if attempt < max_retries:
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    # Rollback current transaction and start fresh
                    try:
                        await self.session.rollback()
                    except Exception:
                        pass
                else:
                    logger.error(f"All retry attempts exhausted. Last error: {e}")
                    raise

            except SQLAlchemyError as e:
                logger.error(f"Non-retryable database error: {e}")
                raise

        if last_exception:
            raise last_exception

    async def commit_with_retry(self, max_retries: int = 3) -> bool:
        """
        Commit transaction with retry logic.

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            True if commit was successful, False otherwise
        """
        async def commit_func(session: AsyncSession) -> bool:
            await session.commit()
            return True

        try:
            return await self.execute_with_retry(commit_func, max_retries)
        except Exception as e:
            logger.error(f"Failed to commit transaction: {e}")
            await self.session.rollback()
            return False

    async def close(self) -> None:
        """Close the session."""
        if not self._closed:
            await self.session.close()
            self._closed = True
            logger.debug("Database session closed")

    def __del__(self):
        """Ensure session is closed on object destruction."""
        if not self._closed and hasattr(self, 'session'):
            logger.warning("Session was not properly closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[DatabaseSession, None]:
    """
    Get a managed database session with advanced features.

    Usage:
        async with get_session() as db:
            result = await db.execute_with_retry(
                lambda session: session.execute(text("SELECT * FROM users"))
            )
    """
    session_factory = get_session_factory()
    session = session_factory()
    db_session = DatabaseSession(session)

    try:
        logger.debug("Creating managed database session")
        yield db_session
    except Exception as e:
        logger.error(f"Error in managed session: {e}")
        await session.rollback()
        raise
    finally:
        await db_session.close()


@asynccontextmanager
async def get_transaction() -> AsyncGenerator[DatabaseSession, None]:
    """
    Get a database session within an explicit transaction.

    The transaction will be committed automatically on success,
    or rolled back on any exception.

    Usage:
        async with get_transaction() as db:
            # All operations here are within a single transaction
            await db.session.execute(text("INSERT INTO users ..."))
            await db.session.execute(text("UPDATE profiles ..."))
            # Transaction committed automatically
    """
    session_factory = get_session_factory()
    session = session_factory()
    db_session = DatabaseSession(session)

    try:
        logger.debug("Starting explicit transaction")
        yield db_session

        # Commit the transaction if no exceptions occurred
        success = await db_session.commit_with_retry()
        if success:
            logger.debug("Transaction committed successfully")
        else:
            logger.error("Failed to commit transaction")
            raise SQLAlchemyError("Transaction commit failed")

    except Exception as e:
        logger.error(f"Transaction failed, rolling back: {e}")
        await session.rollback()
        raise
    finally:
        await db_session.close()


def with_database_session(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to automatically provide a database session to a function.

    Usage:
        @with_database_session
        async def get_user(session: DatabaseSession, user_id: str):
            result = await session.session.execute(
                text("SELECT * FROM users WHERE id = :id"),
                {"id": user_id}
            )
            return result.fetchone()
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_session() as session:
            return await func(session, *args, **kwargs)

    return wrapper


def with_database_transaction(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to automatically wrap a function in a database transaction.

    Usage:
        @with_database_transaction
        async def create_user_with_profile(session: DatabaseSession, user_data: dict):
            # All operations here are within a single transaction
            await session.session.execute(text("INSERT INTO users ..."))
            await session.session.execute(text("INSERT INTO profiles ..."))
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        async with get_transaction() as session:
            return await func(session, *args, **kwargs)

    return wrapper


class SessionManager:
    """
    Session manager for handling multiple concurrent sessions.
    """

    def __init__(self):
        self._sessions: dict[str, DatabaseSession] = {}

    async def create_session(self, session_id: str) -> DatabaseSession:
        """
        Create a new managed session with a specific ID.

        Args:
            session_id: Unique identifier for the session

        Returns:
            DatabaseSession instance
        """
        if session_id in self._sessions:
            logger.warning(f"Session {session_id} already exists, closing old session")
            await self.close_session(session_id)

        session_factory = get_session_factory()
        session = session_factory()
        db_session = DatabaseSession(session)
        self._sessions[session_id] = db_session
        logger.info(f"Created session {session_id}")
        return db_session

    async def get_session(self, session_id: str) -> Optional[DatabaseSession]:
        """
        Get an existing session by ID.

        Args:
            session_id: Session identifier

        Returns:
            DatabaseSession if found, None otherwise
        """
        return self._sessions.get(session_id)

    async def close_session(self, session_id: str) -> bool:
        """
        Close and remove a specific session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was closed, False if not found
        """
        if session_id in self._sessions:
            await self._sessions[session_id].close()
            del self._sessions[session_id]
            logger.info(f"Closed session {session_id}")
            return True
        return False

    async def close_all_sessions(self) -> None:
        """Close all managed sessions."""
        session_ids = list(self._sessions.keys())
        for session_id in session_ids:
            await self.close_session(session_id)
        logger.info("All sessions closed")

    @property
    def active_sessions(self) -> list[str]:
        """Get list of active session IDs."""
        return list(self._sessions.keys())

    @property
    def session_count(self) -> int:
        """Get number of active sessions."""
        return len(self._sessions)


async def execute_raw_sql(
    sql: str,
    params: Optional[dict] = None,
    fetch_one: bool = False,
    fetch_all: bool = False
) -> Any:
    """
    Execute raw SQL with automatic session management.

    Args:
        sql: SQL query string
        params: Query parameters
        fetch_one: Return single row
        fetch_all: Return all rows

    Returns:
        Query result based on fetch parameters
    """
    async with get_session() as db:
        result = await db.execute_with_retry(
            lambda session: session.execute(text(sql), params or {})
        )

        if fetch_one:
            return result.fetchone()
        elif fetch_all:
            return result.fetchall()
        else:
            return result


async def check_session_health() -> dict:
    """
    Check the health of session management.

    Returns:
        Dict with session health information
    """
    health_info = {
        "status": "unknown",
        "session_creation": False,
        "query_execution": False,
        "transaction_handling": False,
        "error": None
    }

    try:
        # Test session creation
        async with get_session() as db:
            health_info["session_creation"] = True

            # Test query execution
            result = await db.execute_with_retry(
                lambda session: session.execute(text("SELECT 1 as test"))
            )
            test_value = result.scalar()
            if test_value == 1:
                health_info["query_execution"] = True

        # Test transaction handling
        async with get_transaction() as db:
            await db.session.execute(text("SELECT 1"))
            health_info["transaction_handling"] = True

        if all([
            health_info["session_creation"],
            health_info["query_execution"],
            health_info["transaction_handling"]
        ]):
            health_info["status"] = "healthy"
        else:
            health_info["status"] = "degraded"

    except Exception as e:
        health_info["status"] = "unhealthy"
        health_info["error"] = str(e)
        logger.error(f"Session health check failed: {e}")

    return health_info


# Global session manager instance
session_manager = SessionManager()