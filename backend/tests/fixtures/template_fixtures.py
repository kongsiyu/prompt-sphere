"""
Template model test fixtures and factories.
"""

import factory
from factory import fuzzy
from datetime import datetime
import uuid
from decimal import Decimal

from database.models.template import Template, TemplateRating


class TemplateFactory(factory.Factory):
    """Factory for creating Template instances for testing."""

    class Meta:
        model = Template

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    name = factory.Sequence(lambda n: f"Test Template {n}")
    description = factory.Faker('text', max_nb_chars=200)
    content = factory.LazyFunction(lambda: """You are an AI assistant. Please help the user with the following request:

{user_request}

Additional context:
{context}

Please provide a helpful and accurate response.""")
    system_prompt = factory.Faker('text', max_nb_chars=100)
    category = fuzzy.FuzzyChoice(['general', 'coding', 'writing', 'analysis', 'creative'])
    tags = factory.LazyFunction(lambda: ['ai', 'assistant', 'helpful'])
    is_public = True
    usage_count = fuzzy.FuzzyInteger(0, 100)
    rating_avg = factory.LazyFunction(lambda: Decimal('4.2'))
    rating_count = fuzzy.FuzzyInteger(1, 50)
    created_by = factory.LazyFunction(lambda: str(uuid.uuid4()))
    version = 1
    parent_template_id = None
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    deleted_at = None


class PrivateTemplateFactory(TemplateFactory):
    """Factory for creating private templates."""
    is_public = False


class PopularTemplateFactory(TemplateFactory):
    """Factory for creating popular templates."""
    usage_count = fuzzy.FuzzyInteger(100, 1000)
    rating_avg = factory.LazyFunction(lambda: Decimal('4.8'))
    rating_count = fuzzy.FuzzyInteger(50, 200)


class TemplateRatingFactory(factory.Factory):
    """Factory for creating TemplateRating instances for testing."""

    class Meta:
        model = TemplateRating

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    template_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    rating = fuzzy.FuzzyInteger(1, 5)
    feedback = factory.Faker('text', max_nb_chars=500)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    deleted_at = None


async def create_test_template(session, user_id, **kwargs):
    """
    Create a test template and save to database.

    Args:
        session: Database session
        user_id: ID of the user creating the template
        **kwargs: Additional template attributes

    Returns:
        Created Template instance
    """
    template_data = {
        'name': 'Test Template',
        'description': 'A template for testing purposes',
        'content': 'Hello {name}, please help with: {task}',
        'created_by': user_id,
        'category': 'testing',
        'tags': ['test', 'example'],
        'is_public': True,
    }
    template_data.update(kwargs)

    template = TemplateFactory.build(**template_data)
    session.add(template)
    await session.flush()
    await session.refresh(template)
    return template


async def create_private_template(session, user_id, **kwargs):
    """
    Create a private template.

    Args:
        session: Database session
        user_id: ID of the user creating the template
        **kwargs: Additional template attributes

    Returns:
        Created private Template instance
    """
    template_data = {
        'is_public': False,
        'name': 'Private Template',
    }
    template_data.update(kwargs)

    return await create_test_template(session, user_id, **template_data)


async def create_template_with_rating(session, user_id, rating_user_id, rating=5, **kwargs):
    """
    Create a template with a rating.

    Args:
        session: Database session
        user_id: ID of the user creating the template
        rating_user_id: ID of the user rating the template
        rating: Rating value (1-5)
        **kwargs: Additional template attributes

    Returns:
        Tuple of (Template, TemplateRating)
    """
    template = await create_test_template(session, user_id, **kwargs)

    rating_data = {
        'template_id': template.id,
        'user_id': rating_user_id,
        'rating': rating,
        'feedback': f'This template is rated {rating} stars'
    }

    template_rating = TemplateRatingFactory.build(**rating_data)
    session.add(template_rating)
    await session.flush()
    await session.refresh(template_rating)

    # Update template rating average
    template.update_rating(rating)
    await session.flush()

    return template, template_rating


async def create_template_versions(session, user_id, base_name="Versioned Template", count=3):
    """
    Create multiple versions of a template.

    Args:
        session: Database session
        user_id: ID of the user creating the templates
        base_name: Base name for the template
        count: Number of versions to create

    Returns:
        List of Template instances (versions)
    """
    templates = []

    # Create the original template
    original = await create_test_template(
        session,
        user_id,
        name=f"{base_name} v1",
        content="Version 1: {prompt}",
        version=1
    )
    templates.append(original)

    # Create subsequent versions
    for i in range(2, count + 1):
        version_data = {
            'name': f"{base_name} v{i}",
            'content': f"Version {i}: {{prompt}} - Updated content",
            'version': i,
            'parent_template_id': original.id,
        }

        version = await create_test_template(session, user_id, **version_data)
        templates.append(version)

    return templates


async def create_templates_by_category(session, user_id):
    """
    Create templates in different categories.

    Args:
        session: Database session
        user_id: ID of the user creating the templates

    Returns:
        Dict of templates by category
    """
    categories = {
        'coding': {
            'name': 'Code Review Template',
            'content': 'Please review this code: {code}',
            'tags': ['code', 'review', 'programming'],
        },
        'writing': {
            'name': 'Essay Writing Template',
            'content': 'Write an essay about: {topic}. Length: {length}',
            'tags': ['writing', 'essay', 'academic'],
        },
        'analysis': {
            'name': 'Data Analysis Template',
            'content': 'Analyze this data: {data}. Focus on: {focus_areas}',
            'tags': ['analysis', 'data', 'insights'],
        },
        'creative': {
            'name': 'Story Writing Template',
            'content': 'Write a {genre} story about {characters} in {setting}',
            'tags': ['creative', 'story', 'fiction'],
        }
    }

    templates = {}
    for category, template_data in categories.items():
        template = await create_test_template(
            session,
            user_id,
            category=category,
            **template_data
        )
        templates[category] = template

    return templates


# Test template data
SAMPLE_TEMPLATES = [
    {
        'name': 'Customer Service Response',
        'description': 'Template for responding to customer inquiries',
        'content': '''Dear {customer_name},

Thank you for contacting us about {issue_type}.

{response_content}

Best regards,
{agent_name}''',
        'category': 'business',
        'tags': ['customer-service', 'email', 'support'],
    },
    {
        'name': 'Code Documentation',
        'description': 'Template for documenting code functions',
        'content': '''/**
 * {function_description}
 *
 * @param {param_type} {param_name} - {param_description}
 * @returns {return_type} {return_description}
 *
 * @example
 * {example_usage}
 */''',
        'category': 'coding',
        'tags': ['documentation', 'code', 'comments'],
    },
    {
        'name': 'Meeting Summary',
        'description': 'Template for summarizing meeting notes',
        'content': '''Meeting Summary: {meeting_title}
Date: {meeting_date}
Attendees: {attendees}

Key Points Discussed:
{discussion_points}

Action Items:
{action_items}

Next Steps:
{next_steps}''',
        'category': 'business',
        'tags': ['meeting', 'summary', 'notes'],
    }
]


async def create_sample_templates(session, user_id):
    """
    Create a set of sample templates for testing.

    Args:
        session: Database session
        user_id: ID of the user creating the templates

    Returns:
        List of created Template instances
    """
    templates = []

    for template_data in SAMPLE_TEMPLATES:
        template = await create_test_template(
            session,
            user_id,
            **template_data
        )
        templates.append(template)

    return templates


async def create_template_with_multiple_ratings(session, user_id, rating_user_ids, ratings):
    """
    Create a template with multiple ratings from different users.

    Args:
        session: Database session
        user_id: ID of the user creating the template
        rating_user_ids: List of user IDs who will rate the template
        ratings: List of ratings corresponding to the users

    Returns:
        Tuple of (Template, List[TemplateRating])
    """
    template = await create_test_template(session, user_id)

    template_ratings = []
    for rating_user_id, rating in zip(rating_user_ids, ratings):
        rating_data = {
            'template_id': template.id,
            'user_id': rating_user_id,
            'rating': rating,
            'feedback': f'Rating: {rating}/5'
        }

        template_rating = TemplateRatingFactory.build(**rating_data)
        session.add(template_rating)
        template_ratings.append(template_rating)

        # Update template rating
        template.update_rating(rating)

    await session.flush()
    for rating in template_ratings:
        await session.refresh(rating)

    await session.refresh(template)
    return template, template_ratings