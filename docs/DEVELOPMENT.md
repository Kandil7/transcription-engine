# Development Guide

Complete development setup, contribution guidelines, and coding standards for the SoutiAI Transcription Engine.

## 🚀 Quick Start Development

### Prerequisites

**System Requirements**:
- **OS**: Linux/macOS/Windows (WSL2 recommended for Windows)
- **Python**: 3.11+ (3.11 recommended)
- **Node.js**: 18+ (20+ recommended)
- **Docker**: 24+ with Docker Compose
- **Git**: 2.30+

**Hardware Requirements**:
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB free space
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional, for faster development)

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/Kandil7/transcription-engine.git
cd transcription-engine

# Copy environment template
cp .env.example .env.dev

# Edit environment variables
nano .env.dev
```

### 2. Backend Development Setup

```bash
# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Install development dependencies
pip install -r backend/requirements-dev.txt

# Run database migrations
cd backend
alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Development Setup

```bash
# Install Node.js dependencies
npm install

# Start development server
npm start

# Frontend will be available at http://localhost:3000
```

### 4. Full Stack Development

```bash
# Start complete development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

## 🏗️ Project Structure

```
transcription-engine/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration management
│   │   ├── api/v1/            # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── api.py         # Main API router
│   │   │   └── endpoints/     # Endpoint modules
│   │   │       ├── upload.py
│   │   │       ├── jobs.py
│   │   │       ├── websocket.py
│   │   │       ├── streaming.py
│   │   │       ├── qa.py
│   │   │       └── voice_analytics.py
│   │   ├── services/          # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── transcription_service.py
│   │   │   ├── translation_service.py
│   │   │   ├── summarization_service.py
│   │   │   ├── rag_service.py
│   │   │   ├── voice_analytics_service.py
│   │   │   ├── streaming_service.py
│   │   │   ├── dialect_detection_service.py
│   │   │   ├── websocket_manager.py
│   │   │   └── job_service.py
│   │   ├── db/                # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── session.py
│   │   │   └── models/
│   │   │       ├── __init__.py
│   │   │       └── job.py
│   │   ├── tasks/             # Celery tasks
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   └── transcription_tasks.py
│   │   ├── utils/             # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── audio.py
│   │   │   └── text.py
│   │   ├── core/              # Core functionality
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── logging.py
│   │   │   ├── monitoring.py
│   │   │   ├── security.py
│   │   │   └── storage.py
│   │   └── models/            # Pydantic models
│   │       ├── __init__.py
│   │       └── job.py
│   ├── scripts/               # Utility scripts
│   │   ├── prepare_egyptian_dataset.py
│   │   ├── finetune_whisper_egyptian.py
│   │   ├── train_dialect_detector.py
│   │   └── evaluate_egyptian_accuracy.py
│   ├── tests/                 # Test suite
│   │   ├── __init__.py
│   │   ├── test_health.py
│   │   ├── test_rag.py
│   │   ├── test_streaming.py
│   │   ├── test_text_utils.py
│   │   ├── test_translation_summarization.py
│   │   └── test_voice_analytics.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/                  # React frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js
│   │   ├── index.js
│   │   ├── index.css
│   │   ├── components/        # Reusable components
│   │   │   ├── Header.js
│   │   │   ├── Timeline.js
│   │   │   ├── SearchAndFilter.js
│   │   │   ├── InteractiveTranscript.js
│   │   │   └── AnalyticsDashboard.js
│   │   ├── pages/             # Page components
│   │   │   ├── Dashboard.js
│   │   │   ├── Upload.js
│   │   │   ├── JobDetails.js
│   │   │   └── Streaming.js
│   │   └── services/          # API services
│   │     └── api.js
│   ├── Dockerfile
│   ├── package.json
│   └── nginx.conf
├── monitoring/                # Observability stack
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── rules.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   ├── alertmanager/
│   │   └── alertmanager.yml
│   └── traefik/
│     └── traefik.yml
├── scripts/                   # Deployment scripts
│   └── deploy.sh
├── docs/                      # Documentation
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── EGYPTIAN_DIALECT_FINETUNING.md
│   └── PRODUCTION_DEPLOYMENT.md
├── docker-compose.yml         # Production compose
├── docker-compose.dev.yml     # Development compose
├── docker-compose.prod.yml    # Production compose
├── .env.example              # Environment template
├── .gitignore
├── README.md
└── requirements-dev.txt
```

## 🔧 Development Workflow

### Git Workflow

We follow a feature branch workflow:

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add your feature description"

# Push branch
git push origin feature/your-feature-name

# Create pull request
# ... PR review process ...

# Merge to main
git checkout main
git pull origin main
```

### Commit Message Convention

We follow conventional commits:

```bash
# Format: type(scope): description

# Examples:
feat: add Egyptian dialect detection
fix: resolve audio processing memory leak
docs: update API reference
refactor: simplify transcription service
test: add integration tests for streaming
chore: update dependencies

# Types:
# feat: new feature
# fix: bug fix
# docs: documentation
# style: formatting
# refactor: code restructuring
# test: adding tests
# chore: maintenance
```

### Code Review Process

1. **Create PR**: Push feature branch and create pull request
2. **Automated Checks**: CI/CD runs tests, linting, security scans
3. **Peer Review**: At least one maintainer review required
4. **Testing**: All tests pass, no regressions
5. **Merge**: Squash merge with descriptive commit message

## 🧪 Testing

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Test Structure

```python
# Unit tests
def test_transcription_service():
    # Test individual functions

# Integration tests
def test_full_transcription_pipeline():
    # Test end-to-end flow

# API tests
def test_upload_endpoint():
    # Test API endpoints

# Performance tests
def test_transcription_speed():
    # Test performance benchmarks
```

### Test Coverage Requirements

- **Unit Tests**: 80%+ coverage
- **Integration Tests**: All major workflows
- **API Tests**: All endpoints with error cases
- **Performance Tests**: Benchmarks for all profiles

## 🎯 Coding Standards

### Python Standards

**PEP 8 Compliance**:
```python
# Good
def process_audio(file_path: str, language: str = "ar") -> Dict[str, Any]:
    """Process audio file for transcription.

    Args:
        file_path: Path to audio file
        language: Language code

    Returns:
        Dictionary with processing results
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    # Function body
    result = {
        "status": "success",
        "language": language,
        "duration": get_audio_duration(file_path)
    }

    return result

# Bad - violates PEP 8
def processaudio(filepath,lang="ar"):
    if not os.path.exists(filepath):raise FileNotFoundError("file not found")
    result={"status":"success","language":lang}
    return result
```

**Type Hints**:
```python
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel

class JobCreate(BaseModel):
    filename: str
    language: str = "ar"
    enable_translation: bool = True

def transcribe_audio(
    job_id: str,
    audio_path: str,
    language: str = "ar",
    progress_callback: Optional[Callable[[float], None]] = None
) -> Tuple[str, List[Dict], ProcessingStats]:
    # Function implementation
```

**Error Handling**:
```python
class TranscriptionError(Exception):
    """Base exception for transcription errors."""
    pass

class ModelLoadError(TranscriptionError):
    """Raised when ML model loading fails."""
    pass

def load_whisper_model(model_size: str) -> WhisperModel:
    """Load Whisper model with error handling."""
    try:
        model = WhisperModel(model_size)
        logger.info(f"Loaded Whisper model: {model_size}")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_size}: {e}")
        raise ModelLoadError(f"Model loading failed: {e}") from e
```

### JavaScript/React Standards

**ES6+ Features**:
```javascript
// Good - modern JavaScript
const processFile = async (file) => {
  try {
    const result = await uploadFile(file);
    setUploadStatus('success');
    return result;
  } catch (error) {
    setUploadStatus('error');
    throw error;
  }
};

// Bad - old JavaScript
function processFile(file) {
  return uploadFile(file).then(function(result) {
    setUploadStatus('success');
    return result;
  }).catch(function(error) {
    setUploadStatus('error');
    throw error;
  });
}
```

**Component Structure**:
```javascript
// Good - functional component with hooks
import React, { useState, useEffect } from 'react';
import { useSnackbar } from 'notistack';

const FileUpload = ({ onUpload }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const { enqueueSnackbar } = useSnackbar();

  const handleUpload = async () => {
    if (!file) {
      enqueueSnackbar('Please select a file', { variant: 'warning' });
      return;
    }

    setUploading(true);
    try {
      await onUpload(file);
      enqueueSnackbar('Upload successful', { variant: 'success' });
    } catch (error) {
      enqueueSnackbar('Upload failed', { variant: 'error' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
        accept="audio/*,video/*"
      />
      <button onClick={handleUpload} disabled={uploading}>
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
    </div>
  );
};

export default FileUpload;
```

## 🔒 Security Standards

### Input Validation

```python
# Backend validation
from pydantic import BaseModel, validator
import re

class JobCreate(BaseModel):
    filename: str

    @validator('filename')
    def validate_filename(cls, v):
        if not v or len(v) > 255:
            raise ValueError('Invalid filename length')

        # Prevent path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename characters')

        return v

# Frontend validation
const validateFile = (file) => {
  const maxSize = 500 * 1024 * 1024; // 500MB
  const allowedTypes = ['audio/', 'video/'];

  if (file.size > maxSize) {
    throw new Error('File too large');
  }

  if (!allowedTypes.some(type => file.type.startsWith(type))) {
    throw new Error('Invalid file type');
  }

  return true;
};
```

### Authentication & Authorization

```python
# JWT token validation
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

### Secure Configuration

```bash
# Environment variables (never commit secrets)
export DATABASE_URL="postgresql://user:password@localhost/db"
export JWT_SECRET_KEY="your-256-bit-secret"
export MINIO_ACCESS_KEY="your-access-key"
export OPENAI_API_KEY="your-openai-key"

# Use .env files for local development
# Never commit .env files to git
echo ".env*" >> .gitignore
```

## 🔍 Debugging & Troubleshooting

### Backend Debugging

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()

# Profile performance
import cProfile
cProfile.run('your_function()')

# Memory profiling
from memory_profiler import profile

@profile
def process_large_file():
    # Function to profile
```

### Frontend Debugging

```javascript
// React DevTools
// Install React DevTools browser extension

// Console logging
console.log('Debug info:', { variable, state, props });

// Breakpoints
debugger; // Add to code for browser debugging

// Performance monitoring
React.useEffect(() => {
  const start = performance.now();
  // Your code
  const end = performance.now();
  console.log(`Operation took ${end - start} milliseconds`);
}, [dependencies]);
```

### Docker Debugging

```bash
# View container logs
docker-compose logs -f api

# Execute commands in running container
docker-compose exec api bash

# Debug with volume mounts
docker run -it --rm \
  -v $(pwd):/app \
  -p 8000:8000 \
  transcription-engine:latest bash
```

## 🚀 Performance Optimization

### Backend Optimization

```python
# Async processing
async def process_job_async(job_id: str):
    # Use async/await for I/O operations
    audio_data = await load_audio_async(file_path)
    transcript = await transcribe_async(audio_data)
    return transcript

# Memory management
@contextmanager
def gpu_memory_manager():
    try:
        torch.cuda.empty_cache()
        yield
    finally:
        torch.cuda.empty_cache()

# Caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_translation_cache_key(text: str, source: str, target: str) -> str:
    return f"{hash(text)}:{source}:{target}"
```

### Frontend Optimization

```javascript
// React.memo for component memoization
const TranscriptSegment = React.memo(({ segment, onClick }) => {
  return (
    <div onClick={() => onClick(segment.id)}>
      <span>{segment.text}</span>
      <span>{segment.timestamp}</span>
    </div>
  );
});

// useMemo for expensive calculations
const processedSegments = React.useMemo(() => {
  return segments.map(segment => ({
    ...segment,
    displayText: highlightSearchTerm(segment.text, searchTerm)
  }));
}, [segments, searchTerm]);

// Code splitting
const StreamingPage = lazy(() => import('./pages/Streaming'));
const JobDetailsPage = lazy(() => import('./pages/JobDetails'));
```

## 📦 Deployment & CI/CD

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    - name: Run tests
      run: |
        cd backend
        pytest tests/ --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - name: Build Docker images
      run: |
        docker build -t transcription-engine:latest ./backend
        docker build -t transcription-frontend:latest ./frontend

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    # Staging deployment steps

  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    # Production deployment steps
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# .pre-commit-config.yaml
repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
  - id: trailing-whitespace
  - id: end-of-file-fixer
  - id: check-yaml
  - id: check-added-large-files

- repo: https://github.com/psf/black
  rev: 23.3.0
  hooks:
  - id: black
    language_version: python3.11

- repo: https://github.com/pycqa/flake8
  rev: 6.0.0
  hooks:
  - id: flake8
    args: [--max-line-length=100, --extend-ignore=E203,W503]
```

## 🤝 Contributing Guidelines

### Getting Started

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/your-username/transcription-engine.git`
3. **Create feature branch**: `git checkout -b feature/your-feature`
4. **Make changes** following coding standards
5. **Add tests** for new functionality
6. **Update documentation** if needed
7. **Commit changes** with conventional commit messages
8. **Push branch** and create pull request

### Code of Conduct

- **Respect**: Be respectful to all contributors
- **Collaboration**: Work together constructively
- **Quality**: Maintain high code quality standards
- **Documentation**: Keep documentation up to date
- **Testing**: Ensure all tests pass

### Issue Reporting

**Bug Reports**:
- Use bug report template
- Include steps to reproduce
- Provide system information
- Attach relevant logs

**Feature Requests**:
- Use feature request template
- Describe use case and benefits
- Provide implementation suggestions

**Questions**:
- Check documentation first
- Use discussions for questions
- Provide context and examples

### Release Process

1. **Version Bumping**: Update version in `pyproject.toml` and `package.json`
2. **Changelog**: Update `CHANGELOG.md` with changes
3. **Testing**: Full test suite passes
4. **Documentation**: Updated for new features
5. **Release**: Create GitHub release with tag
6. **Deployment**: Automated deployment to production

## 📚 Additional Resources

### Learning Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/
- **Kubernetes Documentation**: https://kubernetes.io/docs/

### Community

- **Discord**: https://discord.gg/souti-ai
- **GitHub Discussions**: For questions and discussions
- **Issues**: For bug reports and feature requests
- **Pull Requests**: For code contributions

### Support

- **Enterprise Support**: enterprise@souti.ai
- **Community Support**: GitHub issues and discussions
- **Documentation**: Comprehensive docs in `/docs` directory

Remember: This is an enterprise-grade AI system. All contributions must maintain the highest standards of quality, security, and performance.</content>
</xai:function_call">DEVELOPMENT.md