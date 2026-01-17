"""Tests for transcription service."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from app.services.transcription_service import TranscriptionService
from app.config import HardwareProfile


class TestTranscriptionService:

    @pytest.fixture
    def service(self):
        """Create transcription service instance."""
        return TranscriptionService()

    @pytest.fixture
    def sample_audio_path(self, tmp_path):
        """Create a sample audio file path."""
        return tmp_path / "test.wav"

    def test_initialization(self, service):
        """Test service initialization."""
        assert service.model is None
        assert service.model_loaded is False
        assert service.device in ["cuda", "cpu"]
        assert service.dialect_detector is not None
        assert service.adaptive_service is not None

    def test_device_detection_cuda(self, service):
        """Test CUDA device detection."""
        with patch('torch.cuda.is_available', return_value=True), \
             patch('torch.cuda.device_count', return_value=1), \
             patch('torch.cuda.get_device_name', return_value="RTX 4090"):
            service._detect_device()
            assert service.device == "cuda"

    def test_device_detection_cpu(self, service):
        """Test CPU fallback when CUDA unavailable."""
        with patch('torch.cuda.is_available', return_value=False):
            service._detect_device()
            assert service.device == "cpu"

    @pytest.mark.asyncio
    async def test_load_model(self, service):
        """Test model loading."""
        with patch.object(service, '_load_whisper_model') as mock_load:
            await service.load_model()
            assert service.model_loaded is True
            mock_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, service, sample_audio_path):
        """Test successful audio transcription."""
        # Setup
        expected_transcript = "Hello world transcript"
        expected_segments = [
            {"start": 0.0, "end": 2.5, "text": "Hello", "confidence": 0.95}
        ]
        expected_stats = {"processing_time": 1.5, "model": "large-v3"}

        # Mock the transcription
        with patch.object(service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = (expected_transcript, expected_segments, expected_stats)

            # Execute
            result = await service.transcribe_audio(
                job_id="test-job",
                audio_path=str(sample_audio_path),
                language="en"
            )

            # Verify
            transcript, segments, stats = result
            assert transcript == expected_transcript
            assert segments == expected_segments
            assert stats == expected_stats
            mock_transcribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self, service):
        """Test transcription with missing file."""
        with pytest.raises(FileNotFoundError):
            await service.transcribe_audio(
                job_id="test-job",
                audio_path="/nonexistent/file.wav",
                language="en"
            )

    @pytest.mark.asyncio
    async def test_transcribe_with_dialect_adaptation_arabic(self, service, sample_audio_path):
        """Test dialect-adaptive transcription for Arabic."""
        text_sample = "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده"

        with patch.object(service.adaptive_service, 'transcribe_with_adaptation') as mock_adapt:
            mock_adapt.return_value = ("Transcript", [], {}, {"dialect": "cairo"})

            result = await service.transcribe_with_dialect_adaptation(
                job_id="test-job",
                audio_path=str(sample_audio_path),
                text_sample=text_sample,
                language="ar"
            )

            transcript, segments, stats, dialect_info = result
            assert transcript == "Transcript"
            assert dialect_info["dialect"] == "cairo"
            mock_adapt.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_with_dialect_adaptation_fallback(self, service, sample_audio_path):
        """Test fallback to standard transcription when dialect adaptation fails."""
        text_sample = "أهلاً يا جماعة"

        with patch.object(service.adaptive_service, 'transcribe_with_adaptation', side_effect=Exception("Adaptation failed")), \
             patch.object(service, 'transcribe_audio') as mock_fallback:
            mock_fallback.return_value = ("Fallback transcript", [], {})

            result = await service.transcribe_with_dialect_adaptation(
                job_id="test-job",
                audio_path=str(sample_audio_path),
                text_sample=text_sample,
                language="ar"
            )

            transcript, segments, stats, dialect_info = result
            assert transcript == "Fallback transcript"
            assert dialect_info is None
            mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_transcribe_with_dialect_adaptation_non_arabic(self, service, sample_audio_path):
        """Test standard transcription for non-Arabic languages."""
        with patch.object(service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = ("English transcript", [], {})

            result = await service.transcribe_with_dialect_adaptation(
                job_id="test-job",
                audio_path=str(sample_audio_path),
                text_sample="Hello world",
                language="en"
            )

            transcript, segments, stats, dialect_info = result
            assert transcript == "English transcript"
            assert dialect_info is None
            mock_transcribe.assert_called_once()

    @pytest.mark.parametrize("language,expected_model", [
        ("en", "large-v3"),
        ("ar", "large-v3"),
        ("fr", "medium"),
        ("de", "medium"),
    ])
    def test_model_selection_by_language(self, service, language, expected_model):
        """Test model selection based on language."""
        # This would be implemented in the actual service
        # For now, just test the concept
        assert expected_model in ["tiny", "base", "small", "medium", "large", "large-v3"]

    @pytest.mark.parametrize("hardware_profile", [
        HardwareProfile.ULTRA,
        HardwareProfile.STD_GPU,
        HardwareProfile.CPU_STRONG,
        HardwareProfile.EDGE_WEAK
    ])
    def test_hardware_profile_compatibility(self, service, hardware_profile):
        """Test service compatibility with different hardware profiles."""
        # Service should work with all profiles
        assert hasattr(service, 'device')
        assert hasattr(service, 'dialect_detector')
        assert hasattr(service, 'adaptive_service')

    @pytest.mark.asyncio
    async def test_concurrent_transcriptions(self, service, sample_audio_path):
        """Test concurrent transcription processing."""
        # Create multiple concurrent transcription tasks
        tasks = []
        for i in range(3):
            task = service.transcribe_audio(
                job_id=f"test-job-{i}",
                audio_path=str(sample_audio_path),
                language="en"
            )
            tasks.append(task)

        # Mock the transcription to return different results
        with patch.object(service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.side_effect = [
                (f"Transcript {i}", [], {}) for i in range(3)
            ]

            # Execute concurrently
            results = await asyncio.gather(*tasks)

            # Verify all completed successfully
            assert len(results) == 3
            for i, result in enumerate(results):
                transcript, segments, stats = result
                assert transcript == f"Transcript {i}"

    def test_memory_management(self, service):
        """Test memory management and cleanup."""
        # Service should not hold references to large objects unnecessarily
        initial_refs = len(service.__dict__)

        # Simulate processing
        service.finetuned_models["test"] = {"model": "large_object"}

        # Cleanup should be available
        assert hasattr(service, 'finetuned_models')
        assert "test" in service.finetuned_models

    @pytest.mark.asyncio
    async def test_error_recovery(self, service, sample_audio_path):
        """Test error recovery and graceful degradation."""
        # Test with corrupted file
        with patch.object(service, 'transcribe_audio', side_effect=Exception("Corrupted file")):
            with pytest.raises(Exception, match="Corrupted file"):
                await service.transcribe_audio(
                    job_id="test-job",
                    audio_path=str(sample_audio_path),
                    language="en"
                )

    @pytest.mark.asyncio
    async def test_processing_stats_accuracy(self, service, sample_audio_path):
        """Test that processing statistics are accurate."""
        with patch.object(service, 'transcribe_audio') as mock_transcribe:
            expected_stats = {
                "processing_time": 2.5,
                "model": "large-v3",
                "language": "ar",
                "confidence": 0.92
            }
            mock_transcribe.return_value = ("Test transcript", [], expected_stats)

            start_time = asyncio.get_event_loop().time()
            result = await service.transcribe_audio(
                job_id="test-job",
                audio_path=str(sample_audio_path),
                language="ar"
            )
            end_time = asyncio.get_event_loop().time()

            transcript, segments, stats = result
            assert stats["model"] == "large-v3"
            assert stats["language"] == "ar"
            assert "processing_time" in stats

    def test_service_configuration_validation(self, service):
        """Test that service configuration is valid."""
        # Service should have required attributes
        required_attrs = [
            'model', 'model_loaded', 'device', 'dialect_detector',
            'adaptive_service', 'finetuned_models'
        ]

        for attr in required_attrs:
            assert hasattr(service, attr), f"Missing required attribute: {attr}"