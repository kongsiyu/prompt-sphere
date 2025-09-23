"""
Prompt model test fixtures and factories.
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
import uuid
from decimal import Decimal

from database.models.prompt import Prompt


class PromptFactory(factory.Factory):
    """Factory for creating Prompt instances for testing."""

    class Meta:
        model = Prompt

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    conversation_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    template_id = None
    version = 1
    parent_prompt_id = None
    sequence_number = 1
    content = factory.Faker('text', max_nb_chars=500)
    system_prompt = factory.Faker('text', max_nb_chars=200)
    user_input = factory.Faker('text', max_nb_chars=300)
    ai_response = factory.Faker('text', max_nb_chars=800)
    response_time_ms = fuzzy.FuzzyInteger(500, 5000)
    token_count_input = fuzzy.FuzzyInteger(50, 200)
    token_count_output = fuzzy.FuzzyInteger(100, 400)
    token_count_total = factory.LazyAttribute(lambda obj: obj.token_count_input + obj.token_count_output)
    cost = factory.LazyFunction(lambda: Decimal('0.025'))
    model_used = fuzzy.FuzzyChoice(['gpt-3.5-turbo', 'gpt-4', 'claude-3-sonnet'])
    model_version = factory.LazyFunction(lambda: '2024-01-01')
    temperature = factory.LazyFunction(lambda: Decimal('0.7'))
    max_tokens = fuzzy.FuzzyInteger(1000, 4000)
    status = 'completed'
    error_message = None
    custom_metadata = factory.LazyFunction(lambda: {
        'source': 'test',
        'environment': 'testing'
    })
    user_rating = None
    user_feedback = None
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    deleted_at = None


class PendingPromptFactory(PromptFactory):
    """Factory for creating pending prompts."""
    status = 'pending'
    ai_response = None
    response_time_ms = None
    token_count_input = None
    token_count_output = None
    token_count_total = None
    cost = None


class FailedPromptFactory(PromptFactory):
    """Factory for creating failed prompts."""
    status = 'failed'
    ai_response = None
    error_message = 'Test error: API timeout'
    response_time_ms = None
    token_count_input = None
    token_count_output = None
    token_count_total = None
    cost = None


class RatedPromptFactory(PromptFactory):
    """Factory for creating rated prompts."""
    user_rating = fuzzy.FuzzyInteger(1, 5)
    user_feedback = factory.Faker('text', max_nb_chars=200)


class HighPerformancePromptFactory(PromptFactory):
    """Factory for creating high-performance prompts."""
    response_time_ms = fuzzy.FuzzyInteger(200, 1000)
    token_count_total = fuzzy.FuzzyInteger(300, 600)
    cost = factory.LazyFunction(lambda: Decimal('0.010'))
    user_rating = 5


async def create_test_prompt(session, conversation_id, **kwargs):
    """
    Create a test prompt and save to database.

    Args:
        session: Database session
        conversation_id: ID of the conversation
        **kwargs: Additional prompt attributes

    Returns:
        Created Prompt instance
    """
    prompt_data = {
        'conversation_id': conversation_id,
        'content': 'Test prompt content',
        'user_input': 'Test user input',
        'ai_response': 'Test AI response',
        'sequence_number': 1,
        'status': 'completed',
    }
    prompt_data.update(kwargs)

    prompt = PromptFactory.build(**prompt_data)
    session.add(prompt)
    await session.flush()
    await session.refresh(prompt)
    return prompt


async def create_pending_prompt(session, conversation_id, **kwargs):
    """
    Create a pending prompt.

    Args:
        session: Database session
        conversation_id: ID of the conversation
        **kwargs: Additional prompt attributes

    Returns:
        Created pending Prompt instance
    """
    prompt_data = {
        'status': 'pending',
        'ai_response': None,
        'response_time_ms': None,
        'token_count_input': None,
        'token_count_output': None,
        'token_count_total': None,
        'cost': None
    }
    prompt_data.update(kwargs)

    return await create_test_prompt(session, conversation_id, **prompt_data)


async def create_failed_prompt(session, conversation_id, error_message="Test error", **kwargs):
    """
    Create a failed prompt.

    Args:
        session: Database session
        conversation_id: ID of the conversation
        error_message: Error message
        **kwargs: Additional prompt attributes

    Returns:
        Created failed Prompt instance
    """
    prompt_data = {
        'status': 'failed',
        'error_message': error_message,
        'ai_response': None,
        'response_time_ms': None,
        'token_count_input': None,
        'token_count_output': None,
        'token_count_total': None,
        'cost': None
    }
    prompt_data.update(kwargs)

    return await create_test_prompt(session, conversation_id, **prompt_data)


async def create_prompt_with_rating(session, conversation_id, rating=5, feedback="Great response!", **kwargs):
    """
    Create a prompt with user rating.

    Args:
        session: Database session
        conversation_id: ID of the conversation
        rating: User rating (1-5)
        feedback: User feedback
        **kwargs: Additional prompt attributes

    Returns:
        Created rated Prompt instance
    """
    prompt_data = {
        'user_rating': rating,
        'user_feedback': feedback
    }
    prompt_data.update(kwargs)

    return await create_test_prompt(session, conversation_id, **prompt_data)


async def create_prompt_chain(session, conversation_id, chain_length=3, **kwargs):
    """
    Create a chain of related prompts (follow-ups).

    Args:
        session: Database session
        conversation_id: ID of the conversation
        chain_length: Number of prompts in the chain
        **kwargs: Additional prompt attributes

    Returns:
        List of Prompt instances in the chain
    """
    prompts = []

    # Create the root prompt
    root_prompt = await create_test_prompt(
        session,
        conversation_id,
        content="Root prompt: What is AI?",
        user_input="What is AI?",
        ai_response="AI stands for Artificial Intelligence...",
        sequence_number=1,
        **kwargs
    )
    prompts.append(root_prompt)

    # Create follow-up prompts
    for i in range(1, chain_length):
        parent_prompt = prompts[i - 1]

        followup_data = {
            'content': f"Follow-up {i}: Can you elaborate on that?",
            'user_input': f"Can you elaborate on that? (follow-up {i})",
            'ai_response': f"Certainly! Here's more detail... (response {i})",
            'sequence_number': i + 1,
            'parent_prompt_id': parent_prompt.id,
            'version': 1
        }
        followup_data.update(kwargs)

        followup_prompt = await create_test_prompt(session, conversation_id, **followup_data)
        prompts.append(followup_prompt)

    return prompts


async def create_prompt_variations(session, conversation_id, base_prompt_id=None, count=3):
    """
    Create variations of a prompt (different versions).

    Args:
        session: Database session
        conversation_id: ID of the conversation
        base_prompt_id: ID of the base prompt (if None, creates one)
        count: Number of variations to create

    Returns:
        List of Prompt instances (variations)
    """
    prompts = []

    # Create base prompt if not provided
    if base_prompt_id is None:
        base_prompt = await create_test_prompt(
            session,
            conversation_id,
            content="Base prompt content",
            user_input="Base user input",
            version=1
        )
        base_prompt_id = base_prompt.id
        prompts.append(base_prompt)

    # Create variations
    for i in range(2, count + 2):  # Start from version 2
        variation_data = {
            'content': f"Variation {i} of the prompt content",
            'user_input': f"Variation {i} of user input",
            'ai_response': f"Variation {i} AI response",
            'parent_prompt_id': base_prompt_id,  # Same parent for all variations
            'version': i,
            'sequence_number': 1  # Same sequence, different version
        }

        variation = await create_test_prompt(session, conversation_id, **variation_data)
        prompts.append(variation)

    return prompts


async def create_prompts_by_status(session, conversation_id):
    """
    Create prompts with different statuses.

    Args:
        session: Database session
        conversation_id: ID of the conversation

    Returns:
        Dict of prompts by status
    """
    statuses = {
        'pending': {
            'status': 'pending',
            'ai_response': None,
            'user_input': 'Pending prompt input'
        },
        'processing': {
            'status': 'processing',
            'ai_response': None,
            'user_input': 'Processing prompt input'
        },
        'completed': {
            'status': 'completed',
            'ai_response': 'Completed AI response',
            'user_input': 'Completed prompt input'
        },
        'failed': {
            'status': 'failed',
            'error_message': 'Test failure',
            'ai_response': None,
            'user_input': 'Failed prompt input'
        },
        'cancelled': {
            'status': 'cancelled',
            'ai_response': None,
            'user_input': 'Cancelled prompt input'
        }
    }

    prompts = {}
    for i, (status, prompt_data) in enumerate(statuses.items()):
        prompt_data['sequence_number'] = i + 1
        prompt = await create_test_prompt(session, conversation_id, **prompt_data)
        prompts[status] = prompt

    return prompts


async def create_performance_test_prompts(session, conversation_id, count=10):
    """
    Create prompts with varying performance characteristics.

    Args:
        session: Database session
        conversation_id: ID of the conversation
        count: Number of prompts to create

    Returns:
        List of Prompt instances with varying performance
    """
    prompts = []

    for i in range(count):
        # Vary performance characteristics
        response_time = 1000 + (i * 500)  # 1s to 5.5s
        token_count = 200 + (i * 50)     # 200 to 650 tokens
        cost = Decimal(str(0.01 + (i * 0.005)))  # $0.01 to $0.055

        prompt_data = {
            'content': f'Performance test prompt {i + 1}',
            'user_input': f'Test input {i + 1}',
            'ai_response': f'Performance test response {i + 1}' * (i + 1),  # Varying length
            'sequence_number': i + 1,
            'response_time_ms': response_time,
            'token_count_input': token_count // 3,
            'token_count_output': (token_count * 2) // 3,
            'token_count_total': token_count,
            'cost': cost,
            'model_used': 'gpt-3.5-turbo' if i % 2 == 0 else 'gpt-4'
        }

        prompt = await create_test_prompt(session, conversation_id, **prompt_data)
        prompts.append(prompt)

    return prompts


# Sample prompt data
SAMPLE_PROMPTS = [
    {
        'content': 'Explain quantum computing in simple terms',
        'user_input': 'Can you explain quantum computing?',
        'ai_response': 'Quantum computing is a revolutionary approach to computation that leverages quantum mechanical phenomena...',
        'system_prompt': 'You are a helpful science educator. Explain complex topics clearly.',
        'model_used': 'gpt-4',
        'temperature': Decimal('0.3'),
        'token_count_input': 85,
        'token_count_output': 256,
        'response_time_ms': 2400
    },
    {
        'content': 'Write a creative story about space exploration',
        'user_input': 'Write a short story about discovering a new planet',
        'ai_response': 'Captain Sarah Chen gazed through the viewport as her ship approached the mysterious blue-green world...',
        'system_prompt': 'You are a creative writing assistant. Write engaging, imaginative stories.',
        'model_used': 'gpt-3.5-turbo',
        'temperature': Decimal('0.9'),
        'token_count_input': 120,
        'token_count_output': 512,
        'response_time_ms': 3200
    },
    {
        'content': 'Analyze this data and provide insights: {data}',
        'user_input': 'Analyze this sales data and provide insights',
        'ai_response': 'Based on the sales data provided, I can identify several key trends and patterns...',
        'system_prompt': 'You are a data analyst. Provide clear, actionable insights.',
        'model_used': 'gpt-4',
        'temperature': Decimal('0.1'),
        'token_count_input': 450,
        'token_count_output': 320,
        'response_time_ms': 1800
    }
]


async def create_sample_prompts(session, conversation_id):
    """
    Create a set of sample prompts for testing.

    Args:
        session: Database session
        conversation_id: ID of the conversation

    Returns:
        List of created Prompt instances
    """
    prompts = []

    for i, prompt_data in enumerate(SAMPLE_PROMPTS):
        prompt_data['sequence_number'] = i + 1
        prompt_data['token_count_total'] = prompt_data['token_count_input'] + prompt_data['token_count_output']
        prompt_data['cost'] = Decimal(str(prompt_data['token_count_total'] * 0.00002))  # Rough cost estimate

        prompt = await create_test_prompt(session, conversation_id, **prompt_data)
        prompts.append(prompt)

    return prompts


async def create_prompt_with_template(session, conversation_id, template_id, **kwargs):
    """
    Create a prompt based on a template.

    Args:
        session: Database session
        conversation_id: ID of the conversation
        template_id: ID of the template
        **kwargs: Additional prompt attributes

    Returns:
        Created Prompt instance
    """
    prompt_data = {
        'template_id': template_id,
        'content': 'Rendered template content: Hello {name}!',
        'user_input': 'Use the greeting template',
        'ai_response': 'I\'ve used the template to create: Hello World!'
    }
    prompt_data.update(kwargs)

    return await create_test_prompt(session, conversation_id, **prompt_data)


async def create_conversation_with_prompts(session, user_id, prompt_count=5, **kwargs):
    """
    Create a conversation with a specified number of prompts.

    Args:
        session: Database session
        user_id: ID of the user
        prompt_count: Number of prompts to create
        **kwargs: Additional conversation/prompt attributes

    Returns:
        Tuple of (Conversation, List[Prompt])
    """
    from .conversation_fixtures import create_test_conversation

    conversation = await create_test_conversation(session, user_id, **kwargs)

    prompts = []
    for i in range(prompt_count):
        prompt_data = {
            'content': f'Prompt {i + 1} content',
            'user_input': f'User input {i + 1}',
            'ai_response': f'AI response {i + 1}',
            'sequence_number': i + 1
        }

        prompt = await create_test_prompt(session, conversation.id, **prompt_data)
        prompts.append(prompt)

    return conversation, prompts