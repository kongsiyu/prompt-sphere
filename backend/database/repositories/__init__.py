"""
Repository pattern implementation for database operations.

This module provides the repository pattern for all database entities,
offering a clean abstraction layer over SQLAlchemy ORM operations.
"""

from .base import BaseRepository, RepositoryError
from .user_repository import UserRepository
from .template_repository import TemplateRepository
from .conversation_repository import ConversationRepository
from .prompt_repository import PromptRepository
from .audit_log_repository import AuditLogRepository

__all__ = [
    # Base classes
    'BaseRepository',
    'RepositoryError',

    # Repository implementations
    'UserRepository',
    'TemplateRepository',
    'ConversationRepository',
    'PromptRepository',
    'AuditLogRepository',
]

# Repository registry for dynamic access
REPOSITORY_REGISTRY = {
    'users': UserRepository,
    'templates': TemplateRepository,
    'conversations': ConversationRepository,
    'prompts': PromptRepository,
    'audit_logs': AuditLogRepository,
}


def get_repository(model_name: str, session):
    """
    Get a repository instance by model name.

    Args:
        model_name: Name of the model (table name)
        session: Database session

    Returns:
        Repository instance

    Raises:
        RepositoryError: If repository not found
    """
    repository_class = REPOSITORY_REGISTRY.get(model_name)
    if not repository_class:
        raise RepositoryError(f"No repository found for model: {model_name}")

    return repository_class(session)