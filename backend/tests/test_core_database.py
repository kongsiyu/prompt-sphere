"""Tests for core database management."""

from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from core.database import (
    DatabaseManager,
    db_manager,
    initialize_database,
    shutdown_database,
    get_database_health,
    get_database_info,
    run_maintenance,
    health_check_endpoint,
    database_lifespan
)


class TestDatabaseManager:
    """Test DatabaseManager class functionality."""

    @pytest.fixture
    def manager(self):
        """Create a fresh DatabaseManager for testing."""
        return DatabaseManager()

    def test_initial_state(self, manager):
        """Test initial state of DatabaseManager."""
        assert manager.is_initialized is False
        assert manager._migration_manager is None

    @pytest.mark.asyncio
    async def test_initialize_success(self, manager):
        """Test successful database initialization."""
        with patch('core.database.test_database_connection') as mock_test, \
             patch('core.database.MigrationManager') as mock_migration_cls, \
             patch('core.database.init_database') as mock_init:

            mock_test.return_value = True
            mock_migration_manager = AsyncMock()
            mock_migration_manager.get_pending_migrations.return_value = []
            mock_migration_cls.return_value = mock_migration_manager

            # Mock health check
            with patch.object(manager, 'get_comprehensive_health') as mock_health:
                mock_health.return_value = {"overall_status": "healthy"}

                await manager.initialize()

                assert manager.is_initialized is True
                mock_test.assert_called_once()
                mock_init.assert_called_once()
                mock_migration_manager.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_with_migrations(self, manager):
        """Test initialization with pending migrations."""
        with patch('core.database.test_database_connection') as mock_test, \
             patch('core.database.MigrationManager') as mock_migration_cls, \
             patch('core.database.init_database') as mock_init:

            mock_test.return_value = True
            mock_migration_manager = AsyncMock()
            mock_migration_manager.get_pending_migrations.return_value = ["migration1", "migration2"]
            mock_migration_cls.return_value = mock_migration_manager

            with patch.object(manager, 'get_comprehensive_health') as mock_health:
                mock_health.return_value = {"overall_status": "healthy"}

                await manager.initialize()

                assert manager.is_initialized is True
                assert mock_migration_manager.run_migration.call_count == 2

    @pytest.mark.asyncio
    async def test_initialize_without_migrations(self, manager):
        """Test initialization without running migrations."""
        with patch('core.database.test_database_connection') as mock_test, \
             patch('core.database.init_database') as mock_init:

            mock_test.return_value = True

            with patch.object(manager, 'get_comprehensive_health') as mock_health:
                mock_health.return_value = {"overall_status": "healthy"}

                await manager.initialize(run_migrations=False)

                assert manager.is_initialized is True
                assert manager._migration_manager is None

    @pytest.mark.asyncio
    async def test_initialize_connection_failure(self, manager):
        """Test initialization with connection failure."""
        with patch('core.database.test_database_connection') as mock_test:
            mock_test.return_value = False

            with pytest.raises(Exception, match="Failed to establish database connection"):
                await manager.initialize()

            assert manager.is_initialized is False

    @pytest.mark.asyncio
    async def test_initialize_health_failure(self, manager):
        """Test initialization with health check failure."""
        with patch('core.database.test_database_connection') as mock_test, \
             patch('core.database.init_database') as mock_init:

            mock_test.return_value = True

            with patch.object(manager, 'get_comprehensive_health') as mock_health:
                mock_health.return_value = {"overall_status": "unhealthy"}

                with pytest.raises(Exception, match="Database health check failed"):
                    await manager.initialize()

    @pytest.mark.asyncio
    async def test_shutdown(self, manager):
        """Test database shutdown."""
        with patch('core.database.session_manager') as mock_session_manager, \
             patch('core.database.close_database') as mock_close:

            manager._initialized = True

            await manager.shutdown()

            mock_session_manager.close_all_sessions.assert_called_once()
            mock_close.assert_called_once()
            assert manager.is_initialized is False

    @pytest.mark.asyncio
    async def test_reset_database_without_confirm(self, manager):
        """Test database reset without confirmation."""
        with pytest.raises(ValueError, match="Database reset requires explicit confirmation"):
            await manager.reset_database(confirm=False)

    @pytest.mark.asyncio
    async def test_reset_database_with_confirm(self, manager):
        """Test database reset with confirmation."""
        with patch('core.database.session_manager') as mock_session_manager, \
             patch('core.database.drop_database_tables') as mock_drop, \
             patch('core.database.create_database_tables') as mock_create:

            await manager.reset_database(confirm=True)

            mock_session_manager.close_all_sessions.assert_called_once()
            mock_drop.assert_called_once()
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_comprehensive_health(self, manager):
        """Test comprehensive health check."""
        with patch('core.database.check_database_health') as mock_conn_health, \
             patch('core.database.check_session_health') as mock_session_health, \
             patch('core.database.get_connection_pool_stats') as mock_pool_stats:

            mock_conn_health.return_value = {"status": "healthy"}
            mock_session_health.return_value = {"status": "healthy"}
            mock_pool_stats.return_value = {"pool_size": 10}

            health = await manager.get_comprehensive_health()

            assert health["overall_status"] == "healthy"
            assert health["connection_health"]["status"] == "healthy"
            assert health["session_health"]["status"] == "healthy"
            assert health["pool_stats"]["pool_size"] == 10

    @pytest.mark.asyncio
    async def test_get_comprehensive_health_degraded(self, manager):
        """Test comprehensive health check with degraded status."""
        with patch('core.database.check_database_health') as mock_conn_health, \
             patch('core.database.check_session_health') as mock_session_health, \
             patch('core.database.get_connection_pool_stats') as mock_pool_stats:

            mock_conn_health.return_value = {"status": "healthy"}
            mock_session_health.return_value = {"status": "unhealthy"}
            mock_pool_stats.return_value = {"pool_size": 10}

            health = await manager.get_comprehensive_health()

            assert health["overall_status"] == "degraded"

    @pytest.mark.asyncio
    async def test_get_comprehensive_health_unhealthy(self, manager):
        """Test comprehensive health check with unhealthy status."""
        with patch('core.database.check_database_health') as mock_conn_health, \
             patch('core.database.check_session_health') as mock_session_health, \
             patch('core.database.get_connection_pool_stats') as mock_pool_stats:

            mock_conn_health.return_value = {"status": "unhealthy"}
            mock_session_health.return_value = {"status": "unhealthy"}
            mock_pool_stats.return_value = {"pool_size": 10}

            health = await manager.get_comprehensive_health()

            assert health["overall_status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_get_database_info(self, manager):
        """Test database info retrieval."""
        with patch.object(manager, 'get_comprehensive_health') as mock_health:
            mock_health.return_value = {"overall_status": "healthy"}

            info = await manager.get_database_info()

            assert "configuration" in info
            assert "runtime" in info
            assert "health" in info
            assert info["configuration"]["database_name"] == "prompt_sphere"

    @pytest.mark.asyncio
    async def test_execute_maintenance_tasks(self, manager):
        """Test maintenance task execution."""
        with patch('core.database.session_manager') as mock_session_manager, \
             patch('core.database.get_connection_pool_stats') as mock_pool_stats, \
             patch('core.database.test_database_connection') as mock_test:

            mock_session_manager.session_count = 5
            mock_pool_stats.return_value = {"invalidated_connections": 0}
            mock_test.return_value = True

            results = await manager.execute_maintenance_tasks()

            assert len(results["tasks_executed"]) > 0
            assert len(results["errors"]) == 0
            assert "timestamp" in results

    @pytest.mark.asyncio
    async def test_backup_database_schema(self, manager):
        """Test database schema backup."""
        with patch('core.database.get_session') as mock_get_session:
            mock_db_session = AsyncMock()

            # Mock tables query
            mock_tables_result = AsyncMock()
            mock_tables_result.fetchall.return_value = [("users",), ("prompts",)]

            # Mock CREATE TABLE queries
            mock_create_result = AsyncMock()
            mock_create_result.fetchone.side_effect = [
                ("users", "CREATE TABLE users (id INT)"),
                ("prompts", "CREATE TABLE prompts (id INT)")
            ]

            async def mock_execute_with_retry(func):
                if "information_schema" in str(func):
                    return mock_tables_result
                else:
                    return mock_create_result

            mock_db_session.execute_with_retry = mock_execute_with_retry
            mock_get_session.return_value.__aenter__.return_value = mock_db_session

            schema_sql = await manager.backup_database_schema()

            assert "CREATE TABLE users" in schema_sql
            assert "CREATE TABLE prompts" in schema_sql

    @pytest.mark.asyncio
    async def test_maintenance_mode(self, manager):
        """Test maintenance mode context manager."""
        with patch('core.database.session_manager') as mock_session_manager:
            async with manager.maintenance_mode():
                # Inside maintenance mode
                pass

            # Should close all sessions when entering maintenance mode
            mock_session_manager.close_all_sessions.assert_called_once()


class TestGlobalFunctions:
    """Test global convenience functions."""

    @pytest.mark.asyncio
    async def test_initialize_database(self):
        """Test global initialize_database function."""
        with patch.object(db_manager, 'initialize') as mock_init:
            await initialize_database(run_migrations=False)
            mock_init.assert_called_once_with(False)

    @pytest.mark.asyncio
    async def test_shutdown_database(self):
        """Test global shutdown_database function."""
        with patch.object(db_manager, 'shutdown') as mock_shutdown:
            await shutdown_database()
            mock_shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_database_health(self):
        """Test global get_database_health function."""
        with patch.object(db_manager, 'get_comprehensive_health') as mock_health:
            mock_health.return_value = {"status": "healthy"}
            health = await get_database_health()
            assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_database_info(self):
        """Test global get_database_info function."""
        with patch.object(db_manager, 'get_database_info') as mock_info:
            mock_info.return_value = {"config": "test"}
            info = await get_database_info()
            assert info["config"] == "test"

    @pytest.mark.asyncio
    async def test_run_maintenance(self):
        """Test global run_maintenance function."""
        with patch.object(db_manager, 'execute_maintenance_tasks') as mock_maintenance:
            mock_maintenance.return_value = {"tasks": []}
            result = await run_maintenance()
            assert "tasks" in result

    @pytest.mark.asyncio
    async def test_health_check_endpoint_success(self):
        """Test health check endpoint helper with success."""
        with patch('core.database.get_database_health') as mock_health:
            mock_health.return_value = {
                "overall_status": "healthy",
                "connection_health": {"status": "healthy"},
                "session_health": {"status": "healthy"},
                "pool_stats": {"pool_size": 10, "checked_out_connections": 2},
                "timestamp": "2023-09-22T12:00:00"
            }

            result = await health_check_endpoint()

            assert result["status"] == "healthy"
            assert result["database"] is True
            assert result["sessions"] is True
            assert result["pool_size"] == 10
            assert result["active_connections"] == 2

    @pytest.mark.asyncio
    async def test_health_check_endpoint_failure(self):
        """Test health check endpoint helper with failure."""
        with patch('core.database.get_database_health') as mock_health:
            mock_health.side_effect = Exception("Health check failed")

            result = await health_check_endpoint()

            assert result["status"] == "unhealthy"
            assert "Health check failed" in result["error"]

    @pytest.mark.asyncio
    async def test_database_lifespan(self):
        """Test database lifespan context manager."""
        with patch('core.database.initialize_database') as mock_init, \
             patch('core.database.shutdown_database') as mock_shutdown:

            async with database_lifespan():
                # Inside lifespan
                pass

            mock_init.assert_called_once()
            mock_shutdown.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])