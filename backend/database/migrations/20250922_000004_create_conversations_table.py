"""Migration: Create conversations table

Created: 2025-09-22T00:00:04
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.migration_base import Migration


class Migration20250922_000004(Migration):
    """Migration: Create conversations table."""

    def __init__(self):
        """Initialize migration."""
        super().__init__(
            version="20250922_000004",
            description="Create conversations table"
        )

    async def upgrade(self, session: AsyncSession) -> None:
        """Apply the migration."""
        await session.execute(text("""
            CREATE TABLE conversations (
                id CHAR(36) PRIMARY KEY,
                user_id CHAR(36) NOT NULL,
                prompt_id CHAR(36),
                title VARCHAR(255),
                messages JSON NOT NULL,
                model_used VARCHAR(100),
                model_settings JSON,
                total_tokens INT DEFAULT 0,
                total_cost DECIMAL(10,4) DEFAULT 0.0000,
                status ENUM('active', 'completed', 'failed', 'archived') DEFAULT 'active',
                metadata JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deleted_at DATETIME NULL,
                INDEX idx_conversations_user_id (user_id),
                INDEX idx_conversations_prompt_id (prompt_id),
                INDEX idx_conversations_status (status),
                INDEX idx_conversations_model (model_used),
                INDEX idx_conversations_created_at (created_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    async def downgrade(self, session: AsyncSession) -> None:
        """Reverse the migration."""
        await session.execute(text("DROP TABLE IF EXISTS conversations"))