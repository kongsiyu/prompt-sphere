"""Repository layer integration tests."""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from database.repositories.user import UserRepository
from database.repositories.template import TemplateRepository
from database.repositories.conversation import ConversationRepository
from database.repositories.prompt import PromptRepository
from database.repositories.audit_log import AuditLogRepository


@pytest.mark.database
@pytest.mark.asyncio
class TestUserRepository:
    """Test UserRepository CRUD operations."""

    async def test_user_create_and_get(self, db_session: AsyncSession):
        """Test creating and retrieving a user."""
        repo = UserRepository(db_session)

        user_data = {
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "username": "testuser",
            "preferences": {"theme": "dark", "language": "en"}
        }

        # Create user
        user = await repo.create(user_data)
        assert user is not None
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.preferences["theme"] == "dark"

        # Get user by ID
        retrieved_user = await repo.get_by_id(user.id)
        assert retrieved_user is not None
        assert retrieved_user.email == user.email

    async def test_user_get_by_email(self, db_session: AsyncSession):
        """Test getting user by email."""
        repo = UserRepository(db_session)

        user_data = {
            "email": "unique@example.com",
            "password_hash": "hashed_password",
            "username": "uniqueuser"
        }

        user = await repo.create(user_data)
        retrieved_user = await repo.get_by_email("unique@example.com")

        assert retrieved_user is not None
        assert retrieved_user.id == user.id

    async def test_user_update(self, db_session: AsyncSession):
        """Test updating user data."""
        repo = UserRepository(db_session)

        user_data = {
            "email": "update@example.com",
            "password_hash": "hashed_password",
            "username": "updateuser"
        }

        user = await repo.create(user_data)

        # Update user
        update_data = {"username": "updateduser", "preferences": {"theme": "light"}}
        updated_user = await repo.update(user.id, update_data)

        assert updated_user.username == "updateduser"
        assert updated_user.preferences["theme"] == "light"

    async def test_user_soft_delete(self, db_session: AsyncSession):
        """Test soft deleting a user."""
        repo = UserRepository(db_session)

        user_data = {
            "email": "delete@example.com",
            "password_hash": "hashed_password",
            "username": "deleteuser"
        }

        user = await repo.create(user_data)

        # Soft delete
        deleted_user = await repo.soft_delete(user.id)
        assert deleted_user.deleted_at is not None

        # Should not be found in regular queries
        retrieved_user = await repo.get_by_id(user.id)
        assert retrieved_user is None


@pytest.mark.database
@pytest.mark.asyncio
class TestTemplateRepository:
    """Test TemplateRepository CRUD operations."""

    async def test_template_create_with_user(self, db_session: AsyncSession, sample_user):
        """Test creating template with user relationship."""
        repo = TemplateRepository(db_session)

        template_data = {
            "name": "Test Template",
            "description": "A test template",
            "content": "Template content with {variable}",
            "category": "test",
            "tags": ["test", "sample"],
            "variables": ["variable"],
            "creator_id": sample_user.id
        }

        template = await repo.create(template_data)
        assert template is not None
        assert template.name == "Test Template"
        assert template.creator_id == sample_user.id
        assert "test" in template.tags
        assert "variable" in template.variables

    async def test_template_get_by_category(self, db_session: AsyncSession, sample_user):
        """Test getting templates by category."""
        repo = TemplateRepository(db_session)

        # Create templates in different categories
        template1_data = {
            "name": "Template 1",
            "content": "Content 1",
            "category": "productivity",
            "creator_id": sample_user.id
        }

        template2_data = {
            "name": "Template 2",
            "content": "Content 2",
            "category": "creativity",
            "creator_id": sample_user.id
        }

        await repo.create(template1_data)
        await repo.create(template2_data)

        # Get by category
        productivity_templates = await repo.get_by_category("productivity")
        assert len(productivity_templates) >= 1
        assert all(t.category == "productivity" for t in productivity_templates)

    async def test_template_search_by_tags(self, db_session: AsyncSession, sample_user):
        """Test searching templates by tags."""
        repo = TemplateRepository(db_session)

        template_data = {
            "name": "Tagged Template",
            "content": "Content",
            "category": "test",
            "tags": ["python", "automation", "testing"],
            "creator_id": sample_user.id
        }

        template = await repo.create(template_data)

        # Search by tag
        results = await repo.search_by_tags(["python"])
        assert len(results) >= 1
        assert any(t.id == template.id for t in results)


@pytest.mark.database
@pytest.mark.asyncio
class TestConversationRepository:
    """Test ConversationRepository CRUD operations."""

    async def test_conversation_create_with_context(self, db_session: AsyncSession, sample_user, sample_template):
        """Test creating conversation with context."""
        repo = ConversationRepository(db_session)

        conversation_data = {
            "title": "Test Conversation",
            "context": {
                "user_preferences": {"style": "formal"},
                "session_data": {"start_time": "2024-01-01T10:00:00"}
            },
            "settings": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "user_id": sample_user.id,
            "template_id": sample_template.id
        }

        conversation = await repo.create(conversation_data)
        assert conversation is not None
        assert conversation.title == "Test Conversation"
        assert conversation.context["user_preferences"]["style"] == "formal"
        assert conversation.settings["model"] == "gpt-4"
        assert conversation.user_id == sample_user.id
        assert conversation.template_id == sample_template.id

    async def test_conversation_get_by_user(self, db_session: AsyncSession, sample_user, sample_template):
        """Test getting conversations by user."""
        repo = ConversationRepository(db_session)

        # Create multiple conversations for user
        for i in range(3):
            conversation_data = {
                "title": f"Conversation {i}",
                "user_id": sample_user.id,
                "template_id": sample_template.id
            }
            await repo.create(conversation_data)

        # Get conversations by user
        user_conversations = await repo.get_by_user_id(sample_user.id)
        assert len(user_conversations) >= 3
        assert all(c.user_id == sample_user.id for c in user_conversations)


@pytest.mark.database
@pytest.mark.asyncio
class TestPromptRepository:
    """Test PromptRepository CRUD operations."""

    async def test_prompt_create_with_sequence(self, db_session: AsyncSession, sample_conversation):
        """Test creating prompts with automatic sequence numbering."""
        repo = PromptRepository(db_session)

        # Create first prompt
        prompt1_data = {
            "content": "First prompt",
            "type": "user",
            "conversation_id": sample_conversation.id
        }

        prompt1 = await repo.create(prompt1_data)
        assert prompt1.sequence_number == 1

        # Create second prompt
        prompt2_data = {
            "content": "Second prompt",
            "type": "assistant",
            "conversation_id": sample_conversation.id
        }

        prompt2 = await repo.create(prompt2_data)
        assert prompt2.sequence_number == 2

    async def test_prompt_get_by_conversation(self, db_session: AsyncSession, sample_conversation):
        """Test getting prompts by conversation with ordering."""
        repo = PromptRepository(db_session)

        # Create prompts in conversation
        prompts_data = [
            {"content": "Prompt 1", "type": "user", "conversation_id": sample_conversation.id},
            {"content": "Prompt 2", "type": "assistant", "conversation_id": sample_conversation.id},
            {"content": "Prompt 3", "type": "user", "conversation_id": sample_conversation.id}
        ]

        created_prompts = []
        for data in prompts_data:
            prompt = await repo.create(data)
            created_prompts.append(prompt)

        # Get prompts by conversation
        conversation_prompts = await repo.get_by_conversation_id(sample_conversation.id)

        assert len(conversation_prompts) >= 3
        # Should be ordered by sequence number
        for i in range(len(conversation_prompts) - 1):
            assert conversation_prompts[i].sequence_number <= conversation_prompts[i + 1].sequence_number


@pytest.mark.database
@pytest.mark.asyncio
class TestAuditLogRepository:
    """Test AuditLogRepository operations."""

    async def test_audit_log_create(self, db_session: AsyncSession, sample_user):
        """Test creating audit log entries."""
        repo = AuditLogRepository(db_session)

        log_data = {
            "action": "user_login",
            "entity_type": "User",
            "entity_id": sample_user.id,
            "user_id": sample_user.id,
            "custom_metadata": {
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0...",
                "success": True
            }
        }

        log_entry = await repo.create(log_data)
        assert log_entry is not None
        assert log_entry.action == "user_login"
        assert log_entry.entity_type == "User"
        assert log_entry.custom_metadata["ip_address"] == "192.168.1.1"
        assert log_entry.custom_metadata["success"] is True

    async def test_audit_log_get_by_user(self, db_session: AsyncSession, sample_user):
        """Test getting audit logs by user."""
        repo = AuditLogRepository(db_session)

        # Create multiple log entries
        actions = ["login", "create_template", "start_conversation"]
        for action in actions:
            log_data = {
                "action": action,
                "entity_type": "User",
                "entity_id": sample_user.id,
                "user_id": sample_user.id
            }
            await repo.create(log_data)

        # Get logs by user
        user_logs = await repo.get_by_user_id(sample_user.id)
        assert len(user_logs) >= 3
        assert all(log.user_id == sample_user.id for log in user_logs)

    async def test_audit_log_get_by_action(self, db_session: AsyncSession, sample_user):
        """Test getting audit logs by action type."""
        repo = AuditLogRepository(db_session)

        # Create log entries with different actions
        log_data = {
            "action": "template_deleted",
            "entity_type": "Template",
            "entity_id": 123,
            "user_id": sample_user.id,
            "custom_metadata": {"reason": "user_request"}
        }

        await repo.create(log_data)

        # Get logs by action
        deletion_logs = await repo.get_by_action("template_deleted")
        assert len(deletion_logs) >= 1
        assert all(log.action == "template_deleted" for log in deletion_logs)


@pytest.mark.database
@pytest.mark.asyncio
class TestRepositoryTransactions:
    """Test transaction handling across repositories."""

    async def test_cross_repository_transaction(self, db_session: AsyncSession):
        """Test operations across multiple repositories in same transaction."""
        user_repo = UserRepository(db_session)
        template_repo = TemplateRepository(db_session)
        audit_repo = AuditLogRepository(db_session)

        # Create user
        user_data = {
            "email": "transaction@example.com",
            "password_hash": "hashed_password",
            "username": "transactionuser"
        }
        user = await user_repo.create(user_data)

        # Create template for user
        template_data = {
            "name": "Transaction Template",
            "content": "Template content",
            "category": "test",
            "creator_id": user.id
        }
        template = await template_repo.create(template_data)

        # Create audit log
        audit_data = {
            "action": "template_created",
            "entity_type": "Template",
            "entity_id": template.id,
            "user_id": user.id
        }
        audit_log = await audit_repo.create(audit_data)

        # All should be created successfully
        assert user.id is not None
        assert template.id is not None
        assert audit_log.id is not None
        assert template.creator_id == user.id
        assert audit_log.entity_id == template.id


@pytest.mark.database
@pytest.mark.asyncio
class TestRepositoryErrorHandling:
    """Test error handling in repositories."""

    async def test_duplicate_email_constraint(self, db_session: AsyncSession):
        """Test handling of duplicate email constraint."""
        repo = UserRepository(db_session)

        user_data = {
            "email": "duplicate@example.com",
            "password_hash": "hashed_password",
            "username": "user1"
        }

        # Create first user
        user1 = await repo.create(user_data)
        assert user1 is not None

        # Try to create second user with same email
        user_data["username"] = "user2"

        with pytest.raises(IntegrityError):
            await repo.create(user_data)

    async def test_foreign_key_constraint(self, db_session: AsyncSession):
        """Test foreign key constraint handling."""
        template_repo = TemplateRepository(db_session)

        template_data = {
            "name": "Invalid Template",
            "content": "Content",
            "category": "test",
            "creator_id": 99999  # Non-existent user ID
        }

        with pytest.raises(IntegrityError):
            await template_repo.create(template_data)