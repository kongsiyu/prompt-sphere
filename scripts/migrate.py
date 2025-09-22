#!/usr/bin/env python3
"""Main migration CLI script."""

import sys
from pathlib import Path

# Add backend to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from database.migrate import cli

if __name__ == "__main__":
    cli()