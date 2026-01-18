#!/usr/bin/env python3
"""Development server startup script."""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the development server."""
    print("=" * 70)
    print("Starting Transcription Engine Development Server")
    print("=" * 70)
    print()
    
    # Check if we're in the right directory
    if not Path("backend/app/main.py").exists():
        print("ERROR: Please run this script from the project root directory")
        return 1
    
    # Check if virtual environment exists
    venv_python = Path("backend/venv/Scripts/python.exe")
    if not venv_python.exists():
        print("ERROR: Virtual environment not found!")
        print("Please run: .\setup_manual.ps1 first")
        return 1
    
    # Check if .env exists
    if not Path(".env").exists():
        print("WARNING: .env file not found. Creating basic one...")
        create_basic_env()
    
    # Change to backend directory
    os.chdir("backend")
    
    # Set environment variables
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd())
    
    print("Starting FastAPI server...")
    print("API will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        # Start uvicorn
        subprocess.run(
            [str(venv_python), "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            env=env,
            check=True
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Server failed to start: {e}")
        return 1

def create_basic_env():
    """Create a basic .env file for development."""
    env_content = """# Basic Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database (using SQLite for easy setup)
DATABASE_URL=sqlite+aiosqlite:///./transcription.db

# Redis (optional for development - set to localhost if running Redis)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Storage
STORAGE_TYPE=local
UPLOAD_DIR=./uploads
PROCESSED_DIR=./processed

# Security
SECRET_KEY=dev-secret-key-change-in-production
"""
    with open(".env", "w") as f:
        f.write(env_content)
    print("Created basic .env file")

if __name__ == "__main__":
    sys.exit(main())
