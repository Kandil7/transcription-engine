"""Upload endpoint for handling file uploads and starting transcription jobs."""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from structlog import get_logger

from app.config import settings
from app.core.exceptions import FileProcessingError, ValidationError
from app.core.storage import upload_file
from app.models.job import JobCreate, JobStatus
from app.services.job_service import create_job
from app.utils.audio import validate_audio_file
from app.utils.download import download_file_from_url

logger = get_logger(__name__)
router = APIRouter()


class UploadResponse(BaseModel):
    """Response model for file upload."""

    job_id: str
    status: str
    message: str
    estimated_duration_seconds: Optional[int] = None


@router.post("/file", response_model=UploadResponse)
async def upload_audio_file(
    file: UploadFile = File(...),
    language: str = Form("ar", description="Language code (ar, en, etc.)"),
    enable_translation: bool = Form(True, description="Enable translation to English"),
    enable_summary: bool = Form(True, description="Enable summarization"),
    enable_voice_analytics: bool = Form(False, description="Enable voice analytics (speaker diarization & emotion detection)"),
    target_language: str = Form("en", description="Target language for translation"),
    summary_length: str = Form("medium", description="Summary length (short/medium/long)"),
    text_sample: Optional[str] = Form(None, description="Text sample for Egyptian dialect detection"),
) -> UploadResponse:
    """
    Upload an audio/video file for transcription.

    - **file**: Audio or video file (max 500MB)
    - **language**: Source language code
    - **enable_translation**: Whether to translate the content
    - **enable_summary**: Whether to generate a summary
    - **target_language**: Target language for translation
    - **summary_length**: Length of summary (short/medium/long)
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )

        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB"
            )

        # Validate audio/video file
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in ['.mp3', '.wav', '.mp4', '.avi', '.mov', '.m4a', '.webm']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file format. Supported: mp3, wav, mp4, avi, mov, m4a, webm"
            )

        # Reset file pointer
        await file.seek(0)

        # Generate job ID
        job_id = str(uuid.uuid4())

        # Upload file to storage
        file_path = await upload_file(content, f"{job_id}_{file.filename}")

        # Validate audio file properties
        audio_info = await validate_audio_file(file_path)
        if audio_info["duration"] > settings.max_duration_hours * 3600:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio too long. Maximum duration: {settings.max_duration_hours} hours"
            )

        # Create job record
        job_data = JobCreate(
            id=job_id,
            filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            duration=audio_info["duration"],
            language=language,
            status=JobStatus.PENDING,
            enable_translation=enable_translation,
            enable_summary=enable_summary,
            enable_voice_analytics=enable_voice_analytics,
            target_language=target_language,
            summary_length=summary_length,
            text_sample=text_sample,
        )

        await create_job(job_data)

        # Start the processing task
        from app.tasks.transcription_tasks import process_transcription_job
        process_transcription_job.delay(job_id)

        # Estimate processing time based on hardware profile
        estimated_seconds = _estimate_processing_time(audio_info["duration"])

        logger.info(
            "File uploaded successfully",
            job_id=job_id,
            filename=file.filename,
            file_size=file_size,
            duration=audio_info["duration"],
            profile=settings.detected_profile.value
        )

        return UploadResponse(
            job_id=job_id,
            status="uploaded",
            message="File uploaded successfully. Processing started.",
            estimated_duration_seconds=estimated_seconds
        )

    except HTTPException:
        raise
    except (FileProcessingError, ValidationError):
        raise
    except Exception as e:
        logger.error("Upload failed", error=str(e), filename=file.filename)
        raise FileProcessingError(
            message="Upload failed due to internal error",
            file_path=file.filename,
            details={"error": str(e)}
        )


@router.post("/url", response_model=UploadResponse)
async def upload_from_url(
    url: str = Form(..., description="URL of the audio/video file"),
    language: str = Form("ar", description="Language code (ar, en, etc.)"),
    enable_translation: bool = Form(True, description="Enable translation to English"),
    enable_summary: bool = Form(True, description="Enable summarization"),
    target_language: str = Form("en", description="Target language for translation"),
    summary_length: str = Form("medium", description="Summary length (short/medium/long)"),
) -> UploadResponse:
    """
    Upload from URL for transcription.

    - **url**: URL of the audio/video file
    - **language**: Source language code
    - **enable_translation**: Whether to translate the content
    - **enable_summary**: Whether to generate a summary
    - **target_language**: Target language for translation
    - **summary_length**: Length of summary (short/medium/long)
    """
    try:
        # Generate job ID
        job_id = str(uuid.uuid4())

        # Download file from URL
        logger.info("Downloading file from URL", job_id=job_id, url=url)
        file_path = await download_file_from_url(
            url,
            output_path=os.path.join(settings.upload_dir, f"{job_id}_downloaded"),
            max_size_mb=settings.max_file_size_mb,
        )

        # Get file size
        file_size = os.path.getsize(file_path)

        # Validate audio file and get duration
        audio_info = await validate_audio_file(file_path)
        if audio_info["duration"] > settings.max_duration_hours * 3600:
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Audio too long. Maximum duration: {settings.max_duration_hours} hours"
            )

        # Create job record
        job_data = JobCreate(
            id=job_id,
            filename=os.path.basename(file_path),
            file_path=file_path,
            file_size=file_size,
            duration=audio_info["duration"],
            language=language,
            status=JobStatus.PENDING,
            enable_translation=enable_translation,
            enable_summary=enable_summary,
            target_language=target_language,
            summary_length=summary_length,
        )

        await create_job(job_data)

        # Start the processing task
        from app.tasks.transcription_tasks import process_transcription_job
        process_transcription_job.delay(job_id)

        # Estimate processing time
        estimated_seconds = _estimate_processing_time(audio_info["duration"])

        logger.info(
            "URL upload job created successfully",
            job_id=job_id,
            url=url,
            file_size=file_size,
            duration=audio_info["duration"]
        )

        return UploadResponse(
            job_id=job_id,
            status="uploaded",
            message="File downloaded from URL. Processing started.",
            estimated_duration_seconds=estimated_seconds
        )

    except Exception as e:
        logger.error("URL upload failed", error=str(e), url=url)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="URL upload failed due to internal error"
        )


def _estimate_processing_time(audio_duration_seconds: float) -> int:
    """Estimate processing time based on hardware profile and audio duration."""
    profile = settings.detected_profile

    # Base processing speed (real-time factor) for different profiles
    speed_factors = {
        "ultra": 100,      # 100x real-time
        "std_gpu": 50,     # 50x real-time
        "cpu_strong": 10,  # 10x real-time
        "edge_weak": 2,    # 2x real-time
    }

    speed_factor = speed_factors.get(profile.value, 10)

    # Add overhead for translation, summary, etc.
    overhead_factor = 1.5  # 50% overhead

    estimated_seconds = (audio_duration_seconds / speed_factor) * overhead_factor

    return int(estimated_seconds)