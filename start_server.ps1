# Start Transcription Engine Server
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Transcription Engine Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:DATABASE_URL = "sqlite+aiosqlite:///./transcription.db"
$env:STORAGE_TYPE = "local"
$env:UPLOAD_DIR = ".\uploads"
$env:PROCESSED_DIR = ".\processed"
$env:LOG_LEVEL = "INFO"
$env:ENVIRONMENT = "development"
$env:DEBUG = "true"

# Change to backend directory
Set-Location backend

# Activate virtual environment and start server
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Health Check: http://localhost:8000/health" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

& ..\backend\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
