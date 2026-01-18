#!/usr/bin/env python3
"""Run database migrations with proper environment setup."""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set SQLite as default if DATABASE_URL not set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./transcription.db"
    print("Using SQLite database (default)")
    print(f"Database will be created at: {Path('backend/transcription.db').absolute()}")
else:
    print(f"Using database: {os.environ['DATABASE_URL']}")

# Change to backend directory for alembic
os.chdir("backend")

# Import and run alembic
from alembic.config import Config
from alembic import command

def main():
    """Run migrations."""
    alembic_cfg = Config("alembic.ini")
    
    print("\nRunning database migrations...")
    try:
        command.upgrade(alembic_cfg, "head")
        print("\n[SUCCESS] Migrations completed successfully!")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
