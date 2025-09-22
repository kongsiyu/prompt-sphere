"""
Audit log model test fixtures and factories.
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
import uuid

from database.models.audit_log import AuditLog


class AuditLogFactory(factory.Factory):
    """Factory for creating AuditLog instances for testing."""

    class Meta:
        model = AuditLog

    id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    user_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    session_id = factory.LazyFunction(lambda: f"session_{uuid.uuid4().hex[:8]}")
    entity_type = fuzzy.FuzzyChoice(['user', 'template', 'conversation', 'prompt', 'security'])
    entity_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    action = fuzzy.FuzzyChoice(['CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'SHARE'])
    old_values = None
    new_values = factory.LazyFunction(lambda: {'status': 'active', 'updated': True})
    changes = factory.LazyFunction(lambda: {'status': {'from': 'pending', 'to': 'active'}})
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    request_id = factory.LazyFunction(lambda: f"req_{uuid.uuid4().hex[:8]}")
    endpoint = factory.Faker('uri_path')
    method = fuzzy.FuzzyChoice(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
    metadata = factory.LazyFunction(lambda: {'source': 'test', 'additional_info': 'test_data'})
    severity = fuzzy.FuzzyChoice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    category = fuzzy.FuzzyChoice(['user_action', 'system_action', 'security', 'authentication'])
    created_at = factory.LazyFunction(datetime.utcnow)


class UserActionLogFactory(AuditLogFactory):
    """Factory for creating user action audit logs."""
    category = 'user_action'
    severity = 'LOW'
    action = fuzzy.FuzzyChoice(['CREATE', 'UPDATE', 'DELETE'])


class SecurityLogFactory(AuditLogFactory):
    """Factory for creating security audit logs."""
    category = 'security'
    severity = fuzzy.FuzzyChoice(['HIGH', 'CRITICAL'])
    entity_type = 'security'
    action = fuzzy.FuzzyChoice(['LOGIN', 'LOGOUT', 'FAILED_LOGIN', 'PASSWORD_CHANGE'])


class AuthenticationLogFactory(AuditLogFactory):
    """Factory for creating authentication audit logs."""
    category = 'authentication'
    entity_type = 'authentication'
    action = fuzzy.FuzzyChoice(['LOGIN', 'LOGOUT'])
    severity = 'LOW'


class SystemActionLogFactory(AuditLogFactory):
    """Factory for creating system action audit logs."""
    category = 'system_action'
    user_id = None  # System actions don't have a user
    action = fuzzy.FuzzyChoice(['BACKUP', 'CLEANUP', 'MAINTENANCE', 'UPDATE'])
    severity = 'MEDIUM'


class CriticalLogFactory(AuditLogFactory):
    """Factory for creating critical audit logs."""
    severity = 'CRITICAL'
    category = 'security'
    action = fuzzy.FuzzyChoice(['DELETE', 'EXPORT', 'SECURITY_BREACH'])


async def create_test_audit_log(session, **kwargs):
    """
    Create a test audit log and save to database.

    Args:
        session: Database session
        **kwargs: Additional audit log attributes

    Returns:
        Created AuditLog instance
    """
    log_data = {
        'action': 'CREATE',
        'entity_type': 'test_entity',
        'entity_id': str(uuid.uuid4()),
        'severity': 'LOW',
        'category': 'user_action',
    }
    log_data.update(kwargs)

    audit_log = AuditLogFactory.build(**log_data)
    session.add(audit_log)
    await session.flush()
    await session.refresh(audit_log)
    return audit_log


async def create_user_action_log(session, user_id, action='CREATE', entity_type='template', **kwargs):
    """
    Create a user action audit log.

    Args:
        session: Database session
        user_id: ID of the user performing the action
        action: Action performed
        entity_type: Type of entity
        **kwargs: Additional attributes

    Returns:
        Created AuditLog instance
    """
    log_data = {
        'user_id': user_id,
        'action': action,
        'entity_type': entity_type,
        'category': 'user_action',
        'severity': 'LOW',
        'metadata': {'user_action': True}
    }
    log_data.update(kwargs)

    return await create_test_audit_log(session, **log_data)


async def create_security_log(session, event_type='FAILED_LOGIN', user_id=None, severity='HIGH', **kwargs):
    """
    Create a security audit log.

    Args:
        session: Database session
        event_type: Type of security event
        user_id: ID of the user (if applicable)
        severity: Severity level
        **kwargs: Additional attributes

    Returns:
        Created AuditLog instance
    """
    log_data = {
        'user_id': user_id,
        'action': event_type,
        'entity_type': 'security',
        'category': 'security',
        'severity': severity,
        'metadata': {'security_event': True, 'event_type': event_type}
    }
    log_data.update(kwargs)

    return await create_test_audit_log(session, **log_data)


async def create_authentication_log(session, user_id, action='LOGIN', success=True, ip_address='192.168.1.1', **kwargs):
    """
    Create an authentication audit log.

    Args:
        session: Database session
        user_id: ID of the user
        action: Authentication action
        success: Whether authentication was successful
        ip_address: Client IP address
        **kwargs: Additional attributes

    Returns:
        Created AuditLog instance
    """
    severity = 'LOW' if success else 'MEDIUM'
    log_data = {
        'user_id': user_id,
        'action': action,
        'entity_type': 'authentication',
        'entity_id': user_id,
        'category': 'authentication',
        'severity': severity,
        'ip_address': ip_address,
        'metadata': {'success': success, 'authentication': True}
    }
    log_data.update(kwargs)

    return await create_test_audit_log(session, **log_data)


async def create_system_action_log(session, action='BACKUP', entity_type='system', **kwargs):
    """
    Create a system action audit log.

    Args:
        session: Database session
        action: System action
        entity_type: Type of entity
        **kwargs: Additional attributes

    Returns:
        Created AuditLog instance
    """
    log_data = {
        'user_id': None,  # System actions don't have a user
        'action': action,
        'entity_type': entity_type,
        'category': 'system_action',
        'severity': 'MEDIUM',
        'metadata': {'system_action': True, 'automated': True}
    }
    log_data.update(kwargs)

    return await create_test_audit_log(session, **log_data)


async def create_audit_log_with_changes(session, user_id, old_values, new_values, **kwargs):
    """
    Create an audit log with old and new values for change tracking.

    Args:
        session: Database session
        user_id: ID of the user
        old_values: Previous values
        new_values: New values
        **kwargs: Additional attributes

    Returns:
        Created AuditLog instance
    """
    # Compute changes
    changes = {}
    all_keys = set(old_values.keys()) | set(new_values.keys())

    for key in all_keys:
        old_val = old_values.get(key)
        new_val = new_values.get(key)

        if old_val != new_val:
            changes[key] = {
                'from': old_val,
                'to': new_val
            }

    log_data = {
        'user_id': user_id,
        'action': 'UPDATE',
        'old_values': old_values,
        'new_values': new_values,
        'changes': changes,
        'category': 'user_action',
        'severity': 'LOW'
    }
    log_data.update(kwargs)

    return await create_test_audit_log(session, **log_data)


async def create_audit_logs_timeline(session, user_id, days=7, actions_per_day=3):
    """
    Create a timeline of audit logs over multiple days.

    Args:
        session: Database session
        user_id: ID of the user
        days: Number of days to create logs for
        actions_per_day: Number of actions per day

    Returns:
        List of created AuditLog instances
    """
    logs = []
    actions = ['CREATE', 'READ', 'UPDATE', 'DELETE']
    entity_types = ['template', 'conversation', 'prompt', 'user']

    for day in range(days):
        date = datetime.utcnow() - timedelta(days=day)

        for action_num in range(actions_per_day):
            # Space out actions throughout the day
            action_time = date + timedelta(hours=action_num * (24 // actions_per_day))

            log_data = {
                'user_id': user_id,
                'action': actions[action_num % len(actions)],
                'entity_type': entity_types[action_num % len(entity_types)],
                'created_at': action_time,
                'metadata': {
                    'day': day,
                    'action_number': action_num,
                    'timeline_test': True
                }
            }

            log = await create_test_audit_log(session, **log_data)
            logs.append(log)

    return logs


async def create_audit_logs_by_severity(session, user_id):
    """
    Create audit logs with different severity levels.

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        Dict of audit logs by severity
    """
    severities = {
        'LOW': {
            'action': 'READ',
            'entity_type': 'template',
            'category': 'user_action'
        },
        'MEDIUM': {
            'action': 'UPDATE',
            'entity_type': 'user',
            'category': 'user_action'
        },
        'HIGH': {
            'action': 'DELETE',
            'entity_type': 'conversation',
            'category': 'user_action'
        },
        'CRITICAL': {
            'action': 'SECURITY_BREACH',
            'entity_type': 'security',
            'category': 'security'
        }
    }

    logs = {}
    for severity, log_data in severities.items():
        log_data['user_id'] = user_id
        log_data['severity'] = severity
        log_data['metadata'] = {'severity_test': True, 'level': severity}

        log = await create_test_audit_log(session, **log_data)
        logs[severity.lower()] = log

    return logs


async def create_failed_login_attempts(session, user_id, ip_address='192.168.1.100', count=5):
    """
    Create multiple failed login attempt logs.

    Args:
        session: Database session
        user_id: ID of the user
        ip_address: Client IP address
        count: Number of failed attempts

    Returns:
        List of created AuditLog instances
    """
    logs = []

    for i in range(count):
        attempt_time = datetime.utcnow() - timedelta(minutes=count - i)

        log_data = {
            'user_id': user_id,
            'action': 'FAILED_LOGIN',
            'entity_type': 'authentication',
            'entity_id': user_id,
            'category': 'security',
            'severity': 'MEDIUM',
            'ip_address': ip_address,
            'created_at': attempt_time,
            'metadata': {
                'attempt_number': i + 1,
                'total_attempts': count,
                'reason': 'invalid_password'
            }
        }

        log = await create_test_audit_log(session, **log_data)
        logs.append(log)

    return logs


# Sample audit log data
SAMPLE_AUDIT_LOGS = [
    {
        'action': 'CREATE',
        'entity_type': 'template',
        'category': 'user_action',
        'severity': 'LOW',
        'new_values': {
            'name': 'New Template',
            'category': 'business',
            'is_public': True
        },
        'metadata': {'template_creation': True}
    },
    {
        'action': 'UPDATE',
        'entity_type': 'user',
        'category': 'user_action',
        'severity': 'MEDIUM',
        'old_values': {
            'email': 'old@example.com',
            'role': 'user'
        },
        'new_values': {
            'email': 'new@example.com',
            'role': 'admin'
        },
        'metadata': {'profile_update': True}
    },
    {
        'action': 'DELETE',
        'entity_type': 'conversation',
        'category': 'user_action',
        'severity': 'HIGH',
        'old_values': {
            'title': 'Important Conversation',
            'status': 'active',
            'total_messages': 25
        },
        'metadata': {'permanent_deletion': True}
    },
    {
        'action': 'FAILED_LOGIN',
        'entity_type': 'security',
        'category': 'security',
        'severity': 'MEDIUM',
        'ip_address': '192.168.1.100',
        'metadata': {
            'reason': 'invalid_password',
            'attempt_count': 3
        }
    }
]


async def create_sample_audit_logs(session, user_id):
    """
    Create a set of sample audit logs for testing.

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        List of created AuditLog instances
    """
    logs = []

    for i, log_data in enumerate(SAMPLE_AUDIT_LOGS):
        # Add user_id and vary timestamps
        log_data['user_id'] = user_id
        log_data['created_at'] = datetime.utcnow() - timedelta(hours=i)
        log_data['entity_id'] = str(uuid.uuid4())

        # Compute changes if old and new values exist
        if 'old_values' in log_data and 'new_values' in log_data:
            changes = {}
            old_vals = log_data['old_values']
            new_vals = log_data['new_values']

            for key in set(old_vals.keys()) | set(new_vals.keys()):
                old_val = old_vals.get(key)
                new_val = new_vals.get(key)

                if old_val != new_val:
                    changes[key] = {'from': old_val, 'to': new_val}

            log_data['changes'] = changes

        log = await create_test_audit_log(session, **log_data)
        logs.append(log)

    return logs


async def create_audit_log_test_set(session, user_id):
    """
    Create a comprehensive set of audit logs for testing.

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        Dict of created audit logs by type
    """
    logs = {}

    # User action log
    logs['user_action'] = await create_user_action_log(
        session,
        user_id,
        action='CREATE',
        entity_type='template'
    )

    # Security log
    logs['security'] = await create_security_log(
        session,
        event_type='FAILED_LOGIN',
        user_id=user_id
    )

    # Authentication log
    logs['authentication'] = await create_authentication_log(
        session,
        user_id,
        action='LOGIN',
        success=True
    )

    # System action log
    logs['system_action'] = await create_system_action_log(
        session,
        action='BACKUP'
    )

    # Critical security log
    logs['critical'] = await create_test_audit_log(
        session,
        user_id=user_id,
        action='DELETE',
        entity_type='user',
        category='security',
        severity='CRITICAL'
    )

    # Log with changes
    logs['with_changes'] = await create_audit_log_with_changes(
        session,
        user_id,
        old_values={'status': 'draft', 'public': False},
        new_values={'status': 'published', 'public': True}
    )

    return logs