"""
User model test fixtures and factories.
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
import uuid

from database.models.user import User


class UserFactory(factory.Factory):
    """Factory for creating User instances for testing."""

    class Meta:
        model = User

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    email = factory.Sequence(lambda n: f"test_user_{n}@example.com")
    password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKw.6qN/MZ.V0OW"  # "testpassword"
    full_name = factory.Faker('name')
    role = fuzzy.FuzzyChoice(['admin', 'user', 'viewer'])
    is_active = True
    email_verified = True
    email_verification_token = None
    password_reset_token = None
    password_reset_expires = None
    last_login_at = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(hours=1))
    login_attempts = 0
    locked_until = None
    preferences = factory.LazyFunction(lambda: {
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
    })
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    deleted_at = None


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    role = 'admin'
    email = factory.Sequence(lambda n: f"admin_{n}@example.com")
    full_name = factory.Faker('name')


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive users."""
    is_active = False
    email_verified = False


class LockedUserFactory(UserFactory):
    """Factory for creating locked users."""
    login_attempts = 5
    locked_until = factory.LazyFunction(lambda: datetime.utcnow() + timedelta(minutes=30))


async def create_test_user(session, **kwargs):
    """
    Create a test user and save to database.

    Args:
        session: Database session
        **kwargs: Additional user attributes

    Returns:
        Created User instance
    """
    user_data = {
        'email': 'test@example.com',
        'full_name': 'Test User',
        'role': 'user',
        'is_active': True,
        'email_verified': True,
    }
    user_data.update(kwargs)

    user = UserFactory.build(**user_data)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def create_admin_user(session, **kwargs):
    """
    Create an admin user and save to database.

    Args:
        session: Database session
        **kwargs: Additional user attributes

    Returns:
        Created admin User instance
    """
    admin_data = {
        'email': 'admin@example.com',
        'full_name': 'Admin User',
        'role': 'admin',
        'is_active': True,
        'email_verified': True,
    }
    admin_data.update(kwargs)

    user = AdminUserFactory.build(**admin_data)
    session.add(user)
    await session.flush()
    await session.refresh(user)
    return user


async def create_multiple_users(session, count=5, **kwargs):
    """
    Create multiple test users.

    Args:
        session: Database session
        count: Number of users to create
        **kwargs: Common attributes for all users

    Returns:
        List of created User instances
    """
    users = []
    for i in range(count):
        user_data = {
            'email': f'user_{i}@example.com',
            'full_name': f'Test User {i}',
        }
        user_data.update(kwargs)

        user = UserFactory.build(**user_data)
        session.add(user)
        users.append(user)

    await session.flush()
    for user in users:
        await session.refresh(user)

    return users


def create_user_with_preferences(preferences_override=None):
    """
    Create a user with custom preferences.

    Args:
        preferences_override: Dict to override default preferences

    Returns:
        User factory with custom preferences
    """
    default_preferences = {
        'theme': 'dark',
        'language': 'es',
        'notifications': {
            'email': False,
            'push': True
        },
        'ai_settings': {
            'default_model': 'gpt-4',
            'temperature': 0.5,
            'max_tokens': 4000
        }
    }

    if preferences_override:
        default_preferences.update(preferences_override)

    return UserFactory.build(preferences=default_preferences)


async def create_user_with_reset_token(session, **kwargs):
    """
    Create a user with password reset token.

    Args:
        session: Database session
        **kwargs: Additional user attributes

    Returns:
        Created User instance with reset token
    """
    user_data = {
        'password_reset_token': 'test_reset_token_123',
        'password_reset_expires': datetime.utcnow() + timedelta(hours=1),
    }
    user_data.update(kwargs)

    user = await create_test_user(session, **user_data)
    return user


# Test data constants
TEST_USERS = [
    {
        'email': 'john.doe@example.com',
        'full_name': 'John Doe',
        'role': 'admin',
        'preferences': {
            'theme': 'dark',
            'language': 'en',
            'ai_settings': {'default_model': 'gpt-4'}
        }
    },
    {
        'email': 'jane.smith@example.com',
        'full_name': 'Jane Smith',
        'role': 'user',
        'preferences': {
            'theme': 'light',
            'language': 'fr',
            'ai_settings': {'default_model': 'gpt-3.5-turbo'}
        }
    },
    {
        'email': 'bob.wilson@example.com',
        'full_name': 'Bob Wilson',
        'role': 'viewer',
        'is_active': False,
        'preferences': {}
    }
]


async def create_test_user_set(session):
    """
    Create a standard set of test users for comprehensive testing.

    Args:
        session: Database session

    Returns:
        Dict of created users by role
    """
    users = {}

    # Create admin user
    users['admin'] = await create_admin_user(
        session,
        email='test.admin@example.com',
        full_name='Test Admin'
    )

    # Create regular user
    users['user'] = await create_test_user(
        session,
        email='test.user@example.com',
        full_name='Test User',
        role='user'
    )

    # Create viewer
    users['viewer'] = await create_test_user(
        session,
        email='test.viewer@example.com',
        full_name='Test Viewer',
        role='viewer'
    )

    # Create inactive user
    users['inactive'] = await create_test_user(
        session,
        email='test.inactive@example.com',
        full_name='Inactive User',
        is_active=False
    )

    # Create locked user
    users['locked'] = await create_test_user(
        session,
        email='test.locked@example.com',
        full_name='Locked User',
        login_attempts=5,
        locked_until=datetime.utcnow() + timedelta(minutes=30)
    )

    return users