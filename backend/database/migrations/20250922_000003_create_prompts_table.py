"""Migration: Create prompts table

Created: 2025-09-22T00:00:03
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.migration_base import Migration


class Migration20250922_000003(Migration):
    """Migration: Create prompts table."""

    def __init__(self):
        """Initialize migration."""
        super().__init__(
            version="20250922_000003",
            description="Create prompts table"
        )

    async def upgrade(self, session: AsyncSession) -> None:
        """Apply the migration."""
        await session.execute(text("""
            CREATE TABLE prompts (
                id CHAR(36) PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                system_prompt TEXT,
                version INT DEFAULT 1,
                parent_id CHAR(36),
                template_id CHAR(36),
                category VARCHAR(100),
                tags JSON,
                metadata JSON,
                model_settings JSON,
                is_public BOOLEAN DEFAULT FALSE,
                is_favorite BOOLEAN DEFAULT FALSE,
                usage_count INT DEFAULT 0,
                rating DECIMAL(3,2) DEFAULT 0.00,
                status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
                created_by CHAR(36) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deleted_at DATETIME NULL,
                INDEX idx_prompts_title (title),
                INDEX idx_prompts_category (category),
                INDEX idx_prompts_status (status),
                INDEX idx_prompts_public (is_public),
                INDEX idx_prompts_created_by (created_by),
                INDEX idx_prompts_template_id (template_id),
                INDEX idx_prompts_parent_id (parent_id),
                INDEX idx_prompts_created_at (created_at),
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE SET NULL,
                FOREIGN KEY (parent_id) REFERENCES prompts(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    async def downgrade(self, session: AsyncSession) -> None:
        """Reverse the migration."""
        await session.execute(text("DROP TABLE IF EXISTS prompts"))