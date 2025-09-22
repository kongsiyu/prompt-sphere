"""
Conversation repository for conversation and participant management operations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.conversation import Conversation, ConversationParticipant
from database.models.audit_log import log_user_action
from .base import BaseRepository, RepositoryError


class ConversationRepository(BaseRepository[Conversation]):
    """Repository for Conversation model with sharing and collaboration features."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)

    @property
    def model_class(self) -> type[Conversation]:
        return Conversation

    async def create_conversation(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User ID of the creator
            title: Conversation title
            description: Conversation description
            context: Initial context data
            settings: Conversation settings

        Returns:
            Created Conversation instance

        Raises:
            RepositoryError: If creation fails
        """
        try:
            conversation = Conversation(
                user_id=user_id,
                title=title.strip(),
                description=description.strip() if description else None,
                context=context or {},
                settings=settings or {}
            )

            self.session.add(conversation)
            await self.session.flush()
            await self.session.refresh(conversation)

            # Log conversation creation
            await log_user_action(
                self.session,
                user_id=user_id,
                action='conversation_created',
                entity_type='conversation',
                entity_id=conversation.id,
                details={
                    'title': title,
                    'has_description': description is not None
                }
            )

            self.logger.info(f"Created conversation: {title} by user: {user_id}")
            return conversation

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to create conversation {title}: {e}")
            raise RepositoryError(f"Failed to create conversation: {str(e)}")

    async def get_conversation_with_prompts(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        share_token: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Get conversation with prompts loaded, checking access permissions.

        Args:
            conversation_id: Conversation ID
            user_id: User ID for permission checking
            share_token: Share token for public access

        Returns:
            Conversation instance with prompts loaded or None if not accessible
        """
        try:
            query = (
                select(Conversation)
                .options(
                    selectinload(Conversation.prompts),
                    selectinload(Conversation.participants),
                    selectinload(Conversation.user)
                )
                .where(
                    and_(
                        Conversation.id == conversation_id,
                        Conversation.deleted_at.is_(None)
                    )
                )
            )

            result = await self.session.execute(query)
            conversation = result.scalar_one_or_none()

            if not conversation:
                return None

            # Check access permissions
            if not conversation.is_accessible_by(user_id, share_token):
                self.logger.warning(f"Access denied to conversation {conversation_id} for user {user_id}")
                return None

            self.logger.debug(f"Retrieved conversation with prompts: {conversation_id}")
            return conversation

        except Exception as e:
            self.logger.error(f"Error getting conversation with prompts {conversation_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_user_conversations(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_shared: bool = True
    ) -> List[Conversation]:
        """
        Get conversations for a user including owned and shared conversations.

        Args:
            user_id: User ID
            status: Filter by conversation status
            limit: Maximum number of conversations to return
            offset: Number of conversations to skip
            include_shared: Whether to include conversations where user is a participant

        Returns:
            List of Conversation instances
        """
        try:
            conditions = [Conversation.deleted_at.is_(None)]

            if include_shared:
                # Include owned conversations and conversations where user is a participant
                participant_subquery = (
                    select(ConversationParticipant.conversation_id)
                    .where(
                        and_(
                            ConversationParticipant.user_id == user_id,
                            ConversationParticipant.deleted_at.is_(None)
                        )
                    )
                )

                conditions.append(
                    or_(
                        Conversation.user_id == user_id,
                        Conversation.id.in_(participant_subquery)
                    )
                )
            else:
                conditions.append(Conversation.user_id == user_id)

            if status:
                conditions.append(Conversation.status == status)

            query = (
                select(Conversation)
                .options(selectinload(Conversation.user))
                .where(and_(*conditions))
                .order_by(Conversation.last_activity_at.desc())
            )

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            conversations = result.scalars().all()

            self.logger.debug(f"Retrieved {len(conversations)} conversations for user: {user_id}")
            return list(conversations)

        except Exception as e:
            self.logger.error(f"Error getting user conversations for {user_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def search_conversations(
        self,
        user_id: str,
        search_term: str,
        limit: Optional[int] = None
    ) -> List[Conversation]:
        """
        Search conversations by title or description.

        Args:
            user_id: User ID for permission filtering
            search_term: Search term
            limit: Maximum number of results

        Returns:
            List of matching Conversation instances
        """
        try:
            search_pattern = f"%{search_term.lower()}%"

            # Get conversations user has access to
            participant_subquery = (
                select(ConversationParticipant.conversation_id)
                .where(
                    and_(
                        ConversationParticipant.user_id == user_id,
                        ConversationParticipant.deleted_at.is_(None)
                    )
                )
            )

            query = (
                select(Conversation)
                .options(selectinload(Conversation.user))
                .where(
                    and_(
                        or_(
                            Conversation.title.like(search_pattern),
                            Conversation.description.like(search_pattern)
                        ),
                        or_(
                            Conversation.user_id == user_id,
                            Conversation.id.in_(participant_subquery)
                        ),
                        Conversation.deleted_at.is_(None)
                    )
                )
                .order_by(Conversation.last_activity_at.desc())
            )

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            conversations = result.scalars().all()

            self.logger.debug(f"Search for '{search_term}' found {len(conversations)} conversations")
            return list(conversations)

        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_by_share_token(self, share_token: str) -> Optional[Conversation]:
        """
        Get conversation by share token.

        Args:
            share_token: Share token

        Returns:
            Conversation instance or None if not found
        """
        try:
            query = (
                select(Conversation)
                .options(
                    selectinload(Conversation.prompts),
                    selectinload(Conversation.user)
                )
                .where(
                    and_(
                        Conversation.share_token == share_token,
                        Conversation.shared == True,
                        Conversation.deleted_at.is_(None)
                    )
                )
            )

            result = await self.session.execute(query)
            conversation = result.scalar_one_or_none()

            if conversation:
                self.logger.debug(f"Found conversation by share token: {share_token}")

            return conversation

        except Exception as e:
            self.logger.error(f"Error getting conversation by share token: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def update_conversation_stats(
        self,
        conversation_id: str,
        token_count: int = 0,
        cost: Decimal = Decimal('0')
    ) -> bool:
        """
        Update conversation statistics.

        Args:
            conversation_id: Conversation ID
            token_count: Number of tokens to add
            cost: Cost to add

        Returns:
            True if updated successfully
        """
        try:
            conversation = await self.get_by_id(conversation_id)
            if not conversation:
                return False

            conversation.add_message_stats(token_count, cost)
            await self.session.flush()

            self.logger.debug(f"Updated stats for conversation: {conversation_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update conversation stats {conversation_id}: {e}")
            raise RepositoryError(f"Failed to update conversation stats: {str(e)}")

    async def change_status(
        self,
        conversation_id: str,
        status: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Change conversation status.

        Args:
            conversation_id: Conversation ID
            status: New status
            user_id: User ID for logging

        Returns:
            True if status changed successfully
        """
        try:
            conversation = await self.get_by_id(conversation_id)
            if not conversation:
                return False

            old_status = conversation.status
            conversation.status = status
            conversation.update_activity()
            await self.session.flush()

            if user_id:
                await log_user_action(
                    self.session,
                    user_id=user_id,
                    action='conversation_status_changed',
                    entity_type='conversation',
                    entity_id=conversation_id,
                    details={
                        'old_status': old_status,
                        'new_status': status
                    }
                )

            self.logger.info(f"Changed conversation {conversation_id} status from {old_status} to {status}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to change conversation status {conversation_id}: {e}")
            raise RepositoryError(f"Failed to change conversation status: {str(e)}")

    async def generate_share_token(self, conversation_id: str, user_id: str) -> Optional[str]:
        """
        Generate share token for conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID requesting sharing

        Returns:
            Share token or None if conversation not found
        """
        try:
            conversation = await self.get_by_id(conversation_id)
            if not conversation:
                return None

            # Check if user can admin the conversation
            if not conversation.can_admin(user_id):
                raise RepositoryError("User does not have permission to share this conversation")

            share_token = conversation.generate_share_token()
            await self.session.flush()

            await log_user_action(
                self.session,
                user_id=user_id,
                action='conversation_shared',
                entity_type='conversation',
                entity_id=conversation_id,
                details={'share_token_generated': True}
            )

            self.logger.info(f"Generated share token for conversation: {conversation_id}")
            return share_token

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to generate share token for conversation {conversation_id}: {e}")
            raise RepositoryError(f"Failed to generate share token: {str(e)}")

    async def revoke_sharing(self, conversation_id: str, user_id: str) -> bool:
        """
        Revoke sharing for conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID revoking sharing

        Returns:
            True if sharing revoked successfully
        """
        try:
            conversation = await self.get_by_id(conversation_id)
            if not conversation:
                return False

            # Check if user can admin the conversation
            if not conversation.can_admin(user_id):
                raise RepositoryError("User does not have permission to revoke sharing")

            conversation.revoke_sharing()
            await self.session.flush()

            await log_user_action(
                self.session,
                user_id=user_id,
                action='conversation_sharing_revoked',
                entity_type='conversation',
                entity_id=conversation_id,
                details={'sharing_revoked': True}
            )

            self.logger.info(f"Revoked sharing for conversation: {conversation_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to revoke sharing for conversation {conversation_id}: {e}")
            raise RepositoryError(f"Failed to revoke sharing: {str(e)}")

    async def get_recent_conversations(
        self,
        user_id: str,
        days: int = 7,
        limit: int = 10
    ) -> List[Conversation]:
        """
        Get recent conversations for a user.

        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of conversations to return

        Returns:
            List of recent Conversation instances
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get conversations user has access to
            participant_subquery = (
                select(ConversationParticipant.conversation_id)
                .where(
                    and_(
                        ConversationParticipant.user_id == user_id,
                        ConversationParticipant.deleted_at.is_(None)
                    )
                )
            )

            query = (
                select(Conversation)
                .options(selectinload(Conversation.user))
                .where(
                    and_(
                        Conversation.last_activity_at >= cutoff_date,
                        or_(
                            Conversation.user_id == user_id,
                            Conversation.id.in_(participant_subquery)
                        ),
                        Conversation.deleted_at.is_(None)
                    )
                )
                .order_by(Conversation.last_activity_at.desc())
                .limit(limit)
            )

            result = await self.session.execute(query)
            conversations = result.scalars().all()

            self.logger.debug(f"Retrieved {len(conversations)} recent conversations for user: {user_id}")
            return list(conversations)

        except Exception as e:
            self.logger.error(f"Error getting recent conversations for {user_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_conversation_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get conversation statistics.

        Args:
            user_id: User ID for user-specific stats, None for global stats

        Returns:
            Dictionary with conversation statistics
        """
        try:
            base_conditions = [Conversation.deleted_at.is_(None)]

            if user_id:
                participant_subquery = (
                    select(ConversationParticipant.conversation_id)
                    .where(
                        and_(
                            ConversationParticipant.user_id == user_id,
                            ConversationParticipant.deleted_at.is_(None)
                        )
                    )
                )
                base_conditions.append(
                    or_(
                        Conversation.user_id == user_id,
                        Conversation.id.in_(participant_subquery)
                    )
                )

            # Total conversations
            total_query = select(func.count()).select_from(Conversation).where(
                and_(*base_conditions)
            )
            total_result = await self.session.execute(total_query)
            total_conversations = total_result.scalar()

            # Conversations by status
            status_query = (
                select(Conversation.status, func.count())
                .where(and_(*base_conditions))
                .group_by(Conversation.status)
            )
            status_result = await self.session.execute(status_query)
            conversations_by_status = dict(status_result.all())

            # Shared conversations
            shared_query = select(func.count()).select_from(Conversation).where(
                and_(
                    Conversation.shared == True,
                    *base_conditions
                )
            )
            shared_result = await self.session.execute(shared_query)
            shared_conversations = shared_result.scalar()

            # Average conversation statistics
            avg_stats_query = select(
                func.avg(Conversation.total_messages),
                func.avg(Conversation.total_tokens),
                func.avg(Conversation.total_cost)
            ).where(and_(*base_conditions))
            avg_stats_result = await self.session.execute(avg_stats_query)
            avg_messages, avg_tokens, avg_cost = avg_stats_result.first()

            statistics = {
                'total_conversations': total_conversations,
                'conversations_by_status': conversations_by_status,
                'shared_conversations': shared_conversations,
                'average_messages': float(avg_messages) if avg_messages else 0,
                'average_tokens': float(avg_tokens) if avg_tokens else 0,
                'average_cost': float(avg_cost) if avg_cost else 0.0
            }

            self.logger.debug("Generated conversation statistics")
            return statistics

        except Exception as e:
            self.logger.error(f"Error generating conversation statistics: {e}")
            raise RepositoryError(f"Database error: {str(e)}")


class ConversationParticipantRepository(BaseRepository[ConversationParticipant]):
    """Repository for ConversationParticipant model."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ConversationParticipant)

    @property
    def model_class(self) -> type[ConversationParticipant]:
        return ConversationParticipant

    async def add_participant(
        self,
        conversation_id: str,
        user_id: str,
        role: str = 'viewer',
        permissions: Optional[Dict[str, bool]] = None,
        added_by: Optional[str] = None
    ) -> ConversationParticipant:
        """
        Add a participant to a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to add
            role: Participant role
            permissions: Custom permissions
            added_by: User ID of who added the participant

        Returns:
            Created ConversationParticipant instance

        Raises:
            RepositoryError: If creation fails
        """
        try:
            # Check if participant already exists
            existing = await self.get_participant(conversation_id, user_id)
            if existing:
                raise RepositoryError(f"User {user_id} is already a participant in conversation {conversation_id}")

            if permissions is None:
                permissions = {
                    'owner': {'read': True, 'write': True, 'admin': True},
                    'collaborator': {'read': True, 'write': True, 'admin': False},
                    'viewer': {'read': True, 'write': False, 'admin': False}
                }.get(role, {'read': True, 'write': False, 'admin': False})

            participant = ConversationParticipant(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role,
                permissions=permissions
            )

            self.session.add(participant)
            await self.session.flush()
            await self.session.refresh(participant)

            if added_by:
                await log_user_action(
                    self.session,
                    user_id=added_by,
                    action='conversation_participant_added',
                    entity_type='conversation',
                    entity_id=conversation_id,
                    details={
                        'participant_user_id': user_id,
                        'role': role,
                        'permissions': permissions
                    }
                )

            self.logger.info(f"Added participant {user_id} to conversation {conversation_id} with role {role}")
            return participant

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to add participant: {e}")
            raise RepositoryError(f"Failed to add participant: {str(e)}")

    async def get_participant(
        self,
        conversation_id: str,
        user_id: str
    ) -> Optional[ConversationParticipant]:
        """
        Get participant by conversation and user ID.

        Args:
            conversation_id: Conversation ID
            user_id: User ID

        Returns:
            ConversationParticipant instance or None if not found
        """
        try:
            query = select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                    ConversationParticipant.deleted_at.is_(None)
                )
            )

            result = await self.session.execute(query)
            participant = result.scalar_one_or_none()

            return participant

        except Exception as e:
            self.logger.error(f"Error getting participant: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_conversation_participants(
        self,
        conversation_id: str,
        include_user: bool = True
    ) -> List[ConversationParticipant]:
        """
        Get all participants for a conversation.

        Args:
            conversation_id: Conversation ID
            include_user: Whether to include user information

        Returns:
            List of ConversationParticipant instances
        """
        try:
            query = select(ConversationParticipant).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.deleted_at.is_(None)
                )
            )

            if include_user:
                query = query.options(selectinload(ConversationParticipant.user))

            query = query.order_by(ConversationParticipant.joined_at)

            result = await self.session.execute(query)
            participants = result.scalars().all()

            self.logger.debug(f"Retrieved {len(participants)} participants for conversation: {conversation_id}")
            return list(participants)

        except Exception as e:
            self.logger.error(f"Error getting conversation participants: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def update_participant_role(
        self,
        conversation_id: str,
        user_id: str,
        new_role: str,
        new_permissions: Optional[Dict[str, bool]] = None,
        updated_by: Optional[str] = None
    ) -> bool:
        """
        Update participant role and permissions.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            new_role: New role
            new_permissions: New permissions
            updated_by: User ID of who made the update

        Returns:
            True if updated successfully
        """
        try:
            participant = await self.get_participant(conversation_id, user_id)
            if not participant:
                return False

            old_role = participant.role
            participant.role = new_role

            if new_permissions:
                participant.permissions = new_permissions

            await self.session.flush()

            if updated_by:
                await log_user_action(
                    self.session,
                    user_id=updated_by,
                    action='conversation_participant_updated',
                    entity_type='conversation',
                    entity_id=conversation_id,
                    details={
                        'participant_user_id': user_id,
                        'old_role': old_role,
                        'new_role': new_role,
                        'new_permissions': new_permissions
                    }
                )

            self.logger.info(f"Updated participant {user_id} role from {old_role} to {new_role}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update participant role: {e}")
            raise RepositoryError(f"Failed to update participant role: {str(e)}")

    async def remove_participant(
        self,
        conversation_id: str,
        user_id: str,
        removed_by: Optional[str] = None
    ) -> bool:
        """
        Remove participant from conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to remove
            removed_by: User ID of who removed the participant

        Returns:
            True if removed successfully
        """
        try:
            participant = await self.get_participant(conversation_id, user_id)
            if not participant:
                return False

            participant.soft_delete()
            await self.session.flush()

            if removed_by:
                await log_user_action(
                    self.session,
                    user_id=removed_by,
                    action='conversation_participant_removed',
                    entity_type='conversation',
                    entity_id=conversation_id,
                    details={
                        'participant_user_id': user_id,
                        'role': participant.role
                    }
                )

            self.logger.info(f"Removed participant {user_id} from conversation {conversation_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to remove participant: {e}")
            raise RepositoryError(f"Failed to remove participant: {str(e)}")

    async def update_access_time(self, conversation_id: str, user_id: str) -> bool:
        """
        Update participant's last access time.

        Args:
            conversation_id: Conversation ID
            user_id: User ID

        Returns:
            True if updated successfully
        """
        try:
            participant = await self.get_participant(conversation_id, user_id)
            if not participant:
                return False

            participant.update_access_time()
            await self.session.flush()

            self.logger.debug(f"Updated access time for participant {user_id}")
            return True

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to update access time: {e}")
            raise RepositoryError(f"Failed to update access time: {str(e)}")