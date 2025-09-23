"""Pytest configuration and fixtures."""

import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.main import app
from database.models import Base
from database.models.user import User
from database.models.template import Template
from database.models.conversation import Conversation
from database.models.prompt import Prompt
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_database_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.scalars = AsyncMock()
    session.get = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.merge = AsyncMock()
    return session


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password_hash": "hashed_password",
        "full_name": "Test User",
        "role": "user",
        "is_active": True,
        "email_verified": False,
        "preferences": {"theme": "light", "language": "en"}
    }


@pytest.fixture
def sample_template_data() -> dict:
    """Sample template data for testing."""
    return {
        "name": "Test Template",
        "description": "A test template for unit testing",
        "content": "You are a {role}. Please help with {task}.",
        "system_prompt": "Be helpful and accurate.",
        "category": "general",
        "tags": ["test", "example"],
        "is_public": False,
        "created_by": str(uuid.uuid4())
    }


@pytest.fixture
def sample_conversation_data() -> dict:
    """Sample conversation data for testing."""
    return {
        "title": "Test Conversation",
        "user_id": str(uuid.uuid4()),
        "template_id": str(uuid.uuid4()),
        "status": "active",
        "conversation_data": {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
    }


@pytest.fixture
def sample_prompt_data() -> dict:
    """Sample prompt data for testing."""
    return {
        "content": "Generate a creative story about AI",
        "parameters": {"max_tokens": 100, "temperature": 0.7},
        "template_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "conversation_id": str(uuid.uuid4()),
        "response": "Once upon a time, in a digital realm..."
    }


@pytest.fixture
def sample_prompt_request() -> dict:
    """Sample prompt request data for testing."""
    return {
        "role": "helpful assistant",
        "context": "You are helping a user with programming questions",
        "task": "answer programming questions clearly and accurately",
        "constraints": ["Keep responses concise", "Provide code examples when helpful"],
        "examples": ["Q: How do I reverse a string? A: Use string[::-1] in Python"],
        "tone": "friendly and professional",
        "format": "structured response with explanations"
    }


@pytest.fixture
def sample_user(sample_user_data: dict) -> User:
    """Create a sample User instance."""
    return User(**sample_user_data)


@pytest.fixture
def sample_template(sample_template_data: dict) -> Template:
    """Create a sample Template instance."""
    return Template(**sample_template_data)


@pytest.fixture
def sample_conversation(sample_conversation_data: dict) -> Conversation:
    """Create a sample Conversation instance."""
    return Conversation(**sample_conversation_data)


@pytest.fixture
def sample_prompt(sample_prompt_data: dict) -> Prompt:
    """Create a sample Prompt instance."""
    return Prompt(**sample_prompt_data)


# Mock database connection fixtures
@pytest.fixture
def mock_get_async_session(mock_database_session: AsyncMock):
    """Mock the get_async_session context manager."""
    async def _mock_get_session():
        yield mock_database_session

    return _mock_get_session


@pytest.fixture
def mock_engine():
    """Mock database engine."""
    engine = MagicMock()
    engine.dispose = AsyncMock()
    engine.begin = AsyncMock()

    # Mock pool
    pool = MagicMock()
    pool.size.return_value = 10
    pool.checkedin.return_value = 8
    pool.checkedout.return_value = 2
    pool.overflow.return_value = 0
    pool.invalidated.return_value = 0
    engine.pool = pool

    return engine


# Pytest markers for organizing tests
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "database: mark test as database test")
    config.addinivalue_line("markers", "api: mark test as API test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Skip database tests by default unless explicitly requested
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip database tests by default."""
    if config.getoption("--run-database-tests"):
        return

    skip_database = pytest.mark.skip(reason="database tests skipped by default")
    for item in items:
        if "database" in item.keywords:
            item.add_marker(skip_database)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-database-tests",
        action="store_true",
        default=False,
        help="run database tests"
    )
    parser.addoption(
        "--run-slow-tests",
        action="store_true",
        default=False,
        help="run slow tests"
    )


# Real database fixtures for integration tests
@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    # Use test database URL or in-memory SQLite for testing
    test_db_url = os.getenv("TEST_DATABASE_URL") or "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(
        test_db_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for testing."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        # Start a transaction
        await session.begin()

        try:
            yield session
        finally:
            # Rollback any changes made during the test
            await session.rollback()
            await session.close()


@pytest.fixture
async def sample_user_db(db_session: AsyncSession) -> User:
    """Create a sample user in the database."""
    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        password_hash="hashed_password",
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        preferences={"theme": "dark", "language": "en"}
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def sample_template_db(db_session: AsyncSession, sample_user_db: User) -> Template:
    """Create a sample template in the database."""
    template = Template(
        name=f"Test Template {uuid.uuid4().hex[:8]}",
        description="A test template",
        content="Template content with {variable}",
        category="test",
        tags=["test", "sample"],
        variables=["variable"],
        is_public=True,
        creator_id=sample_user_db.id
    )

    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    return template


@pytest.fixture
async def sample_conversation_db(db_session: AsyncSession, sample_user_db: User, sample_template_db: Template) -> Conversation:
    """Create a sample conversation in the database."""
    conversation = Conversation(
        title=f"Test Conversation {uuid.uuid4().hex[:8]}",
        context={
            "user_preferences": {"style": "formal"},
            "session_data": {"start_time": "2024-01-01T10:00:00"}
        },
        settings={
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 1000
        },
        user_id=sample_user_db.id,
        template_id=sample_template_db.id
    )

    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)

    return conversation


@pytest.fixture
async def sample_prompt_db(db_session: AsyncSession, sample_conversation_db: Conversation) -> Prompt:
    """Create a sample prompt in the database."""
    prompt = Prompt(
        content="Test prompt content",
        type="user",
        sequence_number=1,
        conversation_id=sample_conversation_db.id
    )

    db_session.add(prompt)
    await db_session.commit()
    await db_session.refresh(prompt)

    return prompt