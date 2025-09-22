"""
User model for authentication and profile management.
"""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum, Text
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.orm import relationship

from .base import BaseModel


class User(BaseModel):
    """User model with authentication and profile information."""

    __tablename__ = 'users'

    # Authentication fields
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)

    # Profile fields
    full_name = Column(String(100), nullable=False)
    role = Column(
        Enum('admin', 'user', 'viewer', name='user_role'),
        nullable=False,
        default='user'
    )

    # Account status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    email_verified = Column(Boolean, nullable=False, default=False, index=True)

    # Security fields
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True, index=True)
    login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)

    # User preferences and settings
    preferences = Column(JSON, nullable=True, default={})

    # Relationships
    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    templates = relationship(
        "Template",
        back_populates="creator",
        foreign_keys="Template.created_by"
    )

    template_ratings = relationship(
        "TemplateRating",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="user"
    )

    conversation_participations = relationship(
        "ConversationParticipant",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __init__(self, **kwargs):
        """Initialize user with default preferences."""
        super().__init__(**kwargs)
        if self.preferences is None:
            self.preferences = {
                'theme': 'light',
                'language': 'en',
                'notifications': {
                    'email': True,
                    'push': False
                },
                'ai_settings': {
                    'default_model': 'gpt-3.5-turbo',
                    'temperature': 0.7,
                    'max_tokens': 2000
                }
            }

    def set_password(self, password: str) -> None:
        """Set hashed password."""
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if provided password matches hash."""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == 'admin'

    def can_edit_template(self, template) -> bool:
        """Check if user can edit a template."""
        return self.is_admin() or template.created_by == self.id

    def increment_login_attempts(self) -> None:
        """Increment failed login attempts."""
        self.login_attempts += 1
        if self.login_attempts >= 5:
            self.locked_until = datetime.utcnow().replace(
                minute=datetime.utcnow().minute + 30
            )

    def reset_login_attempts(self) -> None:
        """Reset login attempts after successful login."""
        self.login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()

    def is_locked(self) -> bool:
        """Check if account is locked due to failed attempts."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    def update_preference(self, key: str, value) -> None:
        """Update a specific preference."""
        if self.preferences is None:
            self.preferences = {}

        # Handle nested keys like 'ai_settings.temperature'
        keys = key.split('.')
        current = self.preferences

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def get_preference(self, key: str, default=None):
        """Get a specific preference value."""
        if self.preferences is None:
            return default

        # Handle nested keys
        keys = key.split('.')
        current = self.preferences

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Convert to dictionary, optionally excluding sensitive data."""
        data = super().to_dict()

        if not include_sensitive:
            # Remove sensitive fields
            sensitive_fields = [
                'password_hash',
                'email_verification_token',
                'password_reset_token',
                'login_attempts',
                'locked_until'
            ]
            for field in sensitive_fields:
                data.pop(field, None)

        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"