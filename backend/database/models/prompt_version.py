"""
Prompt version tracking models for comprehensive version control system.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.dialects.mysql import JSON, CHAR, LONGTEXT
from sqlalchemy.orm import relationship

from .base import BaseModel


class PromptVersion(BaseModel):
    """Track all versions of a prompt for complete revision history."""

    __tablename__ = 'prompt_versions'

    # Reference to the current prompt
    prompt_id = Column(
        CHAR(36),
        ForeignKey('prompts.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )

    # Version information
    version_number = Column(Integer, nullable=False, index=True)
    version_label = Column(String(100), nullable=True)  # e.g., "v1.0", "draft", "stable"
    version_description = Column(Text, nullable=True)

    # Content at this version
    content = Column(LONGTEXT, nullable=False)
    system_prompt = Column(Text, nullable=True)
    user_input = Column(Text, nullable=False)

    # Metadata snapshot
    metadata_snapshot = Column(JSON, nullable=True, default={})

    # Change tracking
    changed_by = Column(
        CHAR(36),
        ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True,
        index=True
    )
    change_summary = Column(Text, nullable=True)
    is_major_version = Column(Boolean, nullable=False, default=False)

    # Status and lifecycle
    is_current = Column(Boolean, nullable=False, default=False, index=True)
    is_published = Column(Boolean, nullable=False, default=False)
    published_at = Column(DateTime, nullable=True)

    # Relationships
    prompt = relationship("Prompt", back_populates="versions")
    changed_by_user = relationship("User", foreign_keys=[changed_by])

    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_prompt_versions_lookup', 'prompt_id', 'version_number'),
        Index('idx_prompt_versions_current', 'prompt_id', 'is_current'),
        Index('idx_prompt_versions_published', 'is_published', 'published_at'),
    )

    def __init__(self, **kwargs):
        """Initialize version with metadata defaults."""
        super().__init__(**kwargs)
        if self.metadata_snapshot is None:
            self.metadata_snapshot = {}

    def make_current(self) -> None:
        """Mark this version as the current version."""
        self.is_current = True

    def publish(self, published_by: Optional[str] = None) -> None:
        """Publish this version."""
        self.is_published = True
        self.published_at = datetime.utcnow()
        if published_by:
            self.changed_by = published_by

    def unpublish(self) -> None:
        """Unpublish this version."""
        self.is_published = False
        self.published_at = None

    def create_next_version(self, content: str, changed_by: str, **kwargs) -> 'PromptVersion':
        """
        Create the next version based on this one.

        Args:
            content: New content for the version
            changed_by: User who is making the change
            **kwargs: Additional fields to update

        Returns:
            New PromptVersion instance
        """
        next_version_data = {
            'prompt_id': self.prompt_id,
            'version_number': self.version_number + 1,
            'content': content,
            'system_prompt': kwargs.get('system_prompt', self.system_prompt),
            'user_input': kwargs.get('user_input', self.user_input),
            'changed_by': changed_by,
            'metadata_snapshot': kwargs.get('metadata_snapshot', self.metadata_snapshot.copy() if self.metadata_snapshot else {}),
            'change_summary': kwargs.get('change_summary'),
            'is_major_version': kwargs.get('is_major_version', False),
            'version_label': kwargs.get('version_label'),
            'version_description': kwargs.get('version_description')
        }

        return PromptVersion(**next_version_data)

    def calculate_diff(self, other_version: 'PromptVersion') -> Dict[str, Any]:
        """
        Calculate differences between this version and another.

        Args:
            other_version: Version to compare against

        Returns:
            Dictionary containing differences
        """
        import difflib

        def get_diff_lines(text1: str, text2: str) -> list:
            """Get unified diff between two texts."""
            lines1 = text1.splitlines(keepends=True)
            lines2 = text2.splitlines(keepends=True)
            return list(difflib.unified_diff(lines1, lines2, lineterm=''))

        return {
            'content_diff': get_diff_lines(other_version.content, self.content),
            'system_prompt_diff': get_diff_lines(
                other_version.system_prompt or '',
                self.system_prompt or ''
            ),
            'user_input_diff': get_diff_lines(other_version.user_input, self.user_input),
            'version_difference': self.version_number - other_version.version_number,
            'time_difference': (self.created_at - other_version.created_at).total_seconds()
        }

    def get_change_statistics(self) -> Dict[str, int]:
        """Get basic statistics about changes in this version."""
        content_lines = len(self.content.splitlines())
        content_chars = len(self.content)

        return {
            'content_lines': content_lines,
            'content_characters': content_chars,
            'version_number': self.version_number,
            'is_major': int(self.is_major_version),
            'is_published': int(self.is_published)
        }

    def to_dict(self, include_content: bool = True, include_diff: bool = False) -> dict:
        """Convert to dictionary with optional content inclusion."""
        data = super().to_dict()

        if not include_content:
            data.pop('content', None)
            data.pop('system_prompt', None)
            data.pop('user_input', None)

        # Add computed fields
        data.update(self.get_change_statistics())

        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptVersion(prompt_id={self.prompt_id}, version={self.version_number}, current={self.is_current})>"


class PromptTag(BaseModel):
    """Tags for categorizing and organizing prompts."""

    __tablename__ = 'prompt_tags'

    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    category = Column(String(50), nullable=True, index=True)
    usage_count = Column(Integer, nullable=False, default=0, index=True)

    # Created by system or user
    is_system_tag = Column(Boolean, nullable=False, default=False, index=True)
    created_by = Column(
        CHAR(36),
        ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True,
        index=True
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    def increment_usage(self) -> None:
        """Increment usage count when tag is used."""
        self.usage_count += 1

    def decrement_usage(self) -> None:
        """Decrement usage count when tag is removed."""
        if self.usage_count > 0:
            self.usage_count -= 1

    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptTag(name={self.name}, usage={self.usage_count})>"


class PromptTagAssociation(BaseModel):
    """Many-to-many association between prompts and tags."""

    __tablename__ = 'prompt_tag_associations'

    prompt_id = Column(
        CHAR(36),
        ForeignKey('prompts.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )
    tag_id = Column(
        CHAR(36),
        ForeignKey('prompt_tags.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        index=True
    )

    # Who added this tag to the prompt
    added_by = Column(
        CHAR(36),
        ForeignKey('users.id', ondelete='SET NULL', onupdate='CASCADE'),
        nullable=True,
        index=True
    )

    # Relationships
    prompt = relationship("Prompt", backref="tag_associations")
    tag = relationship("PromptTag", backref="prompt_associations")
    added_by_user = relationship("User", foreign_keys=[added_by])

    # Unique constraint for one tag per prompt
    __table_args__ = (
        Index('uk_prompt_tag', 'prompt_id', 'tag_id', unique=True),
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptTagAssociation(prompt_id={self.prompt_id}, tag_id={self.tag_id})>"


class PromptCategory(BaseModel):
    """Hierarchical categories for organizing prompts."""

    __tablename__ = 'prompt_categories'

    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Icon identifier

    # Hierarchical structure
    parent_id = Column(
        CHAR(36),
        ForeignKey('prompt_categories.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=True,
        index=True
    )
    level = Column(Integer, nullable=False, default=0, index=True)
    sort_order = Column(Integer, nullable=False, default=0)

    # Usage and metadata
    prompt_count = Column(Integer, nullable=False, default=0, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Self-referential relationship
    parent = relationship(
        "PromptCategory",
        remote_side="PromptCategory.id",
        backref="children"
    )

    def get_full_path(self) -> str:
        """Get the full hierarchical path of this category."""
        if self.parent is None:
            return self.name
        return f"{self.parent.get_full_path()} > {self.name}"

    def get_ancestors(self) -> list:
        """Get all ancestor categories."""
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self) -> list:
        """Get all descendant categories."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants

    def increment_prompt_count(self) -> None:
        """Increment prompt count when a prompt is added."""
        self.prompt_count += 1
        # Also increment parent counts
        if self.parent:
            self.parent.increment_prompt_count()

    def decrement_prompt_count(self) -> None:
        """Decrement prompt count when a prompt is removed."""
        if self.prompt_count > 0:
            self.prompt_count -= 1
        # Also decrement parent counts
        if self.parent:
            self.parent.decrement_prompt_count()

    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptCategory(name={self.name}, level={self.level}, count={self.prompt_count})>"


class PromptUsageStatistics(BaseModel):
    """Track usage statistics and analytics for prompts."""

    __tablename__ = 'prompt_usage_statistics'

    prompt_id = Column(
        CHAR(36),
        ForeignKey('prompts.id', ondelete='CASCADE', onupdate='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )

    # Usage metrics
    view_count = Column(Integer, nullable=False, default=0, index=True)
    copy_count = Column(Integer, nullable=False, default=0)
    fork_count = Column(Integer, nullable=False, default=0)
    share_count = Column(Integer, nullable=False, default=0)

    # Time-based metrics
    last_viewed_at = Column(DateTime, nullable=True, index=True)
    last_copied_at = Column(DateTime, nullable=True)
    last_forked_at = Column(DateTime, nullable=True)

    # Performance metrics
    avg_response_time = Column(Integer, nullable=True)  # milliseconds
    success_rate = Column(Integer, nullable=False, default=100)  # percentage
    total_executions = Column(Integer, nullable=False, default=0)

    # User interaction
    unique_users = Column(Integer, nullable=False, default=0)
    bookmark_count = Column(Integer, nullable=False, default=0)

    # Relationship
    prompt = relationship("Prompt", backref="usage_statistics")

    def record_view(self, user_id: Optional[str] = None) -> None:
        """Record a view event."""
        self.view_count += 1
        self.last_viewed_at = datetime.utcnow()

    def record_copy(self) -> None:
        """Record a copy event."""
        self.copy_count += 1
        self.last_copied_at = datetime.utcnow()

    def record_fork(self) -> None:
        """Record a fork event."""
        self.fork_count += 1
        self.last_forked_at = datetime.utcnow()

    def record_share(self) -> None:
        """Record a share event."""
        self.share_count += 1

    def record_execution(self, response_time_ms: int, success: bool) -> None:
        """Record an execution event with performance data."""
        self.total_executions += 1

        # Update average response time
        if self.avg_response_time is None:
            self.avg_response_time = response_time_ms
        else:
            self.avg_response_time = int(
                (self.avg_response_time * (self.total_executions - 1) + response_time_ms) / self.total_executions
            )

        # Update success rate
        if success:
            successful_count = int(self.total_executions * (self.success_rate / 100))
            self.success_rate = int(((successful_count + 1) / self.total_executions) * 100)
        else:
            successful_count = int(self.total_executions * (self.success_rate / 100))
            self.success_rate = int((successful_count / self.total_executions) * 100)

    def get_popularity_score(self) -> float:
        """Calculate a popularity score based on various metrics."""
        # Weighted scoring algorithm
        weights = {
            'views': 1.0,
            'copies': 3.0,
            'forks': 5.0,
            'shares': 2.0,
            'bookmarks': 4.0
        }

        score = (
            self.view_count * weights['views'] +
            self.copy_count * weights['copies'] +
            self.fork_count * weights['forks'] +
            self.share_count * weights['shares'] +
            self.bookmark_count * weights['bookmarks']
        )

        # Apply recency bonus
        if self.last_viewed_at:
            days_since_last_view = (datetime.utcnow() - self.last_viewed_at).days
            recency_multiplier = max(0.1, 1 - (days_since_last_view / 365))
            score *= recency_multiplier

        return round(score, 2)

    def __repr__(self) -> str:
        """String representation."""
        return f"<PromptUsageStatistics(prompt_id={self.prompt_id}, views={self.view_count}, popularity={self.get_popularity_score()})>"