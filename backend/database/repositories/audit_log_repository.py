"""
Audit log repository for security and compliance tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, and_, or_, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.audit_log import AuditLog
from .base import BaseRepository, RepositoryError


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog model with security and compliance features."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLog)

    @property
    def model_class(self) -> type[AuditLog]:
        return AuditLog

    async def log_user_action(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AuditLog:
        """
        Log a user action with full context.

        Args:
            user_id: User performing the action
            action: Action performed
            entity_type: Type of entity affected
            entity_id: ID of affected entity
            old_values: Previous values for updates
            new_values: New values for creates/updates
            details: Additional details in metadata
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request ID for tracing
            endpoint: API endpoint
            method: HTTP method
            session_id: User session ID

        Returns:
            Created AuditLog instance

        Raises:
            RepositoryError: If logging fails
        """
        try:
            metadata = details or {}

            audit_log = AuditLog.create_log(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                endpoint=endpoint,
                method=method,
                session_id=session_id,
                category='user_action',
                metadata=metadata
            )

            self.session.add(audit_log)
            await self.session.flush()
            await self.session.refresh(audit_log)

            self.logger.debug(f"Logged user action: {action} by user {user_id}")
            return audit_log

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to log user action: {e}")
            raise RepositoryError(f"Failed to log user action: {str(e)}")

    async def log_system_action(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = 'LOW'
    ) -> AuditLog:
        """
        Log a system action.

        Args:
            action: Action performed by system
            entity_type: Type of entity affected
            entity_id: ID of affected entity
            details: Additional details
            severity: Severity level

        Returns:
            Created AuditLog instance

        Raises:
            RepositoryError: If logging fails
        """
        try:
            audit_log = AuditLog.create_log(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                severity=severity,
                category='system_action',
                metadata=details or {}
            )

            self.session.add(audit_log)
            await self.session.flush()
            await self.session.refresh(audit_log)

            self.logger.debug(f"Logged system action: {action}")
            return audit_log

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to log system action: {e}")
            raise RepositoryError(f"Failed to log system action: {str(e)}")

    async def log_security_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = 'HIGH',
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Log a security event.

        Args:
            event_type: Type of security event
            user_id: User ID if applicable
            entity_id: Entity ID if applicable
            details: Event details
            severity: Severity level
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created AuditLog instance

        Raises:
            RepositoryError: If logging fails
        """
        try:
            audit_log = AuditLog.create_log(
                action=event_type,
                entity_type='security',
                entity_id=entity_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                category='security',
                metadata=details or {}
            )

            self.session.add(audit_log)
            await self.session.flush()
            await self.session.refresh(audit_log)

            self.logger.warning(f"Logged security event: {event_type} (severity: {severity})")
            return audit_log

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to log security event: {e}")
            raise RepositoryError(f"Failed to log security event: {str(e)}")

    async def log_authentication(
        self,
        user_id: str,
        action: str,
        ip_address: str,
        user_agent: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log authentication events.

        Args:
            user_id: User ID
            action: Authentication action (login, logout, etc.)
            ip_address: Client IP address
            user_agent: Client user agent
            success: Whether authentication was successful
            details: Additional details

        Returns:
            Created AuditLog instance

        Raises:
            RepositoryError: If logging fails
        """
        try:
            severity = 'LOW' if success else 'MEDIUM'
            metadata = {'success': success}
            if details:
                metadata.update(details)

            audit_log = AuditLog.create_log(
                action=action,
                entity_type='authentication',
                entity_id=user_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                category='authentication',
                metadata=metadata
            )

            self.session.add(audit_log)
            await self.session.flush()
            await self.session.refresh(audit_log)

            self.logger.info(f"Logged authentication: {action} for user {user_id} (success: {success})")
            return audit_log

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Failed to log authentication: {e}")
            raise RepositoryError(f"Failed to log authentication: {str(e)}")

    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30,
        limit: Optional[int] = None,
        actions: Optional[List[str]] = None
    ) -> List[AuditLog]:
        """
        Get user activity logs.

        Args:
            user_id: User ID
            days: Number of days to look back
            limit: Maximum number of logs to return
            actions: Filter by specific actions

        Returns:
            List of AuditLog instances
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            conditions = [
                AuditLog.user_id == user_id,
                AuditLog.created_at >= cutoff_date
            ]

            if actions:
                conditions.append(AuditLog.action.in_(actions))

            query = (
                select(AuditLog)
                .options(selectinload(AuditLog.user))
                .where(and_(*conditions))
                .order_by(AuditLog.created_at.desc())
            )

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            logs = result.scalars().all()

            self.logger.debug(f"Retrieved {len(logs)} activity logs for user: {user_id}")
            return list(logs)

        except Exception as e:
            self.logger.error(f"Error getting user activity for {user_id}: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: Optional[int] = None
    ) -> List[AuditLog]:
        """
        Get history of changes for an entity.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            limit: Maximum number of logs to return

        Returns:
            List of AuditLog instances showing entity history
        """
        try:
            query = (
                select(AuditLog)
                .options(selectinload(AuditLog.user))
                .where(
                    and_(
                        AuditLog.entity_type == entity_type,
                        AuditLog.entity_id == entity_id
                    )
                )
                .order_by(AuditLog.created_at.desc())
            )

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            logs = result.scalars().all()

            self.logger.debug(f"Retrieved {len(logs)} history logs for {entity_type}:{entity_id}")
            return list(logs)

        except Exception as e:
            self.logger.error(f"Error getting entity history: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_security_logs(
        self,
        days: int = 7,
        severity: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[AuditLog]:
        """
        Get security-related logs.

        Args:
            days: Number of days to look back
            severity: Filter by severity level
            limit: Maximum number of logs to return

        Returns:
            List of security-related AuditLog instances
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            conditions = [
                AuditLog.created_at >= cutoff_date,
                or_(
                    AuditLog.category == 'security',
                    AuditLog.category == 'authentication',
                    AuditLog.severity.in_(['HIGH', 'CRITICAL'])
                )
            ]

            if severity:
                conditions.append(AuditLog.severity == severity)

            query = (
                select(AuditLog)
                .options(selectinload(AuditLog.user))
                .where(and_(*conditions))
                .order_by(AuditLog.severity.desc(), AuditLog.created_at.desc())
            )

            if limit is not None:
                query = query.limit(limit)

            result = await self.session.execute(query)
            logs = result.scalars().all()

            self.logger.debug(f"Retrieved {len(logs)} security logs")
            return list(logs)

        except Exception as e:
            self.logger.error(f"Error getting security logs: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def search_logs(
        self,
        search_term: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        days: int = 30,
        limit: Optional[int] = None
    ) -> List[AuditLog]:
        """
        Search audit logs.

        Args:
            search_term: Term to search for
            category: Filter by category
            user_id: Filter by user ID
            entity_type: Filter by entity type
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of matching AuditLog instances
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            search_pattern = f"%{search_term.lower()}%"

            conditions = [AuditLog.created_at >= cutoff_date]

            # Text search in various fields
            text_conditions = [
                AuditLog.action.like(search_pattern),
                AuditLog.entity_type.like(search_pattern),
                AuditLog.category.like(search_pattern)
            ]

            # Search in metadata if possible
            if self.session.bind.dialect.name == 'mysql':
                text_conditions.append(
                    text("JSON_SEARCH(metadata, 'one', :search_pattern) IS NOT NULL")
                )

            conditions.append(or_(*text_conditions))

            if category:
                conditions.append(AuditLog.category == category)
            if user_id:
                conditions.append(AuditLog.user_id == user_id)
            if entity_type:
                conditions.append(AuditLog.entity_type == entity_type)

            query = (
                select(AuditLog)
                .options(selectinload(AuditLog.user))
                .where(and_(*conditions))
                .order_by(AuditLog.created_at.desc())
            )

            if limit is not None:
                query = query.limit(limit)

            # Handle MySQL-specific parameter binding
            if self.session.bind.dialect.name == 'mysql':
                result = await self.session.execute(query.params(search_pattern=f"%{search_term}%"))
            else:
                result = await self.session.execute(query)

            logs = result.scalars().all()

            self.logger.debug(f"Search for '{search_term}' found {len(logs)} logs")
            return list(logs)

        except Exception as e:
            self.logger.error(f"Error searching logs: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def get_system_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get audit log statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with audit statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Total logs
            total_query = select(func.count()).select_from(AuditLog).where(
                AuditLog.created_at >= cutoff_date
            )
            total_result = await self.session.execute(total_query)
            total_logs = total_result.scalar()

            # Logs by category
            category_query = (
                select(AuditLog.category, func.count())
                .where(AuditLog.created_at >= cutoff_date)
                .group_by(AuditLog.category)
            )
            category_result = await self.session.execute(category_query)
            logs_by_category = dict(category_result.all())

            # Logs by severity
            severity_query = (
                select(AuditLog.severity, func.count())
                .where(AuditLog.created_at >= cutoff_date)
                .group_by(AuditLog.severity)
            )
            severity_result = await self.session.execute(severity_query)
            logs_by_severity = dict(severity_result.all())

            # Top active users
            user_activity_query = (
                select(AuditLog.user_id, func.count())
                .where(
                    and_(
                        AuditLog.created_at >= cutoff_date,
                        AuditLog.user_id.is_not(None)
                    )
                )
                .group_by(AuditLog.user_id)
                .order_by(func.count().desc())
                .limit(10)
            )
            user_activity_result = await self.session.execute(user_activity_query)
            top_users = dict(user_activity_result.all())

            # Security events count
            security_query = select(func.count()).select_from(AuditLog).where(
                and_(
                    AuditLog.created_at >= cutoff_date,
                    or_(
                        AuditLog.category == 'security',
                        AuditLog.severity.in_(['HIGH', 'CRITICAL'])
                    )
                )
            )
            security_result = await self.session.execute(security_query)
            security_events = security_result.scalar()

            # Failed authentication attempts
            auth_fail_query = select(func.count()).select_from(AuditLog).where(
                and_(
                    AuditLog.created_at >= cutoff_date,
                    AuditLog.category == 'authentication',
                    text("JSON_EXTRACT(metadata, '$.success') = false")
                )
            )
            auth_fail_result = await self.session.execute(auth_fail_query)
            failed_auth = auth_fail_result.scalar()

            statistics = {
                'total_logs': total_logs,
                'logs_by_category': logs_by_category,
                'logs_by_severity': logs_by_severity,
                'top_active_users': top_users,
                'security_events': security_events,
                'failed_authentication_attempts': failed_auth,
                'analysis_period_days': days
            }

            self.logger.debug("Generated audit log statistics")
            return statistics

        except Exception as e:
            self.logger.error(f"Error generating audit statistics: {e}")
            raise RepositoryError(f"Database error: {str(e)}")

    async def cleanup_old_logs(self, days: int = 365) -> int:
        """
        Clean up old audit logs based on retention policy.

        Args:
            days: Number of days to retain logs

        Returns:
            Number of logs deleted

        Raises:
            RepositoryError: If cleanup fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Keep critical and high severity logs longer
            delete_query = select(AuditLog.id).where(
                and_(
                    AuditLog.created_at < cutoff_date,
                    AuditLog.severity.in_(['LOW', 'MEDIUM'])
                )
            )

            result = await self.session.execute(delete_query)
            log_ids = [row[0] for row in result.fetchall()]

            if log_ids:
                # Delete in batches to avoid long-running transactions
                batch_size = 1000
                total_deleted = 0

                for i in range(0, len(log_ids), batch_size):
                    batch_ids = log_ids[i:i + batch_size]
                    delete_batch = AuditLog.__table__.delete().where(
                        AuditLog.id.in_(batch_ids)
                    )
                    batch_result = await self.session.execute(delete_batch)
                    total_deleted += batch_result.rowcount

                await self.session.commit()

                self.logger.info(f"Cleaned up {total_deleted} old audit logs")
                return total_deleted
            else:
                self.logger.info("No old audit logs to clean up")
                return 0

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error cleaning up audit logs: {e}")
            raise RepositoryError(f"Failed to cleanup audit logs: {str(e)}")

    async def anonymize_user_logs(self, user_id: str) -> int:
        """
        Anonymize logs for a specific user (for GDPR compliance).

        Args:
            user_id: User ID to anonymize

        Returns:
            Number of logs anonymized

        Raises:
            RepositoryError: If anonymization fails
        """
        try:
            # Find logs for the user
            logs_query = select(AuditLog).where(AuditLog.user_id == user_id)
            result = await self.session.execute(logs_query)
            logs = result.scalars().all()

            anonymized_count = 0
            for log in logs:
                log.user_id = None  # Remove user reference
                log.anonymize_sensitive_data()  # Remove sensitive data
                log.add_metadata('anonymized', True)
                log.add_metadata('anonymized_at', datetime.utcnow().isoformat())
                anonymized_count += 1

            await self.session.flush()

            self.logger.info(f"Anonymized {anonymized_count} logs for user {user_id}")
            return anonymized_count

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error anonymizing user logs: {e}")
            raise RepositoryError(f"Failed to anonymize user logs: {str(e)}")

    async def export_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_types: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        include_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Export audit logs for compliance or analysis.

        Args:
            start_date: Start date for export
            end_date: End date for export
            entity_types: Filter by entity types
            categories: Filter by categories
            include_sensitive: Whether to include sensitive data

        Returns:
            List of audit log dictionaries

        Raises:
            RepositoryError: If export fails
        """
        try:
            conditions = [
                AuditLog.created_at >= start_date,
                AuditLog.created_at <= end_date
            ]

            if entity_types:
                conditions.append(AuditLog.entity_type.in_(entity_types))
            if categories:
                conditions.append(AuditLog.category.in_(categories))

            query = (
                select(AuditLog)
                .options(selectinload(AuditLog.user))
                .where(and_(*conditions))
                .order_by(AuditLog.created_at)
            )

            result = await self.session.execute(query)
            logs = result.scalars().all()

            exported_logs = []
            for log in logs:
                log_dict = log.to_dict(include_sensitive=include_sensitive)
                # Add user email if available and authorized
                if log.user and include_sensitive:
                    log_dict['user_email'] = log.user.email
                exported_logs.append(log_dict)

            self.logger.info(f"Exported {len(exported_logs)} audit logs")
            return exported_logs

        except Exception as e:
            self.logger.error(f"Error exporting audit logs: {e}")
            raise RepositoryError(f"Failed to export audit logs: {str(e)}")