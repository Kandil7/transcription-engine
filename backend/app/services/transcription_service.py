"""Transcription service using Faster-Whisper."""

import asyncio
import os
import time
from typing import Dict, List, Optional, Tuple

import torch
from faster_whisper import WhisperModel
from structlog import get_logger

from app.config import settings
from app.models.job import JobStatus, ProcessingStats
from app.services.job_service import update_job, update_job_progress

logger = get_logger(__name__)


class TranscriptionService:
    """Service for handling audio transcription using Faster-Whisper."""

    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self.model_loaded = False
        self.device = self._detect_device()

    def _detect_device(self) -> str:
        """Detect the best available device (CUDA, CPU)."""
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            logger.info("CUDA available", device_count=device_count, device_name=torch.cuda.get_device_name(0))
            return "cuda"
        else:
            logger.info("Using CPU for transcription")
            return "cpu"

    async def load_model(self) -> None:
        """Load the Whisper model based on the detected profile."""
        if self.model_loaded:
            return

        try:
            profile_config = settings.profile_configs[settings.detected_profile]

            logger.info(
                "Loading Whisper model",
                model=profile_config["whisper_model"],
                device=self.device,
                profile=settings.detected_profile.value
            )

            # Load model with appropriate settings
            self.model = WhisperModel(
                profile_config["whisper_model"],
                device=self.device,
                compute_type=profile_config["compute_type"],
                cpu_threads=4 if self.device == "cpu" else 0,
                num_workers=1,
            )

            self.model_loaded = True
            logger.info("Whisper model loaded successfully")

        except Exception as e:
            logger.error("Failed to load Whisper model", error=str(e))
            raise

    async def transcribe_audio(
        self,
        job_id: str,
        audio_path: str,
        language: str = "ar",
        progress_callback: Optional[callable] = None
    ) -> Tuple[str, List[Dict], ProcessingStats]:
        """
        Transcribe audio file and return transcript, segments, and stats.

        Args:
            job_id: Job identifier for progress updates
            audio_path: Path to audio file
            language: Language code
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (transcript, segments, stats)
        """
        await self.load_model()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        start_time = time.time()
        logger.info("Starting transcription", job_id=job_id, audio_path=audio_path)

        try:
            # Update job status
            await update_job(job_id, JobStatus.TRANSCRIBING, 5.0, "Starting transcription...")

            # Get profile-specific settings
            profile_config = settings.profile_configs[settings.detected_profile]

            # Run transcription
            segments, info = self.model.transcribe(
                audio_path,
                language=language if language != "auto" else None,
                beam_size=profile_config["beam_size"],
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                without_timestamps=False,
            )

            # Collect segments
            segment_list = []
            transcript_parts = []

            for segment in segments:
                segment_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": getattr(segment, 'confidence', None),
                }
                segment_list.append(segment_dict)
                transcript_parts.append(segment.text.strip())

            transcript = " ".join(transcript_parts)

            # Calculate processing statistics
            processing_time = time.time() - start_time
            stats = ProcessingStats(
                transcription_time_seconds=processing_time,
                whisper_model_used=profile_config["whisper_model"],
                confidence_score=info.language_probability if hasattr(info, 'language_probability') else None,
                gpu_used=self.device == "cuda",
            )

            logger.info(
                "Transcription completed",
                job_id=job_id,
                duration_seconds=processing_time,
                segments_count=len(segment_list),
                detected_language=info.language if hasattr(info, 'language') else language
            )

            # Update job progress
            await update_job_progress(job_id, 60.0, "Transcription completed")

            return transcript, segment_list, stats

        except Exception as e:
            logger.error("Transcription failed", job_id=job_id, error=str(e))
            await update_job(job_id, JobStatus.FAILED, message=f"Transcription failed: {str(e)}")
            raise

    async def transcribe_chunk(
        self,
        audio_chunk_path: str,
        language: str = "ar"
    ) -> Tuple[str, List[Dict]]:
        """
        Transcribe a single audio chunk.

        Used for parallel processing of large files.
        """
        await self.load_model()

        try:
            segments, info = self.model.transcribe(
                audio_chunk_path,
                language=language if language != "auto" else None,
                beam_size=3,  # Smaller beam for chunks
                vad_filter=False,  # VAD already applied
                without_timestamps=False,
            )

            segment_list = []
            transcript_parts = []

            for segment in segments:
                segment_dict = {
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip(),
                    "confidence": getattr(segment, 'confidence', None),
                }
                segment_list.append(segment_dict)
                transcript_parts.append(segment.text.strip())

            return " ".join(transcript_parts), segment_list

        except Exception as e:
            logger.error("Chunk transcription failed", chunk_path=audio_chunk_path, error=str(e))
            raise

    def get_model_info(self) -> Dict:
        """Get information about the loaded model."""
        if not self.model_loaded:
            return {"loaded": False}

        return {
            "loaded": True,
            "device": self.device,
            "profile": settings.detected_profile.value,
            "model_size": settings.profile_configs[settings.detected_profile]["whisper_model"],
        }


# Global transcription service instance
transcription_service = TranscriptionService()