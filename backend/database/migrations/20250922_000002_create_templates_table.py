"""Migration: Create templates table

Created: 2025-09-22T00:00:02
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.migration_base import Migration


class Migration20250922_000002(Migration):
    """Migration: Create templates table."""

    def __init__(self):
        """Initialize migration."""
        super().__init__(
            version="20250922_000002",
            description="Create templates table"
        )

    async def upgrade(self, session: AsyncSession) -> None:
        """Apply the migration."""
        await session.execute(text("""
            CREATE TABLE templates (
                id CHAR(36) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                category VARCHAR(100),
                template_content TEXT NOT NULL,
                variables JSON,
                is_public BOOLEAN DEFAULT FALSE,
                is_system BOOLEAN DEFAULT FALSE,
                usage_count INT DEFAULT 0,
                rating DECIMAL(3,2) DEFAULT 0.00,
                created_by CHAR(36),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deleted_at DATETIME NULL,
                INDEX idx_templates_name (name),
                INDEX idx_templates_category (category),
                INDEX idx_templates_public (is_public),
                INDEX idx_templates_system (is_system),
                INDEX idx_templates_created_by (created_by),
                INDEX idx_templates_created_at (created_at),
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    async def downgrade(self, session: AsyncSession) -> None:
        """Reverse the migration."""
        await session.execute(text("DROP TABLE IF EXISTS templates"))