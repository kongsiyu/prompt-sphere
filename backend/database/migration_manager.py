"""Migration manager for executing and managing database migrations."""

import hashlib
import importlib
import os
import time
from typing import List, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession

from .connection import get_async_session
from .migration_base import Migration, MigrationError, MigrationExecutionError, MigrationValidationError
from .migration_tracker import MigrationTracker


class MigrationManager:
    """Manages database migration execution and tracking."""

    def __init__(self, migrations_path: str = "backend/database/migrations"):
        """
        Initialize migration manager.

        Args:
            migrations_path: Path to migration files directory
        """
        self.migrations_path = migrations_path
        self._migrations_cache: Optional[List[Type[Migration]]] = None

    def _discover_migrations(self) -> List[Type[Migration]]:
        """
        Discover all migration classes from the migrations directory.

        Returns:
            List of migration classes sorted by version
        """
        if self._migrations_cache is not None:
            return self._migrations_cache

        migrations = []
        migrations_dir = os.path.abspath(self.migrations_path)

        if not os.path.exists(migrations_dir):
            self._migrations_cache = []
            return []

        # Get all Python files in migrations directory
        for filename in os.listdir(migrations_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = filename[:-3]  # Remove .py extension

                try:
                    # Import the migration module
                    module_path = f"database.migrations.{module_name}"
                    module = importlib.import_module(module_path)

                    # Look for Migration subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type) and
                            issubclass(attr, Migration) and
                            attr is not Migration
                        ):
                            migrations.append(attr)

                except ImportError as e:
                    raise MigrationError(f"Failed to import migration {module_name}: {e}")

        # Sort migrations by version
        migrations.sort(key=lambda m: m("", "").version)
        self._migrations_cache = migrations
        return migrations

    def _calculate_migration_checksum(self, migration_class: Type[Migration]) -> str:
        """
        Calculate checksum for migration integrity checking.

        Args:
            migration_class: Migration class

        Returns:
            SHA-256 checksum of the migration
        """
        # Get the source code of the migration
        import inspect
        source = inspect.getsource(migration_class)
        return hashlib.sha256(source.encode()).hexdigest()

    async def validate_migrations(self) -> None:
        """
        Validate all discovered migrations.

        Raises:
            MigrationValidationError: If validation fails
        """
        migrations = self._discover_migrations()
        versions = set()

        for migration_class in migrations:
            migration = migration_class("", "")

            # Check for duplicate versions
            if migration.version in versions:
                raise MigrationValidationError(
                    f"Duplicate migration version: {migration.version}"
                )
            versions.add(migration.version)

            # Validate version format (YYYYMMDD_HHMMSS)
            if not self._is_valid_version_format(migration.version):
                raise MigrationValidationError(
                    f"Invalid version format for migration {migration.version}. "
                    "Expected format: YYYYMMDD_HHMMSS"
                )

    def _is_valid_version_format(self, version: str) -> bool:
        """
        Validate migration version format.

        Args:
            version: Version string to validate

        Returns:
            True if version format is valid
        """
        try:
            # Check if version matches YYYYMMDD_HHMMSS format
            if len(version) != 15 or version[8] != "_":
                return False

            date_part = version[:8]
            time_part = version[9:]

            # Validate date part (YYYYMMDD)
            year = int(date_part[:4])
            month = int(date_part[4:6])
            day = int(date_part[6:8])

            if year < 2020 or month < 1 or month > 12 or day < 1 or day > 31:
                return False

            # Validate time part (HHMMSS)
            hour = int(time_part[:2])
            minute = int(time_part[2:4])
            second = int(time_part[4:6])

            if hour > 23 or minute > 59 or second > 59:
                return False

            return True

        except ValueError:
            return False

    async def get_pending_migrations(self) -> List[Type[Migration]]:
        """
        Get list of pending (unapplied) migrations.

        Returns:
            List of pending migration classes
        """
        async with get_async_session() as session:
            tracker = MigrationTracker(session)
            await tracker.ensure_migration_table_exists()

            applied_versions = await tracker.get_applied_migrations()
            all_migrations = self._discover_migrations()

            pending = []
            for migration_class in all_migrations:
                migration = migration_class("", "")
                if migration.version not in applied_versions:
                    pending.append(migration_class)

            return pending

    async def migrate_up(self, target_version: Optional[str] = None) -> List[str]:
        """
        Run pending migrations up to target version.

        Args:
            target_version: Version to migrate to (latest if None)

        Returns:
            List of applied migration versions

        Raises:
            MigrationExecutionError: If migration execution fails
        """
        await self.validate_migrations()
        pending_migrations = await self.get_pending_migrations()

        if target_version:
            # Filter migrations up to target version
            pending_migrations = [
                m for m in pending_migrations
                if m("", "").version <= target_version
            ]

        applied_versions = []

        async with get_async_session() as session:
            tracker = MigrationTracker(session)

            for migration_class in pending_migrations:
                migration_instance = migration_class("", "")
                version = migration_instance.version

                try:
                    start_time = time.time()
                    await migration_instance.upgrade(session)
                    execution_time = int((time.time() - start_time) * 1000)

                    checksum = self._calculate_migration_checksum(migration_class)
                    await tracker.record_migration(
                        version=version,
                        description=migration_instance.description,
                        execution_time_ms=execution_time,
                        checksum=checksum
                    )

                    applied_versions.append(version)

                except Exception as e:
                    await session.rollback()
                    raise MigrationExecutionError(
                        f"Failed to apply migration {version}: {e}"
                    ) from e

        return applied_versions

    async def migrate_down(self, target_version: Optional[str] = None, steps: int = 1) -> List[str]:
        """
        Rollback migrations.

        Args:
            target_version: Version to rollback to
            steps: Number of migrations to rollback (if target_version not specified)

        Returns:
            List of rolled back migration versions

        Raises:
            MigrationExecutionError: If rollback fails
        """
        async with get_async_session() as session:
            tracker = MigrationTracker(session)
            applied_versions = await tracker.get_applied_migrations()

            if not applied_versions:
                return []

            # Determine which migrations to rollback
            if target_version:
                # Rollback to specific version
                rollback_versions = [v for v in applied_versions if v > target_version]
            else:
                # Rollback specified number of steps
                rollback_versions = applied_versions[-steps:]

            rollback_versions.reverse()  # Rollback in reverse order
            rolled_back = []

            all_migrations = self._discover_migrations()
            migration_map = {m("", "").version: m for m in all_migrations}

            for version in rollback_versions:
                if version not in migration_map:
                    raise MigrationExecutionError(
                        f"Migration {version} not found for rollback"
                    )

                migration_class = migration_map[version]
                migration_instance = migration_class("", "")

                try:
                    await migration_instance.downgrade(session)
                    await tracker.remove_migration(version)
                    rolled_back.append(version)

                except Exception as e:
                    await session.rollback()
                    raise MigrationExecutionError(
                        f"Failed to rollback migration {version}: {e}"
                    ) from e

        return rolled_back

    async def get_migration_status(self) -> dict:
        """
        Get current migration status.

        Returns:
            Dictionary with migration status information
        """
        async with get_async_session() as session:
            tracker = MigrationTracker(session)
            await tracker.ensure_migration_table_exists()

            applied_versions = await tracker.get_applied_migrations()
            all_migrations = self._discover_migrations()
            pending_migrations = await self.get_pending_migrations()

            return {
                "total_migrations": len(all_migrations),
                "applied_migrations": len(applied_versions),
                "pending_migrations": len(pending_migrations),
                "last_applied": await tracker.get_last_applied_migration(),
                "applied_versions": applied_versions,
                "pending_versions": [m("", "").version for m in pending_migrations]
            }