#!/usr/bin/env python3
"""Database setup and initialization script."""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

import click
from database.connection import create_database_tables, drop_database_tables
from database.migration_manager import MigrationManager


@click.group()
def cli():
    """Database setup and management commands."""
    pass


@cli.command()
def init():
    """Initialize the database with all tables."""
    click.echo("Initializing database...")

    async def initialize():
        try:
            # Create tables using SQLAlchemy
            await create_database_tables()
            click.echo("✓ Database tables created successfully.")

            # Run all migrations
            manager = MigrationManager()
            applied = await manager.migrate_up()

            if applied:
                click.echo(f"✓ Applied {len(applied)} migrations:")
                for version in applied:
                    click.echo(f"  - {version}")
            else:
                click.echo("✓ No migrations to apply.")

            click.echo("✓ Database initialization complete!")

        except Exception as e:
            click.echo(f"❌ Database initialization failed: {e}", err=True)
            sys.exit(1)

    asyncio.run(initialize())


@cli.command()
@click.confirmation_option(prompt="Are you sure you want to reset the database?")
def reset():
    """Reset the database (drop and recreate all tables)."""
    click.echo("Resetting database...")

    async def reset_db():
        try:
            # Drop all tables
            await drop_database_tables()
            click.echo("✓ Dropped all tables.")

            # Recreate tables
            await create_database_tables()
            click.echo("✓ Recreated all tables.")

            # Run all migrations
            manager = MigrationManager()
            applied = await manager.migrate_up()

            if applied:
                click.echo(f"✓ Applied {len(applied)} migrations:")
                for version in applied:
                    click.echo(f"  - {version}")

            click.echo("✓ Database reset complete!")

        except Exception as e:
            click.echo(f"❌ Database reset failed: {e}", err=True)
            sys.exit(1)

    asyncio.run(reset_db())


@cli.command()
def check():
    """Check database connection and status."""
    click.echo("Checking database connection...")

    async def check_db():
        try:
            from database.connection import engine
            from sqlalchemy import text

            # Test connection
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1

            click.echo("✓ Database connection successful.")

            # Check migration status
            manager = MigrationManager()
            status = await manager.get_migration_status()

            click.echo("\nMigration Status:")
            click.echo(f"  Total migrations: {status['total_migrations']}")
            click.echo(f"  Applied: {status['applied_migrations']}")
            click.echo(f"  Pending: {status['pending_migrations']}")

            if status['last_applied']:
                click.echo(f"  Last applied: {status['last_applied']}")

        except Exception as e:
            click.echo(f"❌ Database check failed: {e}", err=True)
            sys.exit(1)

    asyncio.run(check_db())


if __name__ == "__main__":
    cli()