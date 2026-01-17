"""Celery tasks for transcription processing."""

import os
import time
from typing import Dict, List

from app.config import settings
from app.models.job import JobStatus
from app.services.job_service import get_job, mark_job_completed, mark_job_failed, update_job, update_job_progress
from app.services.transcription_service import transcription_service
from app.services.translation_service import translation_service
from app.services.summarization_service import summarization_service
from app.tasks.celery_app import celery_app
from app.utils.audio import extract_audio_from_video, split_audio_into_chunks, validate_audio_file
from structlog import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="process_transcription_job")
def process_transcription_job(self, job_id: str):
    """
    Main task to process a transcription job end-to-end.

    Pipeline:
    1. Preprocessing (extract audio, chunking)
    2. Transcription
    3. Translation (if enabled)
    4. Summarization (if enabled)
    5. Generate outputs (SRT, VTT, etc.)
    """
    start_time = time.time()
    logger.info("Starting job processing", job_id=job_id)

    try:
        # Get job details
        job = get_job(job_id)
        if not job:
            logger.error("Job not found", job_id=job_id)
            return

        # Update job status
        update_job(job_id, JobStatus.PREPROCESSING, 10.0, "Preparing audio...")

        # Step 1: Preprocessing
        audio_path = await _preprocess_audio(job)
        if not audio_path:
            raise Exception("Audio preprocessing failed")

        update_job_progress(job_id, 20.0, "Audio prepared, starting transcription...")

        # Step 2: Transcription
        transcript, segments, trans_stats = await transcription_service.transcribe_audio(
            job_id=job_id,
            audio_path=audio_path,
            language=job.language,
        )

        update_job_progress(job_id, 60.0, "Transcription completed, processing results...")

        # Step 3: Translation (if enabled)
        translation = None
        if job.enable_translation:
            update_job_progress(job_id, 70.0, "Translating content...")
            translation = await translation_service.translate_text(
                text=transcript,
                source_lang=job.language,
                target_lang=job.target_language or "en"
            )

        # Step 4: Summarization (if enabled)
        summary = None
        if job.enable_summary:
            update_job_progress(job_id, 80.0, "Generating summary...")
            summary = await summarization_service.summarize_text(
                text=translation or transcript,
                length=job.summary_length or "medium"
            )

        # Step 5: Generate outputs
        update_job_progress(job_id, 90.0, "Generating output files...")

        outputs = await _generate_outputs(job_id, segments, translation, summary)

        # Step 6: Finalize job
        total_time = time.time() - start_time
        processing_stats = {
            "total_time_seconds": total_time,
            "transcription_stats": trans_stats.dict() if trans_stats else None,
            "profile_used": settings.detected_profile.value,
            "gpu_used": settings.gpu_memory_gb > 0,
        }

        # Mark job as completed
        await mark_job_completed(
            job_id=job_id,
            transcript=transcript,
            translation=translation,
            summary=summary,
            **outputs,
            processing_stats=processing_stats
        )

        logger.info(
            "Job processing completed",
            job_id=job_id,
            total_time_seconds=total_time,
            profile=settings.detected_profile.value
        )

    except Exception as e:
        logger.error("Job processing failed", job_id=job_id, error=str(e))
        await mark_job_failed(job_id, f"Processing failed: {str(e)}")


async def _preprocess_audio(job) -> str:
    """Preprocess audio/video file for transcription."""
    try:
        file_path = job.file_path

        # Check if it's a URL (for future URL support)
        if file_path.startswith("http"):
            # Download file (implement later)
            raise NotImplementedError("URL downloads not yet implemented")

        # Validate and get audio info
        audio_info = await validate_audio_file(file_path)

        # Extract audio if it's a video
        if file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            audio_path = file_path.rsplit('.', 1)[0] + '.wav'
            audio_path = extract_audio_from_video(file_path, audio_path)
        else:
            audio_path = file_path

        # Check if chunking is needed
        if audio_info["duration"] > settings.chunk_size_seconds:
            # Split into chunks for parallel processing
            chunk_dir = os.path.join(settings.processed_dir, f"chunks_{job.id}")
            os.makedirs(chunk_dir, exist_ok=True)

            chunks = split_audio_into_chunks(
                audio_path,
                chunk_dir,
                chunk_duration=settings.chunk_size_seconds,
                overlap=settings.chunk_overlap_seconds
            )

            logger.info("Audio split into chunks", job_id=job.id, chunks=len(chunks))

            # For now, return the main audio file
            # TODO: Implement parallel chunk processing
            return audio_path
        else:
            return audio_path

    except Exception as e:
        logger.error("Audio preprocessing failed", job_id=job.id, error=str(e))
        raise


async def _generate_outputs(job_id: str, segments: List[Dict], translation: str = None, summary: str = None) -> Dict:
    """Generate output files (SRT, VTT, etc.)."""
    try:
        outputs = {}

        # Generate SRT subtitles
        srt_content = _generate_srt(segments, translation)
        if srt_content:
            outputs["subtitles_srt"] = srt_content

        # Generate VTT subtitles
        vtt_content = _generate_vtt(segments, translation)
        if vtt_content:
            outputs["subtitles_vtt"] = vtt_content

        # TODO: Generate TTS audio summary if enabled
        # if settings.enable_tts and summary:
        #     audio_summary_url = await tts_service.generate_speech(summary)
        #     outputs["audio_summary_url"] = audio_summary_url

        return outputs

    except Exception as e:
        logger.error("Output generation failed", job_id=job_id, error=str(e))
        return {}


@celery_app.task(bind=True, name="transcribe_chunk")
def transcribe_chunk(self, chunk_path: str, language: str = "ar") -> Dict:
    """Transcribe a single audio chunk."""
    try:
        logger.info("Transcribing chunk", chunk_path=chunk_path)

        # This would run in parallel for chunked processing
        transcript, segments = transcription_service.transcribe_chunk(
            chunk_path,
            language=language
        )

        return {
            "transcript": transcript,
            "segments": segments,
        }

    except Exception as e:
        logger.error("Chunk transcription failed", chunk_path=chunk_path, error=str(e))
        raise


def _generate_srt(segments: List[Dict], translation: str = None) -> str:
    """Generate SRT subtitle format."""
    srt_lines = []

    for i, segment in enumerate(segments, 1):
        start_time = _format_timestamp(segment["start"])
        end_time = _format_timestamp(segment["end"])

        # Use translation if available, otherwise original text
        if translation:
            # This is a simplified approach - in reality you'd need to align translation with segments
            text = segment["text"]
        else:
            text = segment["text"]

        srt_lines.extend([
            str(i),
            f"{start_time} --> {end_time}",
            text,
            ""  # Empty line
        ])

    return "\n".join(srt_lines)


def _generate_vtt(segments: List[Dict], translation: str = None) -> str:
    """Generate VTT subtitle format."""
    vtt_lines = ["WEBVTT", ""]

    for segment in segments:
        start_time = _format_timestamp(segment["start"])
        end_time = _format_timestamp(segment["end"])
        text = segment["text"]

        vtt_lines.extend([
            f"{start_time} --> {end_time}",
            text,
            ""
        ])

    return "\n".join(vtt_lines)


def _format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS.mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)

    if hours > 0:
        return "02d"
    else:
        return "02d"