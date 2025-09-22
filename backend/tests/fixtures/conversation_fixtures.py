"""
Conversation model test fixtures and factories.
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
import uuid
import secrets
from decimal import Decimal

from database.models.conversation import Conversation, ConversationParticipant


class ConversationFactory(factory.Factory):
    """Factory for creating Conversation instances for testing."""

    class Meta:
        model = Conversation

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    title = factory.Sequence(lambda n: f"Test Conversation {n}")
    description = factory.Faker('text', max_nb_chars=200)
    context = factory.LazyFunction(lambda: {
        'topic': 'testing',
        'domain': 'software',
        'complexity': 'medium'
    })
    settings = factory.LazyFunction(lambda: {
        'ai_model': 'gpt-3.5-turbo',
        'temperature': 0.7,
        'max_tokens': 2000,
        'auto_title': True
    })
    status = fuzzy.FuzzyChoice(['active', 'archived', 'paused', 'completed'])
    last_activity_at = factory.LazyFunction(datetime.utcnow)
    total_messages = fuzzy.FuzzyInteger(0, 20)
    total_tokens = fuzzy.FuzzyInteger(0, 10000)
    total_cost = factory.LazyFunction(lambda: Decimal('0.50'))
    shared = False
    share_token = None
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    deleted_at = None


class ActiveConversationFactory(ConversationFactory):
    """Factory for creating active conversations."""
    status = 'active'
    last_activity_at = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=5))


class SharedConversationFactory(ConversationFactory):
    """Factory for creating shared conversations."""
    shared = True
    share_token = factory.LazyFunction(lambda: secrets.token_urlsafe(32))


class ArchivedConversationFactory(ConversationFactory):
    """Factory for creating archived conversations."""
    status = 'archived'
    last_activity_at = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(days=7))


class ConversationParticipantFactory(factory.Factory):
    """Factory for creating ConversationParticipant instances for testing."""

    class Meta:
        model = ConversationParticipant

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    conversation_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    role = fuzzy.FuzzyChoice(['owner', 'collaborator', 'viewer'])
    permissions = factory.LazyFunction(lambda: {
        'read': True,
        'write': True,
        'admin': False
    })
    joined_at = factory.LazyFunction(datetime.utcnow)
    last_accessed_at = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(hours=1))
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    deleted_at = None


class OwnerParticipantFactory(ConversationParticipantFactory):
    """Factory for creating owner participants."""
    role = 'owner'
    permissions = factory.LazyFunction(lambda: {
        'read': True,
        'write': True,
        'admin': True
    })


class ViewerParticipantFactory(ConversationParticipantFactory):
    """Factory for creating viewer participants."""
    role = 'viewer'
    permissions = factory.LazyFunction(lambda: {
        'read': True,
        'write': False,
        'admin': False
    })


async def create_test_conversation(session, user_id, **kwargs):
    """
    Create a test conversation and save to database.

    Args:
        session: Database session
        user_id: ID of the user creating the conversation
        **kwargs: Additional conversation attributes

    Returns:
        Created Conversation instance
    """
    conversation_data = {
        'user_id': user_id,
        'title': 'Test Conversation',
        'description': 'A conversation for testing purposes',
        'status': 'active',
        'context': {'test': True},
        'settings': {
            'ai_model': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 2000
        }
    }
    conversation_data.update(kwargs)

    conversation = ConversationFactory.build(**conversation_data)
    session.add(conversation)
    await session.flush()
    await session.refresh(conversation)
    return conversation


async def create_shared_conversation(session, user_id, **kwargs):
    """
    Create a shared conversation with a share token.

    Args:
        session: Database session
        user_id: ID of the user creating the conversation
        **kwargs: Additional conversation attributes

    Returns:
        Created shared Conversation instance
    """
    conversation_data = {
        'shared': True,
        'share_token': secrets.token_urlsafe(32),
        'title': 'Shared Test Conversation',
    }
    conversation_data.update(kwargs)

    return await create_test_conversation(session, user_id, **conversation_data)


async def create_conversation_with_participants(session, owner_id, participant_ids, **kwargs):
    """
    Create a conversation with multiple participants.

    Args:
        session: Database session
        owner_id: ID of the conversation owner
        participant_ids: List of participant user IDs
        **kwargs: Additional conversation attributes

    Returns:
        Tuple of (Conversation, List[ConversationParticipant])
    """
    conversation = await create_test_conversation(session, owner_id, **kwargs)

    participants = []
    for i, participant_id in enumerate(participant_ids):
        role = 'collaborator' if i == 0 else 'viewer'
        permissions = {
            'collaborator': {'read': True, 'write': True, 'admin': False},
            'viewer': {'read': True, 'write': False, 'admin': False}
        }[role]

        participant_data = {
            'conversation_id': conversation.id,
            'user_id': participant_id,
            'role': role,
            'permissions': permissions
        }

        participant = ConversationParticipantFactory.build(**participant_data)
        session.add(participant)
        participants.append(participant)

    await session.flush()
    for participant in participants:
        await session.refresh(participant)

    return conversation, participants


async def create_conversation_with_history(session, user_id, days_old=7, **kwargs):
    """
    Create a conversation with historical activity.

    Args:
        session: Database session
        user_id: ID of the user creating the conversation
        days_old: How many days old the conversation should be
        **kwargs: Additional conversation attributes

    Returns:
        Created Conversation instance
    """
    created_date = datetime.utcnow() - timedelta(days=days_old)
    last_activity = datetime.utcnow() - timedelta(days=max(0, days_old - 1))

    conversation_data = {
        'title': f'Historical Conversation ({days_old} days old)',
        'created_at': created_date,
        'last_activity_at': last_activity,
        'total_messages': days_old * 2,  # Simulate activity
        'total_tokens': days_old * 500,
        'total_cost': Decimal(str(days_old * 0.1))
    }
    conversation_data.update(kwargs)

    return await create_test_conversation(session, user_id, **conversation_data)


async def create_conversations_by_status(session, user_id):
    """
    Create conversations with different statuses.

    Args:
        session: Database session
        user_id: ID of the user creating the conversations

    Returns:
        Dict of conversations by status
    """
    statuses = ['active', 'archived', 'paused', 'completed']
    conversations = {}

    for status in statuses:
        conversation_data = {
            'title': f'{status.title()} Conversation',
            'status': status,
        }

        if status == 'archived':
            conversation_data['last_activity_at'] = datetime.utcnow() - timedelta(days=30)
        elif status == 'completed':
            conversation_data['last_activity_at'] = datetime.utcnow() - timedelta(days=1)

        conversation = await create_test_conversation(session, user_id, **conversation_data)
        conversations[status] = conversation

    return conversations


async def create_conversation_with_stats(session, user_id, message_count=10, token_count=5000, cost=1.25):
    """
    Create a conversation with specific statistics.

    Args:
        session: Database session
        user_id: ID of the user creating the conversation
        message_count: Number of messages
        token_count: Total token count
        cost: Total cost

    Returns:
        Created Conversation instance
    """
    conversation_data = {
        'title': f'Conversation with {message_count} messages',
        'total_messages': message_count,
        'total_tokens': token_count,
        'total_cost': Decimal(str(cost)),
        'last_activity_at': datetime.utcnow() - timedelta(minutes=30)
    }

    return await create_test_conversation(session, user_id, **conversation_data)


# Sample conversation data
SAMPLE_CONVERSATIONS = [
    {
        'title': 'AI Development Discussion',
        'description': 'Discussing best practices for AI development',
        'context': {
            'topic': 'ai_development',
            'expertise_level': 'intermediate',
            'focus_areas': ['ethics', 'performance', 'deployment']
        },
        'settings': {
            'ai_model': 'gpt-4',
            'temperature': 0.3,
            'max_tokens': 4000
        }
    },
    {
        'title': 'Creative Writing Session',
        'description': 'Collaborative creative writing project',
        'context': {
            'genre': 'science_fiction',
            'target_audience': 'young_adult',
            'themes': ['exploration', 'friendship', 'technology']
        },
        'settings': {
            'ai_model': 'gpt-3.5-turbo',
            'temperature': 0.9,
            'max_tokens': 2500
        }
    },
    {
        'title': 'Data Analysis Consultation',
        'description': 'Analyzing customer feedback data',
        'context': {
            'data_type': 'customer_feedback',
            'analysis_type': 'sentiment',
            'time_period': 'Q1_2024'
        },
        'settings': {
            'ai_model': 'gpt-4',
            'temperature': 0.1,
            'max_tokens': 3000
        }
    }
]


async def create_sample_conversations(session, user_id):
    """
    Create a set of sample conversations for testing.

    Args:
        session: Database session
        user_id: ID of the user creating the conversations

    Returns:
        List of created Conversation instances
    """
    conversations = []

    for i, conversation_data in enumerate(SAMPLE_CONVERSATIONS):
        # Add some variation in activity
        conversation_data['last_activity_at'] = datetime.utcnow() - timedelta(hours=i * 2)
        conversation_data['total_messages'] = (i + 1) * 5
        conversation_data['total_tokens'] = (i + 1) * 1000
        conversation_data['total_cost'] = Decimal(str((i + 1) * 0.25))

        conversation = await create_test_conversation(
            session,
            user_id,
            **conversation_data
        )
        conversations.append(conversation)

    return conversations


async def create_participant_with_permissions(session, conversation_id, user_id, role='viewer', custom_permissions=None):
    """
    Create a conversation participant with specific permissions.

    Args:
        session: Database session
        conversation_id: ID of the conversation
        user_id: ID of the user
        role: Participant role
        custom_permissions: Custom permissions dict

    Returns:
        Created ConversationParticipant instance
    """
    default_permissions = {
        'owner': {'read': True, 'write': True, 'admin': True},
        'collaborator': {'read': True, 'write': True, 'admin': False},
        'viewer': {'read': True, 'write': False, 'admin': False}
    }

    permissions = custom_permissions or default_permissions.get(role, default_permissions['viewer'])

    participant_data = {
        'conversation_id': conversation_id,
        'user_id': user_id,
        'role': role,
        'permissions': permissions
    }

    participant = ConversationParticipantFactory.build(**participant_data)
    session.add(participant)
    await session.flush()
    await session.refresh(participant)
    return participant


async def create_conversation_test_set(session, user_id):
    """
    Create a comprehensive set of conversations for testing.

    Args:
        session: Database session
        user_id: ID of the user creating the conversations

    Returns:
        Dict of created conversations by type
    """
    conversations = {}

    # Active conversation
    conversations['active'] = await create_test_conversation(
        session,
        user_id,
        title='Active Test Conversation',
        status='active'
    )

    # Shared conversation
    conversations['shared'] = await create_shared_conversation(
        session,
        user_id,
        title='Shared Test Conversation'
    )

    # Archived conversation
    conversations['archived'] = await create_test_conversation(
        session,
        user_id,
        title='Archived Test Conversation',
        status='archived',
        last_activity_at=datetime.utcnow() - timedelta(days=30)
    )

    # High-activity conversation
    conversations['high_activity'] = await create_conversation_with_stats(
        session,
        user_id,
        message_count=50,
        token_count=25000,
        cost=5.0
    )

    # Historical conversation
    conversations['historical'] = await create_conversation_with_history(
        session,
        user_id,
        days_old=14
    )

    return conversations