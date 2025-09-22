"""
Template model for reusable prompt templates.
"""

from typing import Optional, List, Dict, Any
from decimal import Decimal

from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DECIMAL, Index
from sqlalchemy.dialects.mysql import JSON, CHAR
from sqlalchemy.orm import relationship

from .base import BaseModel


class Template(BaseModel):
    """Template model for reusable prompt structures."""

    __tablename__ = 'templates'

    # Basic template information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)

    # Categorization and tagging
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True, default=[])

    # Sharing and visibility
    is_public = Column(Boolean, nullable=False, default=False, index=True)

    # Usage statistics
    usage_count = Column(Integer, nullable=False, default=0, index=True)
    rating_avg = Column(DECIMAL(3, 2), nullable=True, index=True)
    rating_count = Column(Integer, nullable=False, default=0)

    # Ownership and versioning
    created_by = Column(
        CHAR(36),
        ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    version = Column(Integer, nullable=False, default=1)
    parent_template_id = Column(
        CHAR(36),
        ForeignKey('templates.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True,
        index=True
    )

    # Relationships
    creator = relationship(
        "User",
        back_populates="templates",
        foreign_keys=[created_by]
    )

    # Self-referential relationship for template versioning
    parent_template = relationship(
        "Template",
        remote_side="Template.id",
        backref="child_templates"
    )

    prompts = relationship(
        "Prompt",
        back_populates="template"
    )

    ratings = relationship(
        "TemplateRating",
        back_populates="template",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Indexes for full-text search
    __table_args__ = (
        Index('ft_templates_search', 'name', 'description', 'content', mysql_prefix='FULLTEXT'),
    )

    def __init__(self, **kwargs):
        """Initialize template with default values."""
        super().__init__(**kwargs)
        if self.tags is None:
            self.tags = []

    def add_tag(self, tag: str) -> None:
        """Add a tag to the template."""
        if self.tags is None:
            self.tags = []

        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the template."""
        if self.tags is None:
            return

        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if template has a specific tag."""
        if self.tags is None:
            return False
        return tag.strip().lower() in self.tags

    def increment_usage(self) -> None:
        """Increment usage count when template is used."""
        self.usage_count += 1

    def update_rating(self, new_rating: int, old_rating: Optional[int] = None) -> None:
        """
        Update average rating when a new rating is added or updated.

        Args:
            new_rating: The new rating value (1-5)
            old_rating: The previous rating if this is an update
        """
        if old_rating is None:
            # New rating
            total_points = (self.rating_avg or 0) * self.rating_count + new_rating
            self.rating_count += 1
            self.rating_avg = Decimal(str(total_points / self.rating_count))
        else:
            # Update existing rating
            if self.rating_count > 0:
                total_points = (self.rating_avg or 0) * self.rating_count - old_rating + new_rating
                self.rating_avg = Decimal(str(total_points / self.rating_count))

    def remove_rating(self, rating_value: int) -> None:
        """Remove a rating and update average."""
        if self.rating_count > 1:
            total_points = (self.rating_avg or 0) * self.rating_count - rating_value
            self.rating_count -= 1
            self.rating_avg = Decimal(str(total_points / self.rating_count))
        else:
            self.rating_count = 0
            self.rating_avg = None

    def create_version(self, **updates) -> 'Template':
        """
        Create a new version of this template.

        Args:
            **updates: Fields to update in the new version

        Returns:
            New template instance as a version
        """
        version_data = {
            'name': self.name,
            'description': self.description,
            'content': self.content,
            'system_prompt': self.system_prompt,
            'category': self.category,
            'tags': self.tags.copy() if self.tags else [],
            'is_public': self.is_public,
            'created_by': self.created_by,
            'parent_template_id': self.id,
            'version': self.version + 1
        }

        # Apply updates
        version_data.update(updates)

        return Template(**version_data)

    def get_variables(self) -> List[str]:
        """
        Extract variables from template content.
        Variables are marked with {variable_name} syntax.

        Returns:
            List of variable names found in the template
        """
        import re
        pattern = r'\{([^}]+)\}'
        variables = re.findall(pattern, self.content)
        return list(set(variables))  # Remove duplicates

    def validate_variables(self, variables: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate that all required variables are provided.

        Args:
            variables: Dictionary of variable names and values

        Returns:
            Dictionary with 'missing' and 'extra' variable lists
        """
        template_vars = set(self.get_variables())
        provided_vars = set(variables.keys())

        return {
            'missing': list(template_vars - provided_vars),
            'extra': list(provided_vars - template_vars)
        }

    def render(self, variables: Dict[str, Any]) -> str:
        """
        Render template content with provided variables.

        Args:
            variables: Dictionary of variable names and values

        Returns:
            Rendered template content

        Raises:
            ValueError: If required variables are missing
        """
        validation = self.validate_variables(variables)
        if validation['missing']:
            raise ValueError(f"Missing required variables: {validation['missing']}")

        content = self.content
        for var_name, var_value in variables.items():
            placeholder = f"{{{var_name}}}"
            content = content.replace(placeholder, str(var_value))

        return content

    def is_owned_by(self, user_id: str) -> bool:
        """Check if template is owned by specific user."""
        return self.created_by == user_id

    def can_be_used_by(self, user_id: Optional[str] = None) -> bool:
        """Check if template can be used by a user."""
        if self.is_public:
            return True
        return user_id is not None and self.is_owned_by(user_id)

    def to_dict(self, include_stats: bool = True) -> dict:
        """Convert to dictionary with optional statistics."""
        data = super().to_dict()

        if include_stats:
            data.update({
                'variables': self.get_variables(),
                'rating_avg': float(self.rating_avg) if self.rating_avg else None
            })

        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"<Template(id={self.id}, name={self.name}, version={self.version})>"


class TemplateRating(BaseModel):
    """Rating and feedback for templates."""

    __tablename__ = 'template_ratings'

    template_id = Column(
        CHAR(36),
        ForeignKey('templates.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    user_id = Column(
        CHAR(36),
        ForeignKey('users.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    rating = Column(Integer, nullable=False)  # 1-5 scale
    feedback = Column(Text, nullable=True)

    # Relationships
    template = relationship("Template", back_populates="ratings")
    user = relationship("User", back_populates="template_ratings")

    # Unique constraint for one rating per user per template
    __table_args__ = (
        Index('uk_template_ratings', 'template_id', 'user_id', unique=True),
    )

    def __init__(self, **kwargs):
        """Initialize rating with validation."""
        super().__init__(**kwargs)
        self.validate_rating()

    def validate_rating(self) -> None:
        """Validate rating is within acceptable range."""
        if not (1 <= self.rating <= 5):
            raise ValueError("Rating must be between 1 and 5")

    def __repr__(self) -> str:
        """String representation."""
        return f"<TemplateRating(template_id={self.template_id}, user_id={self.user_id}, rating={self.rating})>"