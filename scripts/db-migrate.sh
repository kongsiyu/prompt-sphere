#!/bin/bash
"""Bash wrapper for migration commands."""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/migrate.py"

# Ensure the Python script is executable
chmod +x "$PYTHON_SCRIPT"

# Function to show usage
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  up [--target VERSION]    Run pending migrations"
    echo "  down [--target VERSION]  Rollback migrations"
    echo "  down [--steps N]         Rollback N migrations"
    echo "  status                   Show migration status"
    echo "  validate                 Validate all migrations"
    echo "  create DESCRIPTION       Create a new migration"
    echo ""
    echo "Examples:"
    echo "  $0 up                              # Apply all pending migrations"
    echo "  $0 up --target 20250922_000003     # Migrate up to specific version"
    echo "  $0 down --steps 2                  # Rollback 2 migrations"
    echo "  $0 down --target 20250922_000001   # Rollback to specific version"
    echo "  $0 status                          # Show current status"
    echo "  $0 create \"Add user preferences\"   # Create new migration"
    exit 1
}

# Check if at least one argument is provided
if [ $# -eq 0 ]; then
    usage
fi

# Execute the Python migration script with all arguments
python3 "$PYTHON_SCRIPT" "$@"