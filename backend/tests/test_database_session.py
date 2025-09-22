"""Tests for database session management."""

from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError

from database.session import (
    DatabaseSession,
    get_session,
    get_transaction,
    with_database_session,
    with_database_transaction,
    SessionManager,
    execute_raw_sql,
    check_session_health,
    session_manager
)


class TestDatabaseSession:
    """Test DatabaseSession class functionality."""

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test successful query execution without retries."""
        mock_session = AsyncMock(spec=AsyncSession)
        db_session = DatabaseSession(mock_session)

        async def query_func(session):
            return "success"

        result = await db_session.execute_with_retry(query_func)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_execute_with_retry_with_retries(self):
        """Test query execution with connection errors and retries."""
        mock_session = AsyncMock(spec=AsyncSession)
        db_session = DatabaseSession(mock_session)

        call_count = 0

        async def query_func(session):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DisconnectionError("Connection lost", None, None)
            return "success_after_retry"

        result = await db_session.execute_with_retry(query_func, max_retries=3)
        assert result == "success_after_retry"
        assert call_count == 3
        assert mock_session.rollback.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_with_retry_exhausted(self):
        """Test query execution when all retries are exhausted."""
        mock_session = AsyncMock(spec=AsyncSession)
        db_session = DatabaseSession(mock_session)

        async def query_func(session):
            raise DisconnectionError("Connection lost", None, None)

        with pytest.raises(DisconnectionError):
            await db_session.execute_with_retry(query_func, max_retries=2)

    @pytest.mark.asyncio
    async def test_execute_with_retry_non_retryable(self):
        """Test query execution with non-retryable error."""
        mock_session = AsyncMock(spec=AsyncSession)
        db_session = DatabaseSession(mock_session)

        async def query_func(session):
            raise SQLAlchemyError("Non-retryable error")

        with pytest.raises(SQLAlchemyError):
            await db_session.execute_with_retry(query_func, max_retries=2)

    @pytest.mark.asyncio
    async def test_commit_with_retry_success(self):
        """Test successful commit with retry logic."""
        mock_session = AsyncMock(spec=AsyncSession)
        db_session = DatabaseSession(mock_session)

        result = await db_session.commit_with_retry()
        assert result is True
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_commit_with_retry_failure(self):
        """Test commit failure with retry logic."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.commit.side_effect = SQLAlchemyError("Commit failed")
        db_session = DatabaseSession(mock_session)

        result = await db_session.commit_with_retry()
        assert result is False
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test session closing."""
        mock_session = AsyncMock(spec=AsyncSession)
        db_session = DatabaseSession(mock_session)

        await db_session.close()
        mock_session.close.assert_called_once()
        assert db_session._closed is True


class TestSessionContextManagers:
    """Test session context managers."""

    @pytest.mark.asyncio
    async def test_get_session_success(self):
        """Test successful session context manager."""
        with patch('database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            async with get_session() as db:
                assert isinstance(db, DatabaseSession)
                assert db.session == mock_session

            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_with_exception(self):
        """Test session context manager with exception."""
        with patch('database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            try:
                async with get_session() as db:
                    raise Exception("Test exception")
            except Exception:
                pass

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transaction_success(self):
        """Test successful transaction context manager."""
        with patch('database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            async with get_transaction() as db:
                assert isinstance(db, DatabaseSession)

            # Should commit and close
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_transaction_with_exception(self):
        """Test transaction context manager with exception."""
        with patch('database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            try:
                async with get_transaction() as db:
                    raise Exception("Test exception")
            except Exception:
                pass

            # Should rollback and close
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()


class TestSessionDecorators:
    """Test session decorators."""

    @pytest.mark.asyncio
    async def test_with_database_session_decorator(self):
        """Test database session decorator."""

        @with_database_session
        async def test_function(session: DatabaseSession, arg1: str):
            assert isinstance(session, DatabaseSession)
            return f"result_{arg1}"

        with patch('database.session.get_session') as mock_get_session:
            mock_db_session = MagicMock(spec=DatabaseSession)
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            result = await test_function("test")
            assert result == "result_test"

    @pytest.mark.asyncio
    async def test_with_database_transaction_decorator(self):
        """Test database transaction decorator."""

        @with_database_transaction
        async def test_function(session: DatabaseSession, arg1: str):
            assert isinstance(session, DatabaseSession)
            return f"transaction_{arg1}"

        with patch('database.session.get_transaction') as mock_get_transaction:
            mock_db_session = MagicMock(spec=DatabaseSession)
            mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

            result = await test_function("test")
            assert result == "transaction_test"


class TestSessionManager:
    """Test SessionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh SessionManager for testing."""
        return SessionManager()

    @pytest.mark.asyncio
    async def test_create_session(self, manager):
        """Test session creation."""
        with patch('database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            db_session = await manager.create_session("test_session")

            assert isinstance(db_session, DatabaseSession)
            assert "test_session" in manager._sessions
            assert manager.session_count == 1

    @pytest.mark.asyncio
    async def test_get_session(self, manager):
        """Test getting existing session."""
        with patch('database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            # Create session first
            created_session = await manager.create_session("test_session")

            # Get the session
            retrieved_session = await manager.get_session("test_session")

            assert retrieved_session == created_session

    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, manager):
        """Test getting non-existent session."""
        session = await manager.get_session("nonexistent")
        assert session is None

    @pytest.mark.asyncio
    async def test_close_session(self, manager):
        """Test closing specific session."""
        with patch('database.session.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            await manager.create_session("test_session")
            result = await manager.close_session("test_session")

            assert result is True
            assert "test_session" not in manager._sessions
            assert manager.session_count == 0
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_nonexistent_session(self, manager):
        """Test closing non-existent session."""
        result = await manager.close_session("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_close_all_sessions(self, manager):
        """Test closing all sessions."""
        with patch('database.session.AsyncSessionLocal') as mock_session_local:
            mock_session1 = AsyncMock(spec=AsyncSession)
            mock_session2 = AsyncMock(spec=AsyncSession)
            mock_session_local.side_effect = [mock_session1, mock_session2]

            await manager.create_session("session1")
            await manager.create_session("session2")

            assert manager.session_count == 2

            await manager.close_all_sessions()

            assert manager.session_count == 0
            mock_session1.close.assert_called_once()
            mock_session2.close.assert_called_once()

    def test_active_sessions_property(self, manager):
        """Test active sessions property."""
        assert manager.active_sessions == []

        # Add some mock sessions directly to test the property
        manager._sessions["session1"] = MagicMock()
        manager._sessions["session2"] = MagicMock()

        active = manager.active_sessions
        assert len(active) == 2
        assert "session1" in active
        assert "session2" in active


class TestUtilityFunctions:
    """Test utility functions."""

    @pytest.mark.asyncio
    async def test_execute_raw_sql_with_fetch_one(self):
        """Test raw SQL execution with fetch_one."""
        with patch('database.session.get_session') as mock_get_session:
            mock_db_session = AsyncMock(spec=DatabaseSession)
            mock_result = AsyncMock()
            mock_result.fetchone.return_value = ("result",)

            async def mock_execute_with_retry(func):
                return mock_result

            mock_db_session.execute_with_retry = mock_execute_with_retry
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            result = await execute_raw_sql("SELECT 1", fetch_one=True)
            assert result == ("result",)

    @pytest.mark.asyncio
    async def test_execute_raw_sql_with_fetch_all(self):
        """Test raw SQL execution with fetch_all."""
        with patch('database.session.get_session') as mock_get_session:
            mock_db_session = AsyncMock(spec=DatabaseSession)
            mock_result = AsyncMock()
            mock_result.fetchall.return_value = [("result1",), ("result2",)]

            async def mock_execute_with_retry(func):
                return mock_result

            mock_db_session.execute_with_retry = mock_execute_with_retry
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            result = await execute_raw_sql("SELECT * FROM test", fetch_all=True)
            assert result == [("result1",), ("result2",)]

    @pytest.mark.asyncio
    async def test_check_session_health_success(self):
        """Test successful session health check."""
        with patch('database.session.get_session') as mock_get_session, \
             patch('database.session.get_transaction') as mock_get_transaction:

            # Mock successful session operations
            mock_db_session = AsyncMock(spec=DatabaseSession)
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 1

            async def mock_execute_with_retry(func):
                return mock_result

            mock_db_session.execute_with_retry = mock_execute_with_retry
            mock_get_session.return_value.__aenter__.return_value = mock_db_session
            mock_get_transaction.return_value.__aenter__.return_value = mock_db_session

            health = await check_session_health()

            assert health["status"] == "healthy"
            assert health["session_creation"] is True
            assert health["query_execution"] is True
            assert health["transaction_handling"] is True

    @pytest.mark.asyncio
    async def test_check_session_health_failure(self):
        """Test session health check failure."""
        with patch('database.session.get_session') as mock_get_session:
            mock_get_session.side_effect = Exception("Session creation failed")

            health = await check_session_health()

            assert health["status"] == "unhealthy"
            assert "Session creation failed" in health["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])