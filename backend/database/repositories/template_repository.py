"""
Template repository for template and rating management operations.
"""

from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal

from sqlalchemy import select, and_, or_, func, text, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.template import Template, TemplateRating
from database.models.audit_log import log_user_action
from .base import BaseRepository, RepositoryError


class TemplateRepository(BaseRepository[Template]):
    """Repository for Template model with rating and search features."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Template)

    @property
    def model_class(self) -> type[Template]:
        return Template

    async def create_template(
        self,
        name: str,
        content: str,
        created_by: str,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = False
    ) -> Template:
        """
        Create a new template.

        Args:
            name: Template name
            content: Template content
            created_by: User ID of the creator
            description: Template description
            system_prompt: System prompt
            category: Template category
            tags: List of tags
            is_public: Whether template is public

        Returns:
            Created Template instance

        Raises:
            RepositoryError: If creation fails
        """
        try:
            template = Template(
                name=name.strip(),
                content=content.strip(),
                created_by=created_by,
                description=description.strip() if description else None,
                system_prompt=system_prompt.strip() if system_prompt else None,
                category=category.strip() if category else None,
                tags=tags or [],
                is_public=is_public
            )

            self.session.add(template)
            await self.session.flush()
            await self.session.refresh(template)

            # Log template creation
            await log_user_action(
                self.session,
                user_id=created_by,
                action='template_created',
                entity_type='template',
                entity_id=template.id,
                details={
                    'name': name,
                    'category': category,
                    'is_public': is_public,
                    'tags': tags
                }
            )

            self.logger.info(f"Created template: {name} by user: {created_by}")
            return template

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create template {name}: {e}")
            raise RepositoryError(f"Failed to create template: {str(e)}")

    async def get_template_with_creator(self, template_id: str) -> Optional[Template]:
        """
        Get template with creator information loaded.

        Args:
            template_id: Template ID

        Returns:
            Template instance with creator loaded or None if not found
        """
        try:
            query = (
                select(Template)
                .options(selectinload(Template.creator))
                .where(
                    and_(
                        Template.id == template_id,
                        Template.deleted_at.is_(None)
                    )
                )
            )

            result = await self.session.execute(query)
            template = result.scalar_one_or_none()

            if template:
                self.logger.debug(f"Found template with creator: {template_id}")

            return template

        except Exception as e:
            self.logger.error(f"Error getting template with creator {template_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_public_templates(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: str = 'created_at',
        order_desc: bool = True,
        category: Optional[str] = None
    ) -> List[Template]:
        """
        Get public templates with optional filtering.

        Args:
            limit: Maximum number of templates to return
            offset: Number of templates to skip
            order_by: Field to order by
            order_desc: Whether to order in descending order
            category: Category filter

        Returns:
            List of public Template instances
        """
        try:
            query = (
                select(Template)
                .options(selectinload(Template.creator))
                .where(
                    and_(
                        Template.is_public == True,
                        Template.deleted_at.is_(None)
                    )
                )
            )

            if category:
                query = query.where(Template.category == category)

            if order_by and hasattr(Template, order_by):
                order_column = getattr(Template, order_by)
                if order_desc:
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column)

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            templates = result.scalars().all()

            self.logger.debug(f"Retrieved {len(templates)} public templates")
            return list(templates)

        except Exception as e:
            self.logger.error(f"Error getting public templates: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_user_templates(
        self,
        user_id: str,
        include_public: bool = True,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Template]:
        """
        Get templates owned by a specific user.

        Args:
            user_id: User ID
            include_public: Whether to include public templates
            limit: Maximum number of templates to return
            offset: Number of templates to skip

        Returns:
            List of Template instances
        """
        try:
            conditions = [Template.deleted_at.is_(None)]

            if include_public:
                conditions.append(
                    or_(
                        Template.created_by == user_id,
                        Template.is_public == True
                    )
                )
            else:
                conditions.append(Template.created_by == user_id)

            query = (
                select(Template)
                .options(selectinload(Template.creator))
                .where(and_(*conditions))
                .order_by(Template.created_at.desc())
            )

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            templates = result.scalars().all()

            self.logger.debug(f"Retrieved {len(templates)} templates for user: {user_id}")
            return list(templates)

        except Exception as e:
            self.logger.error(f"Error getting user templates for {user_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def search_templates(
        self,
        search_term: str,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Template]:
        """
        Search templates using full-text search.

        Args:
            search_term: Search term for name, description, or content
            user_id: User ID for permission filtering
            category: Category filter
            tags: Tags filter
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching Template instances
        """
        try:
            # Use MySQL FULLTEXT search if available, otherwise LIKE search
            search_pattern = f"%{search_term.lower()}%"

            base_conditions = [Template.deleted_at.is_(None)]

            # Permission filtering
            if user_id:
                base_conditions.append(
                    or_(
                        Template.is_public == True,
                        Template.created_by == user_id
                    )
                )
            else:
                base_conditions.append(Template.is_public == True)

            # Category filter
            if category:
                base_conditions.append(Template.category == category)

            # Try FULLTEXT search first
            try:
                query = (
                    select(Template)
                    .options(selectinload(Template.creator))
                    .where(
                        and_(
                            text("MATCH(name, description, content) AGAINST(:search_term IN NATURAL LANGUAGE MODE)"),
                            *base_conditions
                        )
                    )
                    .order_by(desc(text("MATCH(name, description, content) AGAINST(:search_term IN NATURAL LANGUAGE MODE)")))
                )

                if tags:
                    # Filter by tags using JSON operations
                    for tag in tags:
                        query = query.where(text("JSON_CONTAINS(tags, :tag)")).params(tag=f'"{tag.lower()}"')

                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)

                result = await self.session.execute(query.params(search_term=search_term))
                templates = result.scalars().all()

            except Exception:
                # Fallback to LIKE search
                search_conditions = [
                    or_(
                        Template.name.like(search_pattern),
                        Template.description.like(search_pattern),
                        Template.content.like(search_pattern)
                    )
                ]

                query = (
                    select(Template)
                    .options(selectinload(Template.creator))
                    .where(and_(*(base_conditions + search_conditions)))
                    .order_by(Template.usage_count.desc(), Template.rating_avg.desc())
                )

                if tags:
                    # Simple tag filtering for fallback
                    for tag in tags:
                        query = query.where(Template.tags.like(f'%"{tag.lower()}"%'))

                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)

                result = await self.session.execute(query)
                templates = result.scalars().all()

            self.logger.debug(f"Search for '{search_term}' found {len(templates)} templates")
            return list(templates)

        except Exception as e:
            self.logger.error(f"Error searching templates: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_templates_by_category(self, category: str, user_id: Optional[str] = None) -> List[Template]:
        """
        Get templates by category.

        Args:
            category: Category name
            user_id: User ID for permission filtering

        Returns:
            List of Template instances in the category
        """
        try:
            conditions = [
                Template.category == category,
                Template.deleted_at.is_(None)
            ]

            if user_id:
                conditions.append(
                    or_(
                        Template.is_public == True,
                        Template.created_by == user_id
                    )
                )
            else:
                conditions.append(Template.is_public == True)

            query = (
                select(Template)
                .options(selectinload(Template.creator))
                .where(and_(*conditions))
                .order_by(Template.usage_count.desc(), Template.rating_avg.desc())
            )

            result = await self.session.execute(query)
            templates = result.scalars().all()

            self.logger.debug(f"Found {len(templates)} templates in category: {category}")
            return list(templates)

        except Exception as e:
            self.logger.error(f"Error getting templates by category {category}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_popular_templates(
        self,
        limit: int = 10,
        user_id: Optional[str] = None,
        min_rating: Optional[float] = None
    ) -> List[Template]:
        """
        Get popular templates based on usage and rating.

        Args:
            limit: Maximum number of templates to return
            user_id: User ID for permission filtering
            min_rating: Minimum rating filter

        Returns:
            List of popular Template instances
        """
        try:
            conditions = [Template.deleted_at.is_(None)]

            if user_id:
                conditions.append(
                    or_(
                        Template.is_public == True,
                        Template.created_by == user_id
                    )
                )
            else:
                conditions.append(Template.is_public == True)

            if min_rating is not None:
                conditions.append(Template.rating_avg >= min_rating)

            query = (
                select(Template)
                .options(selectinload(Template.creator))
                .where(and_(*conditions))
                .order_by(
                    Template.usage_count.desc(),
                    Template.rating_avg.desc(),
                    Template.rating_count.desc()
                )
                .limit(limit)
            )

            result = await self.session.execute(query)
            templates = result.scalars().all()

            self.logger.debug(f"Retrieved {len(templates)} popular templates")
            return list(templates)

        except Exception as e:
            self.logger.error(f"Error getting popular templates: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def increment_usage(self, template_id: str, user_id: Optional[str] = None) -> bool:
        """
        Increment template usage count.

        Args:
            template_id: Template ID
            user_id: User ID for logging

        Returns:
            True if updated successfully
        """
        try:
            template = await self.get_by_id(template_id)
            if not template:
                return False

            template.increment_usage()
            await self.session.flush()

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='template_used',
                    entity_type='template',
                    entity_id=template_id,
                    details={'usage_count': template.usage_count}
                )

            self.logger.debug(f"Incremented usage for template: {template_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to increment usage for template {template_id}: {e}")
            raise RepositoryError(f"Failed to increment usage: {str(e)}")

    async def create_version(
        self,
        template_id: str,
        user_id: str,
        **updates
    ) -> Optional[Template]:
        """
        Create a new version of an existing template.

        Args:
            template_id: Original template ID
            user_id: User creating the version
            **updates: Fields to update in the new version

        Returns:
            New template version or None if original not found
        """
        try:
            original_template = await self.get_by_id(template_id)
            if not original_template:
                return None

            # Create new version
            new_version = original_template.create_version(**updates)
            new_version.created_by = user_id

            self.session.add(new_version)
            await self.session.flush()
            await self.session.refresh(new_version)

            # Log version creation
            await log_user_action(
                self.session,
                user_id=user_id,
                action='template_version_created',
                entity_type='template',
                entity_id=new_version.id,
                details={
                    'original_template_id': template_id,
                    'version': new_version.version,
                    'updates': list(updates.keys())
                }
            )

            self.logger.info(f"Created version {new_version.version} of template: {template_id}")
            return new_version

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create version of template {template_id}: {e}")
            raise RepositoryError(f"Failed to create version: {str(e)}")

    async def get_template_versions(self, template_id: str) -> List[Template]:
        """
        Get all versions of a template.

        Args:
            template_id: Template ID

        Returns:
            List of template versions ordered by version number
        """
        try:
            query = (
                select(Template)
                .options(selectinload(Template.creator))
                .where(
                    and_(
                        or_(
                            Template.id == template_id,
                            Template.parent_template_id == template_id
                        ),
                        Template.deleted_at.is_(None)
                    )
                )
                .order_by(Template.version)
            )

            result = await self.session.execute(query)
            templates = result.scalars().all()

            self.logger.debug(f"Found {len(templates)} versions for template: {template_id}")
            return list(templates)

        except Exception as e:
            self.logger.error(f"Error getting template versions for {template_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_categories(self) -> List[Tuple[str, int]]:
        """
        Get all template categories with count.

        Returns:
            List of tuples (category, count)
        """
        try:
            query = (
                select(Template.category, func.count())
                .where(
                    and_(
                        Template.category.is_not(None),
                        Template.is_public == True,
                        Template.deleted_at.is_(None)
                    )
                )
                .group_by(Template.category)
                .order_by(func.count().desc())
            )

            result = await self.session.execute(query)
            categories = result.all()

            self.logger.debug(f"Found {len(categories)} template categories")
            return list(categories)

        except Exception as e:
            self.logger.error(f"Error getting template categories: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_template_statistics(self) -> Dict[str, Any]:
        """
        Get template statistics.

        Returns:
            Dictionary with template statistics
        """
        try:
            # Total templates
            total_query = select(func.count()).select_from(Template).where(
                Template.deleted_at.is_(None)
            )
            total_result = await self.session.execute(total_query)
            total_templates = total_result.scalar()

            # Public templates
            public_query = select(func.count()).select_from(Template).where(
                and_(
                    Template.is_public == True,
                    Template.deleted_at.is_(None)
                )
            )
            public_result = await self.session.execute(public_query)
            public_templates = public_result.scalar()

            # Average rating
            rating_query = select(func.avg(Template.rating_avg)).where(
                and_(
                    Template.rating_avg.is_not(None),
                    Template.deleted_at.is_(None)
                )
            )
            rating_result = await self.session.execute(rating_query)
            avg_rating = rating_result.scalar()

            # Most used template
            popular_query = (
                select(Template.name, Template.usage_count)
                .where(Template.deleted_at.is_(None))
                .order_by(Template.usage_count.desc())
                .limit(1)
            )
            popular_result = await self.session.execute(popular_query)
            most_used = popular_result.first()

            statistics = {
                'total_templates': total_templates,
                'public_templates': public_templates,
                'private_templates': total_templates - public_templates,
                'average_rating': float(avg_rating) if avg_rating else None,
                'most_used_template': {
                    'name': most_used[0] if most_used else None,
                    'usage_count': most_used[1] if most_used else 0
                }
            }

            self.logger.debug("Generated template statistics")
            return statistics

        except Exception as e:
            self.logger.error(f"Error generating template statistics: {e}")
            raise RepositoryError(f"Database error: {str(e)}")


class TemplateRatingRepository(BaseRepository[TemplateRating]):
    """Repository for TemplateRating model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, TemplateRating)

    @property
    def model_class(self) -> type[TemplateRating]:
        return TemplateRating

    async def create_rating(
        self,
        template_id: str,
        user_id: str,
        rating: int,
        feedback: Optional[str] = None
    ) -> TemplateRating:
        """
        Create or update a template rating.

        Args:
            template_id: Template ID
            user_id: User ID
            rating: Rating value (1-5)
            feedback: Optional feedback text

        Returns:
            TemplateRating instance

        Raises:
            RepositoryError: If creation fails
        """
        try:
            # Check for existing rating
            existing_rating = await self.get_user_rating(template_id, user_id)

            if existing_rating:
                # Update existing rating
                old_rating = existing_rating.rating
                existing_rating.rating = rating
                existing_rating.feedback = feedback

                # Update template's average rating
                template = await self.session.get(Template, template_id)
                if template:
                    template.update_rating(rating, old_rating)

                await self.session.flush()

                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='template_rating_updated',
                    entity_type='template',
                    entity_id=template_id,
                    details={
                        'old_rating': old_rating,
                        'new_rating': rating,
                        'has_feedback': feedback is not None
                    }
                )

                self.logger.info(f"Updated rating for template {template_id} by user {user_id}")
                return existing_rating

            else:
                # Create new rating
                new_rating = TemplateRating(
                    template_id=template_id,
                    user_id=user_id,
                    rating=rating,
                    feedback=feedback
                )

                self.session.add(new_rating)

                # Update template's average rating
                template = await self.session.get(Template, template_id)
                if template:
                    template.update_rating(rating)

                await self.session.flush()
                await self.session.refresh(new_rating)

                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='template_rating_created',
                    entity_type='template',
                    entity_id=template_id,
                    details={
                        'rating': rating,
                        'has_feedback': feedback is not None
                    }
                )

                self.logger.info(f"Created rating for template {template_id} by user {user_id}")
                return new_rating

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create/update rating: {e}")
            raise RepositoryError(f"Failed to create/update rating: {str(e)}")

    async def get_user_rating(self, template_id: str, user_id: str) -> Optional[TemplateRating]:
        """
        Get user's rating for a template.

        Args:
            template_id: Template ID
            user_id: User ID

        Returns:
            TemplateRating instance or None if not found
        """
        try:
            query = select(TemplateRating).where(
                and_(
                    TemplateRating.template_id == template_id,
                    TemplateRating.user_id == user_id,
                    TemplateRating.deleted_at.is_(None)
                )
            )

            result = await self.session.execute(query)
            rating = result.scalar_one_or_none()

            return rating

        except Exception as e:
            self.logger.error(f"Error getting user rating: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_template_ratings(
        self,
        template_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[TemplateRating]:
        """
        Get all ratings for a template.

        Args:
            template_id: Template ID
            limit: Maximum number of ratings to return
            offset: Number of ratings to skip

        Returns:
            List of TemplateRating instances
        """
        try:
            query = (
                select(TemplateRating)
                .where(
                    and_(
                        TemplateRating.template_id == template_id,
                        TemplateRating.deleted_at.is_(None)
                    )
                )
                .order_by(TemplateRating.created_at.desc())
            )

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            ratings = result.scalars().all()

            self.logger.debug(f"Retrieved {len(ratings)} ratings for template: {template_id}")
            return list(ratings)

        except Exception as e:
            self.logger.error(f"Error getting template ratings: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def delete_rating(self, template_id: str, user_id: str) -> bool:
        """
        Delete a user's rating for a template.

        Args:
            template_id: Template ID
            user_id: User ID

        Returns:
            True if rating was deleted
        """
        try:
            rating = await self.get_user_rating(template_id, user_id)
            if not rating:
                return False

            # Update template's average rating
            template = await self.session.get(Template, template_id)
            if template:
                template.remove_rating(rating.rating)

            rating.soft_delete()
            await self.session.flush()

            await log_user_action(
                self.session,
                user_id=user_id,
                action='template_rating_deleted',
                entity_type='template',
                entity_id=template_id,
                details={'deleted_rating': rating.rating}
            )

            self.logger.info(f"Deleted rating for template {template_id} by user {user_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to delete rating: {e}")
            raise RepositoryError(f"Failed to delete rating: {str(e)}")