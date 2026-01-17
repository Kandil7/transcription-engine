# Testing Guide

Comprehensive testing strategy and implementation for the SoutiAI Transcription Engine.

## Overview

The testing strategy follows a pyramid approach with comprehensive coverage across unit, integration, and end-to-end tests. All tests are automated and run in CI/CD pipelines.

## Testing Pyramid

```
E2E Tests (5-10%)
├── API Integration Tests
├── UI Integration Tests

Integration Tests (20-25%)
├── Service Integration
├── Database Integration
├── External API Integration

Unit Tests (70-75%)
├── Service Layer Tests
├── Utility Function Tests
├── Model Validation Tests
├── Configuration Tests
```

## Test Structure

### Directory Structure

```
backend/tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures and configuration
├── test_health.py                # Health check tests
├── test_rag.py                   # RAG service tests
├── test_streaming.py             # Real-time streaming tests
├── test_text_utils.py            # Text processing utilities
├── test_translation_summarization.py  # NLP service tests
├── test_voice_analytics.py       # Voice analytics tests
├── integration/                  # Integration tests
│   ├── __init__.py
│   ├── test_api_endpoints.py     # API endpoint integration
│   ├── test_database.py          # Database integration
│   ├── test_queue_processing.py  # Celery queue tests
│   └── test_external_services.py # External API tests
├── e2e/                         # End-to-end tests
│   ├── __init__.py
│   ├── test_full_workflow.py     # Complete transcription workflow
│   └── test_user_journey.py      # User experience tests
└── fixtures/                     # Test data and mocks
    ├── sample_audio.wav
    ├── sample_video.mp4
    ├── test_transcripts.json
    └── mock_responses.json
```

### Test Categories

#### 1. Unit Tests

**Purpose**: Test individual functions and classes in isolation

**Coverage Areas**:
- Service methods
- Utility functions
- Data validation
- Error handling
- Edge cases

**Example**:
```python
# tests/test_transcription_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.transcription_service import TranscriptionService

class TestTranscriptionService:

    @pytest.fixture
    def service(self):
        return TranscriptionService()

    def test_detect_device_cuda_available(self, service):
        """Test device detection when CUDA is available."""
        with patch('torch.cuda.is_available', return_value=True):
            device = service._detect_device()
            assert device == "cuda"

    def test_detect_device_cpu_fallback(self, service):
        """Test device detection fallback to CPU."""
        with patch('torch.cuda.is_available', return_value=False):
            device = service._detect_device()
            assert device == "cpu"

    @patch('app.services.transcription_service.WhisperModel')
    def test_load_model_success(self, mock_whisper, service):
        """Test successful model loading."""
        mock_model = Mock()
        mock_whisper.return_value = mock_model

        await service.load_model()

        assert service.model_loaded is True
        assert service.model == mock_model
        mock_whisper.assert_called_once()

    @patch('app.services.transcription_service.WhisperModel')
    def test_load_model_failure(self, mock_whisper, service):
        """Test model loading failure."""
        mock_whisper.side_effect = Exception("Model load failed")

        with pytest.raises(Exception, match="Model load failed"):
            await service.load_model()

        assert service.model_loaded is False
```

#### 2. Integration Tests

**Purpose**: Test interactions between components

**Coverage Areas**:
- API endpoints with database
- Service-to-service communication
- External API integrations
- Message queue processing

**Example**:
```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

class TestAPIEndpoints:

    @pytest.mark.asyncio
    async def test_upload_file_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful file upload."""
        # Prepare test file
        test_file = create_test_audio_file()

        # Make request
        response = await client.post(
            "/api/v1/upload/file",
            files={"file": ("test.wav", test_file, "audio/wav")},
            data={
                "language": "ar",
                "enable_translation": "true",
                "target_language": "en"
            }
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

        # Verify database state
        job = await db_session.get(Job, data["job_id"])
        assert job is not None
        assert job.language == "ar"
        assert job.enable_translation is True

    @pytest.mark.asyncio
    async def test_get_job_status(self, client: AsyncClient, sample_job):
        """Test job status retrieval."""
        response = await client.get(f"/api/v1/jobs/{sample_job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_job.id)
        assert data["status"] in ["pending", "processing", "completed", "failed"]
```

#### 3. End-to-End Tests

**Purpose**: Test complete user workflows

**Coverage Areas**:
- File upload to results
- Real-time streaming
- Error recovery
- Performance validation

**Example**:
```python
# tests/e2e/test_full_workflow.py
import pytest
from pathlib import Path

class TestFullWorkflow:

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_transcription_workflow(self, client, test_audio_file):
        """Test complete transcription workflow from upload to results."""
        # Step 1: Upload file
        upload_response = await client.post(
            "/api/v1/upload/file",
            files={"file": ("test.wav", test_audio_file, "audio/wav")},
            data={"language": "ar", "enable_translation": "true"}
        )
        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]

        # Step 2: Wait for completion (with timeout)
        max_attempts = 60  # 5 minutes max
        for attempt in range(max_attempts):
            status_response = await client.get(f"/api/v1/jobs/{job_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            if status_data["status"] == "completed":
                break
            elif status_data["status"] == "failed":
                pytest.fail(f"Job failed: {status_data.get('message', 'Unknown error')}")

            await asyncio.sleep(5)  # Wait 5 seconds

        # Step 3: Verify results
        results_response = await client.get(f"/api/v1/jobs/{job_id}/results")
        assert results_response.status_code == 200

        results = results_response.json()
        assert "transcript" in results
        assert "translation" in results
        assert len(results["transcript"]) > 0
        assert len(results["translation"]) > 0
```

## Test Configuration

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest.ini_options]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    asyncio: marks tests as async
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.db.session import get_db
from app.config import get_config

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """Create test database."""
    config = get_config()
    test_db_url = config.database_url.replace("transcription_db", "transcription_test")

    engine = create_async_engine(test_db_url, echo=False)

    # Create tables
    async with engine.begin() as conn:
        # Import all models here to create tables
        from app.db.models import job  # noqa
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(test_db):
    """Provide database session for tests."""
    async with AsyncSession(test_db) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client(db_session):
    """Provide test client with database session."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()

@pytest.fixture
def sample_job(db_session):
    """Create sample job for testing."""
    job = Job(
        id="test-job-123",
        filename="test.wav",
        file_path="/tmp/test.wav",
        file_size=1024,
        duration=10.5,
        language="ar",
        status="pending"
    )
    db_session.add(job)
    db_session.commit()
    return job
```

## Test Data Management

### Test Fixtures and Mocks

```python
# tests/fixtures/audio.py
import numpy as np
from pathlib import Path

def create_test_audio_file(duration=5.0, sample_rate=16000):
    """Create a test audio file with speech-like content."""
    # Generate white noise with some structure
    samples = int(duration * sample_rate)
    audio_data = np.random.normal(0, 0.1, samples).astype(np.float32)

    # Add some "speech-like" patterns (simplified)
    for i in range(0, samples, sample_rate // 2):  # Every 0.5 seconds
        if np.random.random() > 0.3:  # 70% speech probability
            speech_length = int(0.3 * sample_rate)  # 0.3 second speech
            start = min(i, samples - speech_length)
            end = start + speech_length
            # Add some energy variation
            audio_data[start:end] *= np.random.uniform(1.5, 3.0)

    # Save to temporary file
    import io
    import wave

    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        # Convert to 16-bit PCM
        audio_int16 = (audio_data * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())

    buffer.seek(0)
    return buffer

def mock_whisper_transcription():
    """Mock Whisper transcription response."""
    return {
        "text": "هذا نص تجريبي باللغة العربية",
        "segments": [
            {
                "start": 0.0,
                "end": 2.5,
                "text": "هذا نص تجريبي",
                "confidence": 0.95
            },
            {
                "start": 2.5,
                "end": 5.0,
                "text": "باللغة العربية",
                "confidence": 0.92
            }
        ],
        "language": "ar",
        "language_probability": 0.98
    }
```

### Mock Services

```python
# tests/mocks/__init__.py
from unittest.mock import Mock, MagicMock
import pytest

@pytest.fixture
def mock_whisper_service():
    """Mock Whisper transcription service."""
    mock_service = Mock()
    mock_service.transcribe_audio.return_value = {
        "transcript": "Mock transcription result",
        "segments": [{"start": 0, "end": 1, "text": "Mock", "confidence": 0.9}],
        "stats": {"processing_time": 1.0}
    }
    return mock_service

@pytest.fixture
def mock_translation_service():
    """Mock translation service."""
    mock_service = Mock()
    mock_service.translate.return_value = "Mock translation result"
    return mock_service

@pytest.fixture
def mock_rag_service():
    """Mock RAG service."""
    mock_service = Mock()
    mock_service.enhance_transcript.return_value = "Enhanced transcript"
    mock_service.ask_question.return_value = {
        "answer": "Mock answer",
        "sources": [],
        "confidence": 0.8
    }
    return mock_service
```

## Performance Testing

### Benchmark Tests

```python
# tests/performance/test_transcription_performance.py
import pytest
import time
import psutil
from pathlib import Path

class TestTranscriptionPerformance:

    @pytest.mark.performance
    @pytest.mark.parametrize("audio_duration", [30, 60, 120])  # seconds
    def test_transcription_speed(self, audio_duration):
        """Test transcription speed for different audio lengths."""
        # Generate test audio
        test_audio = create_test_audio_file(duration=audio_duration)

        # Measure transcription time
        start_time = time.time()
        result = transcribe_audio(test_audio)
        end_time = time.time()

        processing_time = end_time - start_time

        # Assert performance requirements
        if audio_duration == 30:
            assert processing_time < 10  # 30s audio should process in <10s
        elif audio_duration == 60:
            assert processing_time < 20  # 1min audio should process in <20s
        elif audio_duration == 120:
            assert processing_time < 45  # 2min audio should process in <45s

        # Log performance metrics
        print(f"Audio duration: {audio_duration}s")
        print(f"Processing time: {processing_time:.2f}s")
        print(f"Speed ratio: {audio_duration/processing_time:.2f}x")

    @pytest.mark.performance
    def test_memory_usage(self):
        """Test memory usage during transcription."""
        process = psutil.Process()

        # Get initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Perform transcription
        test_audio = create_test_audio_file(duration=30)
        transcribe_audio(test_audio)

        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_increase = final_memory - initial_memory

        # Assert memory usage is reasonable
        assert memory_increase < 500  # Less than 500MB increase

        print(f"Memory increase: {memory_increase:.2f}MB")

    @pytest.mark.performance
    def test_concurrent_transcriptions(self):
        """Test performance with concurrent transcriptions."""
        import concurrent.futures

        # Create multiple test files
        test_files = [create_test_audio_file(duration=10) for _ in range(5)]

        # Time concurrent processing
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(transcribe_audio, audio) for audio in test_files]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # Assert all transcriptions completed
        assert len(results) == 5
        assert all(result["transcript"] for result in results)

        # Assert reasonable total time (should be faster than sequential)
        sequential_estimate = 5 * 8  # 5 files * ~8s each
        assert total_time < sequential_estimate

        print(f"Concurrent processing time: {total_time:.2f}s")
```

### Load Testing

```python
# tests/load/test_load.py
import locust
from locust import HttpUser, task, between

class TranscriptionUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def upload_and_transcribe(self):
        # Create test file
        files = {"file": ("test.wav", create_test_audio_file(), "audio/wav")}
        data = {"language": "ar"}

        # Upload file
        response = self.client.post("/api/v1/upload/file", files=files, data=data)
        if response.status_code == 200:
            job_id = response.json()["job_id"]

            # Poll for completion
            for _ in range(60):  # Max 5 minutes
                status_response = self.client.get(f"/api/v1/jobs/{job_id}")
                if status_response.json()["status"] == "completed":
                    break
                time.sleep(5)

# Run with: locust -f tests/load/test_load.py --host=http://localhost:8000
```

## Security Testing

### Authentication Tests

```python
# tests/security/test_authentication.py
import pytest
from jose import jwt

class TestAuthentication:

    def test_valid_jwt_token(self, client):
        """Test access with valid JWT token."""
        # Create valid token
        token = create_test_jwt_token()

        response = client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

    def test_invalid_jwt_token(self, client):
        """Test access with invalid JWT token."""
        response = client.get(
            "/api/v1/jobs",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    def test_missing_authentication(self, client):
        """Test access without authentication."""
        response = client.get("/api/v1/jobs")

        assert response.status_code == 401

    def test_expired_token(self, client):
        """Test access with expired token."""
        expired_token = create_expired_jwt_token()

        response = client.get(
            "/api/v1/jobs",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
```

### Input Validation Tests

```python
# tests/security/test_input_validation.py
class TestInputValidation:

    def test_file_size_limit(self, client):
        """Test file size limit enforcement."""
        # Create file larger than limit
        large_file = create_large_test_file(size_mb=600)  # 600MB

        response = client.post(
            "/api/v1/upload/file",
            files={"file": ("large.wav", large_file, "audio/wav")}
        )

        assert response.status_code == 413  # Payload Too Large

    def test_malicious_file_upload(self, client):
        """Test protection against malicious file uploads."""
        # Create file with malicious content
        malicious_file = create_malicious_file()

        response = client.post(
            "/api/v1/upload/file",
            files={"file": ("malicious.exe", malicious_file, "application/octet-stream")}
        )

        assert response.status_code == 400

    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection."""
        malicious_input = "'; DROP TABLE jobs; --"

        response = client.get(f"/api/v1/jobs/{malicious_input}")

        # Should not execute SQL injection
        assert response.status_code in [400, 404]  # Bad request or not found
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('**/requirements*.txt') }}

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linting
      run: |
        cd backend
        flake8 app/ tests/
        black --check app/ tests/

    - name: Run tests
      run: |
        cd backend
        pytest tests/ -v --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
```

### Code Quality Checks

```yaml
# Code quality checks
- name: Security scan
  uses: github/super-linter/slim@v5
  env:
    DEFAULT_BRANCH: main
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

- name: Dependency vulnerability scan
  uses: snyk/actions/python@master
  env:
    SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
```

## Test Reporting

### Coverage Reports

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

### Test Results

```bash
# JUnit XML output for CI
pytest tests/ --junitxml=test-results.xml

# Allure reports
pytest tests/ --alluredir=allure-results
allure serve allure-results
```

## Test Data Management

### Test Database

```python
# tests/conftest.py
@pytest.fixture(scope="session")
def test_db_url():
    """Create test database URL."""
    return os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost/test_db")

@pytest.fixture(scope="session")
async def test_db_engine(test_db_url):
    """Create test database engine."""
    engine = create_async_engine(test_db_url, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Cleanup Strategies

```python
@pytest.fixture(autouse=True)
async def cleanup_files():
    """Clean up test files after each test."""
    # Setup - nothing to do

    yield

    # Cleanup
    test_files = Path("./test_files").glob("*")
    for file_path in test_files:
        if file_path.exists():
            file_path.unlink()

@pytest.fixture(scope="session", autouse=True)
async def cleanup_database(test_db_engine):
    """Clean up database after test session."""
    yield

    # Clean up any remaining test data
    async with test_db_engine.begin() as conn:
        # Delete test data
        await conn.execute(text("DELETE FROM jobs WHERE id LIKE 'test-%'"))
```

## Performance Benchmarks

### Baseline Metrics

```python
# tests/benchmarks/baseline.py
BASELINE_METRICS = {
    "transcription_speed": {
        "30s_audio": 8.5,  # seconds
        "60s_audio": 15.2,
        "120s_audio": 28.7
    },
    "memory_usage": {
        "peak_mb": 450,
        "average_mb": 280
    },
    "accuracy": {
        "ar_wer": 0.12,  # Word Error Rate
        "en_wer": 0.08
    }
}

def assert_performance_baseline(metric_name, actual_value, tolerance=0.1):
    """Assert that performance meets baseline requirements."""
    baseline = BASELINE_METRICS.get(metric_name)
    if baseline is None:
        pytest.skip(f"No baseline defined for {metric_name}")

    # Allow tolerance (e.g., 10% worse than baseline)
    max_allowed = baseline * (1 + tolerance)

    assert actual_value <= max_allowed, (
        f"Performance regression: {metric_name} = {actual_value}, "
        f"baseline = {baseline}, max_allowed = {max_allowed}"
    )
```

### Regression Detection

```python
# tests/regression/test_regression.py
import json
from pathlib import Path

class TestRegression:

    def test_no_accuracy_regression(self):
        """Test that accuracy hasn't regressed from previous versions."""
        # Load previous test results
        history_file = Path("test_history.json")
        if not history_file.exists():
            pytest.skip("No test history available")

        with open(history_file) as f:
            history = json.load(f)

        # Compare current accuracy with historical average
        current_accuracy = get_current_accuracy()
        historical_avg = history.get("average_accuracy", current_accuracy)

        # Allow small regression tolerance
        assert current_accuracy >= historical_avg * 0.95, (
            f"Accuracy regression: current={current_accuracy:.3f}, "
            f"historical_avg={historical_avg:.3f}"
        )
```

This comprehensive testing strategy ensures the Transcription Engine maintains high quality, performance, and reliability across all features and use cases.</content>
</xai:function_call">TESTING.md