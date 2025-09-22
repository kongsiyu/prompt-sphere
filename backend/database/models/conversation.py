"""
Conversation model for grouping related prompts.
"""

from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime
import secrets

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, DECIMAL, Enum, DateTime
from sqlalchemy.dialects.mysql import JSON, CHAR
from sqlalchemy.orm import relationship

from .base import BaseModel


class Conversation(BaseModel):
    """Conversation model for grouping related prompts into threads."""

    __tablename__ = 'conversations'

    # Basic conversation information
    user_id = Column(
        CHAR(36),
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Conversation context and metadata
    context = Column(JSON, nullable=True, default={})
    settings = Column(JSON, nullable=True, default={})

    # Status and activity tracking
    status = Column(
        Enum('active', 'archived', 'paused', 'completed', name='conversation_status'),
        nullable=False,
        default='active',
        index=True
    )
    last_activity_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    # Statistics and metrics
    total_messages = Column(Integer, nullable=False, default=0)
    total_tokens = Column(Integer, nullable=False, default=0)
    total_cost = Column(DECIMAL(10, 6), nullable=False, default=Decimal('0.000000'))

    # Sharing functionality
    shared = Column(Boolean, nullable=False, default=False, index=True)
    share_token = Column(String(255), nullable=True, unique=True, index=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    prompts = relationship(
        "Prompt",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Prompt.sequence_number"
    )
    participants = relationship(
        "ConversationParticipant",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __init__(self, **kwargs):
        """Initialize conversation with default settings."""
        super().__init__(**kwargs)
        if self.context is None:
            self.context = {}
        if self.settings is None:
            self.settings = {
                'ai_model': 'gpt-3.5-turbo',
                'temperature': 0.7,
                'max_tokens': 2000,
                'auto_title': True
            }

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()

    def add_message_stats(self, token_count: int = 0, cost: Decimal = Decimal('0')) -> None:
        """Update conversation statistics when a message is added."""
        self.total_messages += 1
        self.total_tokens += token_count
        self.total_cost += cost
        self.update_activity()

    def generate_share_token(self) -> str:
        """Generate a secure share token for the conversation."""
        if not self.share_token:
            self.share_token = secrets.token_urlsafe(32)
        self.shared = True
        return self.share_token

    def revoke_sharing(self) -> None:
        """Revoke sharing access for the conversation."""
        self.shared = False
        self.share_token = None

    def is_accessible_by(self, user_id: Optional[str] = None, share_token: Optional[str] = None) -> bool:
        """
        Check if conversation is accessible by a user or share token.

        Args:
            user_id: ID of the user trying to access
            share_token: Share token for public access

        Returns:
            True if accessible, False otherwise
        """
        # Owner access
        if user_id and self.user_id == user_id:
            return True

        # Shared access via token
        if share_token and self.shared and self.share_token == share_token:
            return True

        # Participant access
        if user_id:
            participant = next(
                (p for p in self.participants if p.user_id == user_id), None
            )
            if participant:
                return True

        return False

    def can_edit(self, user_id: str) -> bool:
        """Check if user can edit the conversation."""
        # Owner can always edit
        if self.user_id == user_id:
            return True

        # Check participant permissions
        participant = next(
            (p for p in self.participants if p.user_id == user_id), None
        )
        if participant:
            permissions = participant.permissions or {}
            return permissions.get('write', False)

        return False

    def can_admin(self, user_id: str) -> bool:
        """Check if user has admin permissions for the conversation."""
        # Owner has admin access
        if self.user_id == user_id:
            return True

        # Check participant admin permissions
        participant = next(
            (p for p in self.participants if p.user_id == user_id), None
        )
        if participant:
            permissions = participant.permissions or {}
            return permissions.get('admin', False)

        return False

    def add_participant(self, user_id: str, role: str = 'viewer',
                       permissions: Optional[Dict[str, bool]] = None) -> 'ConversationParticipant':
        """
        Add a participant to the conversation.

        Args:
            user_id: ID of the user to add
            role: Role of the participant (owner, collaborator, viewer)
            permissions: Custom permissions dict

        Returns:
            Created ConversationParticipant instance
        """
        if permissions is None:
            permissions = {
                'owner': {'read': True, 'write': True, 'admin': True},
                'collaborator': {'read': True, 'write': True, 'admin': False},
                'viewer': {'read': True, 'write': False, 'admin': False}
            }.get(role, {'read': True, 'write': False, 'admin': False})

        participant = ConversationParticipant(
            conversation_id=self.id,
            user_id=user_id,
            role=role,
            permissions=permissions
        )

        self.participants.append(participant)
        return participant

    def update_context(self, key: str, value: Any) -> None:
        """Update a specific context value."""
        if self.context is None:
            self.context = {}
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a specific context value."""
        if self.context is None:
            return default
        return self.context.get(key, default)

    def update_setting(self, key: str, value: Any) -> None:
        """Update a specific setting value."""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        if self.settings is None:
            return default
        return self.settings.get(key, default)

    def get_latest_prompts(self, limit: int = 10) -> List['Prompt']:
        """Get the latest prompts in the conversation."""
        return sorted(
            [p for p in self.prompts if not p.is_deleted],
            key=lambda x: x.sequence_number,
            reverse=True
        )[:limit]

    def archive(self) -> None:
        """Archive the conversation."""
        self.status = 'archived'
        self.update_activity()

    def complete(self) -> None:
        """Mark conversation as completed."""
        self.status = 'completed'
        self.update_activity()

    def pause(self) -> None:
        """Pause the conversation."""
        self.status = 'paused'
        self.update_activity()

    def reactivate(self) -> None:
        """Reactivate an archived/paused conversation."""
        self.status = 'active'
        self.update_activity()

    def to_dict(self, include_stats: bool = True, include_participants: bool = False) -> dict:
        """Convert to dictionary with optional additional data."""
        data = super().to_dict()

        if include_stats:
            data.update({
                'total_cost': float(self.total_cost),
                'latest_activity': self.last_activity_at.isoformat() if self.last_activity_at else None
            })

        if include_participants:
            data['participants'] = [p.to_dict() for p in self.participants]

        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"<Conversation(id={self.id}, title={self.title}, status={self.status})>"


class ConversationParticipant(BaseModel):
    """Participant in a shared conversation."""

    __tablename__ = 'conversation_participants'

    conversation_id = Column(
        CHAR(36),
        ForeignKey('conversations.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    user_id = Column(
        CHAR(36),
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    role = Column(
        Enum('owner', 'collaborator', 'viewer', name='participant_role'),
        nullable=False,
        default='viewer',
        index=True
    )
    permissions = Column(
        JSON,
        nullable=False,
        default={'read': True, 'write': False, 'admin': False}
    )
    joined_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    last_accessed_at = Column(DateTime, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", back_populates="conversation_participations")

    # Unique constraint
    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )

    def __init__(self, **kwargs):
        """Initialize participant with default permissions."""
        super().__init__(**kwargs)
        if self.permissions is None:
            self.permissions = {'read': True, 'write': False, 'admin': False}

    def update_access_time(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed_at = datetime.utcnow()

    def has_permission(self, permission: str) -> bool:
        """Check if participant has a specific permission."""
        if self.permissions is None:
            return False
        return self.permissions.get(permission, False)

    def grant_permission(self, permission: str) -> None:
        """Grant a specific permission."""
        if self.permissions is None:
            self.permissions = {}
        self.permissions[permission] = True

    def revoke_permission(self, permission: str) -> None:
        """Revoke a specific permission."""
        if self.permissions is None:
            return
        self.permissions[permission] = False

    def __repr__(self) -> str:
        """String representation."""
        return f"<ConversationParticipant(conversation_id={self.conversation_id}, user_id={self.user_id}, role={self.role})>"