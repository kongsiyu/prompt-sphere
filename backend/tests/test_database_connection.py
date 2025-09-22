"""Tests for database connection and configuration."""

from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import (
    Base, get_db, close_database, create_database_tables, drop_database_tables,
    check_database_health, get_connection_pool_stats, test_database_connection,
    init_database, get_db_session
)


class TestDatabaseConnection:
    """Test database connection functionality."""

    def test_base_class(self):
        """Test Base class exists and is properly configured."""
        assert Base is not None
        assert hasattr(Base, 'metadata')

    @pytest.mark.asyncio
    async def test_get_db_session(self):
        """Test database session creation and cleanup."""
        with patch('database.connection.AsyncSessionLocal') as mock_session_local:
            # Mock the session
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            # Create context manager mock
            async_context = mock_session_local.return_value

            # Test the generator
            async for session in get_db():
                assert session == mock_session
                break

    @pytest.mark.asyncio
    async def test_get_db_session_with_exception(self):
        """Test database session rollback on exception."""
        with patch('database.connection.AsyncSessionLocal') as mock_session_local:
            # Mock the session
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value.__aenter__.return_value = mock_session
            mock_session_local.return_value.__aexit__.return_value = None

            # Simulate an exception during session use
            try:
                async for session in get_db():
                    # Simulate an exception
                    raise Exception("Test exception")
            except Exception:
                pass

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_database_tables(self):
        """Test database table creation."""
        with patch('database.connection.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            await create_database_tables()

            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_drop_database_tables(self):
        """Test database table dropping."""
        with patch('database.connection.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            await drop_database_tables()

            mock_conn.run_sync.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_database(self):
        """Test database engine disposal."""
        with patch('database.connection.engine') as mock_engine:
            await close_database()
            mock_engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_context_manager(self):
        """Test database session context manager."""
        with patch('database.connection.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            async with get_db_session() as session:
                assert isinstance(session, AsyncSession)
                # Session should not be committed yet during context
                mock_session.commit.assert_not_called()

            # Session should be committed and closed after context
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_db_session_with_exception(self):
        """Test database session context manager with exception."""
        with patch('database.connection.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock(spec=AsyncSession)
            mock_session_local.return_value = mock_session

            try:
                async with get_db_session() as session:
                    raise Exception("Test exception")
            except Exception:
                pass

            # Session should be rolled back and closed on exception
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_health_success(self):
        """Test successful database health check."""
        with patch('database.connection.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            # Mock successful health check query
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 1
            mock_conn.execute.return_value = mock_result

            # Mock version query
            mock_version_result = AsyncMock()
            mock_version_result.scalar.return_value = "MySQL 8.0.33"

            # Mock timestamp query
            mock_time_result = AsyncMock()
            mock_time_result.scalar.return_value = "2023-09-22 12:00:00"

            mock_conn.execute.side_effect = [
                mock_result,  # Health check
                mock_version_result,  # Version
                mock_time_result  # Timestamp
            ]

            # Mock pool stats
            mock_pool = MagicMock()
            mock_pool.size.return_value = 10
            mock_pool.checkedin.return_value = 8
            mock_pool.checkedout.return_value = 2
            mock_pool.overflow.return_value = 0
            mock_pool.invalidated.return_value = 0
            mock_engine.pool = mock_pool

            health = await check_database_health()

            assert health["status"] == "healthy"
            assert health["database_info"]["version"] == "MySQL 8.0.33"
            assert health["connection_pool"]["size"] == 10
            assert health["connection_pool"]["checked_out"] == 2

    @pytest.mark.asyncio
    async def test_check_database_health_failure(self):
        """Test database health check failure."""
        with patch('database.connection.engine') as mock_engine:
            mock_engine.begin.side_effect = Exception("Connection failed")

            health = await check_database_health()

            assert health["status"] == "unhealthy"
            assert "Connection failed" in health["error"]

    @pytest.mark.asyncio
    async def test_get_connection_pool_stats(self):
        """Test connection pool statistics."""
        with patch('database.connection.engine') as mock_engine:
            mock_pool = MagicMock()
            mock_pool.size.return_value = 10
            mock_pool.checkedin.return_value = 7
            mock_pool.checkedout.return_value = 3
            mock_pool.overflow.return_value = 2
            mock_pool.invalidated.return_value = 1
            mock_engine.pool = mock_pool

            stats = await get_connection_pool_stats()

            assert stats["pool_size"] == 10
            assert stats["checked_in_connections"] == 7
            assert stats["checked_out_connections"] == 3
            assert stats["overflow_connections"] == 2
            assert stats["invalidated_connections"] == 1
            assert stats["total_connections"] == 12  # size + overflow
            assert stats["available_connections"] == 7

    @pytest.mark.asyncio
    async def test_test_database_connection_success(self):
        """Test successful database connection test."""
        with patch('database.connection.engine') as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.begin.return_value.__aenter__.return_value = mock_conn

            result = await test_database_connection()

            assert result is True
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_database_connection_failure(self):
        """Test failed database connection test."""
        with patch('database.connection.engine') as mock_engine:
            mock_engine.begin.side_effect = Exception("Connection failed")

            result = await test_database_connection()

            assert result is False

    @pytest.mark.asyncio
    async def test_init_database_success(self):
        """Test successful database initialization."""
        with patch('database.connection.test_database_connection') as mock_test, \
             patch('database.connection.create_database_tables') as mock_create, \
             patch('database.connection.check_database_health') as mock_health:

            mock_test.return_value = True
            mock_health.return_value = {"status": "healthy"}

            await init_database()

            mock_test.assert_called_once()
            mock_create.assert_called_once()
            mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_init_database_connection_failure(self):
        """Test database initialization with connection failure."""
        with patch('database.connection.test_database_connection') as mock_test:
            mock_test.return_value = False

            with pytest.raises(Exception, match="Cannot establish database connection"):
                await init_database()

    @pytest.mark.asyncio
    async def test_init_database_health_failure(self):
        """Test database initialization with health check failure."""
        with patch('database.connection.test_database_connection') as mock_test, \
             patch('database.connection.create_database_tables') as mock_create, \
             patch('database.connection.check_database_health') as mock_health:

            mock_test.return_value = True
            mock_health.return_value = {"status": "unhealthy", "error": "Health check failed"}

            with pytest.raises(Exception, match="Database initialization failed"):
                await init_database()


class TestDatabaseConfiguration:
    """Test database configuration."""

    def test_database_url_construction(self):
        """Test database URL is properly constructed from settings."""
        from app.core.config import settings

        # Verify database configuration exists
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'database_host')
        assert hasattr(settings, 'database_port')
        assert hasattr(settings, 'database_user')
        assert hasattr(settings, 'database_password')
        assert hasattr(settings, 'database_name')

        # Verify defaults
        assert settings.database_host == "localhost"
        assert settings.database_port == 3306
        assert settings.database_user == "root"
        assert settings.database_name == "prompt_sphere"

    def test_connection_pool_settings(self):
        """Test connection pool configuration."""
        from app.core.config import settings

        assert hasattr(settings, 'database_pool_size')
        assert hasattr(settings, 'database_max_overflow')
        assert settings.database_pool_size == 10
        assert settings.database_max_overflow == 20

    @patch.dict('os.environ', {
        'DB_HOST': 'test-host',
        'DB_PORT': '5432',
        'DB_USER': 'test-user',
        'DB_PASSWORD': 'test-pass',
        'DB_NAME': 'test-db'
    })
    def test_database_config_from_env(self):
        """Test database configuration from environment variables."""
        from app.core.config import Settings

        # Create new settings instance to pick up env vars
        test_settings = Settings()

        assert test_settings.database_host == 'test-host'
        assert test_settings.database_port == 5432
        assert test_settings.database_user == 'test-user'
        assert test_settings.database_password == 'test-pass'
        assert test_settings.database_name == 'test-db'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])