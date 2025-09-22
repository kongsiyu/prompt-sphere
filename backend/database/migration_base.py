"""Base classes and interfaces for database migrations."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


class Migration(ABC):
    """Base class for all database migrations."""

    def __init__(self, version: str, description: str):
        """
        Initialize migration.

        Args:
            version: Migration version (timestamp format: YYYYMMDD_HHMMSS)
            description: Human-readable description of the migration
        """
        self.version = version
        self.description = description
        self.created_at = datetime.utcnow()

    @abstractmethod
    async def upgrade(self, session: AsyncSession) -> None:
        """
        Apply the migration (forward operation).

        Args:
            session: Database session
        """
        pass

    @abstractmethod
    async def downgrade(self, session: AsyncSession) -> None:
        """
        Reverse the migration (rollback operation).

        Args:
            session: Database session
        """
        pass

    def __str__(self) -> str:
        """String representation of the migration."""
        return f"Migration {self.version}: {self.description}"

    def __repr__(self) -> str:
        """Detailed string representation of the migration."""
        return f"Migration(version='{self.version}', description='{self.description}')"


class MigrationError(Exception):
    """Base exception for migration-related errors."""
    pass


class MigrationValidationError(MigrationError):
    """Exception raised when migration validation fails."""
    pass


class MigrationExecutionError(MigrationError):
    """Exception raised when migration execution fails."""
    pass


class MigrationRollbackError(MigrationError):
    """Exception raised when migration rollback fails."""
    pass