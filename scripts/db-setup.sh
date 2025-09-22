#!/bin/bash
"""Bash wrapper for database setup commands."""

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/db-setup.py"

# Ensure the Python script is executable
chmod +x "$PYTHON_SCRIPT"

# Function to show usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  init     Initialize the database with all tables and migrations"
    echo "  reset    Reset the database (drop and recreate all tables)"
    echo "  check    Check database connection and migration status"
    echo ""
    echo "Examples:"
    echo "  $0 init    # Set up database for first time"
    echo "  $0 reset   # Reset database (will prompt for confirmation)"
    echo "  $0 check   # Check database status"
    exit 1
}

# Check if at least one argument is provided
if [ $# -eq 0 ]; then
    usage
fi

# Execute the Python setup script with all arguments
python3 "$PYTHON_SCRIPT" "$@"