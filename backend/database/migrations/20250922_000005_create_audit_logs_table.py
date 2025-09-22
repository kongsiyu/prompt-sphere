"""Migration: Create audit logs table

Created: 2025-09-22T00:00:05
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.migration_base import Migration


class Migration20250922_000005(Migration):
    """Migration: Create audit logs table."""

    def __init__(self):
        """Initialize migration."""
        super().__init__(
            version="20250922_000005",
            description="Create audit logs table"
        )

    async def upgrade(self, session: AsyncSession) -> None:
        """Apply the migration."""
        await session.execute(text("""
            CREATE TABLE audit_logs (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36),
                entity_type VARCHAR(100) NOT NULL,
                entity_id CHAR(36),
                action VARCHAR(50) NOT NULL,
                old_values JSON,
                new_values JSON,
                ip_address VARCHAR(45),
                user_agent TEXT,
                request_id VARCHAR(100),
                session_id VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_audit_logs_user_id (user_id),
                INDEX idx_audit_logs_entity_type (entity_type),
                INDEX idx_audit_logs_entity_id (entity_id),
                INDEX idx_audit_logs_action (action),
                INDEX idx_audit_logs_created_at (created_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    async def downgrade(self, session: AsyncSession) -> None:
        """Reverse the migration."""
        await session.execute(text("DROP TABLE IF EXISTS audit_logs"))