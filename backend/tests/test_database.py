"""
Comprehensive test suite for database repositories and CRUD operations.

This module tests all repository implementations, CRUD operations,
database constraints, performance, and integration scenarios.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, select, func

# Repository imports
from database.repositories import (
    UserRepository, TemplateRepository, ConversationRepository,
    PromptRepository, AuditLogRepository, RepositoryError
)

# Model imports
from database.models import (
    User, Template, TemplateRating, Conversation, ConversationParticipant,
    Prompt, AuditLog
)

# Fixture imports
from tests.fixtures import (
    create_test_user, create_admin_user, create_test_user_set,
    create_test_template, create_template_with_rating, create_sample_templates,
    create_test_conversation, create_shared_conversation, create_conversation_with_participants,
    create_test_prompt, create_prompt_chain, create_sample_prompts,
    create_test_audit_log, create_sample_audit_logs
)


class TestUserRepository:
    """Test suite for UserRepository."""

    @pytest.fixture
    async def user_repo(self, async_session: AsyncSession):
        """Create UserRepository instance."""
        return UserRepository(async_session)

    async def test_create_user(self, user_repo: UserRepository):
        """Test user creation with password hashing."""
        user = await user_repo.create_user(
            email="test@example.com",
            password="testpassword123",
            full_name="Test User",
            role="user"
        )

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.role == "user"
        assert user.is_active is True
        assert user.check_password("testpassword123")
        assert not user.check_password("wrongpassword")

    async def test_create_duplicate_user_fails(self, user_repo: UserRepository):
        """Test that creating duplicate email fails."""
        await user_repo.create_user(
            email="duplicate@example.com",
            password="password123",
            full_name="First User"
        )

        with pytest.raises(RepositoryError, match="already exists"):
            await user_repo.create_user(
                email="duplicate@example.com",
                password="password456",
                full_name="Second User"
            )

    async def test_find_by_email(self, user_repo: UserRepository):
        """Test finding user by email."""
        created_user = await user_repo.create_user(
            email="findme@example.com",
            password="password123",
            full_name="Find Me"
        )

        found_user = await user_repo.find_by_email("findme@example.com")
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == "findme@example.com"

        # Test case insensitivity
        found_user_upper = await user_repo.find_by_email("FINDME@EXAMPLE.COM")
        assert found_user_upper is not None
        assert found_user_upper.id == created_user.id

    async def test_authenticate_user(self, user_repo: UserRepository):
        """Test user authentication."""
        user = await user_repo.create_user(
            email="auth@example.com",
            password="correctpassword",
            full_name="Auth User"
        )

        # Test successful authentication
        authenticated = await user_repo.authenticate("auth@example.com", "correctpassword")
        assert authenticated is not None
        assert authenticated.id == user.id
        assert authenticated.last_login_at is not None

        # Test failed authentication
        failed_auth = await user_repo.authenticate("auth@example.com", "wrongpassword")
        assert failed_auth is None

        # Test non-existent user
        no_user = await user_repo.authenticate("nonexistent@example.com", "password")
        assert no_user is None

    async def test_account_locking(self, user_repo: UserRepository):
        """Test account locking after failed attempts."""
        user = await user_repo.create_user(
            email="locktest@example.com",
            password="password123",
            full_name="Lock Test"
        )

        # Make 5 failed attempts to lock account
        for _ in range(5):
            result = await user_repo.authenticate("locktest@example.com", "wrongpassword")
            assert result is None

        # Refresh user to check lock status
        locked_user = await user_repo.get_by_id(user.id)
        assert locked_user.is_locked() is True

        # Even correct password should fail when locked
        locked_auth = await user_repo.authenticate("locktest@example.com", "password123")
        assert locked_auth is None

    async def test_update_password(self, user_repo: UserRepository):
        """Test password update functionality."""
        user = await user_repo.create_user(
            email="password@example.com",
            password="oldpassword",
            full_name="Password User"
        )

        # Update password
        success = await user_repo.update_password(user.id, "newpassword123")
        assert success is True

        # Test authentication with new password
        auth_new = await user_repo.authenticate("password@example.com", "newpassword123")
        assert auth_new is not None

        # Test old password no longer works
        auth_old = await user_repo.authenticate("password@example.com", "oldpassword")
        assert auth_old is None

    async def test_user_preferences(self, user_repo: UserRepository):
        """Test user preferences management."""
        user = await user_repo.create_user(
            email="prefs@example.com",
            password="password123",
            full_name="Prefs User"
        )

        # Update preferences
        new_prefs = {
            'theme': 'dark',
            'ai_settings.temperature': 0.9,
            'notifications.email': False
        }

        success = await user_repo.update_preferences(user.id, new_prefs)
        assert success is True

        # Verify preferences were updated
        updated_user = await user_repo.get_by_id(user.id)
        assert updated_user.get_preference('theme') == 'dark'
        assert updated_user.get_preference('ai_settings.temperature') == 0.9
        assert updated_user.get_preference('notifications.email') is False

    async def test_search_users(self, user_repo: UserRepository):
        """Test user search functionality."""
        # Create test users
        await user_repo.create_user("john.doe@example.com", "pass", "John Doe")
        await user_repo.create_user("jane.smith@example.com", "pass", "Jane Smith")
        await user_repo.create_user("bob.wilson@example.com", "pass", "Bob Wilson")

        # Search by name
        john_results = await user_repo.search_users("John")
        assert len(john_results) == 1
        assert john_results[0].full_name == "John Doe"

        # Search by email
        smith_results = await user_repo.search_users("smith")
        assert len(smith_results) == 1
        assert smith_results[0].email == "jane.smith@example.com"

    async def test_get_user_statistics(self, user_repo: UserRepository):
        """Test user statistics generation."""
        # Create users with different roles and states
        await user_repo.create_user("admin@example.com", "pass", "Admin", role="admin")
        await user_repo.create_user("user1@example.com", "pass", "User 1", role="user")
        await user_repo.create_user("user2@example.com", "pass", "User 2", role="user", is_active=False)
        await user_repo.create_user("viewer@example.com", "pass", "Viewer", role="viewer")

        stats = await user_repo.get_user_statistics()

        assert stats['total_users'] == 4
        assert stats['active_users'] == 3
        assert stats['inactive_users'] == 1
        assert stats['users_by_role']['admin'] == 1
        assert stats['users_by_role']['user'] == 2
        assert stats['users_by_role']['viewer'] == 1

    async def test_soft_delete_user(self, user_repo: UserRepository):
        """Test soft delete functionality."""
        user = await user_repo.create_user(
            email="delete@example.com",
            password="password123",
            full_name="Delete User"
        )

        # Soft delete user
        deleted = await user_repo.delete(user.id, soft_delete=True)
        assert deleted is True

        # User should not be found in normal queries
        found = await user_repo.get_by_id(user.id)
        assert found is None

        # User should be found when including deleted
        found_deleted = await user_repo.get_by_id(user.id, include_deleted=True)
        assert found_deleted is not None
        assert found_deleted.is_deleted is True

        # Restore user
        restored = await user_repo.restore(user.id)
        assert restored is not None
        assert restored.is_deleted is False


class TestTemplateRepository:
    """Test suite for TemplateRepository."""

    @pytest.fixture
    async def template_repo(self, async_session: AsyncSession):
        """Create TemplateRepository instance."""
        return TemplateRepository(async_session)

    @pytest.fixture
    async def test_user(self, async_session: AsyncSession):
        """Create a test user for template operations."""
        return await create_test_user(async_session)

    async def test_create_template(self, template_repo: TemplateRepository, test_user: User):
        """Test template creation."""
        template = await template_repo.create_template(
            name="Test Template",
            content="Hello {name}, welcome to {platform}!",
            created_by=test_user.id,
            description="A test template",
            category="greeting",
            tags=["greeting", "welcome"],
            is_public=True
        )

        assert template.id is not None
        assert template.name == "Test Template"
        assert template.content == "Hello {name}, welcome to {platform}!"
        assert template.created_by == test_user.id
        assert template.category == "greeting"
        assert template.tags == ["greeting", "welcome"]
        assert template.is_public is True
        assert template.usage_count == 0
        assert template.version == 1

    async def test_template_variables_extraction(self, template_repo: TemplateRepository, test_user: User):
        """Test template variable extraction."""
        template = await template_repo.create_template(
            name="Variable Template",
            content="Hello {name}, your {item} costs ${price}. Contact {support_email}.",
            created_by=test_user.id
        )

        variables = template.get_variables()
        expected_vars = {"name", "item", "price", "support_email"}
        assert set(variables) == expected_vars

    async def test_template_rendering(self, template_repo: TemplateRepository, test_user: User):
        """Test template rendering with variables."""
        template = await template_repo.create_template(
            name="Render Template",
            content="Hello {name}, your order #{order_id} is {status}.",
            created_by=test_user.id
        )

        rendered = template.render({
            "name": "John",
            "order_id": "12345",
            "status": "shipped"
        })

        expected = "Hello John, your order #12345 is shipped."
        assert rendered == expected

    async def test_template_usage_tracking(self, template_repo: TemplateRepository, test_user: User):
        """Test template usage tracking."""
        template = await template_repo.create_template(
            name="Usage Template",
            content="Test content",
            created_by=test_user.id
        )

        initial_usage = template.usage_count

        # Increment usage
        success = await template_repo.increment_usage(template.id, test_user.id)
        assert success is True

        # Verify usage count increased
        updated_template = await template_repo.get_by_id(template.id)
        assert updated_template.usage_count == initial_usage + 1

    async def test_search_templates(self, template_repo: TemplateRepository, test_user: User):
        """Test template search functionality."""
        # Create templates with different content
        await template_repo.create_template(
            name="Email Template",
            content="Dear customer, your order is ready",
            created_by=test_user.id,
            category="email",
            tags=["email", "order"]
        )

        await template_repo.create_template(
            name="SMS Template",
            content="Your order #123 has shipped",
            created_by=test_user.id,
            category="sms",
            tags=["sms", "shipping"]
        )

        # Search by content
        order_templates = await template_repo.search_templates("order", user_id=test_user.id)
        assert len(order_templates) == 2

        # Search by category
        email_templates = await template_repo.get_templates_by_category("email", user_id=test_user.id)
        assert len(email_templates) == 1
        assert email_templates[0].category == "email"

    async def test_template_versioning(self, template_repo: TemplateRepository, test_user: User):
        """Test template versioning system."""
        # Create original template
        original = await template_repo.create_template(
            name="Versioned Template",
            content="Version 1 content",
            created_by=test_user.id
        )

        # Create new version
        version2 = await template_repo.create_version(
            original.id,
            test_user.id,
            content="Version 2 content with improvements",
            name="Versioned Template v2"
        )

        assert version2 is not None
        assert version2.version == 2
        assert version2.parent_template_id == original.id
        assert version2.content == "Version 2 content with improvements"

        # Get all versions
        versions = await template_repo.get_template_versions(original.id)
        assert len(versions) == 2
        assert versions[0].version == 1
        assert versions[1].version == 2

    async def test_template_categories(self, template_repo: TemplateRepository, test_user: User):
        """Test template category management."""
        # Create templates in different categories
        categories = ["email", "sms", "letter", "announcement"]
        for category in categories:
            await template_repo.create_template(
                name=f"{category.title()} Template",
                content=f"Content for {category}",
                created_by=test_user.id,
                category=category,
                is_public=True
            )

        # Get categories with counts
        category_list = await template_repo.get_categories()
        category_names = [cat[0] for cat in category_list]

        for category in categories:
            assert category in category_names

    async def test_popular_templates(self, template_repo: TemplateRepository, test_user: User):
        """Test popular templates retrieval."""
        # Create templates with different usage and ratings
        low_usage = await template_repo.create_template(
            name="Low Usage",
            content="Low usage template",
            created_by=test_user.id,
            is_public=True
        )

        high_usage = await template_repo.create_template(
            name="High Usage",
            content="High usage template",
            created_by=test_user.id,
            is_public=True
        )

        # Simulate usage
        for _ in range(10):
            await template_repo.increment_usage(high_usage.id, test_user.id)

        for _ in range(2):
            await template_repo.increment_usage(low_usage.id, test_user.id)

        # Get popular templates
        popular = await template_repo.get_popular_templates(limit=5, user_id=test_user.id)

        assert len(popular) >= 2
        # High usage template should be first
        assert popular[0].id == high_usage.id
        assert popular[0].usage_count > popular[1].usage_count


class TestConversationRepository:
    """Test suite for ConversationRepository."""

    @pytest.fixture
    async def conversation_repo(self, async_session: AsyncSession):
        """Create ConversationRepository instance."""
        return ConversationRepository(async_session)

    @pytest.fixture
    async def test_user(self, async_session: AsyncSession):
        """Create a test user for conversation operations."""
        return await create_test_user(async_session)

    async def test_create_conversation(self, conversation_repo: ConversationRepository, test_user: User):
        """Test conversation creation."""
        conversation = await conversation_repo.create_conversation(
            user_id=test_user.id,
            title="Test Conversation",
            description="A test conversation",
            context={"topic": "testing"},
            settings={"model": "gpt-4", "temperature": 0.7}
        )

        assert conversation.id is not None
        assert conversation.user_id == test_user.id
        assert conversation.title == "Test Conversation"
        assert conversation.description == "A test conversation"
        assert conversation.context["topic"] == "testing"
        assert conversation.settings["model"] == "gpt-4"
        assert conversation.status == "active"

    async def test_conversation_sharing(self, conversation_repo: ConversationRepository, test_user: User):
        """Test conversation sharing functionality."""
        conversation = await conversation_repo.create_conversation(
            user_id=test_user.id,
            title="Shared Conversation"
        )

        # Generate share token
        share_token = await conversation_repo.generate_share_token(conversation.id, test_user.id)
        assert share_token is not None
        assert len(share_token) > 20  # Should be a secure token

        # Retrieve by share token
        shared_conv = await conversation_repo.get_by_share_token(share_token)
        assert shared_conv is not None
        assert shared_conv.id == conversation.id
        assert shared_conv.shared is True

        # Revoke sharing
        revoked = await conversation_repo.revoke_sharing(conversation.id, test_user.id)
        assert revoked is True

        # Should no longer be accessible by token
        revoked_conv = await conversation_repo.get_by_share_token(share_token)
        assert revoked_conv is None

    async def test_conversation_stats_update(self, conversation_repo: ConversationRepository, test_user: User):
        """Test conversation statistics updates."""
        conversation = await conversation_repo.create_conversation(
            user_id=test_user.id,
            title="Stats Conversation"
        )

        initial_messages = conversation.total_messages
        initial_tokens = conversation.total_tokens
        initial_cost = conversation.total_cost

        # Update stats
        success = await conversation_repo.update_conversation_stats(
            conversation.id,
            token_count=100,
            cost=Decimal('0.05')
        )
        assert success is True

        # Verify stats updated
        updated_conv = await conversation_repo.get_by_id(conversation.id)
        assert updated_conv.total_messages == initial_messages + 1
        assert updated_conv.total_tokens == initial_tokens + 100
        assert updated_conv.total_cost == initial_cost + Decimal('0.05')

    async def test_conversation_status_changes(self, conversation_repo: ConversationRepository, test_user: User):
        """Test conversation status management."""
        conversation = await conversation_repo.create_conversation(
            user_id=test_user.id,
            title="Status Conversation"
        )

        assert conversation.status == "active"

        # Archive conversation
        success = await conversation_repo.change_status(conversation.id, "archived", test_user.id)
        assert success is True

        archived_conv = await conversation_repo.get_by_id(conversation.id)
        assert archived_conv.status == "archived"

        # Complete conversation
        success = await conversation_repo.change_status(conversation.id, "completed", test_user.id)
        assert success is True

        completed_conv = await conversation_repo.get_by_id(conversation.id)
        assert completed_conv.status == "completed"

    async def test_search_conversations(self, conversation_repo: ConversationRepository, test_user: User):
        """Test conversation search functionality."""
        # Create conversations with different titles
        await conversation_repo.create_conversation(
            user_id=test_user.id,
            title="AI Development Discussion",
            description="Discussing AI best practices"
        )

        await conversation_repo.create_conversation(
            user_id=test_user.id,
            title="Project Planning",
            description="Planning the new AI project"
        )

        # Search by title
        ai_convs = await conversation_repo.search_conversations(test_user.id, "AI")
        assert len(ai_convs) == 2

        # Search by description
        project_convs = await conversation_repo.search_conversations(test_user.id, "project")
        assert len(project_convs) == 1

    async def test_recent_conversations(self, conversation_repo: ConversationRepository, test_user: User):
        """Test recent conversations retrieval."""
        # Create conversations with different activity times
        old_conv = await conversation_repo.create_conversation(
            user_id=test_user.id,
            title="Old Conversation"
        )

        recent_conv = await conversation_repo.create_conversation(
            user_id=test_user.id,
            title="Recent Conversation"
        )

        # Update activity times to simulate age
        old_time = datetime.utcnow() - timedelta(days=10)
        await conversation_repo.session.execute(
            text("UPDATE conversations SET last_activity_at = :time WHERE id = :id"),
            {"time": old_time, "id": old_conv.id}
        )

        # Get recent conversations (last 7 days)
        recent = await conversation_repo.get_recent_conversations(test_user.id, days=7, limit=5)

        # Should only include the recent conversation
        recent_ids = [conv.id for conv in recent]
        assert recent_conv.id in recent_ids
        assert old_conv.id not in recent_ids


class TestPromptRepository:
    """Test suite for PromptRepository."""

    @pytest.fixture
    async def prompt_repo(self, async_session: AsyncSession):
        """Create PromptRepository instance."""
        return PromptRepository(async_session)

    @pytest.fixture
    async def test_user(self, async_session: AsyncSession):
        """Create a test user."""
        return await create_test_user(async_session)

    @pytest.fixture
    async def test_conversation(self, async_session: AsyncSession, test_user: User):
        """Create a test conversation."""
        return await create_test_conversation(async_session, test_user.id)

    async def test_create_prompt(self, prompt_repo: PromptRepository, test_conversation: Conversation):
        """Test prompt creation."""
        prompt = await prompt_repo.create_prompt(
            conversation_id=test_conversation.id,
            user_input="What is artificial intelligence?",
            content="Please explain artificial intelligence",
            system_prompt="You are a helpful AI assistant",
            model_settings={
                "model_used": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )

        assert prompt.id is not None
        assert prompt.conversation_id == test_conversation.id
        assert prompt.user_input == "What is artificial intelligence?"
        assert prompt.content == "Please explain artificial intelligence"
        assert prompt.sequence_number == 1
        assert prompt.status == "pending"
        assert prompt.model_used == "gpt-4"

    async def test_prompt_processing_lifecycle(self, prompt_repo: PromptRepository, test_conversation: Conversation):
        """Test complete prompt processing lifecycle."""
        # Create prompt
        prompt = await prompt_repo.create_prompt(
            conversation_id=test_conversation.id,
            user_input="Test input",
            content="Test content"
        )

        assert prompt.status == "pending"

        # Start processing
        started = await prompt_repo.start_processing(prompt.id)
        assert started is True

        updated_prompt = await prompt_repo.get_by_id(prompt.id)
        assert updated_prompt.status == "processing"

        # Complete processing
        completed = await prompt_repo.complete_processing(
            prompt.id,
            ai_response="This is the AI response",
            response_time_ms=1500,
            token_input=50,
            token_output=100,
            model_used="gpt-3.5-turbo",
            cost=Decimal('0.025')
        )
        assert completed is True

        final_prompt = await prompt_repo.get_by_id(prompt.id)
        assert final_prompt.status == "completed"
        assert final_prompt.ai_response == "This is the AI response"
        assert final_prompt.response_time_ms == 1500
        assert final_prompt.token_count_total == 150
        assert final_prompt.cost == Decimal('0.025')

    async def test_prompt_failure_handling(self, prompt_repo: PromptRepository, test_conversation: Conversation):
        """Test prompt failure handling."""
        prompt = await prompt_repo.create_prompt(
            conversation_id=test_conversation.id,
            user_input="Test input",
            content="Test content"
        )

        # Start processing
        await prompt_repo.start_processing(prompt.id)

        # Fail processing
        failed = await prompt_repo.fail_processing(prompt.id, "API timeout error")
        assert failed is True

        failed_prompt = await prompt_repo.get_by_id(prompt.id)
        assert failed_prompt.status == "failed"
        assert failed_prompt.error_message == "API timeout error"

    async def test_prompt_rating(self, prompt_repo: PromptRepository, test_conversation: Conversation):
        """Test prompt rating functionality."""
        # Create and complete a prompt
        prompt = await prompt_repo.create_prompt(
            conversation_id=test_conversation.id,
            user_input="Test input",
            content="Test content"
        )

        await prompt_repo.complete_processing(
            prompt.id,
            ai_response="Great response",
            response_time_ms=1000,
            token_input=50,
            token_output=100,
            model_used="gpt-4"
        )

        # Rate the prompt
        rated = await prompt_repo.set_rating(prompt.id, 5, "Excellent response!")
        assert rated is True

        rated_prompt = await prompt_repo.get_by_id(prompt.id)
        assert rated_prompt.user_rating == 5
        assert rated_prompt.user_feedback == "Excellent response!"

    async def test_prompt_chains(self, prompt_repo: PromptRepository, test_conversation: Conversation):
        """Test prompt follow-up chains."""
        # Create initial prompt
        initial = await prompt_repo.create_prompt(
            conversation_id=test_conversation.id,
            user_input="What is AI?",
            content="Explain AI"
        )

        await prompt_repo.complete_processing(
            initial.id,
            ai_response="AI is artificial intelligence...",
            response_time_ms=1000,
            token_input=10,
            token_output=50,
            model_used="gpt-4"
        )

        # Create follow-up
        followup = await prompt_repo.create_followup(
            initial.id,
            user_input="Can you elaborate on machine learning?",
            content="Please elaborate on machine learning aspects"
        )

        assert followup is not None
        assert followup.parent_prompt_id == initial.id
        assert followup.sequence_number == 2
        assert followup.conversation_id == test_conversation.id

        # Get prompt chain
        chain = await prompt_repo.get_prompt_chain(followup.id)
        assert len(chain) >= 2
        chain_ids = [p.id for p in chain]
        assert initial.id in chain_ids
        assert followup.id in chain_ids

    async def test_prompt_variations(self, prompt_repo: PromptRepository, test_conversation: Conversation):
        """Test prompt variations."""
        # Create original prompt
        original = await prompt_repo.create_prompt(
            conversation_id=test_conversation.id,
            user_input="Original input",
            content="Original content"
        )

        # Create variation
        variation = await prompt_repo.create_variation(
            original.id,
            user_input="Modified input",
            content="Modified content",
            temperature=Decimal('0.9')
        )

        assert variation is not None
        assert variation.version == 2
        assert variation.user_input == "Modified input"
        assert variation.temperature == Decimal('0.9')
        assert variation.sequence_number == original.sequence_number  # Same sequence

    async def test_search_prompts(self, prompt_repo: PromptRepository, test_conversation: Conversation):
        """Test prompt search functionality."""
        # Create prompts with different content
        await prompt_repo.create_prompt(
            conversation_id=test_conversation.id,
            user_input="Explain machine learning",
            content="Machine learning explanation",
            sequence_number=1
        )

        await prompt_repo.create_prompt(
            conversation_id=test_conversation.id,
            user_input="Describe neural networks",
            content="Neural network description",
            sequence_number=2
        )

        # Search by content
        ml_prompts = await prompt_repo.search_prompts(
            "machine learning",
            conversation_id=test_conversation.id
        )
        assert len(ml_prompts) == 1

        neural_prompts = await prompt_repo.search_prompts(
            "neural",
            conversation_id=test_conversation.id
        )
        assert len(neural_prompts) == 1

    async def test_prompt_analytics(self, prompt_repo: PromptRepository, test_conversation: Conversation):
        """Test prompt analytics generation."""
        # Create prompts with different characteristics
        for i in range(5):
            prompt = await prompt_repo.create_prompt(
                conversation_id=test_conversation.id,
                user_input=f"Test input {i}",
                content=f"Test content {i}",
                sequence_number=i + 1
            )

            await prompt_repo.complete_processing(
                prompt.id,
                ai_response=f"Response {i}",
                response_time_ms=1000 + (i * 200),
                token_input=50 + (i * 10),
                token_output=100 + (i * 20),
                model_used="gpt-3.5-turbo",
                cost=Decimal(str(0.01 + (i * 0.005)))
            )

        # Get analytics
        analytics = await prompt_repo.get_prompt_analytics(
            conversation_id=test_conversation.id,
            days=30
        )

        assert analytics['total_prompts'] == 5
        assert analytics['prompts_by_status']['completed'] == 5
        assert analytics['token_statistics']['total'] > 0
        assert analytics['cost_statistics']['total'] > 0
        assert analytics['model_usage']['gpt-3.5-turbo'] == 5


class TestAuditLogRepository:
    """Test suite for AuditLogRepository."""

    @pytest.fixture
    async def audit_repo(self, async_session: AsyncSession):
        """Create AuditLogRepository instance."""
        return AuditLogRepository(async_session)

    @pytest.fixture
    async def test_user(self, async_session: AsyncSession):
        """Create a test user."""
        return await create_test_user(async_session)

    async def test_log_user_action(self, audit_repo: AuditLogRepository, test_user: User):
        """Test user action logging."""
        audit_log = await audit_repo.log_user_action(
            user_id=test_user.id,
            action="CREATE",
            entity_type="template",
            entity_id="template_123",
            details={"template_name": "Test Template"},
            ip_address="192.168.1.1",
            user_agent="TestAgent/1.0"
        )

        assert audit_log.id is not None
        assert audit_log.user_id == test_user.id
        assert audit_log.action == "CREATE"
        assert audit_log.entity_type == "template"
        assert audit_log.entity_id == "template_123"
        assert audit_log.category == "user_action"
        assert audit_log.ip_address == "192.168.1.1"

    async def test_log_security_event(self, audit_repo: AuditLogRepository, test_user: User):
        """Test security event logging."""
        audit_log = await audit_repo.log_security_event(
            event_type="FAILED_LOGIN",
            user_id=test_user.id,
            details={"reason": "invalid_password", "attempts": 3},
            severity="MEDIUM",
            ip_address="192.168.1.100"
        )

        assert audit_log.action == "FAILED_LOGIN"
        assert audit_log.entity_type == "security"
        assert audit_log.category == "security"
        assert audit_log.severity == "MEDIUM"
        assert audit_log.metadata["reason"] == "invalid_password"

    async def test_log_authentication(self, audit_repo: AuditLogRepository, test_user: User):
        """Test authentication logging."""
        # Successful login
        success_log = await audit_repo.log_authentication(
            user_id=test_user.id,
            action="LOGIN",
            ip_address="192.168.1.1",
            user_agent="Browser/1.0",
            success=True
        )

        assert success_log.action == "LOGIN"
        assert success_log.category == "authentication"
        assert success_log.severity == "LOW"
        assert success_log.metadata["success"] is True

        # Failed login
        failed_log = await audit_repo.log_authentication(
            user_id=test_user.id,
            action="LOGIN",
            ip_address="192.168.1.1",
            user_agent="Browser/1.0",
            success=False,
            details={"reason": "invalid_credentials"}
        )

        assert failed_log.severity == "MEDIUM"
        assert failed_log.metadata["success"] is False

    async def test_get_user_activity(self, audit_repo: AuditLogRepository, test_user: User):
        """Test user activity retrieval."""
        # Create several user actions
        actions = ["CREATE", "UPDATE", "DELETE"]
        for action in actions:
            await audit_repo.log_user_action(
                user_id=test_user.id,
                action=action,
                entity_type="template",
                entity_id=f"template_{action.lower()}"
            )

        # Get user activity
        activity = await audit_repo.get_user_activity(test_user.id, days=1)
        assert len(activity) == 3

        action_types = [log.action for log in activity]
        for action in actions:
            assert action in action_types

    async def test_get_entity_history(self, audit_repo: AuditLogRepository, test_user: User):
        """Test entity history retrieval."""
        entity_id = "template_history_test"

        # Create history for an entity
        await audit_repo.log_user_action(
            user_id=test_user.id,
            action="CREATE",
            entity_type="template",
            entity_id=entity_id
        )

        await audit_repo.log_user_action(
            user_id=test_user.id,
            action="UPDATE",
            entity_type="template",
            entity_id=entity_id
        )

        # Get entity history
        history = await audit_repo.get_entity_history("template", entity_id)
        assert len(history) == 2

        # Should be ordered by creation time (newest first)
        assert history[0].action == "UPDATE"
        assert history[1].action == "CREATE"

    async def test_search_logs(self, audit_repo: AuditLogRepository, test_user: User):
        """Test audit log search functionality."""
        # Create logs with different content
        await audit_repo.log_user_action(
            user_id=test_user.id,
            action="CREATE",
            entity_type="template",
            details={"search_term": "machine_learning"}
        )

        await audit_repo.log_user_action(
            user_id=test_user.id,
            action="UPDATE",
            entity_type="conversation",
            details={"search_term": "data_analysis"}
        )

        # Search by entity type
        template_logs = await audit_repo.search_logs(
            search_term="template",
            user_id=test_user.id,
            days=1
        )
        assert len(template_logs) >= 1

        # Search by action
        create_logs = await audit_repo.search_logs(
            search_term="CREATE",
            user_id=test_user.id,
            days=1
        )
        assert len(create_logs) >= 1

    async def test_get_security_logs(self, audit_repo: AuditLogRepository, test_user: User):
        """Test security logs retrieval."""
        # Create various security events
        await audit_repo.log_security_event(
            event_type="FAILED_LOGIN",
            user_id=test_user.id,
            severity="MEDIUM"
        )

        await audit_repo.log_security_event(
            event_type="PASSWORD_CHANGE",
            user_id=test_user.id,
            severity="LOW"
        )

        await audit_repo.log_security_event(
            event_type="SECURITY_BREACH",
            severity="CRITICAL"
        )

        # Get all security logs
        security_logs = await audit_repo.get_security_logs(days=1)
        assert len(security_logs) >= 3

        # Get only critical logs
        critical_logs = await audit_repo.get_security_logs(days=1, severity="CRITICAL")
        assert len(critical_logs) >= 1
        assert all(log.severity == "CRITICAL" for log in critical_logs)

    async def test_system_statistics(self, audit_repo: AuditLogRepository, test_user: User):
        """Test audit system statistics."""
        # Create various types of logs
        await audit_repo.log_user_action(test_user.id, "CREATE", "template")
        await audit_repo.log_security_event("FAILED_LOGIN", user_id=test_user.id)
        await audit_repo.log_authentication(test_user.id, "LOGIN", "192.168.1.1", "Browser/1.0")
        await audit_repo.log_system_action("BACKUP", "system")

        # Get statistics
        stats = await audit_repo.get_system_statistics(days=1)

        assert stats['total_logs'] >= 4
        assert 'logs_by_category' in stats
        assert 'logs_by_severity' in stats
        assert 'security_events' in stats
        assert stats['analysis_period_days'] == 1


class TestDatabaseIntegration:
    """Integration tests for the complete database layer."""

    @pytest.fixture
    async def repositories(self, async_session: AsyncSession):
        """Create all repository instances."""
        return {
            'user': UserRepository(async_session),
            'template': TemplateRepository(async_session),
            'conversation': ConversationRepository(async_session),
            'prompt': PromptRepository(async_session),
            'audit': AuditLogRepository(async_session)
        }

    async def test_complete_workflow(self, repositories: Dict):
        """Test complete application workflow integration."""
        # 1. Create a user
        user = await repositories['user'].create_user(
            email="workflow@example.com",
            password="password123",
            full_name="Workflow User"
        )

        # 2. Create a template
        template = await repositories['template'].create_template(
            name="Workflow Template",
            content="Hello {name}, let's discuss {topic}",
            created_by=user.id,
            category="workflow",
            is_public=True
        )

        # 3. Create a conversation
        conversation = await repositories['conversation'].create_conversation(
            user_id=user.id,
            title="Workflow Conversation",
            description="Testing complete workflow"
        )

        # 4. Create prompts in the conversation
        prompt1 = await repositories['prompt'].create_prompt(
            conversation_id=conversation.id,
            user_input="Hello, I want to discuss AI",
            content="Hello AI Assistant, I want to discuss AI",
            template_id=template.id
        )

        # 5. Process the prompt
        await repositories['prompt'].complete_processing(
            prompt1.id,
            ai_response="Hello! I'd be happy to discuss AI with you.",
            response_time_ms=1200,
            token_input=20,
            token_output=40,
            model_used="gpt-3.5-turbo",
            cost=Decimal('0.015')
        )

        # 6. Create a follow-up prompt
        prompt2 = await repositories['prompt'].create_followup(
            prompt1.id,
            user_input="What are the main AI paradigms?",
            content="Please explain the main AI paradigms"
        )

        # 7. Rate the first prompt
        await repositories['prompt'].set_rating(prompt1.id, 5, "Great response!")

        # 8. Update template usage
        await repositories['template'].increment_usage(template.id, user.id)

        # 9. Verify the complete state
        final_conversation = await repositories['conversation'].get_conversation_with_prompts(
            conversation.id,
            user_id=user.id
        )

        assert final_conversation is not None
        assert len(final_conversation.prompts) == 2
        assert final_conversation.prompts[0].user_rating == 5

        final_template = await repositories['template'].get_by_id(template.id)
        assert final_template.usage_count == 1

        # 10. Check audit logs were created
        user_activity = await repositories['audit'].get_user_activity(user.id, days=1)
        assert len(user_activity) > 0

    async def test_data_consistency(self, repositories: Dict):
        """Test data consistency across repositories."""
        # Create user and related data
        user = await repositories['user'].create_user(
            email="consistency@example.com",
            password="password123",
            full_name="Consistency User"
        )

        template = await repositories['template'].create_template(
            name="Consistency Template",
            content="Test content",
            created_by=user.id
        )

        conversation = await repositories['conversation'].create_conversation(
            user_id=user.id,
            title="Consistency Conversation"
        )

        prompt = await repositories['prompt'].create_prompt(
            conversation_id=conversation.id,
            user_input="Test input",
            content="Test content",
            template_id=template.id
        )

        # Verify relationships
        conversation_with_prompts = await repositories['conversation'].get_conversation_with_prompts(
            conversation.id,
            user_id=user.id
        )
        assert len(conversation_with_prompts.prompts) == 1
        assert conversation_with_prompts.prompts[0].id == prompt.id

        template_with_creator = await repositories['template'].get_template_with_creator(template.id)
        assert template_with_creator.creator.id == user.id

        prompt_with_context = await repositories['prompt'].get_prompt_with_context(prompt.id)
        assert prompt_with_context.conversation.id == conversation.id
        assert prompt_with_context.template.id == template.id

    async def test_transaction_rollback(self, repositories: Dict):
        """Test transaction rollback on errors."""
        user = await repositories['user'].create_user(
            email="rollback@example.com",
            password="password123",
            full_name="Rollback User"
        )

        # This should fail due to duplicate email
        with pytest.raises(RepositoryError):
            await repositories['user'].create_user(
                email="rollback@example.com",  # Duplicate email
                password="password456",
                full_name="Duplicate User"
            )

        # Original user should still exist
        found_user = await repositories['user'].find_by_email("rollback@example.com")
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.full_name == "Rollback User"


class TestDatabasePerformance:
    """Performance tests for database operations."""

    @pytest.fixture
    async def repositories(self, async_session: AsyncSession):
        """Create repository instances."""
        return {
            'user': UserRepository(async_session),
            'template': TemplateRepository(async_session),
            'conversation': ConversationRepository(async_session),
            'prompt': PromptRepository(async_session)
        }

    async def test_bulk_operations_performance(self, repositories: Dict):
        """Test performance of bulk operations."""
        # Create a user for the test
        user = await repositories['user'].create_user(
            email="bulk@example.com",
            password="password123",
            full_name="Bulk User"
        )

        # Test bulk template creation
        start_time = time.time()
        templates = []
        for i in range(100):
            template = await repositories['template'].create_template(
                name=f"Bulk Template {i}",
                content=f"Content for template {i}",
                created_by=user.id,
                category="bulk_test"
            )
            templates.append(template)

        creation_time = time.time() - start_time
        print(f"Created 100 templates in {creation_time:.2f} seconds")

        # Test bulk retrieval
        start_time = time.time()
        retrieved_templates = await repositories['template'].get_templates_by_category(
            "bulk_test",
            user_id=user.id
        )
        retrieval_time = time.time() - start_time

        print(f"Retrieved {len(retrieved_templates)} templates in {retrieval_time:.2f} seconds")
        assert len(retrieved_templates) == 100

        # Performance assertions (adjust thresholds as needed)
        assert creation_time < 30.0  # Should create 100 templates in under 30 seconds
        assert retrieval_time < 5.0   # Should retrieve 100 templates in under 5 seconds

    async def test_search_performance(self, repositories: Dict):
        """Test search operation performance."""
        user = await repositories['user'].create_user(
            email="search@example.com",
            password="password123",
            full_name="Search User"
        )

        # Create templates with searchable content
        search_terms = ["machine learning", "artificial intelligence", "data science", "neural networks"]
        for i in range(50):
            term = search_terms[i % len(search_terms)]
            await repositories['template'].create_template(
                name=f"Template about {term} {i}",
                content=f"This template discusses {term} and related concepts",
                created_by=user.id,
                tags=[term.replace(" ", "_")],
                is_public=True
            )

        # Test search performance
        start_time = time.time()
        results = await repositories['template'].search_templates(
            "machine learning",
            user_id=user.id,
            limit=20
        )
        search_time = time.time() - start_time

        print(f"Search completed in {search_time:.3f} seconds, found {len(results)} results")

        # Performance assertion
        assert search_time < 2.0  # Search should complete in under 2 seconds
        assert len(results) > 0

    async def test_complex_query_performance(self, repositories: Dict):
        """Test performance of complex queries with joins."""
        user = await repositories['user'].create_user(
            email="complex@example.com",
            password="password123",
            full_name="Complex User"
        )

        # Create related data
        conversation = await repositories['conversation'].create_conversation(
            user_id=user.id,
            title="Complex Query Test"
        )

        template = await repositories['template'].create_template(
            name="Complex Template",
            content="Complex content",
            created_by=user.id
        )

        # Create multiple prompts
        for i in range(20):
            prompt = await repositories['prompt'].create_prompt(
                conversation_id=conversation.id,
                user_input=f"Input {i}",
                content=f"Content {i}",
                template_id=template.id,
                sequence_number=i + 1
            )

            await repositories['prompt'].complete_processing(
                prompt.id,
                ai_response=f"Response {i}",
                response_time_ms=1000 + (i * 100),
                token_input=50,
                token_output=100,
                model_used="gpt-3.5-turbo"
            )

        # Test complex query performance
        start_time = time.time()
        conversation_with_data = await repositories['conversation'].get_conversation_with_prompts(
            conversation.id,
            user_id=user.id
        )
        query_time = time.time() - start_time

        print(f"Complex query completed in {query_time:.3f} seconds")

        assert conversation_with_data is not None
        assert len(conversation_with_data.prompts) == 20
        assert query_time < 1.0  # Complex query should complete in under 1 second

    @pytest.mark.skip(reason="Long-running test, enable for performance validation")
    async def test_stress_operations(self, repositories: Dict):
        """Stress test with high load operations."""
        # Create multiple users concurrently
        users = []
        start_time = time.time()

        for i in range(50):
            user = await repositories['user'].create_user(
                email=f"stress{i}@example.com",
                password="password123",
                full_name=f"Stress User {i}"
            )
            users.append(user)

        user_creation_time = time.time() - start_time
        print(f"Created 50 users in {user_creation_time:.2f} seconds")

        # Create conversations and prompts for each user
        start_time = time.time()
        for user in users:
            conversation = await repositories['conversation'].create_conversation(
                user_id=user.id,
                title=f"Stress test conversation for {user.full_name}"
            )

            for j in range(5):
                await repositories['prompt'].create_prompt(
                    conversation_id=conversation.id,
                    user_input=f"Stress test input {j}",
                    content=f"Stress test content {j}",
                    sequence_number=j + 1
                )

        data_creation_time = time.time() - start_time
        print(f"Created conversations and prompts in {data_creation_time:.2f} seconds")

        # Performance assertions for stress test
        assert user_creation_time < 60.0  # Should create 50 users in under 1 minute
        assert data_creation_time < 120.0  # Should create all data in under 2 minutes


# Test fixtures and setup
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_session(async_db_session):
    """Get async database session for tests."""
    async with async_db_session() as session:
        yield session


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "not stress"  # Skip stress tests by default
    ])