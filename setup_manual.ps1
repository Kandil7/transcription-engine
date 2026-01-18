# Manual Setup Script for Transcription Engine
# This script sets up the project for manual execution

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Transcription Engine - Manual Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create virtual environment
Write-Host "[1/4] Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "backend\venv") {
    Write-Host "  Virtual environment already exists, skipping..." -ForegroundColor Gray
} else {
    python -m venv backend\venv
    Write-Host "  Virtual environment created!" -ForegroundColor Green
}

# Step 2: Activate virtual environment and install dependencies
Write-Host "[2/4] Installing dependencies..." -ForegroundColor Yellow
Write-Host "  This may take several minutes..." -ForegroundColor Gray
& backend\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip --quiet
Write-Host "  Installing core dependencies (this may take a while)..." -ForegroundColor Gray

# Install minimal dependencies first for faster setup
python -m pip install fastapi uvicorn pydantic pydantic-settings structlog sqlalchemy asyncpg alembic redis httpx python-dotenv --quiet
Write-Host "  Core dependencies installed!" -ForegroundColor Green

# Step 3: Create .env file
Write-Host "[3/4] Setting up environment variables..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  .env file already exists, skipping..." -ForegroundColor Gray
} else {
    if (Test-Path "env-example.txt") {
        Copy-Item "env-example.txt" ".env"
        Write-Host "  Created .env from env-example.txt" -ForegroundColor Green
        Write-Host "  Please edit .env file with your configuration" -ForegroundColor Yellow
    } else {
        Write-Host "  Creating basic .env file..." -ForegroundColor Gray
        @"
# Basic Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Database (using SQLite for easy setup)
DATABASE_URL=sqlite+aiosqlite:///./transcription.db

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Storage
STORAGE_TYPE=local
UPLOAD_DIR=./uploads
PROCESSED_DIR=./processed

# Security
SECRET_KEY=dev-secret-key-change-in-production
"@ | Out-File -FilePath ".env" -Encoding utf8
        Write-Host "  Created basic .env file for development" -ForegroundColor Green
    }
}

# Step 4: Create required directories
Write-Host "[4/4] Creating required directories..." -ForegroundColor Yellow
$dirs = @("uploads", "processed", "backend\logs")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review and edit .env file if needed" -ForegroundColor White
Write-Host "  2. Run database migrations:" -ForegroundColor White
Write-Host "     cd backend" -ForegroundColor Gray
Write-Host "     ..\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "     alembic upgrade head" -ForegroundColor Gray
Write-Host "  3. Start the application:" -ForegroundColor White
Write-Host "     python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Gray
Write-Host ""
Write-Host "Or run: python start_dev.py" -ForegroundColor Cyan
Write-Host ""
