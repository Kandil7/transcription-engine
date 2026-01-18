"""Service layer for job management."""

from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.job import Job as DBJob
from app.db.session import get_db
from app.models.job import Job, JobCreate, JobStatus, JobUpdate
from app.services.websocket_manager import ws_manager


async def create_job(job_data: JobCreate) -> Job:
    """Create a new transcription job."""
    async with get_db() as session:
        db_job = DBJob(
            id=job_data.id,
            filename=job_data.filename,
            file_path=job_data.file_path,
            file_size=job_data.file_size,
            duration=job_data.duration,
            language=job_data.language,
            status=job_data.status.value,
            enable_translation=job_data.enable_translation,
            enable_summary=job_data.enable_summary,
            enable_voice_analytics=job_data.enable_voice_analytics,
            target_language=job_data.target_language,
            summary_length=job_data.summary_length,
            text_sample=job_data.text_sample,
        )

        session.add(db_job)
        await session.commit()
        await session.refresh(db_job)

        return _db_to_model(db_job)


async def get_job(job_id: str) -> Optional[Job]:
    """Get a job by ID."""
    async with get_db() as session:
        db_job = await session.get(DBJob, job_id)
        return _db_to_model(db_job) if db_job else None


async def update_job(job_id: str, update_data: JobUpdate) -> Optional[Job]:
    """Update an existing job."""
    async with get_db() as session:
        db_job = await session.get(DBJob, job_id)
        if not db_job:
            return None

        # Update fields
        for field, value in update_data.dict(exclude_unset=True).items():
            if field == "status" and isinstance(value, JobStatus):
                setattr(db_job, field, value.value)
            else:
                setattr(db_job, field, value)

        # Set timestamps
        if update_data.status == JobStatus.PROCESSING and not db_job.started_at:
            from datetime import datetime
            db_job.started_at = datetime.utcnow()
        elif update_data.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            from datetime import datetime
            db_job.completed_at = datetime.utcnow()

        await session.commit()
        await session.refresh(db_job)

        # Notify WebSocket clients
        updated_job = _db_to_model(db_job)
        await ws_manager.send_to_job(job_id, {
            "type": "job_status",
            "job_id": job_id,
            "status": updated_job.status.value,
            "progress": updated_job.progress,
            "message": updated_job.message,
        })

        return updated_job


async def get_user_jobs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[JobStatus] = None
) -> List[Job]:
    """Get jobs with optional filtering."""
    async with get_db() as session:
        query = session.query(DBJob).order_by(desc(DBJob.created_at))

        if status:
            query = query.filter(DBJob.status == status.value)

        query = query.limit(limit).offset(offset)

        db_jobs = await session.execute(query)
        db_jobs = db_jobs.scalars().all()

        return [_db_to_model(db_job) for db_job in db_jobs]


async def get_job_results(job_id: str) -> dict:
    """Get the results of a completed job."""
    job = await get_job(job_id)
    if not job or job.status != JobStatus.COMPLETED:
        return {}

    return {
        "transcript": job.transcript,
        "translation": job.translation,
        "summary": job.summary,
        "hierarchical_summary": job.hierarchical_summary,
        "voice_analytics": job.voice_analytics,
        "subtitles_srt": job.subtitles_srt,
        "subtitles_vtt": job.subtitles_vtt,
        "audio_summary_url": job.audio_summary_url,
        "processing_stats": job.processing_stats,
    }


async def delete_job(job_id: str) -> bool:
    """Delete a job by ID."""
    async with get_db() as session:
        db_job = await session.get(DBJob, job_id)
        if not db_job:
            return False

        await session.delete(db_job)
        await session.commit()
        return True


async def update_job_progress(job_id: str, progress: float, message: Optional[str] = None) -> None:
    """Update job progress (convenience method)."""
    await update_job(job_id, JobUpdate(progress=progress, message=message))


async def mark_job_completed(job_id: str, results: dict) -> None:
    """Mark a job as completed with results."""
    update_data = JobUpdate(
        status=JobStatus.COMPLETED,
        progress=100.0,
        message="Job completed successfully",
        **results
    )
    await update_job(job_id, update_data)


async def mark_job_failed(job_id: str, error_message: str) -> None:
    """Mark a job as failed."""
    await update_job(job_id, JobUpdate(
        status=JobStatus.FAILED,
        message=error_message
    ))


def _db_to_model(db_job: DBJob) -> Job:
    """Convert database model to Pydantic model."""
    return Job(
        id=db_job.id,
        filename=db_job.filename,
        file_path=db_job.file_path,
        file_size=db_job.file_size,
        duration=db_job.duration,
        language=db_job.language,
        status=JobStatus(db_job.status),
        progress=db_job.progress,
        message=db_job.message,
        enable_translation=db_job.enable_translation,
        enable_summary=db_job.enable_summary,
        enable_voice_analytics=db_job.enable_voice_analytics,
        target_language=db_job.target_language,
        summary_length=db_job.summary_length,
        text_sample=db_job.text_sample,
        transcript=db_job.transcript,
    translation=db_job.translation,
    summary=db_job.summary,
    hierarchical_summary=db_job.hierarchical_summary,
    voice_analytics=db_job.voice_analytics,
    subtitles_srt=db_job.subtitles_srt,
    subtitles_vtt=db_job.subtitles_vtt,
    audio_summary_url=db_job.audio_summary_url,
        created_at=db_job.created_at,
        updated_at=db_job.updated_at,
        started_at=db_job.started_at,
        completed_at=db_job.completed_at,
        processing_stats=db_job.processing_stats,
        processing_profile=db_job.processing_profile,
        gpu_used=db_job.gpu_used,
    )