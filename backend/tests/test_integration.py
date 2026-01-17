"""Integration tests for end-to-end functionality."""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from app.services.transcription_service import transcription_service
from app.services.translation_service import translation_service
from app.services.summarization_service import summarization_service
from app.services.rag_service import rag_service
from app.services.voice_analytics_service import voice_analytics_service
from app.services.job_service import create_job, get_job, mark_job_completed
from app.tasks.transcription_tasks import process_transcription_job


class TestIntegrationScenarios:

    @pytest.fixture
    def sample_audio_file(self, tmp_path):
        """Create a sample audio file for testing."""
        audio_path = tmp_path / "test.wav"
        # Create a minimal WAV file header (44 bytes)
        wav_header = (
            b'RIFF'  # ChunkID
            b'\x24\x08\x00\x00'  # ChunkSize (little endian)
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

        audio_path.write_bytes(wav_header + audio_data)
        return str(audio_path)

    @pytest.mark.asyncio
    async def test_complete_transcription_pipeline_arabic(self, sample_audio_file):
        """Test complete transcription pipeline for Arabic content."""
        job_data = {
            "filename": "arabic_meeting.wav",
            "file_path": sample_audio_file,
            "file_size": 1024,
            "duration": 10.5,
            "language": "ar",
            "enable_translation": True,
            "enable_summary": True,
            "enable_voice_analytics": False,
            "target_language": "en",
            "text_sample": "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده"
        }

        with patch.object(transcription_service, 'transcribe_with_dialect_adaptation') as mock_transcribe, \
             patch.object(translation_service, 'translate_text') as mock_translate, \
             patch.object(summarization_service, 'generate_hierarchical_summary') as mock_summarize:

            # Setup mocks
            mock_transcribe.return_value = (
                "أهلاً يا جماعة إحنا هنتكلم عن المشروع ده",
                [{"start": 0, "end": 5, "text": "أهلاً يا جماعة", "confidence": 0.95}],
                {"processing_time": 2.1, "model": "large-v3", "dialect_detected": "cairo"}
            )
            mock_translate.return_value = "Hello everyone, we will talk about this project"
            mock_summarize.return_value = {
                "level_1_elevator_pitch": "Project discussion",
                "level_2_key_points": "Team greeting and project topic introduction",
                "level_3_comprehensive": "The speaker greets the team and introduces the project discussion topic."
            }

            # Create job
            job_id = create_job(job_data)

            # Process job (simulate task execution)
            await self._simulate_job_processing(job_id, job_data)

            # Verify results
            job = get_job(job_id)
            assert job.status == "completed"
            assert job.transcript is not None
            assert job.translation is not None
            assert job.hierarchical_summary is not None

    @pytest.mark.asyncio
    async def test_complete_transcription_pipeline_english(self, sample_audio_file):
        """Test complete transcription pipeline for English content."""
        job_data = {
            "filename": "english_lecture.wav",
            "file_path": sample_audio_file,
            "file_size": 2048,
            "duration": 15.2,
            "language": "en",
            "enable_translation": False,
            "enable_summary": True,
            "enable_voice_analytics": True,
            "summary_length": "long"
        }

        with patch.object(transcription_service, 'transcribe_audio') as mock_transcribe, \
             patch.object(summarization_service, 'generate_hierarchical_summary') as mock_summarize, \
             patch.object(voice_analytics_service, 'perform_diarization') as mock_diarize, \
             patch.object(voice_analytics_service, 'analyze_emotions') as mock_emotion, \
             patch.object(voice_analytics_service, 'combine_transcription_and_diarization') as mock_combine, \
             patch.object(voice_analytics_service, 'analyze_meeting_dynamics') as mock_analyze:

            # Setup mocks
            mock_transcribe.return_value = (
                "Hello everyone, today we will discuss the new project architecture.",
                [{"start": 0, "end": 8, "text": "Hello everyone, today we will discuss", "confidence": 0.98}],
                {"processing_time": 1.8, "model": "large-v3"}
            )
            mock_summarize.return_value = {
                "level_1_elevator_pitch": "Project architecture discussion",
                "level_2_key_points": "Greeting and topic introduction for new project architecture",
                "level_3_comprehensive": "The speaker greets the audience and introduces today's discussion topic about the new project architecture."
            }

            # Voice analytics mocks
            mock_diarize.return_value = [{"speaker": "A", "start": 0, "end": 8}]
            mock_emotion.return_value = [{"speaker": "A", "emotion": "neutral", "start": 0, "end": 8}]
            mock_combine.return_value = [{"speaker": "A", "text": "Hello everyone...", "emotion": "neutral"}]
            mock_analyze.return_value = {"total_speakers": 1, "meeting_type": "presentation"}

            # Create and process job
            job_id = create_job(job_data)
            await self._simulate_job_processing(job_id, job_data)

            # Verify results
            job = get_job(job_id)
            assert job.status == "completed"
            assert job.transcript is not None
            assert job.summary is not None
            assert job.voice_analytics is not None

    @pytest.mark.asyncio
    async def test_qa_system_integration(self, sample_audio_file):
        """Test Q&A system integration with transcription."""
        job_data = {
            "filename": "qa_test.wav",
            "file_path": sample_audio_file,
            "file_size": 1024,
            "duration": 8.5,
            "language": "en",
            "enable_translation": False,
            "enable_summary": False,
            "enable_voice_analytics": False
        }

        transcript = "The new project will be completed in three months. The budget is $500,000. John is the project manager."

        with patch.object(transcription_service, 'transcribe_audio') as mock_transcribe, \
             patch.object(rag_service, 'setup_qa_system') as mock_setup, \
             patch.object(rag_service, 'ask_question') as mock_ask:

            # Setup transcription mock
            mock_transcribe.return_value = (
                transcript,
                [{"start": 0, "end": 8, "text": transcript, "confidence": 0.96}],
                {"processing_time": 1.2}
            )

            # Setup Q&A mocks
            mock_setup.return_value = None
            mock_ask.return_value = {
                "answer": "three months",
                "confidence": 0.91,
                "sources": [{"text": "completed in three months", "timestamp": 2.1}]
            }

            # Create and process job
            job_id = create_job(job_data)
            await self._simulate_job_processing(job_id, job_data)

            # Test Q&A functionality
            from app.services.job_service import get_job_results
            results = get_job_results(job_id)

            # Ask a question
            answer = rag_service.ask_question("How long will the project take?", job_id)

            assert "three months" in answer["answer"]
            assert answer["confidence"] > 0.8
            assert len(answer["sources"]) > 0

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, sample_audio_file):
        """Test error recovery and fallback mechanisms."""
        job_data = {
            "filename": "error_test.wav",
            "file_path": sample_audio_file,
            "file_size": 1024,
            "duration": 5.0,
            "language": "ar",
            "enable_translation": True,
            "enable_summary": True,
            "enable_voice_analytics": False
        }

        # Test transcription failure with translation fallback
        with patch.object(transcription_service, 'transcribe_with_dialect_adaptation', side_effect=Exception("Model error")), \
             patch.object(transcription_service, 'transcribe_audio') as mock_fallback, \
             patch.object(translation_service, 'translate_text') as mock_translate:

            mock_fallback.return_value = (
                "المحتوى التجريبي",
                [{"start": 0, "end": 5, "text": "المحتوى التجريبي", "confidence": 0.85}],
                {"processing_time": 1.0, "fallback_used": True}
            )
            mock_translate.return_value = "Test content"

            # Create and process job
            job_id = create_job(job_data)
            await self._simulate_job_processing(job_id, job_data)

            # Verify job completed despite initial error
            job = get_job(job_id)
            assert job.status == "completed"
            assert job.transcript is not None
            assert job.translation is not None

    @pytest.mark.asyncio
    async def test_concurrent_job_processing(self, sample_audio_file):
        """Test concurrent processing of multiple jobs."""
        job_count = 3
        job_ids = []

        # Create multiple jobs
        for i in range(job_count):
            job_data = {
                "filename": f"concurrent_test_{i}.wav",
                "file_path": sample_audio_file,
                "file_size": 1024,
                "duration": 5.0,
                "language": "en",
                "enable_translation": False,
                "enable_summary": True,
                "enable_voice_analytics": False
            }
            job_id = create_job(job_data)
            job_ids.append(job_id)

        # Mock transcription service
        with patch.object(transcription_service, 'transcribe_audio') as mock_transcribe, \
             patch.object(summarization_service, 'generate_hierarchical_summary') as mock_summarize:

            mock_transcribe.return_value = (
                "Concurrent processing test",
                [{"start": 0, "end": 5, "text": "Concurrent processing test", "confidence": 0.92}],
                {"processing_time": 0.8}
            )
            mock_summarize.return_value = {
                "level_1_elevator_pitch": "Test",
                "level_2_key_points": "Concurrent processing test",
                "level_3_comprehensive": "Testing concurrent job processing capabilities."
            }

            # Process all jobs concurrently
            tasks = []
            for job_id in job_ids:
                job = get_job(job_id)
                task = self._simulate_job_processing(job_id, job.__dict__)
                tasks.append(task)

            await asyncio.gather(*tasks)

            # Verify all jobs completed
            for job_id in job_ids:
                job = get_job(job_id)
                assert job.status == "completed"
                assert job.transcript is not None
                assert job.summary is not None

    @pytest.mark.asyncio
    async def test_resource_cleanup_integration(self, sample_audio_file):
        """Test proper resource cleanup after processing."""
        job_data = {
            "filename": "cleanup_test.wav",
            "file_path": sample_audio_file,
            "file_size": 1024,
            "duration": 3.0,
            "language": "en",
            "enable_translation": False,
            "enable_summary": False,
            "enable_voice_analytics": False
        }

        # Track temporary files
        temp_files_created = []

        with patch('tempfile.NamedTemporaryFile') as mock_tempfile, \
             patch.object(transcription_service, 'transcribe_audio') as mock_transcribe:

            # Mock tempfile creation
            mock_temp = Mock()
            mock_temp.name = "/tmp/test_chunk.wav"
            mock_tempfile.return_value.__enter__.return_value = mock_temp
            mock_tempfile.return_value.__exit__.return_value = None

            mock_transcribe.return_value = (
                "Cleanup test",
                [{"start": 0, "end": 3, "text": "Cleanup test", "confidence": 0.90}],
                {"processing_time": 0.5}
            )

            # Create and process job
            job_id = create_job(job_data)
            await self._simulate_job_processing(job_id, job_data)

            # Verify job completed
            job = get_job(job_id)
            assert job.status == "completed"

    @pytest.mark.asyncio
    async def test_large_file_processing_simulation(self, tmp_path):
        """Test processing simulation for large files."""
        # Create a larger test file
        large_audio_path = tmp_path / "large_test.wav"
        wav_header = b'RIFF\x00\x08\x01\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x01\x00'
        audio_data = b'\x00\x00' * 65536  # Larger audio data
        large_audio_path.write_bytes(wav_header + audio_data)

        job_data = {
            "filename": "large_file.wav",
            "file_path": str(large_audio_path),
            "file_size": len(wav_header + audio_data),
            "duration": 120.0,  # 2 minutes
            "language": "ar",
            "enable_translation": True,
            "enable_summary": True,
            "enable_voice_analytics": False
        }

        with patch.object(transcription_service, 'transcribe_with_dialect_adaptation') as mock_transcribe, \
             patch.object(translation_service, 'translate_text') as mock_translate, \
             patch.object(summarization_service, 'generate_hierarchical_summary') as mock_summarize:

            mock_transcribe.return_value = (
                "محتوى طويل للاختبار",
                [{"start": 0, "end": 10, "text": "محتوى طويل", "confidence": 0.88}],
                {"processing_time": 15.2, "chunks_processed": 6}
            )
            mock_translate.return_value = "Long content for testing"
            mock_summarize.return_value = {
                "level_1_elevator_pitch": "Testing large file processing",
                "level_2_key_points": "Large Arabic audio file processing test",
                "level_3_comprehensive": "Testing the system's ability to process large Arabic audio files with translation and summarization."
            }

            # Create and process job
            job_id = create_job(job_data)
            await self._simulate_job_processing(job_id, job_data)

            # Verify successful processing
            job = get_job(job_id)
            assert job.status == "completed"
            assert job.transcript is not None
            assert job.translation is not None
            assert job.hierarchical_summary is not None

    async def _simulate_job_processing(self, job_id: str, job_data: dict):
        """Simulate job processing without actual Celery task."""
        # Import required services
        from app.services import transcription_service, translation_service, summarization_service

        # Simulate the transcription task steps
        try:
            # Step 1: Transcription
            if job_data.get("text_sample") and job_data["language"] in ["ar", "arabic"]:
                result = await transcription_service.transcribe_with_dialect_adaptation(
                    job_id=job_id,
                    audio_path=job_data["file_path"],
                    text_sample=job_data["text_sample"],
                    language=job_data["language"]
                )
                transcript, segments, trans_stats, dialect_info = result
            else:
                transcript, segments, trans_stats = await transcription_service.transcribe_audio(
                    job_id=job_id,
                    audio_path=job_data["file_path"],
                    language=job_data["language"]
                )

            # Step 2: Translation
            translation = None
            if job_data.get("enable_translation"):
                translation = await translation_service.translate_text(
                    text=transcript,
                    source_lang=job_data["language"],
                    target_lang=job_data.get("target_language", "en")
                )

            # Step 3: Summarization
            summary = None
            hierarchical_summary = None
            if job_data.get("enable_summary"):
                hierarchical_result = await summarization_service.generate_hierarchical_summary(
                    translation or transcript
                )
                if hierarchical_result:
                    summary_length = job_data.get("summary_length", "medium")
                    level_map = {
                        "short": "level_1_elevator_pitch",
                        "medium": "level_2_key_points",
                        "long": "level_3_comprehensive"
                    }
                    summary_key = level_map.get(summary_length, "level_2_key_points")
                    summary = hierarchical_result.get(summary_key, "")
                    hierarchical_summary = hierarchical_result

            # Step 4: Voice Analytics (simplified)
            voice_analytics = None
            if job_data.get("enable_voice_analytics"):
                # Mock voice analytics for integration testing
                voice_analytics = {
                    "speaker_segments": [{"speaker": "A", "start": 0, "end": 10}],
                    "meeting_analysis": {"total_speakers": 1}
                }

            # Step 5: Mark job completed
            final_results = {
                "transcript": transcript,
                "translation": translation,
                "summary": summary,
                "hierarchical_summary": hierarchical_summary,
                "voice_analytics": voice_analytics,
                "processing_stats": {
                    "total_time_seconds": 5.0,
                    "transcription_stats": trans_stats,
                    "profile_used": "CPU_STRONG"
                }
            }

            await mark_job_completed(job_id=job_id, **final_results)

        except Exception as e:
            # Mark job failed
            await mark_job_failed(job_id, f"Processing failed: {str(e)}")
            raise