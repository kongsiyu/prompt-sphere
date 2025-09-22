"""Tests for database migration framework."""

import os
import tempfile
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import AsyncSessionLocal, engine
from database.migration_base import Migration, MigrationError, MigrationExecutionError, MigrationValidationError
from database.migration_manager import MigrationManager
from database.migration_tracker import MigrationHistory, MigrationTracker


class TestMigration(Migration):
    """Test migration class."""

    def __init__(self, version: str = "20250922_000001", description: str = "Test migration"):
        super().__init__(version, description)

    async def upgrade(self, session: AsyncSession) -> None:
        """Test upgrade implementation."""
        await session.execute(text("CREATE TABLE test_table (id INT PRIMARY KEY)"))

    async def downgrade(self, session: AsyncSession) -> None:
        """Test downgrade implementation."""
        await session.execute(text("DROP TABLE IF EXISTS test_table"))


class TestMigrationWithError(Migration):
    """Test migration that raises an error."""

    def __init__(self):
        super().__init__("20250922_000002", "Migration with error")

    async def upgrade(self, session: AsyncSession) -> None:
        """Upgrade that raises an error."""
        raise Exception("Test error")

    async def downgrade(self, session: AsyncSession) -> None:
        """Downgrade that raises an error."""
        raise Exception("Test downgrade error")


@pytest.fixture
async def test_session():
    """Create test database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
async def migration_tracker(test_session):
    """Create migration tracker for testing."""
    tracker = MigrationTracker(test_session)
    await tracker.ensure_migration_table_exists()
    return tracker


class TestMigrationBase:
    """Test migration base class."""

    def test_migration_init(self):
        """Test migration initialization."""
        migration = TestMigration()
        assert migration.version == "20250922_000001"
        assert migration.description == "Test migration"
        assert migration.created_at is not None

    def test_migration_str(self):
        """Test migration string representation."""
        migration = TestMigration()
        assert str(migration) == "Migration 20250922_000001: Test migration"

    def test_migration_repr(self):
        """Test migration detailed representation."""
        migration = TestMigration()
        expected = "Migration(version='20250922_000001', description='Test migration')"
        assert repr(migration) == expected


class TestMigrationTracker:
    """Test migration tracking functionality."""

    async def test_ensure_migration_table_exists(self, migration_tracker):
        """Test migration table creation."""
        # Table should exist after fixture setup
        result = await migration_tracker.session.execute(
            text("SHOW TABLES LIKE 'migration_history'")
        )
        assert result.fetchone() is not None

    async def test_get_applied_migrations_empty(self, migration_tracker):
        """Test getting applied migrations when none exist."""
        applied = await migration_tracker.get_applied_migrations()
        assert applied == []

    async def test_record_and_get_migration(self, migration_tracker):
        """Test recording and retrieving migrations."""
        version = "20250922_000001"
        description = "Test migration"

        await migration_tracker.record_migration(version, description, 100, "checksum123")

        applied = await migration_tracker.get_applied_migrations()
        assert version in applied

        is_applied = await migration_tracker.is_migration_applied(version)
        assert is_applied is True

    async def test_remove_migration(self, migration_tracker):
        """Test removing migration record."""
        version = "20250922_000001"
        description = "Test migration"

        # First record a migration
        await migration_tracker.record_migration(version, description)
        assert await migration_tracker.is_migration_applied(version) is True

        # Then remove it
        removed = await migration_tracker.remove_migration(version)
        assert removed is True
        assert await migration_tracker.is_migration_applied(version) is False

        # Try removing non-existent migration
        removed = await migration_tracker.remove_migration("nonexistent")
        assert removed is False

    async def test_get_migration_history(self, migration_tracker):
        """Test getting migration history."""
        # Record multiple migrations
        await migration_tracker.record_migration("20250922_000001", "First migration")
        await migration_tracker.record_migration("20250922_000002", "Second migration")

        history = await migration_tracker.get_migration_history()
        assert len(history) == 2
        assert all(isinstance(h, MigrationHistory) for h in history)

    async def test_get_last_applied_migration(self, migration_tracker):
        """Test getting last applied migration."""
        # Initially no migrations
        last = await migration_tracker.get_last_applied_migration()
        assert last is None

        # Record migrations
        await migration_tracker.record_migration("20250922_000001", "First migration")
        await migration_tracker.record_migration("20250922_000003", "Third migration")
        await migration_tracker.record_migration("20250922_000002", "Second migration")

        last = await migration_tracker.get_last_applied_migration()
        assert last == "20250922_000003"  # Latest version, not last recorded


class TestMigrationManager:
    """Test migration manager functionality."""

    @pytest.fixture
    def temp_migrations_dir(self):
        """Create temporary migrations directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_init(self, temp_migrations_dir):
        """Test migration manager initialization."""
        manager = MigrationManager(temp_migrations_dir)
        assert manager.migrations_path == temp_migrations_dir

    def test_version_format_validation(self):
        """Test migration version format validation."""
        manager = MigrationManager()

        # Valid formats
        assert manager._is_valid_version_format("20250922_123456") is True
        assert manager._is_valid_version_format("20251231_235959") is True

        # Invalid formats
        assert manager._is_valid_version_format("2025922_123456") is False  # Wrong date format
        assert manager._is_valid_version_format("20250922-123456") is False  # Wrong separator
        assert manager._is_valid_version_format("20250922_1234567") is False  # Too long
        assert manager._is_valid_version_format("20250922_12345") is False  # Too short
        assert manager._is_valid_version_format("20251301_123456") is False  # Invalid month
        assert manager._is_valid_version_format("20250932_123456") is False  # Invalid day
        assert manager._is_valid_version_format("20250922_253456") is False  # Invalid hour
        assert manager._is_valid_version_format("20250922_126556") is False  # Invalid minute
        assert manager._is_valid_version_format("20250922_123466") is False  # Invalid second

    @patch('database.migration_manager.MigrationManager._discover_migrations')
    async def test_validate_migrations_success(self, mock_discover):
        """Test successful migration validation."""
        mock_discover.return_value = [TestMigration]

        manager = MigrationManager()
        await manager.validate_migrations()  # Should not raise

    @patch('database.migration_manager.MigrationManager._discover_migrations')
    async def test_validate_migrations_duplicate_version(self, mock_discover):
        """Test validation failure with duplicate versions."""
        # Two migrations with same version
        class Migration1(Migration):
            def __init__(self):
                super().__init__("20250922_000001", "First")
            async def upgrade(self, session): pass
            async def downgrade(self, session): pass

        class Migration2(Migration):
            def __init__(self):
                super().__init__("20250922_000001", "Second")  # Same version
            async def upgrade(self, session): pass
            async def downgrade(self, session): pass

        mock_discover.return_value = [Migration1, Migration2]

        manager = MigrationManager()
        with pytest.raises(MigrationValidationError, match="Duplicate migration version"):
            await manager.validate_migrations()

    @patch('database.migration_manager.MigrationManager._discover_migrations')
    async def test_validate_migrations_invalid_format(self, mock_discover):
        """Test validation failure with invalid version format."""
        class InvalidMigration(Migration):
            def __init__(self):
                super().__init__("invalid_version", "Invalid")
            async def upgrade(self, session): pass
            async def downgrade(self, session): pass

        mock_discover.return_value = [InvalidMigration]

        manager = MigrationManager()
        with pytest.raises(MigrationValidationError, match="Invalid version format"):
            await manager.validate_migrations()

    @patch('database.migration_manager.MigrationManager._discover_migrations')
    @patch('database.migration_manager.get_db')
    async def test_migrate_up_success(self, mock_get_db, mock_discover):
        """Test successful migration up."""
        # Mock session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session

        # Mock tracker
        mock_tracker = AsyncMock()
        mock_tracker.get_applied_migrations.return_value = []

        mock_discover.return_value = [TestMigration]

        manager = MigrationManager()

        # Mock the tracker creation
        with patch('database.migration_manager.MigrationTracker', return_value=mock_tracker):
            applied = await manager.migrate_up()

        assert len(applied) == 1
        assert applied[0] == "20250922_000001"
        mock_tracker.record_migration.assert_called_once()

    @patch('database.migration_manager.MigrationManager._discover_migrations')
    @patch('database.migration_manager.get_db')
    async def test_migrate_up_with_error(self, mock_get_db, mock_discover):
        """Test migration up with error."""
        # Mock session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session

        # Mock tracker
        mock_tracker = AsyncMock()
        mock_tracker.get_applied_migrations.return_value = []

        mock_discover.return_value = [TestMigrationWithError]

        manager = MigrationManager()

        with patch('database.migration_manager.MigrationTracker', return_value=mock_tracker):
            with pytest.raises(MigrationExecutionError, match="Failed to apply migration"):
                await manager.migrate_up()

        mock_session.rollback.assert_called_once()

    @patch('database.migration_manager.MigrationManager._discover_migrations')
    @patch('database.migration_manager.get_db')
    async def test_migrate_down_success(self, mock_get_db, mock_discover):
        """Test successful migration down."""
        # Mock session
        mock_session = AsyncMock()
        mock_get_db.return_value.__aenter__.return_value = mock_session

        # Mock tracker
        mock_tracker = AsyncMock()
        mock_tracker.get_applied_migrations.return_value = ["20250922_000001"]

        mock_discover.return_value = [TestMigration]

        manager = MigrationManager()

        with patch('database.migration_manager.MigrationTracker', return_value=mock_tracker):
            rolled_back = await manager.migrate_down(steps=1)

        assert len(rolled_back) == 1
        assert rolled_back[0] == "20250922_000001"
        mock_tracker.remove_migration.assert_called_once()

    async def test_get_migration_status(self):
        """Test getting migration status."""
        with patch('database.migration_manager.MigrationManager._discover_migrations') as mock_discover:
            with patch('database.migration_manager.get_db') as mock_get_db:
                # Mock session
                mock_session = AsyncMock()
                mock_get_db.return_value.__aenter__.return_value = mock_session

                # Mock tracker
                mock_tracker = AsyncMock()
                mock_tracker.get_applied_migrations.return_value = ["20250922_000001"]
                mock_tracker.get_last_applied_migration.return_value = "20250922_000001"

                mock_discover.return_value = [TestMigration]

                manager = MigrationManager()

                with patch('database.migration_manager.MigrationTracker', return_value=mock_tracker):
                    status = await manager.get_migration_status()

                assert status["total_migrations"] == 1
                assert status["applied_migrations"] == 1
                assert status["pending_migrations"] == 0
                assert status["last_applied"] == "20250922_000001"


class TestMigrationIntegration:
    """Integration tests for migration system."""

    async def test_end_to_end_migration_flow(self):
        """Test complete migration flow."""
        # This test would require a real test database
        # For now, we'll test the components work together

        manager = MigrationManager()

        # Test that status can be retrieved
        with patch('database.migration_manager.get_db') as mock_get_db:
            mock_session = AsyncMock()
            mock_get_db.return_value.__aenter__.return_value = mock_session

            mock_tracker = AsyncMock()
            mock_tracker.get_applied_migrations.return_value = []
            mock_tracker.get_last_applied_migration.return_value = None

            with patch('database.migration_manager.MigrationTracker', return_value=mock_tracker):
                status = await manager.get_migration_status()

            assert "total_migrations" in status
            assert "applied_migrations" in status
            assert "pending_migrations" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])