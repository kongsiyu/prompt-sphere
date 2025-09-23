"""Unit tests for database models."""

import pytest

from database.models.user import User
from database.models.template import Template
from database.models.conversation import Conversation
from database.models.prompt import Prompt
from database.models.audit_log import AuditLog


@pytest.mark.unit
class TestUserModel:
    """Test User model functionality."""

    def test_user_creation(self):
        """Test creating a User instance."""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            full_name="Test User"
        )

        assert user.email == "test@example.com"
        assert user.password_hash == "hashed_password"
        assert user.full_name == "Test User"

    def test_user_with_preferences(self):
        """Test user with preferences JSON field."""
        preferences = {"theme": "dark", "language": "en"}
        user = User(
            email="test@example.com",
            password_hash="hash",
            full_name="Test User",
            preferences=preferences
        )
        assert user.preferences == preferences

    def test_user_repr(self):
        """Test User string representation."""
        user = User(
            email="test@example.com",
            password_hash="hash",
            full_name="Test User"
        )
        result = repr(user)
        assert "User" in result


@pytest.mark.unit
class TestTemplateModel:
    """Test Template model functionality."""

    def test_template_creation(self):
        """Test creating a Template instance."""
        template = Template(
            name="Test Template",
            content="Test content",
            created_by="user-id"
        )

        assert template.name == "Test Template"
        assert template.content == "Test content"
        assert template.created_by == "user-id"

    def test_template_with_tags(self):
        """Test template with tags JSON field."""
        tags = ["ai", "helpful"]
        template = Template(
            name="Test Template",
            content="Test content",
            created_by="user-id",
            tags=tags
        )
        assert template.tags == tags

    def test_template_repr(self):
        """Test Template string representation."""
        template = Template(
            name="Test Template",
            content="Content",
            created_by="user-id"
        )
        result = repr(template)
        assert "Template" in result


@pytest.mark.unit
class TestConversationModel:
    """Test Conversation model functionality."""

    def test_conversation_creation(self):
        """Test creating a Conversation instance."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user-id"
        )

        assert conversation.title == "Test Conversation"
        assert conversation.user_id == "user-id"

    def test_conversation_with_context(self):
        """Test conversation with context JSON field."""
        context = {"topic": "programming"}
        conversation = Conversation(
            title="Test Conversation",
            user_id="user-id",
            context=context
        )
        assert conversation.context == context

    def test_conversation_repr(self):
        """Test Conversation string representation."""
        conversation = Conversation(
            title="Test Conversation",
            user_id="user-id"
        )
        result = repr(conversation)
        assert "Conversation" in result


@pytest.mark.unit
class TestPromptModel:
    """Test Prompt model functionality."""

    def test_prompt_creation(self):
        """Test creating a Prompt instance."""
        prompt = Prompt(
            conversation_id="conv-id",
            content="Test prompt content",
            user_input="User question",
            sequence_number=1
        )

        assert prompt.conversation_id == "conv-id"
        assert prompt.content == "Test prompt content"
        assert prompt.user_input == "User question"
        assert prompt.sequence_number == 1

    def test_prompt_repr(self):
        """Test Prompt string representation."""
        prompt = Prompt(
            conversation_id="conv-id",
            content="Test prompt",
            user_input="User input",
            sequence_number=1
        )
        result = repr(prompt)
        assert "Prompt" in result


@pytest.mark.unit
class TestAuditLogModel:
    """Test AuditLog model functionality."""

    def test_audit_log_creation(self):
        """Test creating an AuditLog instance."""
        audit_log = AuditLog(
            action="create_user",
            entity_type="user"
        )

        assert audit_log.action == "create_user"
        assert audit_log.entity_type == "user"

    def test_audit_log_with_metadata(self):
        """Test audit log with custom_metadata JSON field."""
        metadata = {"email": "test@example.com"}
        audit_log = AuditLog(
            action="create_user",
            entity_type="user",
            entity_id="user-123",
            custom_metadata=metadata
        )
        assert audit_log.custom_metadata == metadata

    def test_audit_log_repr(self):
        """Test AuditLog string representation."""
        audit_log = AuditLog(
            action="test_action",
            entity_type="test_type"
        )
        result = repr(audit_log)
        assert "AuditLog" in result


@pytest.mark.unit
class TestModelInheritance:
    """Test model inheritance and base features."""

    def test_models_inherit_from_base(self):
        """Test that most models inherit from BaseModel."""
        from database.models.base import BaseModel, Base

        base_models = [User, Template, Conversation, Prompt]
        for model_class in base_models:
            assert issubclass(model_class, BaseModel)

        # AuditLog inherits directly from Base
        assert issubclass(AuditLog, Base)

    def test_models_have_table_names(self):
        """Test that models have correct table names."""
        assert User.__tablename__ == "users"
        assert Template.__tablename__ == "templates"
        assert Conversation.__tablename__ == "conversations"
        assert Prompt.__tablename__ == "prompts"
        assert AuditLog.__tablename__ == "audit_logs"

    def test_models_can_be_created_without_database(self):
        """Test that model instances can be created without database connection."""
        user = User(email="test@example.com", password_hash="hash", full_name="Test")
        template = Template(name="Test", content="Content", created_by="user-id")
        conversation = Conversation(title="Test", user_id="user-id")
        prompt = Prompt(conversation_id="conv-id", content="Test", user_input="Input", sequence_number=1)
        audit_log = AuditLog(action="test", entity_type="test")

        assert user.email == "test@example.com"
        assert template.name == "Test"
        assert conversation.title == "Test"
        assert prompt.content == "Test"
        assert audit_log.action == "test"


@pytest.mark.unit
class TestModelFields:
    """Test specific model field behavior."""

    def test_user_required_fields(self):
        """Test user model required fields."""
        user = User(
            email="required@example.com",
            password_hash="required_hash",
            full_name="Required Name"
        )
        assert user.email is not None
        assert user.password_hash is not None
        assert user.full_name is not None

    def test_template_required_fields(self):
        """Test template model required fields."""
        template = Template(
            name="Required Name",
            content="Required Content",
            created_by="required-user-id"
        )
        assert template.name is not None
        assert template.content is not None
        assert template.created_by is not None

    def test_conversation_required_fields(self):
        """Test conversation model required fields."""
        conversation = Conversation(
            title="Required Title",
            user_id="required-user-id"
        )
        assert conversation.title is not None
        assert conversation.user_id is not None

    def test_prompt_required_fields(self):
        """Test prompt model required fields."""
        prompt = Prompt(
            conversation_id="required-conv-id",
            content="Required Content",
            user_input="Required Input",
            sequence_number=1
        )
        assert prompt.conversation_id is not None
        assert prompt.content is not None
        assert prompt.user_input is not None
        assert prompt.sequence_number is not None

    def test_audit_log_required_fields(self):
        """Test audit log model required fields."""
        audit_log = AuditLog(
            action="required_action",
            entity_type="required_type"
        )
        assert audit_log.action is not None
        assert audit_log.entity_type is not None