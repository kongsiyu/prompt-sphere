"""
Database models for the AI System Prompt Generator.

This module provides SQLAlchemy models for all database entities
with proper relationships, constraints, and business logic.
"""

from .base import Base, BaseModel, TimestampMixin, AuditMixin
from .user import User
from .template import Template, TemplateRating
from .conversation import Conversation, ConversationParticipant
from .prompt import Prompt
from .audit_log import (
    AuditLog,
    log_user_action,
    log_system_action,
    log_security_event,
    log_authentication
)

# Export all models for easy importing
__all__ = [
    # Base classes
    'Base',
    'BaseModel',
    'TimestampMixin',
    'AuditMixin',

    # Core models
    'User',
    'Template',
    'TemplateRating',
    'Conversation',
    'ConversationParticipant',
    'Prompt',
    'AuditLog',

    # Audit logging functions
    'log_user_action',
    'log_system_action',
    'log_security_event',
    'log_authentication',
]

# Metadata for the database schema
SCHEMA_VERSION = "1.0.0"
SCHEMA_DESCRIPTION = "AI System Prompt Generator Database Schema"

# Model registry for dynamic operations
MODEL_REGISTRY = {
    'users': User,
    'templates': Template,
    'template_ratings': TemplateRating,
    'conversations': Conversation,
    'conversation_participants': ConversationParticipant,
    'prompts': Prompt,
    'audit_logs': AuditLog,
}

# Entity type mapping for audit logs
ENTITY_TYPES = {
    'user': 'users',
    'template': 'templates',
    'conversation': 'conversations',
    'prompt': 'prompts',
    'template_rating': 'template_ratings',
    'conversation_participant': 'conversation_participants',
}


def get_model_by_name(model_name: str):
    """
    Get a model class by its name.

    Args:
        model_name: Name of the model (table name)

    Returns:
        Model class or None if not found
    """
    return MODEL_REGISTRY.get(model_name)


def get_entity_type(model_class) -> str:
    """
    Get the entity type string for a model class.

    Args:
        model_class: SQLAlchemy model class

    Returns:
        Entity type string for audit logging
    """
    table_name = getattr(model_class, '__tablename__', None)
    return table_name or model_class.__name__.lower()


def create_all_tables(engine):
    """
    Create all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine):
    """
    Drop all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    Base.metadata.drop_all(bind=engine)