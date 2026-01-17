"""Tests for real-time streaming transcription."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.streaming_service import StreamingTranscriptionService


@pytest.mark.asyncio
async def test_streaming_service_initialization():
    """Test streaming service initialization."""
    service = StreamingTranscriptionService()

    # Mock model loading
    with patch.object(service, 'load_model', new_callable=AsyncMock) as mock_load:
        await service.load_model()
        mock_load.assert_called_once()


@pytest.mark.asyncio
async def test_start_stream():
    """Test starting a streaming session."""
    service = StreamingTranscriptionService()

    # Mock model loading
    with patch.object(service, 'load_model', new_callable=AsyncMock):
        await service.start_stream("test-stream", "ar")

        assert "test-stream" in service.active_streams
        assert service.active_streams["test-stream"]["language"] == "ar"
        assert service.active_streams["test-stream"]["is_active"] is True


@pytest.mark.asyncio
async def test_process_audio_chunk():
    """Test processing audio chunks."""
    service = StreamingTranscriptionService()

    # Mock model and transcription
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 2.0
    mock_segment.text = "Test transcription"
    mock_segment.confidence = 0.95

    mock_info = MagicMock()
    mock_info.language = "ar"

    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    service.model = mock_model
    service.model_loaded = True

    # Start stream
    await service.start_stream("test-stream")

    # Process chunk
    results = []
    async for result in service.process_audio_chunk("test-stream", b"audio_data"):
        results.append(result)

    assert len(results) > 0
    assert results[0]["type"] == "transcription_chunk"
    assert results[0]["segment"]["text"] == "Test transcription"


@pytest.mark.asyncio
async def test_end_stream():
    """Test ending a streaming session."""
    service = StreamingTranscriptionService()

    # Start and configure stream
    await service.start_stream("test-stream")
    service.active_streams["test-stream"]["segments"] = [
        {"start": 0, "end": 1, "text": "Hello"},
        {"start": 1, "end": 2, "text": "world"}
    ]

    # End stream
    result = await service.end_stream("test-stream")

    assert result["stream_id"] == "test-stream"
    assert "Hello world" in result["full_transcript"]
    assert result["total_segments"] == 2
    assert "test-stream" not in service.active_streams


@pytest.mark.asyncio
async def test_get_stream_status():
    """Test getting stream status."""
    service = StreamingTranscriptionService()

    # Test non-existent stream
    status = await service.get_stream_status("non-existent")
    assert status["status"] == "not_found"

    # Test active stream
    await service.start_stream("test-stream", "ar")
    status = await service.get_stream_status("test-stream")

    assert status["status"] == "active"
    assert status["language"] == "ar"


def test_list_active_streams():
    """Test listing active streams."""
    service = StreamingTranscriptionService()

    # Add some test streams
    service.active_streams = {
        "stream1": {"language": "ar", "segments": [], "is_active": True},
        "stream2": {"language": "en", "segments": [1, 2], "is_active": True},
        "stream3": {"language": "ar", "segments": [], "is_active": False}  # Inactive
    }

    active_streams = service.list_active_streams()

    assert len(active_streams) == 2  # Only active streams
    assert any(s["stream_id"] == "stream1" for s in active_streams)
    assert any(s["stream_id"] == "stream2" for s in active_streams)
    assert not any(s["stream_id"] == "stream3" for s in active_streams)


@pytest.mark.asyncio
async def test_stream_error_handling():
    """Test error handling in streaming operations."""
    service = StreamingTranscriptionService()

    # Test ending non-existent stream
    with pytest.raises(ValueError, match="Stream nonexistent not found"):
        await service.end_stream("nonexistent")

    # Test processing chunk for non-existent stream
    with pytest.raises(ValueError, match="Stream nonexistent not found"):
        async for _ in service.process_audio_chunk("nonexistent", b"data"):
            pass


@pytest.mark.asyncio
async def test_inactive_stream_processing():
    """Test processing chunks for inactive streams."""
    service = StreamingTranscriptionService()

    await service.start_stream("test-stream")
    service.active_streams["test-stream"]["is_active"] = False

    # Should not yield any results for inactive streams
    results = []
    async for result in service.process_audio_chunk("test-stream", b"audio_data"):
        results.append(result)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_model_loading_failure():
    """Test handling model loading failures."""
    service = StreamingTranscriptionService()

    # Mock failed model loading
    with patch.object(service, 'load_model', side_effect=Exception("Model load failed")):
        with pytest.raises(Exception, match="Model load failed"):
            await service.start_stream("test-stream")


@pytest.mark.asyncio
async def test_transcription_error_recovery():
    """Test recovery from transcription errors."""
    service = StreamingTranscriptionService()

    # Mock model that sometimes fails
    mock_model = MagicMock()
    mock_model.transcribe.side_effect = [
        Exception("Temporary error"),
        ([MagicMock(start=0, end=1, text="Recovered", confidence=0.8)], MagicMock(language="ar"))
    ]

    service.model = mock_model
    service.model_loaded = True

    await service.start_stream("test-stream")

    # First chunk should fail silently
    results1 = []
    async for result in service.process_audio_chunk("test-stream", b"chunk1"):
        results1.append(result)

    # Should contain error result
    assert any(r["type"] == "error" for r in results1)

    # Second chunk should succeed
    results2 = []
    async for result in service.process_audio_chunk("test-stream", b"chunk2"):
        results2.append(result)

    # Should contain transcription result
    assert any(r["type"] == "transcription_chunk" for r in results2)


@pytest.mark.asyncio
async def test_buffer_management():
    """Test audio buffer management."""
    service = StreamingTranscriptionService()

    await service.start_stream("test-stream")

    # Add large audio data
    large_audio = b"x" * (1024 * 1024 + 100)  # > 1MB

    # Mock transcription to avoid actual processing
    service.model = MagicMock()
    service.model.transcribe.return_value = ([], MagicMock(language="ar"))

    async for _ in service.process_audio_chunk("test-stream", large_audio):
        pass

    # Buffer should be trimmed
    buffer_size = len(service.active_streams["test-stream"]["audio_buffer"])
    assert buffer_size <= 512 * 1024  # Should be <= 512KB