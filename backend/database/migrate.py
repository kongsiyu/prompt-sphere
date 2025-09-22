#!/usr/bin/env python3
"""Database migration runner script."""

import asyncio
import sys
from typing import Optional

import click

from .migration_manager import MigrationManager


@click.group()
def cli():
    """Database migration commands."""
    pass


@cli.command()
@click.option(
    "--target", "-t",
    help="Target migration version (migrate up to this version)"
)
def up(target: Optional[str] = None):
    """Run pending migrations."""
    click.echo("Running migrations...")

    async def run_migrations():
        manager = MigrationManager()
        try:
            applied = await manager.migrate_up(target_version=target)
            if applied:
                click.echo(f"Applied {len(applied)} migrations:")
                for version in applied:
                    click.echo(f"  ✓ {version}")
            else:
                click.echo("No pending migrations found.")
        except Exception as e:
            click.echo(f"❌ Migration failed: {e}", err=True)
            sys.exit(1)

    asyncio.run(run_migrations())


@cli.command()
@click.option(
    "--target", "-t",
    help="Target migration version (rollback to this version)"
)
@click.option(
    "--steps", "-s",
    type=int,
    default=1,
    help="Number of migrations to rollback (default: 1)"
)
def down(target: Optional[str] = None, steps: int = 1):
    """Rollback migrations."""
    if target and steps != 1:
        click.echo("❌ Cannot specify both --target and --steps", err=True)
        sys.exit(1)

    if target:
        click.echo(f"Rolling back to version {target}...")
    else:
        click.echo(f"Rolling back {steps} migration(s)...")

    async def run_rollback():
        manager = MigrationManager()
        try:
            rolled_back = await manager.migrate_down(
                target_version=target,
                steps=steps
            )
            if rolled_back:
                click.echo(f"Rolled back {len(rolled_back)} migrations:")
                for version in rolled_back:
                    click.echo(f"  ✓ {version}")
            else:
                click.echo("No migrations to rollback.")
        except Exception as e:
            click.echo(f"❌ Rollback failed: {e}", err=True)
            sys.exit(1)

    asyncio.run(run_rollback())


@cli.command()
def status():
    """Show migration status."""
    click.echo("Migration Status")
    click.echo("=" * 50)

    async def show_status():
        manager = MigrationManager()
        try:
            status_info = await manager.get_migration_status()

            click.echo(f"Total migrations: {status_info['total_migrations']}")
            click.echo(f"Applied migrations: {status_info['applied_migrations']}")
            click.echo(f"Pending migrations: {status_info['pending_migrations']}")

            if status_info['last_applied']:
                click.echo(f"Last applied: {status_info['last_applied']}")
            else:
                click.echo("Last applied: None")

            if status_info['applied_versions']:
                click.echo("\nApplied migrations:")
                for version in status_info['applied_versions']:
                    click.echo(f"  ✓ {version}")

            if status_info['pending_versions']:
                click.echo("\nPending migrations:")
                for version in status_info['pending_versions']:
                    click.echo(f"  ⏳ {version}")

        except Exception as e:
            click.echo(f"❌ Failed to get status: {e}", err=True)
            sys.exit(1)

    asyncio.run(show_status())


@cli.command()
def validate():
    """Validate all migrations."""
    click.echo("Validating migrations...")

    async def validate_migrations():
        manager = MigrationManager()
        try:
            await manager.validate_migrations()
            click.echo("✓ All migrations are valid.")
        except Exception as e:
            click.echo(f"❌ Validation failed: {e}", err=True)
            sys.exit(1)

    asyncio.run(validate_migrations())


@cli.command()
@click.argument("description")
def create(description: str):
    """Create a new migration file."""
    from datetime import datetime
    import os

    # Generate version timestamp
    now = datetime.now()
    version = now.strftime("%Y%m%d_%H%M%S")

    # Create filename
    safe_description = "".join(c if c.isalnum() or c in "_-" else "_" for c in description.lower())
    filename = f"{version}_{safe_description}.py"

    # Migration template
    template = f'''"""Migration: {description}

Created: {now.isoformat()}
"""

from sqlalchemy.ext.asyncio import AsyncSession

from database.migration_base import Migration


class Migration{version}(Migration):
    """Migration: {description}."""

    def __init__(self):
        """Initialize migration."""
        super().__init__(
            version="{version}",
            description="{description}"
        )

    async def upgrade(self, session: AsyncSession) -> None:
        """Apply the migration."""
        # TODO: Implement upgrade logic
        pass

    async def downgrade(self, session: AsyncSession) -> None:
        """Reverse the migration."""
        # TODO: Implement downgrade logic
        pass
'''

    # Write migration file
    migrations_dir = "backend/database/migrations"
    os.makedirs(migrations_dir, exist_ok=True)

    filepath = os.path.join(migrations_dir, filename)
    with open(filepath, "w") as f:
        f.write(template)

    click.echo(f"✓ Created migration: {filepath}")


if __name__ == "__main__":
    cli()