"""Migration tracking and status management."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import Base


class MigrationHistory(Base):
    """Model to track applied migrations."""

    __tablename__ = "migration_history"

    version = Column(String(20), primary_key=True, index=True)
    description = Column(Text, nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    checksum = Column(String(64), nullable=True)  # For integrity checking
    execution_time_ms = Column(String(10), nullable=True)  # Execution time in milliseconds

    def __repr__(self) -> str:
        """String representation of migration history entry."""
        return f"<MigrationHistory(version='{self.version}', applied_at='{self.applied_at}')>"


class MigrationTracker:
    """Tracks migration status and history."""

    def __init__(self, session: AsyncSession):
        """
        Initialize migration tracker.

        Args:
            session: Database session
        """
        self.session = session

    async def ensure_migration_table_exists(self) -> None:
        """Ensure the migration history table exists."""
        # Import here to avoid circular imports
        from .connection import engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all, tables=[MigrationHistory.__table__])

    async def get_applied_migrations(self) -> List[str]:
        """
        Get list of applied migration versions.

        Returns:
            List of applied migration versions sorted by version
        """
        result = await self.session.execute(
            select(MigrationHistory.version).order_by(MigrationHistory.version)
        )
        return [row[0] for row in result.fetchall()]

    async def is_migration_applied(self, version: str) -> bool:
        """
        Check if a migration has been applied.

        Args:
            version: Migration version to check

        Returns:
            True if migration has been applied, False otherwise
        """
        result = await self.session.execute(
            select(MigrationHistory).where(MigrationHistory.version == version)
        )
        return result.fetchone() is not None

    async def record_migration(
        self,
        version: str,
        description: str,
        execution_time_ms: Optional[int] = None,
        checksum: Optional[str] = None
    ) -> None:
        """
        Record a successful migration application.

        Args:
            version: Migration version
            description: Migration description
            execution_time_ms: Execution time in milliseconds
            checksum: Migration checksum for integrity checking
        """
        migration_record = MigrationHistory(
            version=version,
            description=description,
            applied_at=datetime.utcnow(),
            execution_time_ms=str(execution_time_ms) if execution_time_ms else None,
            checksum=checksum
        )

        self.session.add(migration_record)
        await self.session.commit()

    async def remove_migration(self, version: str) -> bool:
        """
        Remove a migration record (for rollbacks).

        Args:
            version: Migration version to remove

        Returns:
            True if migration was removed, False if it wasn't found
        """
        result = await self.session.execute(
            select(MigrationHistory).where(MigrationHistory.version == version)
        )
        migration = result.fetchone()

        if migration:
            await self.session.delete(migration[0])
            await self.session.commit()
            return True

        return False

    async def get_migration_history(self) -> List[MigrationHistory]:
        """
        Get full migration history ordered by application time.

        Returns:
            List of migration history entries
        """
        result = await self.session.execute(
            select(MigrationHistory).order_by(MigrationHistory.applied_at)
        )
        return [row[0] for row in result.fetchall()]

    async def get_last_applied_migration(self) -> Optional[str]:
        """
        Get the version of the last applied migration.

        Returns:
            Version of the last applied migration, or None if no migrations applied
        """
        result = await self.session.execute(
            select(MigrationHistory.version)
            .order_by(MigrationHistory.version.desc())
            .limit(1)
        )
        row = result.fetchone()
        return row[0] if row else None