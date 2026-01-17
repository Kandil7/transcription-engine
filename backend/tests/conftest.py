"""
Pytest configuration and fixtures for the transcription engine tests.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.db.session import get_db
from app.main import app
from app.db.models import Base


# Test database setup
@pytest.fixture(scope="session")
def test_db_url():
    """Generate test database URL."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine(test_db_url):
    """Create test database engine."""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with database session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# Audio file fixtures
@pytest.fixture
def sample_wav_data():
    """Create minimal valid WAV file data for testing."""
    # WAV header (44 bytes) + minimal audio data
    wav_header = (
        b'RIFF'  # ChunkID
        b'\x24\x08\x00\x00'  # ChunkSize
        b'WAVE'  # Format
        b'fmt '  # Subchunk1ID
        b'\x10\x00\x00\x00'  # Subchunk1Size
        b'\x01\x00'  # AudioFormat (PCM)
        b'\x01\x00'  # NumChannels
        b'\x80>\x00\x00'  # SampleRate (16000)
        b'\x00}\x00\x00'  # ByteRate
        b'\x02\x00'  # BlockAlign
        b'\x10\x00'  # BitsPerSample
        b'data'  # Subchunk2ID
        b'\x00\x08\x00\x00'  # Subchunk2Size
    )
    # Add some dummy audio data
    audio_data = b'\x00\x00' * 1024
    return wav_header + audio_data


@pytest.fixture
def temp_audio_file(sample_wav_data) -> Generator[Path, None, None]:
    """Create temporary audio file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        f.write(sample_wav_data)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


# Async fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def async_client(db_session):
    """Create async FastAPI test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    from httpx import AsyncClient
    async with AsyncClient(app=app, base_url="http://testserver") as async_client:
        yield async_client

    app.dependency_overrides.clear()


# Mock fixtures
@pytest.fixture
def mock_transcription_service():
    """Mock transcription service for testing."""
    class MockTranscriptionService:
        async def transcribe_audio(self, *args, **kwargs):
            return {
                "text": "Mock transcription result",
                "confidence": 0.95,
                "segments": [
                    {"start": 0.0, "end": 2.0, "text": "Mock", "confidence": 0.95},
                    {"start": 2.0, "end": 4.0, "text": "transcription", "confidence": 0.95},
                    {"start": 4.0, "end": 6.0, "text": "result", "confidence": 0.95}
                ]
            }

        async def transcribe_with_dialect_adaptation(self, *args, **kwargs):
            return (
                "Mock Arabic transcription result",
                [
                    {"start": 0.0, "end": 2.0, "text": "Mock Arabic", "confidence": 0.95},
                    {"start": 2.0, "end": 4.0, "text": "transcription", "confidence": 0.95},
                    {"start": 4.0, "end": 6.0, "text": "result", "confidence": 0.95}
                ],
                {"dialect": "cairo", "confidence": 0.88},
                {"dialect_info": {"detected": "cairo", "confidence": 0.88}}
            )

    return MockTranscriptionService()


@pytest.fixture
def mock_voice_analytics_service():
    """Mock voice analytics service for testing."""
    class MockVoiceAnalyticsService:
        async def analyze_audio(self, *args, **kwargs):
            return {
                "speaker_segments": [
                    {"speaker": "Speaker 1", "start": 0.0, "end": 3.0},
                    {"speaker": "Speaker 2", "start": 3.0, "end": 6.0}
                ],
                "emotion_analysis": {
                    "overall": "neutral",
                    "segments": [
                        {"start": 0.0, "end": 3.0, "emotion": "confident"},
                        {"start": 3.0, "end": 6.0, "emotion": "questioning"}
                    ]
                },
                "speech_rate": 150.5,
                "pause_patterns": {"total_pauses": 2, "avg_pause_length": 0.8}
            }

    return MockVoiceAnalyticsService()


@pytest.fixture
def mock_translation_service():
    """Mock translation service for testing."""
    class MockTranslationService:
        async def translate_text(self, text, target_lang="en"):
            translations = {
                "ar": f"English translation of: {text}",
                "en": f"Arabic translation of: {text}",
                "fr": f"English translation of: {text}"
            }
            return translations.get(target_lang, text)

    return MockTranslationService()


@pytest.fixture
def mock_summarization_service():
    """Mock summarization service for testing."""
    class MockSummarizationService:
        async def generate_hierarchical_summary(self, text, **kwargs):
            return {
                "one_liner": "Brief summary of the content",
                "key_points": [
                    "First main point",
                    "Second main point",
                    "Third main point"
                ],
                "chapter_summary": {
                    "Chapter 1": "Summary of first chapter",
                    "Chapter 2": "Summary of second chapter"
                },
                "detailed_summary": "Comprehensive summary of the entire content..."
            }

        async def summarize_text(self, text, **kwargs):
            return "Mock summary of the provided text"

    return MockSummarizationService()


@pytest.fixture
def mock_rag_service():
    """Mock RAG service for testing."""
    class MockRAGService:
        async def correct_transcription(self, text, **kwargs):
            return {
                "corrected_text": f"Corrected: {text}",
                "corrections_made": [
                    {"original": "teh", "corrected": "the", "position": 10},
                    {"original": "recieve", "corrected": "receive", "position": 25}
                ],
                "confidence": 0.92
            }

        async def setup_qa_system(self, *args, **kwargs):
            return {"message": "QA system setup successfully", "status": "ready"}

        async def ask_question(self, question, **kwargs):
            return {
                "answer": f"Mock answer to: {question}",
                "confidence": 0.85,
                "sources": [
                    {"text": "Source text 1", "start": 0, "end": 50},
                    {"text": "Source text 2", "start": 51, "end": 100}
                ]
            }

    return MockRAGService()


# Environment fixtures
@pytest.fixture
def test_env_vars(monkeypatch):
    """Set test environment variables."""
    test_vars = {
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "DATABASE_URL": "sqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/1",  # Use different DB for tests
        "OPENAI_API_KEY": "test-openai-key",
        "ENVIRONMENT": "testing",
        "DEBUG": "true"
    }

    for key, value in test_vars.items():
        monkeypatch.setenv(key, value)

    yield test_vars


@pytest.fixture
def test_settings(test_env_vars):
    """Create test settings instance."""
    # Force reload of settings to pick up test environment
    from app.config import Settings
    settings = Settings()
    return settings


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up any temporary files created during tests."""
    temp_files = []

    yield temp_files

    # Cleanup after test
    for temp_file in temp_files:
        if os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass  # Ignore cleanup errors in tests


# Performance testing fixtures
@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time

    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0

        def reset(self):
            self.start_time = None
            self.end_time = None

    return PerformanceTimer()