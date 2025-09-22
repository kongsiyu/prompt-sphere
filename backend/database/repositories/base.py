"""
Base repository class providing common CRUD operations.
"""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, Union
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from database.models.base import BaseModel

# Type variable for model classes
ModelType = TypeVar('ModelType', bound=BaseModel)

logger = logging.getLogger(__name__)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class BaseRepository(Generic[ModelType], ABC):
    """
    Base repository class providing common CRUD operations.

    This class implements the repository pattern with async SQLAlchemy support,
    providing a clean abstraction over database operations with proper error
    handling, logging, and performance optimizations.
    """

    def __init__(self, session: AsyncSession, model_class: type[ModelType]):
        """
        Initialize repository with session and model class.

        Args:
            session: Async SQLAlchemy session
            model_class: SQLAlchemy model class
        """
        self.session = session
        self.model_class = model_class
        self.logger = logging.getLogger(f"{__name__}.{model_class.__name__}Repository")

    @property
    @abstractmethod
    def model_class(self) -> type[ModelType]:
        """Return the model class for this repository."""
        pass

    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance

        Raises:
            RepositoryError: If creation fails
        """
        try:
            instance = self.model_class(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)

            self.logger.info(f"Created {self.model_class.__name__} with ID: {instance.id}")
            return instance

        except IntegrityError as e:
            await self.session.rollback()
            self.logger.error(f"Integrity error creating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to create {self.model_class.__name__}: {str(e)}")

        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error creating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_by_id(self, id: str, include_deleted: bool = False) -> Optional[ModelType]:
        """
        Get record by ID.

        Args:
            id: Record ID
            include_deleted: Whether to include soft-deleted records

        Returns:
            Model instance or None if not found
        """
        try:
            query = select(self.model_class).where(self.model_class.id == id)

            if not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            result = await self.session.execute(query)
            instance = result.scalar_one_or_none()

            if instance:
                self.logger.debug(f"Found {self.model_class.__name__} with ID: {id}")
            else:
                self.logger.debug(f"No {self.model_class.__name__} found with ID: {id}")

            return instance

        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting {self.model_class.__name__} by ID: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_all(
        self,
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Get all records with optional filtering and pagination.

        Args:
            include_deleted: Whether to include soft-deleted records
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field name to order by
            order_desc: Whether to order in descending order

        Returns:
            List of model instances
        """
        try:
            query = select(self.model_class)

            if not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            if order_by:
                order_column = getattr(self.model_class, order_by, None)
                if order_column is not None:
                    if order_desc:
                        query = query.order_by(order_column.desc())
                    else:
                        query = query.order_by(order_column)

            if offset is not None:
                query = query.offset(offset)

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            instances = result.scalars().all()

            self.logger.debug(f"Retrieved {len(instances)} {self.model_class.__name__} records")
            return list(instances)

        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting all {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def update(self, id: str, **kwargs) -> Optional[ModelType]:
        """
        Update record by ID.

        Args:
            id: Record ID
            **kwargs: Fields to update

        Returns:
            Updated model instance or None if not found

        Raises:
            RepositoryError: If update fails
        """
        try:
            # First get the record
            instance = await self.get_by_id(id)
            if not instance:
                return None

            # Update fields
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            await self.session.flush()
            await self.session.refresh(instance)

            self.logger.info(f"Updated {self.model_class.__name__} with ID: {id}")
            return instance

        except IntegrityError as e:
            await self.session.rollback()
            self.logger.error(f"Integrity error updating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to update {self.model_class.__name__}: {str(e)}")

        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error updating {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def delete(self, id: str, soft_delete: bool = True) -> bool:
        """
        Delete record by ID (soft or hard delete).

        Args:
            id: Record ID
            soft_delete: Whether to perform soft delete

        Returns:
            True if record was deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        try:
            instance = await self.get_by_id(id)
            if not instance:
                return False

            if soft_delete:
                instance.soft_delete()
                await self.session.flush()
                self.logger.info(f"Soft deleted {self.model_class.__name__} with ID: {id}")
            else:
                await self.session.delete(instance)
                await self.session.flush()
                self.logger.info(f"Hard deleted {self.model_class.__name__} with ID: {id}")

            return True

        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error deleting {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def restore(self, id: str) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.

        Args:
            id: Record ID

        Returns:
            Restored model instance or None if not found

        Raises:
            RepositoryError: If restoration fails
        """
        try:
            instance = await self.get_by_id(id, include_deleted=True)
            if not instance or not instance.is_deleted:
                return None

            instance.restore()
            await self.session.flush()
            await self.session.refresh(instance)

            self.logger.info(f"Restored {self.model_class.__name__} with ID: {id}")
            return instance

        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error restoring {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def count(self, include_deleted: bool = False, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filters.

        Args:
            include_deleted: Whether to include soft-deleted records
            filters: Dictionary of field filters

        Returns:
            Total count of records
        """
        try:
            query = select(func.count()).select_from(self.model_class)

            if not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field):
                        column = getattr(self.model_class, field)
                        if isinstance(value, list):
                            query = query.where(column.in_(value))
                        else:
                            query = query.where(column == value)

            result = await self.session.execute(query)
            count = result.scalar()

            self.logger.debug(f"Counted {count} {self.model_class.__name__} records")
            return count

        except SQLAlchemyError as e:
            self.logger.error(f"Database error counting {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def exists(self, id: str, include_deleted: bool = False) -> bool:
        """
        Check if record exists by ID.

        Args:
            id: Record ID
            include_deleted: Whether to include soft-deleted records

        Returns:
            True if record exists, False otherwise
        """
        try:
            query = select(self.model_class.id).where(self.model_class.id == id)

            if not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            result = await self.session.execute(query)
            exists = result.scalar_one_or_none() is not None

            self.logger.debug(f"{self.model_class.__name__} with ID {id} exists: {exists}")
            return exists

        except SQLAlchemyError as e:
            self.logger.error(f"Database error checking {self.model_class.__name__} existence: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def find_by_field(
        self,
        field: str,
        value: Any,
        include_deleted: bool = False,
        limit: Optional[int] = None
    ) -> List[ModelType]:
        """
        Find records by field value.

        Args:
            field: Field name to search
            value: Field value to match
            include_deleted: Whether to include soft-deleted records
            limit: Maximum number of records to return

        Returns:
            List of matching model instances
        """
        try:
            if not hasattr(self.model_class, field):
                raise RepositoryError(f"Field '{field}' not found in {self.model_class.__name__}")

            column = getattr(self.model_class, field)
            query = select(self.model_class).where(column == value)

            if not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            instances = result.scalars().all()

            self.logger.debug(f"Found {len(instances)} {self.model_class.__name__} records by {field}")
            return list(instances)

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding {self.model_class.__name__} by field: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def bulk_create(self, records: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Create multiple records in bulk.

        Args:
            records: List of dictionaries with field values

        Returns:
            List of created model instances

        Raises:
            RepositoryError: If bulk creation fails
        """
        try:
            instances = []
            for record_data in records:
                instance = self.model_class(**record_data)
                instances.append(instance)

            self.session.add_all(instances)
            await self.session.flush()

            # Refresh all instances to get generated IDs
            for instance in instances:
                await self.session.refresh(instance)

            self.logger.info(f"Bulk created {len(instances)} {self.model_class.__name__} records")
            return instances

        except IntegrityError as e:
            await self.session.rollback()
            self.logger.error(f"Integrity error in bulk create {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Failed to bulk create {self.model_class.__name__}: {str(e)}")

        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error in bulk create {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records in bulk.

        Args:
            updates: List of dictionaries with 'id' and update fields

        Returns:
            Number of updated records

        Raises:
            RepositoryError: If bulk update fails
        """
        try:
            updated_count = 0

            for update_data in updates:
                if 'id' not in update_data:
                    continue

                record_id = update_data.pop('id')
                query = (
                    update(self.model_class)
                    .where(self.model_class.id == record_id)
                    .where(self.model_class.deleted_at.is_(None))
                    .values(**update_data)
                )

                result = await self.session.execute(query)
                updated_count += result.rowcount

            await self.session.flush()
            self.logger.info(f"Bulk updated {updated_count} {self.model_class.__name__} records")
            return updated_count

        except SQLAlchemyError as e:
            await self.session.rollback()
            self.logger.error(f"Database error in bulk update {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def search(
        self,
        filters: Dict[str, Any],
        include_deleted: bool = False,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False
    ) -> List[ModelType]:
        """
        Search records with complex filters.

        Args:
            filters: Dictionary of search criteria
            include_deleted: Whether to include soft-deleted records
            limit: Maximum number of records to return
            offset: Number of records to skip
            order_by: Field name to order by
            order_desc: Whether to order in descending order

        Returns:
            List of matching model instances
        """
        try:
            query = select(self.model_class)

            if not include_deleted:
                query = query.where(self.model_class.deleted_at.is_(None))

            # Apply filters
            for field, value in filters.items():
                if not hasattr(self.model_class, field):
                    continue

                column = getattr(self.model_class, field)

                if isinstance(value, dict):
                    # Handle complex filters like {'gte': 100}, {'like': '%test%'}
                    for operator, op_value in value.items():
                        if operator == 'gte':
                            query = query.where(column >= op_value)
                        elif operator == 'lte':
                            query = query.where(column <= op_value)
                        elif operator == 'gt':
                            query = query.where(column > op_value)
                        elif operator == 'lt':
                            query = query.where(column < op_value)
                        elif operator == 'like':
                            query = query.where(column.like(op_value))
                        elif operator == 'ilike':
                            query = query.where(column.ilike(op_value))
                        elif operator == 'in':
                            query = query.where(column.in_(op_value))
                        elif operator == 'not_in':
                            query = query.where(~column.in_(op_value))
                elif isinstance(value, list):
                    query = query.where(column.in_(value))
                else:
                    query = query.where(column == value)

            # Apply ordering
            if order_by and hasattr(self.model_class, order_by):
                order_column = getattr(self.model_class, order_by)
                if order_desc:
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column)

            # Apply pagination
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            instances = result.scalars().all()

            self.logger.debug(f"Search found {len(instances)} {self.model_class.__name__} records")
            return list(instances)

        except SQLAlchemyError as e:
            self.logger.error(f"Database error searching {self.model_class.__name__}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")