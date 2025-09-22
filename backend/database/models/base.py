"""
Base model class with common functionality for all database models.
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, DateTime, String, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import CHAR


Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common fields and functionality.
    """
    __abstract__ = True

    # Primary key using UUID
    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        server_default=text("(UUID())")
    )

    # Timestamp fields
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )

    # Soft delete support
    deleted_at = Column(DateTime, nullable=True, default=None)

    def soft_delete(self) -> None:
        """Mark record as deleted without actually deleting it."""
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.deleted_at = None

    @property
    def is_deleted(self) -> bool:
        """Check if record is soft-deleted."""
        return self.deleted_at is not None

    def to_dict(self, exclude_deleted: bool = True) -> dict:
        """
        Convert model instance to dictionary.

        Args:
            exclude_deleted: Whether to exclude deleted_at field

        Returns:
            Dictionary representation of the model
        """
        data = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)

            # Convert datetime to ISO format
            if isinstance(value, datetime):
                value = value.isoformat()

            # Exclude deleted_at if requested and it's None
            if exclude_deleted and column.name == 'deleted_at' and value is None:
                continue

            data[column.name] = value

        return data

    def update_from_dict(self, data: dict, exclude_fields: Optional[list] = None) -> None:
        """
        Update model fields from dictionary.

        Args:
            data: Dictionary with field values
            exclude_fields: List of fields to exclude from update
        """
        if exclude_fields is None:
            exclude_fields = ['id', 'created_at', 'updated_at', 'deleted_at']

        for key, value in data.items():
            if key not in exclude_fields and hasattr(self, key):
                setattr(self, key, value)

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """
    Mixin for models that only need timestamps without soft delete.
    """
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    )


class AuditMixin:
    """
    Mixin for audit-related fields.
    """
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP")
    )