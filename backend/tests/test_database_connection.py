"""Tests for database connection and configuration."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import Base, get_db, close_database, create_database_tables, drop_database_tables


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