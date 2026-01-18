"""QA endpoint for asking questions about transcripts."""

from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from structlog import get_logger

from app.services.job_service import get_job

try:
    from app.services.rag_service import rag_service
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    # Create a dummy service for when RAG is not available
    class DummyRAGService:
        async def ask_question(self, question: str, job_id: str):
            return {
                "answer": "RAG service is not available. Install chromadb and transformers to enable Q&A.",
                "sources": [],
                "confidence": 0.0,
                "job_id": job_id
            }
        async def setup_qa_system(self, transcript: str, job_id: str):
            pass
    rag_service = DummyRAGService()

logger = get_logger(__name__)
router = APIRouter()


class QuestionRequest(BaseModel):
    """Request model for asking questions."""

    question: str


class AnswerResponse(BaseModel):
    """Response model for answers."""

    answer: str
    sources: list
    confidence: float
    job_id: str


@router.post("/{job_id}/ask", response_model=AnswerResponse)
async def ask_question(job_id: str, request: QuestionRequest) -> AnswerResponse:
    """
    Ask a question about a transcript.

    - **job_id**: Unique job identifier
    - **question**: Question to ask about the transcript
    """
    try:
        # Validate job exists and is completed
        job = await get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        if job.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is not completed. Current status: {job.status}"
            )

        if not job.transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript available for this job"
            )

        # Ask the question using RAG
        result = await rag_service.ask_question(request.question, job_id)

        return AnswerResponse(
            answer=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            job_id=job_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Question answering failed", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to answer question"
        )


@router.post("/{job_id}/setup-qa")
async def setup_qa_system(job_id: str):
    """
    Set up QA system for a completed job.

    - **job_id**: Unique job identifier
    """
    try:
        # Validate job exists and is completed
        job = await get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )

        if job.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job is not completed. Current status: {job.status}"
            )

        if not job.transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No transcript available for this job"
            )

        # Set up QA system
        await rag_service.setup_qa_system(job.transcript, job_id)

        return {
            "message": "QA system set up successfully",
            "job_id": job_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("QA setup failed", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set up QA system"
        )