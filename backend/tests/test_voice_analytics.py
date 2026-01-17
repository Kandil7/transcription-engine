"""Tests for voice analytics service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.voice_analytics_service import VoiceAnalyticsService


@pytest.mark.asyncio
async def test_voice_analytics_service_initialization():
    """Test voice analytics service initialization."""
    service = VoiceAnalyticsService()

    # Mock model loading
    with patch.object(service, 'load_diarization_model', new_callable=AsyncMock), \
         patch.object(service, 'load_emotion_model', new_callable=AsyncMock):

        await service.load_diarization_model()
        await service.load_emotion_model()

        assert service.diarization_loaded
        assert service.emotion_loaded


@pytest.mark.asyncio
async def test_perform_diarization():
    """Test speaker diarization."""
    service = VoiceAnalyticsService()

    # Mock PyAnnote pipeline
    mock_pipeline = MagicMock()
    mock_turn = MagicMock()
    mock_turn.start = 0.0
    mock_turn.end = 5.0
    mock_pipeline.return_value.itertracks.return_value = [(mock_turn, None, "SPEAKER_01")]

    service.diarization_pipeline = mock_pipeline
    service.diarization_loaded = True

    # Mock file existence
    with patch('os.path.exists', return_value=True):
        segments = await service.perform_diarization("/path/to/audio.wav")

        assert len(segments) == 1
        assert segments[0]["speaker"] == "SPEAKER_01"
        assert segments[0]["start"] == 0.0
        assert segments[0]["end"] == 5.0


@pytest.mark.asyncio
async def test_analyze_emotions():
    """Test emotion analysis."""
    service = VoiceAnalyticsService()

    # Mock emotion analysis
    service.emotion_loaded = True

    segments = [
        {"speaker": "SPEAKER_01", "start": 0, "end": 2, "duration": 2},
        {"speaker": "SPEAKER_02", "start": 2, "end": 4, "duration": 2}
    ]

    enhanced_segments = await service.analyze_emotions("/path/to/audio.wav", segments)

    assert len(enhanced_segments) == 2
    assert "emotion" in enhanced_segments[0]
    assert "confidence" in enhanced_segments[0]


@pytest.mark.asyncio
async def test_combine_transcription_and_diarization():
    """Test combining transcription with speaker diarization."""
    service = VoiceAnalyticsService()

    transcription_segments = [
        {"start": 0.5, "end": 2.5, "text": "Hello world", "confidence": 0.95},
        {"start": 3.0, "end": 5.0, "text": "How are you", "confidence": 0.90}
    ]

    diarization_segments = [
        {"speaker": "SPEAKER_01", "start": 0.0, "end": 3.0, "duration": 3.0},
        {"speaker": "SPEAKER_02", "start": 3.0, "end": 6.0, "duration": 3.0}
    ]

    combined = await service.combine_transcription_and_diarization(
        transcription_segments, diarization_segments
    )

    assert len(combined) == 2
    assert combined[0]["speaker"] == "SPEAKER_01"
    assert combined[1]["speaker"] == "SPEAKER_02"
    assert "emotion" in combined[0]


@pytest.mark.asyncio
async def test_analyze_meeting_dynamics():
    """Test meeting dynamics analysis."""
    service = VoiceAnalyticsService()

    segments = [
        {"speaker": "SPEAKER_01", "duration": 60, "emotion": "confident"},
        {"speaker": "SPEAKER_01", "duration": 30, "emotion": "neutral"},
        {"speaker": "SPEAKER_02", "duration": 45, "emotion": "excited"},
    ]

    analysis = await service.analyze_meeting_dynamics(segments)

    assert analysis["total_duration"] == 135
    assert analysis["total_speakers"] == 2
    assert analysis["dominant_speaker"] == "SPEAKER_01"
    assert "speaker_stats" in analysis
    assert "meeting_balance_score" in analysis


def test_calculate_balance_score():
    """Test balance score calculation."""
    service = VoiceAnalyticsService()

    # Perfect balance
    speaker_stats = {
        "A": {"total_speech_time": 50},
        "B": {"total_speech_time": 50}
    }
    score = service._calculate_balance_score(speaker_stats)
    assert score == 100.0

    # Poor balance
    speaker_stats = {
        "A": {"total_speech_time": 90},
        "B": {"total_speech_time": 10}
    }
    score = service._calculate_balance_score(speaker_stats)
    assert score < 50.0


def test_get_model_status():
    """Test model status retrieval."""
    service = VoiceAnalyticsService()

    service.diarization_loaded = True
    service.emotion_loaded = False

    status = service.get_model_status()

    assert status["diarization_loaded"] is True
    assert status["emotion_loaded"] is False
    assert "device" in status


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in voice analytics."""
    service = VoiceAnalyticsService()

    # Test diarization with non-existent file
    with patch('os.path.exists', return_value=False):
        segments = await service.perform_diarization("/nonexistent.wav")
        assert segments == []

    # Test emotion analysis without loaded model
    service.emotion_loaded = False
    segments = await service.analyze_emotions("/path.wav", [])
    # Should return segments unchanged or with default emotions


@pytest.mark.asyncio
async def test_empty_segments():
    """Test handling of empty segment lists."""
    service = VoiceAnalyticsService()

    # Empty transcription segments
    combined = await service.combine_transcription_and_diarization([], [])
    assert combined == []

    # Empty meeting analysis
    analysis = await service.analyze_meeting_dynamics([])
    assert analysis.get("total_speakers") == 0


@pytest.mark.asyncio
async def test_single_speaker_balance():
    """Test balance score with single speaker."""
    service = VoiceAnalyticsService()

    speaker_stats = {
        "A": {"total_speech_time": 100}
    }
    score = service._calculate_balance_score(speaker_stats)
    assert score == 100.0  # Single speaker = perfect balance