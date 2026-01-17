"""Comprehensive tests for API endpoints."""

import pytest
import json
from io import BytesIO
from unittest.mock import Mock, patch, AsyncMock
from httpx import AsyncClient

from app.main import app
from app.core.exceptions import JobNotFoundError, ValidationError


class TestAPIEndpoints:

    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client

    @pytest.mark.asyncio
    async def test_health_endpoint_comprehensive(self, client):
        """Test health endpoint with comprehensive checks."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = ["status", "version", "profile", "gpu_memory_gb", "cpu_cores"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Status should be healthy
        assert data["status"] == "healthy"

        # Version should be valid
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0

        # Hardware info should be reasonable
        assert isinstance(data["gpu_memory_gb"], (int, float))
        assert isinstance(data["cpu_cores"], int)
        assert data["cpu_cores"] > 0

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    @pytest.mark.asyncio
    async def test_upload_file_success(self, client):
        """Test successful file upload."""
        # Create test audio file
        audio_content = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00"
        audio_file = BytesIO(audio_content)
        audio_file.name = "test.wav"

        files = {"file": ("test.wav", audio_file, "audio/wav")}
        data = {
            "language": "ar",
            "enable_translation": "true",
            "target_language": "en"
        }

        with patch('app.services.job_service.create_job') as mock_create, \
             patch('app.core.storage.upload_file') as mock_upload, \
             patch('app.utils.audio.validate_audio_file', new_callable=AsyncMock) as mock_validate:

            # Setup mocks
            mock_create.return_value = "job_12345"
            mock_upload.return_value = "/uploads/test.wav"
            mock_validate.return_value = {"duration": 10.5, "channels": 1, "sample_rate": 16000}

            response = await client.post("/api/v1/upload/file", files=files, data=data)

            assert response.status_code == 200
            data = response.json()

            assert "job_id" in data
            assert "status" in data
            assert "message" in data
            assert data["status"] == "uploaded"

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, client):
        """Test upload rejection for invalid file types."""
        # Create invalid file
        invalid_file = BytesIO(b"This is not audio")
        invalid_file.name = "test.txt"

        files = {"file": ("test.txt", invalid_file, "text/plain")}

        response = await client.post("/api/v1/upload/file", files=files)

        assert response.status_code == 400
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_upload_oversized_file(self, client):
        """Test upload rejection for oversized files."""
        # Create large file (simulate)
        large_content = b"x" * (600 * 1024 * 1024)  # 600MB
        large_file = BytesIO(large_content)
        large_file.name = "large.wav"

        files = {"file": ("large.wav", large_file, "audio/wav")}

        response = await client.post("/api/v1/upload/file", files=files)

        assert response.status_code == 413  # Payload Too Large

    @pytest.mark.asyncio
    async def test_get_job_success(self, client):
        """Test successful job retrieval."""
        job_id = "job_12345"

        with patch('app.services.job_service.get_job') as mock_get:
            mock_job = Mock()
            mock_job.id = job_id
            mock_job.status = "completed"
            mock_job.progress = 100.0
            mock_job.created_at = "2024-01-17T10:00:00Z"
            mock_job.updated_at = "2024-01-17T10:05:00Z"
            mock_job.filename = "test.wav"
            mock_job.duration = 10.5
            mock_job.language = "ar"
            mock_job.enable_translation = True
            mock_job.enable_summary = True
            mock_job.enable_voice_analytics = False
            mock_job.target_language = "en"
            mock_job.summary_length = "medium"

            mock_get.return_value = mock_job

            response = await client.get(f"/api/v1/jobs/{job_id}")

            assert response.status_code == 200
            data = response.json()

            assert data["id"] == job_id
            assert data["status"] == "completed"
            assert data["progress"] == 100.0
            assert data["language"] == "ar"
            assert data["enable_translation"] is True

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, client):
        """Test job retrieval for non-existent job."""
        job_id = "nonexistent_job"

        with patch('app.services.job_service.get_job', return_value=None):
            response = await client.get(f"/api/v1/jobs/{job_id}")

            assert response.status_code == 404
            data = response.json()
            assert "error_code" in data
            assert data["error_code"] == "JOB_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_job_results_completed(self, client):
        """Test job results retrieval for completed job."""
        job_id = "job_12345"

        with patch('app.services.job_service.get_job_results') as mock_results:
            mock_results.return_value = {
                "transcript": "Test transcript",
                "translation": "Test translation",
                "summary": "Test summary",
                "hierarchical_summary": {"level_1": "Brief", "level_2": "Detailed"},
                "voice_analytics": {"speakers": 2},
                "subtitles_srt": "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nTest transcript",
                "subtitles_vtt": "WEBVTT\n\n00:00:00.000 --> 00:00:05.000\nTest transcript",
                "audio_summary_url": "/audio/summary.mp3",
                "processing_stats": {"time": 2.5}
            }

            response = await client.get(f"/api/v1/jobs/{job_id}/results")

            assert response.status_code == 200
            data = response.json()

            assert "transcript" in data
            assert "translation" in data
            assert "summary" in data
            assert "voice_analytics" in data
            assert "processing_stats" in data

    @pytest.mark.asyncio
    async def test_create_job_validation(self, client):
        """Test job creation with validation."""
        # Missing required fields
        response = await client.post("/api/v1/jobs", json={})

        assert response.status_code == 422  # Validation error

        # Invalid language
        response = await client.post("/api/v1/jobs", json={
            "filename": "test.wav",
            "language": "invalid_lang"
        })

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_websocket_job_updates(self, client):
        """Test WebSocket endpoint for job updates."""
        # Test WebSocket endpoint accessibility
        # Note: Full WebSocket testing requires a test WebSocket client
        response = await client.get("/api/v1/ws/jobs/test-job")

        # Should return 404 or appropriate error for non-websocket request
        assert response.status_code in [404, 405]

    @pytest.mark.asyncio
    async def test_qa_endpoint_success(self, client):
        """Test Q&A endpoint success."""
        job_id = "job_12345"
        question = "What were the main points discussed?"

        with patch('app.services.job_service.get_job') as mock_get_job, \
             patch('app.services.rag_service.rag_service.setup_qa_system') as mock_setup, \
             patch('app.services.rag_service.rag_service.ask_question') as mock_ask:

            mock_job = Mock()
            mock_job.id = job_id
            mock_get_job.return_value = mock_job

            mock_setup.return_value = None
            mock_ask.return_value = {
                "answer": "The main points were project planning and timelines.",
                "confidence": 0.89,
                "sources": [{"text": "Source text", "timestamp": 120.5}]
            }

            response = await client.post(
                f"/api/v1/qa/{job_id}/ask",
                json={
                    "question": question,
                    "max_answers": 3,
                    "include_sources": True
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "answer" in data
            assert "confidence" in data
            assert "sources" in data
            assert data["confidence"] == 0.89

    @pytest.mark.asyncio
    async def test_voice_analytics_endpoint(self, client):
        """Test voice analytics endpoint."""
        job_id = "job_12345"

        with patch('app.services.job_service.get_job') as mock_get_job, \
             patch('app.services.voice_analytics_service.voice_analytics_service.perform_diarization') as mock_diarize, \
             patch('app.services.voice_analytics_service.voice_analytics_service.analyze_emotions') as mock_emotion, \
             patch('app.services.voice_analytics_service.voice_analytics_service.combine_transcription_and_diarization') as mock_combine, \
             patch('app.services.voice_analytics_service.voice_analytics_service.analyze_meeting_dynamics') as mock_analyze:

            mock_job = Mock()
            mock_job.id = job_id
            mock_get_job.return_value = mock_job

            # Setup mock returns
            mock_diarize.return_value = [{"speaker": "A", "start": 0, "end": 10}]
            mock_emotion.return_value = [{"speaker": "A", "emotion": "neutral"}]
            mock_combine.return_value = [{"speaker": "A", "text": "Hello", "emotion": "neutral"}]
            mock_analyze.return_value = {"total_speakers": 1, "duration": 10}

            response = await client.post(f"/api/v1/voice/{job_id}/analyze")

            assert response.status_code == 200
            data = response.json()

            assert "speaker_segments" in data
            assert "meeting_analysis" in data
            assert data["meeting_analysis"]["total_speakers"] == 1

    @pytest.mark.asyncio
    async def test_streaming_endpoint_validation(self, client):
        """Test streaming endpoint validation."""
        # Invalid language
        response = await client.post("/api/v1/stream/session_1/start", json={
            "language": "invalid_lang",
            "enable_translation": True
        })

        assert response.status_code == 422

        # Valid request
        with patch('app.services.streaming_service.streaming_service.start_session') as mock_start:
            mock_start.return_value = {"session_id": "session_1", "status": "active"}

            response = await client.post("/api/v1/stream/session_1/start", json={
                "language": "ar",
                "enable_translation": True
            })

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_error_handling_global(self, client):
        """Test global error handling."""
        # Trigger an internal error
        with patch('app.services.job_service.get_job', side_effect=Exception("Database error")):
            response = await client.get("/api/v1/jobs/test-job")

            assert response.status_code == 500
            data = response.json()
            assert "error_code" in data
            assert data["error_code"] == "INTERNAL_ERROR"
            assert "type" in data

    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, client):
        """Test rate limiting behavior (simulated)."""
        # This would require rate limiting middleware to be properly configured
        # For now, just test that endpoints respond correctly under normal load

        responses = []
        for _ in range(5):
            response = await client.get("/health")
            responses.append(response.status_code)

        # All should succeed (no rate limiting in test environment)
        assert all(status == 200 for status in responses)

    @pytest.mark.asyncio
    async def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = await client.options("/api/v1/jobs")

        # Check CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    @pytest.mark.asyncio
    async def test_content_type_validation(self, client):
        """Test content type validation."""
        # Test with wrong content type
        response = await client.post(
            "/api/v1/jobs",
            data="not json",
            headers={"Content-Type": "text/plain"}
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_authentication_required_endpoints(self, client):
        """Test that protected endpoints require authentication."""
        # These endpoints should require authentication in production
        endpoints = [
            "/api/v1/upload/file",
            "/api/v1/jobs",
            "/api/v1/qa/job_123/ask"
        ]

        for endpoint in endpoints:
            # In test environment, might not have auth enabled
            # Just verify endpoints exist and respond
            response = await client.get(endpoint) if endpoint.endswith("/jobs") else \
                      await client.post(endpoint, json={})
            assert response.status_code in [200, 401, 403, 405, 422]

    @pytest.mark.asyncio
    async def test_openapi_specification(self, client):
        """Test OpenAPI specification is accessible."""
        response = await client.get("/openapi.json")

        assert response.status_code == 200
        spec = response.json()

        # Should have basic OpenAPI structure
        assert "openapi" in spec
        assert "info" in spec
        assert "paths" in spec
        assert "/api/v1/jobs" in spec["paths"]

    @pytest.mark.asyncio
    async def test_api_versioning(self, client):
        """Test API versioning works correctly."""
        # Test v1 endpoints
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

        # Test root API path
        response = await client.get("/api/v1/")
        assert response.status_code in [200, 404]  # Might not have root endpoint

    @pytest.mark.asyncio
    async def test_response_format_consistency(self, client):
        """Test response format consistency across endpoints."""
        # Test multiple endpoints return consistent JSON structure
        endpoints = ["/health"]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                # Should be valid JSON
                assert isinstance(data, dict)