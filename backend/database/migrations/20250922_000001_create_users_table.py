"""Migration: Create users table

Created: 2025-09-22T00:00:01
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database.migration_base import Migration


class Migration20250922_000001(Migration):
    """Migration: Create users table."""

    def __init__(self):
        """Initialize migration."""
        super().__init__(
            version="20250922_000001",
            description="Create users table"
        )

    async def upgrade(self, session: AsyncSession) -> None:
        """Apply the migration."""
        await session.execute(text("""
            CREATE TABLE users (
                id CHAR(36) PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                avatar_url VARCHAR(500),
                is_active BOOLEAN DEFAULT TRUE,
                is_verified BOOLEAN DEFAULT FALSE,
                is_superuser BOOLEAN DEFAULT FALSE,
                preferences JSON,
                last_login_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deleted_at DATETIME NULL,
                INDEX idx_users_email (email),
                INDEX idx_users_username (username),
                INDEX idx_users_active (is_active),
                INDEX idx_users_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))

    async def downgrade(self, session: AsyncSession) -> None:
        """Reverse the migration."""
        await session.execute(text("DROP TABLE IF EXISTS users"))