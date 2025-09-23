"""
Prompt model for individual AI interactions.
"""

from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, ForeignKey, DECIMAL, Enum, CheckConstraint, Index
from sqlalchemy.dialects.mysql import JSON, CHAR, TINYINT
from sqlalchemy.orm import relationship

from .base import BaseModel


class Prompt(BaseModel):
    """Prompt model for individual AI prompt-response interactions."""

    __tablename__ = 'prompts'

    # Relationship identifiers
    conversation_id = Column(
        CHAR(36),
        ForeignKey('conversations.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    template_id = Column(
        CHAR(36),
        ForeignKey('templates.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True,
        index=True
    )

    # Versioning and hierarchy
    version = Column(Integer, nullable=False, default=1)
    parent_prompt_id = Column(
        CHAR(36),
        ForeignKey('prompts.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True,
        index=True
    )
    sequence_number = Column(Integer, nullable=False, index=True)

    # Prompt content
    content = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    user_input = Column(Text, nullable=False)

    # AI response data
    ai_response = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Token usage tracking
    token_count_input = Column(Integer, nullable=True)
    token_count_output = Column(Integer, nullable=True)
    token_count_total = Column(Integer, nullable=True, index=True)
    cost = Column(DECIMAL(10, 6), nullable=True, default=Decimal('0.000000'), index=True)

    # AI model configuration
    model_used = Column(String(100), nullable=True, index=True)
    model_version = Column(String(50), nullable=True)
    temperature = Column(DECIMAL(3, 2), nullable=True)
    max_tokens = Column(Integer, nullable=True)

    # Status tracking
    status = Column(
        Enum('pending', 'processing', 'completed', 'failed', 'cancelled', name='prompt_status'),
        nullable=False,
        default='pending',
        index=True
    )
    error_message = Column(Text, nullable=True)

    # Additional metadata
    custom_metadata = Column(JSON, nullable=True, default={})

    # Quality metrics
    user_rating = Column(
        TINYINT,
        nullable=True,
        index=True
    )
    user_feedback = Column(Text, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="prompts")
    template = relationship("Template", back_populates="prompts")

    # Self-referential relationship for prompt chains
    parent_prompt = relationship(
        "Prompt",
        remote_side="Prompt.id",
        backref="child_prompts"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint('user_rating BETWEEN 1 AND 5', name='chk_user_rating_range'),
        Index('idx_prompts_sequence', 'conversation_id', 'sequence_number'),
        Index('ft_prompts_search', 'content', 'user_input', 'ai_response', mysql_prefix='FULLTEXT'),
    )

    def __init__(self, **kwargs):
        """Initialize prompt with default metadata."""
        super().__init__(**kwargs)
        if self.custom_metadata is None:
            self.custom_metadata = {}

        # Auto-calculate total tokens if not provided
        if (self.token_count_total is None and
            self.token_count_input is not None and
            self.token_count_output is not None):
            self.token_count_total = self.token_count_input + self.token_count_output

    def start_processing(self) -> None:
        """Mark prompt as being processed."""
        self.status = 'processing'

    def complete_processing(self, ai_response: str, response_time_ms: int,
                          token_input: int, token_output: int,
                          model_used: str, cost: Optional[Decimal] = None) -> None:
        """
        Mark prompt as completed with response data.

        Args:
            ai_response: The AI's response text
            response_time_ms: Response time in milliseconds
            token_input: Input token count
            token_output: Output token count
            model_used: AI model that was used
            cost: Cost of the API call
        """
        self.ai_response = ai_response
        self.response_time_ms = response_time_ms
        self.token_count_input = token_input
        self.token_count_output = token_output
        self.token_count_total = token_input + token_output
        self.model_used = model_used
        self.status = 'completed'

        if cost is not None:
            self.cost = cost

    def fail_processing(self, error_message: str) -> None:
        """Mark prompt as failed with error message."""
        self.status = 'failed'
        self.error_message = error_message

    def cancel_processing(self) -> None:
        """Mark prompt as cancelled."""
        self.status = 'cancelled'

    def set_rating(self, rating: int, feedback: Optional[str] = None) -> None:
        """
        Set user rating and feedback.

        Args:
            rating: Rating from 1-5
            feedback: Optional text feedback

        Raises:
            ValueError: If rating is not between 1 and 5
        """
        if not (1 <= rating <= 5):
            raise ValueError("Rating must be between 1 and 5")

        self.user_rating = rating
        self.user_feedback = feedback

    def clear_rating(self) -> None:
        """Clear user rating and feedback."""
        self.user_rating = None
        self.user_feedback = None

    def create_followup(self, user_input: str, **kwargs) -> 'Prompt':
        """
        Create a follow-up prompt based on this one.

        Args:
            user_input: The new user input
            **kwargs: Additional fields for the new prompt

        Returns:
            New Prompt instance as a follow-up
        """
        followup_data = {
            'conversation_id': self.conversation_id,
            'template_id': self.template_id,
            'parent_prompt_id': self.id,
            'user_input': user_input,
            'content': kwargs.get('content', user_input),
            'system_prompt': kwargs.get('system_prompt', self.system_prompt),
            'sequence_number': kwargs.get('sequence_number', self.sequence_number + 1),
            'version': 1,
            'custom_metadata': kwargs.get('custom_metadata', {})
        }

        # Copy AI model settings if not provided
        if 'model_used' not in kwargs and self.model_used:
            followup_data.update({
                'model_used': self.model_used,
                'model_version': self.model_version,
                'temperature': self.temperature,
                'max_tokens': self.max_tokens
            })

        followup_data.update(kwargs)
        return Prompt(**followup_data)

    def create_variation(self, **changes) -> 'Prompt':
        """
        Create a variation of this prompt with changes.

        Args:
            **changes: Fields to change in the variation

        Returns:
            New Prompt instance as a variation
        """
        variation_data = {
            'conversation_id': self.conversation_id,
            'template_id': self.template_id,
            'parent_prompt_id': self.parent_prompt_id,  # Same parent
            'content': self.content,
            'system_prompt': self.system_prompt,
            'user_input': self.user_input,
            'sequence_number': self.sequence_number,
            'version': self.version + 1,
            'model_used': self.model_used,
            'model_version': self.model_version,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'custom_metadata': self.custom_metadata.copy() if self.custom_metadata else {}
        }

        variation_data.update(changes)
        return Prompt(**variation_data)

    def update_metadata(self, key: str, value: Any) -> None:
        """Update a specific metadata value."""
        if self.custom_metadata is None:
            self.custom_metadata = {}
        self.custom_metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a specific metadata value."""
        if self.custom_metadata is None:
            return default
        return self.custom_metadata.get(key, default)

    def calculate_cost_per_token(self) -> Optional[Decimal]:
        """Calculate cost per token if data is available."""
        if self.cost and self.token_count_total and self.token_count_total > 0:
            return self.cost / self.token_count_total
        return None

    def get_efficiency_score(self) -> Optional[float]:
        """
        Calculate efficiency score based on response time and tokens.
        Higher score means better efficiency.
        """
        if not (self.response_time_ms and self.token_count_total):
            return None

        # Tokens per second
        tokens_per_second = (self.token_count_total / self.response_time_ms) * 1000

        # Normalize to a 0-100 scale (assuming 50 tokens/second is average)
        efficiency_score = min(100, (tokens_per_second / 50) * 100)
        return round(efficiency_score, 2)

    def is_successful(self) -> bool:
        """Check if prompt was successfully processed."""
        return self.status == 'completed' and self.ai_response is not None

    def has_parent(self) -> bool:
        """Check if this prompt has a parent prompt."""
        return self.parent_prompt_id is not None

    def has_children(self) -> bool:
        """Check if this prompt has child prompts."""
        return len(getattr(self, 'child_prompts', [])) > 0

    def to_dict(self, include_response: bool = True, include_metadata: bool = True) -> dict:
        """
        Convert to dictionary with optional data inclusion.

        Args:
            include_response: Whether to include AI response
            include_metadata: Whether to include metadata

        Returns:
            Dictionary representation
        """
        data = super().to_dict()

        if not include_response:
            data.pop('ai_response', None)

        if not include_metadata:
            data.pop('custom_metadata', None)

        # Convert Decimal to float for JSON serialization
        if 'cost' in data and data['cost'] is not None:
            data['cost'] = float(data['cost'])
        if 'temperature' in data and data['temperature'] is not None:
            data['temperature'] = float(data['temperature'])

        # Add computed fields
        data.update({
            'is_successful': self.is_successful(),
            'efficiency_score': self.get_efficiency_score(),
            'cost_per_token': float(self.calculate_cost_per_token()) if self.calculate_cost_per_token() else None
        })

        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"<Prompt(id={self.id}, conversation_id={self.conversation_id}, status={self.status})>"