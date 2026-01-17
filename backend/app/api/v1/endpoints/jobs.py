"""Jobs endpoint for managing transcription jobs."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from structlog import get_logger

from app.models.job import JobStatus
from app.services.job_service import get_job, get_job_results, get_user_jobs

logger = get_logger(__name__)
router = APIRouter()


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    created_at: str
    updated_at: str
    filename: str
    duration: Optional[float] = None
    language: str
    enable_translation: bool
    enable_summary: bool
    target_language: Optional[str] = None
    summary_length: Optional[str] = None


class JobResultsResponse(BaseModel):
    """Response model for job results."""

    id: str
    transcript: Optional[str] = None
    translation: Optional[str] = None
    summary: Optional[str] = None
    hierarchical_summary: Optional[dict] = None
    subtitles_srt: Optional[str] = None
    subtitles_vtt: Optional[str] = None
    audio_summary_url: Optional[str] = None
    processing_stats: Optional[dict] = None


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a transcription job.

    - **job_id**: Unique job identifier
    """
    try:
        job = await get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        return JobStatusResponse(
            id=job.id,
            status=job.status.value,
            progress=job.progress,
            message=job.message,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat(),
            filename=job.filename,
            duration=job.duration,
            language=job.language,
            enable_translation=job.enable_translation,
            enable_summary=job.enable_summary,
            target_language=job.target_language,
            summary_length=job.summary_length,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )


@router.get("/{job_id}/results", response_model=JobResultsResponse)
async def get_job_results_endpoint(job_id: str) -> JobResultsResponse:
    """
    Get the results of a completed transcription job.

    - **job_id**: Unique job identifier
    """
    try:
        job = await get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        if job.status != JobStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is not completed. Current status: {job.status.value}"
            )

        results = await get_job_results(job_id)

        return JobResultsResponse(
            id=job_id,
            transcript=results.get("transcript"),
            translation=results.get("translation"),
            summary=results.get("summary"),
            hierarchical_summary=results.get("hierarchical_summary"),
            subtitles_srt=results.get("subtitles_srt"),
            subtitles_vtt=results.get("subtitles_vtt"),
            audio_summary_url=results.get("audio_summary_url"),
            processing_stats=results.get("processing_stats"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get job results", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job results"
        )


@router.get("/", response_model=List[JobStatusResponse])
async def list_jobs(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None
) -> List[JobStatusResponse]:
    """
    List transcription jobs.

    - **limit**: Maximum number of jobs to return (default: 50)
    - **offset**: Number of jobs to skip (default: 0)
    - **status_filter**: Filter by job status (pending, processing, completed, failed)
    """
    try:
        status_enum = None
        if status_filter:
            try:
                status_enum = JobStatus(status_filter.lower())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )

        jobs = await get_user_jobs(limit=limit, offset=offset, status=status_enum)

        return [
            JobStatusResponse(
                id=job.id,
                status=job.status.value,
                progress=job.progress,
                message=job.message,
                created_at=job.created_at.isoformat(),
                updated_at=job.updated_at.isoformat(),
                filename=job.filename,
                duration=job.duration,
                language=job.language,
                enable_translation=job.enable_translation,
                enable_summary=job.enable_summary,
                target_language=job.target_language,
                summary_length=job.summary_length,
            )
            for job in jobs
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )