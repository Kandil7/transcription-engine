"""Transcription service using Faster-Whisper with Egyptian dialect support."""

import asyncio
import os
import time
from typing import Dict, List, Optional, Tuple

import torch
from faster_whisper import WhisperModel
from structlog import get_logger
from transformers import WhisperForConditionalGeneration, WhisperProcessor

from app.config import settings
from app.models.job import JobStatus, ProcessingStats
from app.services.job_service import update_job, update_job_progress
from app.services.dialect_detection_service import (
    EgyptianDialectDetector,
    DialectAdaptiveTranscriptionService
)

logger = get_logger(__name__)


class TranscriptionService:
    """Service for handling audio transcription using Faster-Whisper with dialect support."""

    def __init__(self):
        self.model: Optional[WhisperModel] = None
        self.finetuned_models: Dict[str, Dict] = {}  # Cache for fine-tuned models
        self.model_loaded = False
        self.device = self._detect_device()

        # Initialize dialect detection
        self.dialect_detector = EgyptianDialectDetector()
        self.adaptive_service = DialectAdaptiveTranscriptionService(self.dialect_detector)

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

    async def load_finetuned_model(self, model_name: str) -> Dict[str, any]:
        """Load a fine-tuned Whisper model for Egyptian dialects."""
        if model_name in self.finetuned_models:
            return self.finetuned_models[model_name]

        try:
            # Model paths for different Egyptian dialects
            model_paths = {
                'egyptian_cairo_finetuned': 'models/egyptian/cairo/final_model',
                'egyptian_alexandria_finetuned': 'models/egyptian/alexandria/final_model',
                'egyptian_upper_egypt_finetuned': 'models/egyptian/upper_egypt/final_model',
                'egyptian_delta_finetuned': 'models/egyptian/delta/final_model',
                'egyptian_mixed_finetuned': 'models/egyptian/mixed/final_model',
            }

            model_path = model_paths.get(model_name)
            if not model_path or not os.path.exists(model_path):
                logger.warning(f"Fine-tuned model {model_name} not found, falling back to base model")
                return None

            # Load fine-tuned model
            processor = WhisperProcessor.from_pretrained(model_path)
            model = WhisperForConditionalGeneration.from_pretrained(model_path)

            # Move to appropriate device
            model = model.to(self.device)

            model_info = {
                'processor': processor,
                'model': model,
                'model_name': model_name,
                'device': self.device
            }

            self.finetuned_models[model_name] = model_info
            logger.info(f"Loaded fine-tuned model: {model_name}")

            return model_info

        except Exception as e:
            logger.error(f"Failed to load fine-tuned model {model_name}: {e}")
            return None

    async def transcribe_with_dialect_adaptation(
        self,
        job_id: str,
        audio_path: str,
        text_sample: Optional[str] = None,
        language: str = "ar",
        progress_callback: Optional[callable] = None
    ) -> Tuple[str, List[Dict], ProcessingStats, Dict]:
        """
        Transcribe audio with dialect-adaptive model selection.

        Args:
            job_id: Job identifier for progress updates
            audio_path: Path to audio file
            text_sample: Optional text sample for dialect detection
            language: Language code
            progress_callback: Optional callback for progress updates

        Returns:
            Tuple of (transcript, segments, stats, dialect_info)
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        start_time = time.time()
        logger.info("Starting dialect-adaptive transcription", job_id=job_id, audio_path=audio_path)

        try:
            # Update job status
            await update_job(job_id, JobStatus.TRANSCRIBING, 5.0, "Analyzing dialect...")

            # Get dialect-adaptive configuration
            dialect_config = None
            if text_sample:
                dialect_config = self.adaptive_service.get_adaptive_config(text_sample)
                logger.info("Dialect detection complete",
                          primary_dialect=dialect_config['dialect_info']['primary_dialect'],
                          confidence=dialect_config['dialect_info']['confidence'],
                          recommended_model=dialect_config['model_name'])

            # Load appropriate model
            if dialect_config and dialect_config['boost_colloquial']:
                model_info = await self.load_finetuned_model(dialect_config['model_name'])
                if model_info:
                    return await self._transcribe_with_finetuned_model(
                        job_id, audio_path, model_info, dialect_config, start_time
                    )

            # Fall back to standard Faster-Whisper transcription
            return await self.transcribe_audio(job_id, audio_path, language, progress_callback)

        except Exception as e:
            logger.error("Dialect-adaptive transcription failed", job_id=job_id, error=str(e))
            await update_job(job_id, JobStatus.FAILED, message=f"Transcription failed: {str(e)}")
            raise

    async def _transcribe_with_finetuned_model(
        self,
        job_id: str,
        audio_path: str,
        model_info: Dict,
        dialect_config: Dict,
        start_time: float
    ) -> Tuple[str, List[Dict], ProcessingStats, Dict]:
        """Transcribe using fine-tuned Transformers model."""
        processor = model_info['processor']
        model = model_info['model']

        try:
            # Update job status
            await update_job(job_id, JobStatus.TRANSCRIBING, 10.0, "Loading fine-tuned model...")

            # Load and process audio
            import librosa
            audio_input, sample_rate = librosa.load(audio_path, sr=16000)

            # Process audio
            inputs = processor(
                audio_input,
                sampling_rate=sample_rate,
                return_tensors="pt",
                return_attention_mask=True
            ).to(model.device)

            # Generate transcription
            with torch.no_grad():
                generated_ids = model.generate(
                    inputs.input_features,
                    attention_mask=inputs.attention_mask,
                    forced_decoder_ids=processor.get_decoder_prompt_ids(language="ar", task="transcribe"),
                    max_length=448,
                    num_beams=5,
                    early_stopping=True,
                )

            # Decode transcription
            transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

            # Create segments (simplified - full segmentation would need VAD)
            segments = [{
                "start": 0.0,
                "end": len(audio_input) / sample_rate,
                "text": transcription,
                "confidence": dialect_config['dialect_info']['confidence']
            }]

            # Calculate processing statistics
            processing_time = time.time() - start_time
            stats = ProcessingStats(
                transcription_time_seconds=processing_time,
                whisper_model_used=dialect_config['model_name'],
                confidence_score=dialect_config['dialect_info']['confidence'],
                gpu_used=self.device == "cuda",
            )

            logger.info(
                "Fine-tuned transcription completed",
                job_id=job_id,
                duration_seconds=processing_time,
                model=dialect_config['model_name'],
                dialect=dialect_config['dialect_info']['primary_dialect']
            )

            # Update job progress
            await update_job_progress(job_id, 60.0, "Dialect-adaptive transcription completed")

            return transcription, segments, stats, dialect_config['dialect_info']

        except Exception as e:
            logger.error("Fine-tuned transcription failed", job_id=job_id, error=str(e))
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