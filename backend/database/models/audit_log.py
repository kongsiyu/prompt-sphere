"""
Audit log model for tracking system activities.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy import Column, String, Text, ForeignKey, Enum, Index
from sqlalchemy.dialects.mysql import JSON, CHAR
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base


class AuditLog(AuditMixin, Base):
    """Audit log model for comprehensive activity tracking."""

    __tablename__ = 'audit_logs'

    # Primary key
    id = Column(
        CHAR(36),
        primary_key=True,
        default=lambda: str(__import__('uuid').uuid4()),
        server_default=__import__('sqlalchemy').text("(UUID())")
    )

    # User and session information
    user_id = Column(
        CHAR(36),
        ForeignKey('users.id', ondelete='RESTRICT', onupdate='CASCADE'),
        nullable=True,
        index=True
    )
    session_id = Column(String(255), nullable=True, index=True)

    # Entity information
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(CHAR(36), nullable=True, index=True)
    action = Column(
        Enum(
            'CREATE', 'READ', 'UPDATE', 'DELETE',
            'LOGIN', 'LOGOUT', 'EXPORT', 'SHARE',
            name='audit_action'
        ),
        nullable=False,
        index=True
    )

    # Change tracking
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    changes = Column(JSON, nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True, index=True)  # Supports IPv6
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(255), nullable=True)
    endpoint = Column(String(255), nullable=True)
    method = Column(
        Enum('GET', 'POST', 'PUT', 'PATCH', 'DELETE', name='http_method'),
        nullable=True
    )

    # Additional metadata
    metadata = Column(JSON, nullable=True, default={})
    severity = Column(
        Enum('LOW', 'MEDIUM', 'HIGH', 'CRITICAL', name='audit_severity'),
        nullable=False,
        default='LOW',
        index=True
    )
    category = Column(String(50), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_logs_user_action', 'user_id', 'action'),
        Index('idx_audit_logs_severity_created', 'severity', 'created_at'),
    )

    def __init__(self, **kwargs):
        """Initialize audit log with default metadata."""
        super().__init__(**kwargs)
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def create_log(cls,
                   action: str,
                   entity_type: str,
                   entity_id: Optional[str] = None,
                   user_id: Optional[str] = None,
                   old_values: Optional[Dict[str, Any]] = None,
                   new_values: Optional[Dict[str, Any]] = None,
                   ip_address: Optional[str] = None,
                   user_agent: Optional[str] = None,
                   request_id: Optional[str] = None,
                   endpoint: Optional[str] = None,
                   method: Optional[str] = None,
                   session_id: Optional[str] = None,
                   severity: str = 'LOW',
                   category: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> 'AuditLog':
        """
        Create an audit log entry with computed changes.

        Args:
            action: The action performed
            entity_type: Type of entity affected
            entity_id: ID of the affected entity
            user_id: ID of the user performing the action
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Unique request identifier
            endpoint: API endpoint called
            method: HTTP method used
            session_id: User session identifier
            severity: Severity level of the action
            category: Category for grouping logs
            metadata: Additional metadata

        Returns:
            AuditLog instance
        """
        changes = None
        if old_values and new_values:
            changes = cls._compute_changes(old_values, new_values)

        return cls(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            endpoint=endpoint,
            method=method,
            session_id=session_id,
            severity=severity,
            category=category,
            metadata=metadata or {}
        )

    @staticmethod
    def _compute_changes(old_values: Dict[str, Any], new_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute changes between old and new values.

        Args:
            old_values: Previous state
            new_values: New state

        Returns:
            Dictionary of changes with before/after values
        """
        changes = {}

        # Find all keys that were changed, added, or removed
        all_keys = set(old_values.keys()) | set(new_values.keys())

        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)

            if old_val != new_val:
                changes[key] = {
                    'from': old_val,
                    'to': new_val
                }

        return changes

    def add_metadata(self, key: str, value: Any) -> None:
        """Add a metadata entry."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)

    def get_change_summary(self) -> str:
        """Get a human-readable summary of changes."""
        if not self.changes:
            return f"{self.action} {self.entity_type}"

        change_count = len(self.changes)
        if change_count == 1:
            field = list(self.changes.keys())[0]
            return f"{self.action} {self.entity_type}: {field} changed"
        else:
            return f"{self.action} {self.entity_type}: {change_count} fields changed"

    def is_sensitive_action(self) -> bool:
        """Check if this is a sensitive action that requires special attention."""
        sensitive_actions = {'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'SHARE'}
        sensitive_entities = {'users', 'audit_logs'}

        return (
            self.action in sensitive_actions or
            self.entity_type in sensitive_entities or
            self.severity in ['HIGH', 'CRITICAL']
        )

    def is_security_related(self) -> bool:
        """Check if this log entry is security-related."""
        security_actions = {'LOGIN', 'LOGOUT', 'DELETE'}
        security_categories = {'authentication', 'authorization', 'security'}

        return (
            self.action in security_actions or
            (self.category and self.category in security_categories) or
            self.severity == 'CRITICAL'
        )

    def anonymize_sensitive_data(self) -> None:
        """Remove or mask sensitive data from the audit log."""
        sensitive_fields = ['password', 'password_hash', 'token', 'secret', 'key']

        for values_dict in [self.old_values, self.new_values]:
            if values_dict:
                for field in sensitive_fields:
                    if field in values_dict:
                        values_dict[field] = '[REDACTED]'

        # Update changes if they exist
        if self.changes:
            for field in sensitive_fields:
                if field in self.changes:
                    self.changes[field] = {
                        'from': '[REDACTED]',
                        'to': '[REDACTED]'
                    }

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert to dictionary.

        Args:
            include_sensitive: Whether to include potentially sensitive data

        Returns:
            Dictionary representation
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'ip_address': self.ip_address,
            'endpoint': self.endpoint,
            'method': self.method,
            'severity': self.severity,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'change_summary': self.get_change_summary()
        }

        if include_sensitive:
            data.update({
                'old_values': self.old_values,
                'new_values': self.new_values,
                'changes': self.changes,
                'user_agent': self.user_agent,
                'metadata': self.metadata
            })

        return data

    def __repr__(self) -> str:
        """String representation."""
        return f"<AuditLog(id={self.id}, action={self.action}, entity_type={self.entity_type})>"


# Convenience functions for common audit operations

def log_user_action(user_id: str, action: str, entity_type: str, entity_id: Optional[str] = None,
                   **kwargs) -> AuditLog:
    """Log a user action."""
    return AuditLog.create_log(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        category='user_action',
        **kwargs
    )


def log_system_action(action: str, entity_type: str, entity_id: Optional[str] = None,
                     **kwargs) -> AuditLog:
    """Log a system action."""
    return AuditLog.create_log(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        category='system_action',
        **kwargs
    )


def log_security_event(action: str, user_id: Optional[str] = None, severity: str = 'HIGH',
                      **kwargs) -> AuditLog:
    """Log a security event."""
    return AuditLog.create_log(
        action=action,
        entity_type='security',
        user_id=user_id,
        severity=severity,
        category='security',
        **kwargs
    )


def log_authentication(user_id: str, action: str, ip_address: str, user_agent: str,
                      success: bool = True, **kwargs) -> AuditLog:
    """Log authentication events."""
    severity = 'LOW' if success else 'MEDIUM'
    metadata = {'success': success}
    metadata.update(kwargs.get('metadata', {}))

    return AuditLog.create_log(
        action=action,
        entity_type='authentication',
        entity_id=user_id,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        severity=severity,
        category='authentication',
        metadata=metadata,
        **{k: v for k, v in kwargs.items() if k != 'metadata'}
    )