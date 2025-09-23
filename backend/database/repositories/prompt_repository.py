"""
Prompt repository for prompt management and AI interaction tracking.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, and_, or_, func, desc, asc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.prompt import Prompt
from database.models.audit_log import log_user_action
from .base import BaseRepository, RepositoryError


class PromptRepository(BaseRepository[Prompt]):
    """Repository for Prompt model with AI interaction tracking and analytics."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Prompt)

    @property
    def model_class(self) -> type[Prompt]:
        return Prompt

    async def create_prompt(
        self,
        conversation_id: str,
        user_input: str,
        content: str,
        sequence_number: Optional[int] = None,
        template_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model_settings: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Prompt:
        """
        Create a new prompt.

        Args:
            conversation_id: Conversation ID
            user_input: User's input text
            content: Full prompt content
            sequence_number: Sequence number in conversation
            template_id: Template ID if based on template
            system_prompt: System prompt
            model_settings: AI model configuration
            metadata: Additional metadata
            user_id: User ID for logging

        Returns:
            Created Prompt instance

        Raises:
            RepositoryError: If creation fails
        """
        try:
            # Auto-generate sequence number if not provided
            if sequence_number is None:
                max_seq_query = (
                    select(func.coalesce(func.max(Prompt.sequence_number), 0))
                    .where(Prompt.conversation_id == conversation_id)
                )
                result = await self.session.execute(max_seq_query)
                sequence_number = result.scalar() + 1

            prompt = Prompt(
                conversation_id=conversation_id,
                user_input=user_input.strip(),
                content=content.strip(),
                sequence_number=sequence_number,
                template_id=template_id,
                system_prompt=system_prompt.strip() if system_prompt else None,
                custom_metadata=metadata or {}
            )

            # Apply model settings if provided
            if model_settings:
                prompt.model_used = model_settings.get('model_used')
                prompt.model_version = model_settings.get('model_version')
                prompt.temperature = model_settings.get('temperature')
                prompt.max_tokens = model_settings.get('max_tokens')

            self.session.add(prompt)
            await self.session.flush()
            await self.session.refresh(prompt)

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='prompt_created',
                    entity_type='prompt',
                    entity_id=prompt.id,
                    details={
                        'conversation_id': conversation_id,
                        'sequence_number': sequence_number,
                        'template_id': template_id,
                        'has_system_prompt': system_prompt is not None
                    }
                )

            self.logger.info(f"Created prompt in conversation {conversation_id}, sequence {sequence_number}")
            return prompt

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create prompt: {e}")
            raise RepositoryError(f"Failed to create prompt: {str(e)}")

    async def get_conversation_prompts(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_failed: bool = False,
        order_desc: bool = False
    ) -> List[Prompt]:
        """
        Get prompts for a conversation.

        Args:
            conversation_id: Conversation ID
            limit: Maximum number of prompts to return
            offset: Number of prompts to skip
            include_failed: Whether to include failed prompts
            order_desc: Whether to order by sequence number descending

        Returns:
            List of Prompt instances
        """
        try:
            conditions = [
                Prompt.conversation_id == conversation_id,
                Prompt.deleted_at.is_(None)
            ]

            if not include_failed:
                conditions.append(Prompt.status != 'failed')

            query = (
                select(Prompt)
                .options(selectinload(Prompt.template))
                .where(and_(*conditions))
            )

            if order_desc:
                query = query.order_by(Prompt.sequence_number.desc())
            else:
                query = query.order_by(Prompt.sequence_number.asc())

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            prompts = result.scalars().all()

            self.logger.debug(f"Retrieved {len(prompts)} prompts for conversation: {conversation_id}")
            return list(prompts)

        except Exception as e:
            self.logger.error(f"Error getting conversation prompts: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_prompt_with_context(self, prompt_id: str) -> Optional[Prompt]:
        """
        Get prompt with conversation and template context.

        Args:
            prompt_id: Prompt ID

        Returns:
            Prompt instance with related data loaded
        """
        try:
            query = (
                select(Prompt)
                .options(
                    selectinload(Prompt.conversation),
                    selectinload(Prompt.template),
                    selectinload(Prompt.parent_prompt)
                )
                .where(
                    and_(
                        Prompt.id == prompt_id,
                        Prompt.deleted_at.is_(None)
                    )
                )
            )

            result = await self.session.execute(query)
            prompt = result.scalar_one_or_none()

            if prompt:
                self.logger.debug(f"Retrieved prompt with context: {prompt_id}")

            return prompt

        except Exception as e:
            self.logger.error(f"Error getting prompt with context {prompt_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def start_processing(self, prompt_id: str, user_id: Optional[str] = None) -> bool:
        """
        Mark prompt as being processed.

        Args:
            prompt_id: Prompt ID
            user_id: User ID for logging

        Returns:
            True if updated successfully
        """
        try:
            prompt = await self.get_by_id(prompt_id)
            if not prompt:
                return False

            prompt.start_processing()
            await self.session.flush()

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='prompt_processing_started',
                    entity_type='prompt',
                    entity_id=prompt_id,
                    details={'conversation_id': prompt.conversation_id}
                )

            self.logger.debug(f"Started processing prompt: {prompt_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to start processing prompt {prompt_id}: {e}")
            raise RepositoryError(f"Failed to start processing: {str(e)}")

    async def complete_processing(
        self,
        prompt_id: str,
        ai_response: str,
        response_time_ms: int,
        token_input: int,
        token_output: int,
        model_used: str,
        cost: Optional[Decimal] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Mark prompt as completed with response data.

        Args:
            prompt_id: Prompt ID
            ai_response: AI response text
            response_time_ms: Response time in milliseconds
            token_input: Input token count
            token_output: Output token count
            model_used: AI model used
            cost: API call cost
            user_id: User ID for logging

        Returns:
            True if updated successfully
        """
        try:
            prompt = await self.get_by_id(prompt_id)
            if not prompt:
                return False

            prompt.complete_processing(
                ai_response=ai_response,
                response_time_ms=response_time_ms,
                token_input=token_input,
                token_output=token_output,
                model_used=model_used,
                cost=cost
            )

            await self.session.flush()

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='prompt_processing_completed',
                    entity_type='prompt',
                    entity_id=prompt_id,
                    details={
                        'conversation_id': prompt.conversation_id,
                        'response_time_ms': response_time_ms,
                        'token_total': token_input + token_output,
                        'model_used': model_used,
                        'cost': float(cost) if cost else None
                    }
                )

            self.logger.info(f"Completed processing prompt: {prompt_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to complete processing prompt {prompt_id}: {e}")
            raise RepositoryError(f"Failed to complete processing: {str(e)}")

    async def fail_processing(
        self,
        prompt_id: str,
        error_message: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Mark prompt as failed with error message.

        Args:
            prompt_id: Prompt ID
            error_message: Error message
            user_id: User ID for logging

        Returns:
            True if updated successfully
        """
        try:
            prompt = await self.get_by_id(prompt_id)
            if not prompt:
                return False

            prompt.fail_processing(error_message)
            await self.session.flush()

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='prompt_processing_failed',
                    entity_type='prompt',
                    entity_id=prompt_id,
                    details={
                        'conversation_id': prompt.conversation_id,
                        'error_message': error_message
                    }
                )

            self.logger.warning(f"Failed processing prompt {prompt_id}: {error_message}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to mark prompt as failed {prompt_id}: {e}")
            raise RepositoryError(f"Failed to mark as failed: {str(e)}")

    async def set_rating(
        self,
        prompt_id: str,
        rating: int,
        feedback: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Set user rating for prompt.

        Args:
            prompt_id: Prompt ID
            rating: Rating from 1-5
            feedback: Optional feedback text
            user_id: User ID for logging

        Returns:
            True if rating set successfully
        """
        try:
            prompt = await self.get_by_id(prompt_id)
            if not prompt:
                return False

            old_rating = prompt.user_rating
            prompt.set_rating(rating, feedback)
            await self.session.flush()

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='prompt_rated',
                    entity_type='prompt',
                    entity_id=prompt_id,
                    details={
                        'conversation_id': prompt.conversation_id,
                        'old_rating': old_rating,
                        'new_rating': rating,
                        'has_feedback': feedback is not None
                    }
                )

            self.logger.info(f"Set rating {rating} for prompt: {prompt_id}")
            return True

        except ValueError as e:
            self.logger.error(f"Invalid rating for prompt {prompt_id}: {e}")
            raise RepositoryError(f"Invalid rating: {str(e)}")
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to set rating for prompt {prompt_id}: {e}")
            raise RepositoryError(f"Failed to set rating: {str(e)}")

    async def create_followup(
        self,
        parent_prompt_id: str,
        user_input: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Prompt]:
        """
        Create a follow-up prompt.

        Args:
            parent_prompt_id: Parent prompt ID
            user_input: New user input
            user_id: User ID for logging
            **kwargs: Additional prompt fields

        Returns:
            Created follow-up Prompt instance or None if parent not found
        """
        try:
            parent_prompt = await self.get_by_id(parent_prompt_id)
            if not parent_prompt:
                return None

            followup = parent_prompt.create_followup(user_input, **kwargs)
            self.session.add(followup)
            await self.session.flush()
            await self.session.refresh(followup)

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='prompt_followup_created',
                    entity_type='prompt',
                    entity_id=followup.id,
                    details={
                        'parent_prompt_id': parent_prompt_id,
                        'conversation_id': followup.conversation_id,
                        'sequence_number': followup.sequence_number
                    }
                )

            self.logger.info(f"Created follow-up prompt from {parent_prompt_id}")
            return followup

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create follow-up prompt: {e}")
            raise RepositoryError(f"Failed to create follow-up: {str(e)}")

    async def create_variation(
        self,
        original_prompt_id: str,
        user_id: Optional[str] = None,
        **changes
    ) -> Optional[Prompt]:
        """
        Create a variation of an existing prompt.

        Args:
            original_prompt_id: Original prompt ID
            user_id: User ID for logging
            **changes: Changes to make in the variation

        Returns:
            Created variation Prompt instance or None if original not found
        """
        try:
            original_prompt = await self.get_by_id(original_prompt_id)
            if not original_prompt:
                return None

            variation = original_prompt.create_variation(**changes)
            self.session.add(variation)
            await self.session.flush()
            await self.session.refresh(variation)

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='prompt_variation_created',
                    entity_type='prompt',
                    entity_id=variation.id,
                    details={
                        'original_prompt_id': original_prompt_id,
                        'conversation_id': variation.conversation_id,
                        'version': variation.version,
                        'changes': list(changes.keys())
                    }
                )

            self.logger.info(f"Created variation of prompt {original_prompt_id}")
            return variation

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create prompt variation: {e}")
            raise RepositoryError(f"Failed to create variation: {str(e)}")

    async def search_prompts(
        self,
        search_term: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        status_filter: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Prompt]:
        """
        Search prompts using full-text search.

        Args:
            search_term: Search term
            conversation_id: Conversation ID filter
            user_id: User ID for permission filtering
            status_filter: List of statuses to include
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of matching Prompt instances
        """
        try:
            search_pattern = f"%{search_term.lower()}%"
            conditions = [Prompt.deleted_at.is_(None)]

            if conversation_id:
                conditions.append(Prompt.conversation_id == conversation_id)

            if status_filter:
                conditions.append(Prompt.status.in_(status_filter))

            # Try FULLTEXT search first
            try:
                query = (
                    select(Prompt)
                    .options(
                        selectinload(Prompt.conversation),
                        selectinload(Prompt.template)
                    )
                    .where(
                        and_(
                            text("MATCH(content, user_input, ai_response) AGAINST(:search_term IN NATURAL LANGUAGE MODE)"),
                            *conditions
                        )
                    )
                    .order_by(desc(text("MATCH(content, user_input, ai_response) AGAINST(:search_term IN NATURAL LANGUAGE MODE)")))
                )

                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)

                result = await self.session.execute(query.params(search_term=search_term))
                prompts = result.scalars().all()

            except Exception:
                # Fallback to LIKE search
                search_conditions = [
                    or_(
                        Prompt.content.like(search_pattern),
                        Prompt.user_input.like(search_pattern),
                        Prompt.ai_response.like(search_pattern)
                    )
                ]

                query = (
                    select(Prompt)
                    .options(
                        selectinload(Prompt.conversation),
                        selectinload(Prompt.template)
                    )
                    .where(and_(*(conditions + search_conditions)))
                    .order_by(Prompt.created_at.desc())
                )

                if offset is not None:
                    query = query.offset(offset)
                if limit is not None:
                    query = query.limit(limit)

                result = await self.session.execute(query)
                prompts = result.scalars().all()

            self.logger.debug(f"Search for '{search_term}' found {len(prompts)} prompts")
            return list(prompts)

        except Exception as e:
            self.logger.error(f"Error searching prompts: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_prompt_chain(self, prompt_id: str) -> List[Prompt]:
        """
        Get the full prompt chain (parent and all children).

        Args:
            prompt_id: Any prompt ID in the chain

        Returns:
            List of Prompt instances in the chain, ordered by sequence
        """
        try:
            # First get the prompt to find the conversation
            prompt = await self.get_by_id(prompt_id)
            if not prompt:
                return []

            # Get the root prompt of the chain
            current = prompt
            while current.parent_prompt_id:
                parent = await self.get_by_id(current.parent_prompt_id)
                if not parent:
                    break
                current = parent

            root_prompt_id = current.id

            # Get all prompts in the chain recursively
            chain_query = text("""
                WITH RECURSIVE prompt_chain AS (
                    SELECT * FROM prompts WHERE id = :root_id AND deleted_at IS NULL
                    UNION ALL
                    SELECT p.* FROM prompts p
                    INNER JOIN prompt_chain pc ON p.parent_prompt_id = pc.id
                    WHERE p.deleted_at IS NULL
                )
                SELECT * FROM prompt_chain ORDER BY sequence_number
            """)

            result = await self.session.execute(chain_query.params(root_id=root_prompt_id))
            rows = result.fetchall()

            # Convert to Prompt objects
            prompts = []
            for row in rows:
                prompt_dict = dict(row._mapping)
                prompt = Prompt(**prompt_dict)
                prompts.append(prompt)

            self.logger.debug(f"Retrieved chain of {len(prompts)} prompts for prompt: {prompt_id}")
            return prompts

        except Exception as e:
            self.logger.error(f"Error getting prompt chain for {prompt_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_prompt_analytics(
        self,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get prompt analytics and statistics.

        Args:
            conversation_id: Conversation ID filter
            user_id: User ID filter (via conversation ownership)
            days: Number of days to analyze

        Returns:
            Dictionary with analytics data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            conditions = [
                Prompt.deleted_at.is_(None),
                Prompt.created_at >= cutoff_date
            ]

            if conversation_id:
                conditions.append(Prompt.conversation_id == conversation_id)

            # Total prompts
            total_query = select(func.count()).select_from(Prompt).where(and_(*conditions))
            total_result = await self.session.execute(total_query)
            total_prompts = total_result.scalar()

            # Prompts by status
            status_query = (
                select(Prompt.status, func.count())
                .where(and_(*conditions))
                .group_by(Prompt.status)
            )
            status_result = await self.session.execute(status_query)
            prompts_by_status = dict(status_result.all())

            # Token statistics
            token_stats_query = select(
                func.avg(Prompt.token_count_total),
                func.sum(Prompt.token_count_total),
                func.max(Prompt.token_count_total),
                func.min(Prompt.token_count_total)
            ).where(
                and_(
                    Prompt.token_count_total.is_not(None),
                    *conditions
                )
            )
            token_stats_result = await self.session.execute(token_stats_query)
            avg_tokens, total_tokens, max_tokens, min_tokens = token_stats_result.first()

            # Cost statistics
            cost_stats_query = select(
                func.avg(Prompt.cost),
                func.sum(Prompt.cost),
                func.max(Prompt.cost),
                func.min(Prompt.cost)
            ).where(
                and_(
                    Prompt.cost.is_not(None),
                    *conditions
                )
            )
            cost_stats_result = await self.session.execute(cost_stats_query)
            avg_cost, total_cost, max_cost, min_cost = cost_stats_result.first()

            # Response time statistics
            response_time_query = select(
                func.avg(Prompt.response_time_ms),
                func.max(Prompt.response_time_ms),
                func.min(Prompt.response_time_ms)
            ).where(
                and_(
                    Prompt.response_time_ms.is_not(None),
                    *conditions
                )
            )
            response_time_result = await self.session.execute(response_time_query)
            avg_response_time, max_response_time, min_response_time = response_time_result.first()

            # Model usage
            model_usage_query = (
                select(Prompt.model_used, func.count())
                .where(
                    and_(
                        Prompt.model_used.is_not(None),
                        *conditions
                    )
                )
                .group_by(Prompt.model_used)
                .order_by(func.count().desc())
            )
            model_usage_result = await self.session.execute(model_usage_query)
            model_usage = dict(model_usage_result.all())

            # Rating statistics
            rating_stats_query = select(
                func.avg(Prompt.user_rating),
                func.count(Prompt.user_rating)
            ).where(
                and_(
                    Prompt.user_rating.is_not(None),
                    *conditions
                )
            )
            rating_stats_result = await self.session.execute(rating_stats_query)
            avg_rating, rated_count = rating_stats_result.first()

            analytics = {
                'total_prompts': total_prompts,
                'prompts_by_status': prompts_by_status,
                'token_statistics': {
                    'average': float(avg_tokens) if avg_tokens else 0,
                    'total': int(total_tokens) if total_tokens else 0,
                    'maximum': int(max_tokens) if max_tokens else 0,
                    'minimum': int(min_tokens) if min_tokens else 0
                },
                'cost_statistics': {
                    'average': float(avg_cost) if avg_cost else 0.0,
                    'total': float(total_cost) if total_cost else 0.0,
                    'maximum': float(max_cost) if max_cost else 0.0,
                    'minimum': float(min_cost) if min_cost else 0.0
                },
                'response_time_statistics': {
                    'average_ms': float(avg_response_time) if avg_response_time else 0,
                    'maximum_ms': int(max_response_time) if max_response_time else 0,
                    'minimum_ms': int(min_response_time) if min_response_time else 0
                },
                'model_usage': model_usage,
                'rating_statistics': {
                    'average_rating': float(avg_rating) if avg_rating else None,
                    'total_rated': int(rated_count) if rated_count else 0
                },
                'analysis_period_days': days
            }

            self.logger.debug("Generated prompt analytics")
            return analytics

        except Exception as e:
            self.logger.error(f"Error generating prompt analytics: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_top_performing_prompts(
        self,
        limit: int = 10,
        metric: str = 'rating',
        conversation_id: Optional[str] = None
    ) -> List[Prompt]:
        """
        Get top performing prompts by various metrics.

        Args:
            limit: Maximum number of prompts to return
            metric: Metric to sort by ('rating', 'efficiency', 'cost_efficiency')
            conversation_id: Conversation ID filter

        Returns:
            List of top performing Prompt instances
        """
        try:
            conditions = [
                Prompt.status == 'completed',
                Prompt.deleted_at.is_(None)
            ]

            if conversation_id:
                conditions.append(Prompt.conversation_id == conversation_id)

            query = (
                select(Prompt)
                .options(
                    selectinload(Prompt.conversation),
                    selectinload(Prompt.template)
                )
                .where(and_(*conditions))
            )

            if metric == 'rating':
                query = query.where(Prompt.user_rating.is_not(None)).order_by(
                    Prompt.user_rating.desc(),
                    Prompt.created_at.desc()
                )
            elif metric == 'efficiency':
                query = query.where(
                    and_(
                        Prompt.response_time_ms.is_not(None),
                        Prompt.token_count_total.is_not(None),
                        Prompt.token_count_total > 0
                    )
                ).order_by(
                    (Prompt.token_count_total / Prompt.response_time_ms).desc()
                )
            elif metric == 'cost_efficiency':
                query = query.where(
                    and_(
                        Prompt.cost.is_not(None),
                        Prompt.token_count_total.is_not(None),
                        Prompt.cost > 0,
                        Prompt.token_count_total > 0
                    )
                ).order_by(
                    (Prompt.token_count_total / Prompt.cost).desc()
                )
            else:
                # Default to creation date
                query = query.order_by(Prompt.created_at.desc())

            query = query.limit(limit)

            result = await self.session.execute(query)
            prompts = result.scalars().all()

            self.logger.debug(f"Retrieved {len(prompts)} top performing prompts by {metric}")
            return list(prompts)

        except Exception as e:
            self.logger.error(f"Error getting top performing prompts: {e}")
            raise RepositoryError(f"Database error: {str(e)}")