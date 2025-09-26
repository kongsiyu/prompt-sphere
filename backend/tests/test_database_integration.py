"""Database connection and session integration tests."""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

from app.core.config import settings


@pytest.mark.database
@pytest.mark.asyncio
class TestDatabaseConnection:
    """Test database connection and session management."""

    async def test_database_connection_basic(self):
        """Test basic database connection."""
        database_url = settings.database_url or "sqlite+aiosqlite:///:memory:"
        engine = create_async_engine(database_url)

        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                assert row[0] == 1
        finally:
            await engine.dispose()

    async def test_database_session_creation(self, db_session: AsyncSession):
        """Test database session creation and cleanup."""
        assert isinstance(db_session, AsyncSession)
        assert db_session.is_active

        # Test simple query
        result = await db_session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        assert row[0] == 1

    async def test_session_transaction_commit(self, db_session: AsyncSession):
        """Test transaction commit behavior."""
        # Create a temporary table for testing
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_commit (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        """))

        # Insert data and commit
        await db_session.execute(text(
            "INSERT INTO test_commit (value) VALUES ('test_value')"
        ))
        await db_session.commit()

        # Verify data was committed
        result = await db_session.execute(text(
            "SELECT value FROM test_commit WHERE value = 'test_value'"
        ))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'test_value'

    async def test_session_transaction_rollback(self, db_session: AsyncSession):
        """Test transaction rollback behavior."""
        # Create a temporary table for testing
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_rollback (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        """))
        await db_session.commit()

        # Insert data but rollback
        await db_session.execute(text(
            "INSERT INTO test_rollback (value) VALUES ('rollback_value')"
        ))
        await db_session.rollback()

        # Verify data was not committed
        result = await db_session.execute(text(
            "SELECT value FROM test_rollback WHERE value = 'rollback_value'"
        ))
        row = result.fetchone()
        assert row is None


@pytest.mark.database
@pytest.mark.asyncio
class TestDatabasePerformance:
    """Test database performance and connection handling."""

    async def test_concurrent_sessions(self):
        """Test multiple concurrent sessions."""
        database_url = settings.database_url or "sqlite+aiosqlite:///:memory:"
        engine = create_async_engine(database_url)

        async def worker_task(worker_id: int):
            """Worker task that performs database operations."""
            async with AsyncSession(engine) as session:
                # Simulate work with multiple queries
                for i in range(5):
                    result = await session.execute(text(
                        f"SELECT {worker_id} as worker, {i} as iteration"
                    ))
                    row = result.fetchone()
                    assert row[0] == worker_id
                    assert row[1] == i

                return worker_id

        try:
            # Run multiple concurrent workers
            workers = [worker_task(i) for i in range(5)]
            results = await asyncio.gather(*workers)

            # All workers should complete successfully
            assert len(results) == 5
            assert set(results) == set(range(5))
        finally:
            await engine.dispose()

    async def test_long_running_session(self, db_session: AsyncSession):
        """Test long-running session stability."""
        # Create temporary table
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_long_running (
                id INTEGER PRIMARY KEY,
                batch_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Perform multiple batches of operations
        for batch in range(3):
            # Insert multiple records in each batch
            for record in range(10):
                await db_session.execute(text(
                    f"INSERT INTO test_long_running (batch_id) VALUES ({batch})"
                ))

            # Commit after each batch
            await db_session.commit()

            # Verify batch was inserted
            result = await db_session.execute(text(
                f"SELECT COUNT(*) FROM test_long_running WHERE batch_id = {batch}"
            ))
            count = result.scalar()
            assert count == 10

        # Verify total records
        result = await db_session.execute(text(
            "SELECT COUNT(*) FROM test_long_running"
        ))
        total_count = result.scalar()
        assert total_count == 30


@pytest.mark.database
@pytest.mark.asyncio
class TestDatabaseErrorHandling:
    """Test database error handling and recovery."""

    async def test_invalid_query_handling(self, db_session: AsyncSession):
        """Test handling of invalid SQL queries."""
        with pytest.raises(Exception):  # Could be various SQL-related exceptions
            await db_session.execute(text("SELECT FROM invalid_syntax"))

        # Session should still be usable after error
        result = await db_session.execute(text("SELECT 1 as recovery_test"))
        row = result.fetchone()
        assert row[0] == 1

    async def test_transaction_after_error(self, db_session: AsyncSession):
        """Test transaction handling after an error."""
        # Create temporary table
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_error_recovery (
                id INTEGER PRIMARY KEY,
                value TEXT NOT NULL
            )
        """))
        await db_session.commit()

        try:
            # Try to insert invalid data (this should fail)
            await db_session.execute(text(
                "INSERT INTO test_error_recovery (value) VALUES (NULL)"
            ))
            await db_session.commit()
        except Exception:
            # Rollback the failed transaction
            await db_session.rollback()

        # Should be able to perform valid operations after rollback
        await db_session.execute(text(
            "INSERT INTO test_error_recovery (value) VALUES ('valid_value')"
        ))
        await db_session.commit()

        # Verify the valid data was inserted
        result = await db_session.execute(text(
            "SELECT value FROM test_error_recovery WHERE value = 'valid_value'"
        ))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'valid_value'


@pytest.mark.database
@pytest.mark.asyncio
class TestDatabaseSchema:
    """Test database schema operations."""

    async def test_table_creation_and_constraints(self, db_session: AsyncSession):
        """Test creating tables with proper constraints."""
        # Create test tables with relationships
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_parent (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_child (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER REFERENCES test_parent(id) ON DELETE CASCADE,
                value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))

        await db_session.commit()

        # Test foreign key constraint
        # Insert parent record
        await db_session.execute(text(
            "INSERT INTO test_parent (name) VALUES ('parent1')"
        ))
        await db_session.commit()

        # Get parent ID
        result = await db_session.execute(text(
            "SELECT id FROM test_parent WHERE name = 'parent1'"
        ))
        parent_id = result.scalar()

        # Insert child record
        await db_session.execute(text(
            f"INSERT INTO test_child (parent_id, value) VALUES ({parent_id}, 'child1')"
        ))
        await db_session.commit()

        # Verify relationship
        result = await db_session.execute(text("""
            SELECT p.name, c.value
            FROM test_parent p
            JOIN test_child c ON p.id = c.parent_id
        """))
        row = result.fetchone()
        assert row[0] == 'parent1'
        assert row[1] == 'child1'

    async def test_index_creation_and_usage(self, db_session: AsyncSession):
        """Test index creation and query performance."""
        # Create table with indexed column
        await db_session.execute(text("""
            CREATE TEMPORARY TABLE test_indexed (
                id INTEGER PRIMARY KEY,
                search_value TEXT,
                data TEXT
            )
        """))

        # Create index
        await db_session.execute(text(
            "CREATE INDEX idx_test_search ON test_indexed (search_value)"
        ))

        await db_session.commit()

        # Insert test data
        for i in range(50):
            await db_session.execute(text(f"""
                INSERT INTO test_indexed (search_value, data)
                VALUES ('value_{i}', 'data_{i}')
            """))

        await db_session.commit()

        # Test query with index
        result = await db_session.execute(text(
            "SELECT data FROM test_indexed WHERE search_value = 'value_25'"
        ))
        row = result.fetchone()
        assert row is not None
        assert row[0] == 'data_25'

        # Test range query
        result = await db_session.execute(text(
            "SELECT COUNT(*) FROM test_indexed WHERE search_value LIKE 'value_1%'"
        ))
        count = result.scalar()
        assert count >= 10  # Should find value_1, value_10-19