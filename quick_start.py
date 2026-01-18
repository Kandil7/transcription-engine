#!/usr/bin/env python3
"""Quick start script to validate and demonstrate the Transcription Engine setup."""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    """Run quick validation."""
    print("=" * 70)
    print("SoutiAI Transcription Engine - Quick Start Validation")
    print("=" * 70)
    print()
    
    # Set UTF-8 encoding for Windows
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # Check Python version
    print(f"[OK] Python Version: {sys.version.split()[0]}")
    
    # Check if we can import basic modules
    try:
        import os
        print("[OK] OS module available")
    except ImportError as e:
        print(f"[ERROR] OS module error: {e}")
        return 1
    
    # Check directory structure
    print("\n[DIRS] Checking Project Structure:")
    required_dirs = [
        "backend/app",
        "backend/app/api",
        "backend/app/services",
        "backend/app/db",
        "frontend/src",
        "docs",
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [MISSING] {dir_path}")
            all_exist = False
    
    # Check key files
    print("\n[FILES] Checking Key Files:")
    key_files = [
        "backend/app/main.py",
        "backend/app/config.py",
        "backend/app/api/v1/api.py",
        "backend/alembic.ini",
        "backend/alembic/versions/001_initial_schema.py",
        "backend/app/utils/download.py",
        "backend/app/core/validation.py",
        "README.md",
    ]
    
    for file_path in key_files:
        if Path(file_path).exists():
            print(f"  [OK] {file_path}")
        else:
            print(f"  [MISSING] {file_path}")
            all_exist = False
    
    print("\n" + "=" * 70)
    if all_exist:
        print("[SUCCESS] Project structure is complete!")
        print("\n[NEXT STEPS]")
        print("  1. Install dependencies: pip install -r backend/requirements.txt")
        print("  2. Set up environment variables (see env-example.txt)")
        print("  3. Run database migrations: cd backend && alembic upgrade head")
        print("  4. Start the application: python -m uvicorn app.main:app --reload")
        print("\n  Or use Docker:")
        print("  docker-compose up -d")
        return 0
    else:
        print("⚠️  Some files or directories are missing.")
        print("   Please check the project structure.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
