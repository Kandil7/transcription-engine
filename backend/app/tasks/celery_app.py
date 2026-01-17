"""Celery application configuration."""

from celery import Celery
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "transcription_engine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.transcription_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Worker settings
    worker_prefetch_multiplier=1,  # Important for GPU tasks
    task_acks_late=True,
    worker_disable_rate_limits=False,

    # Result backend settings
    result_expires=3600,  # 1 hour

    # Routing for GPU tasks
    task_routes={
        "app.tasks.transcription_tasks.process_transcription_job": {"queue": "gpu"},
        "app.tasks.transcription_tasks.transcribe_chunk": {"queue": "gpu"},
    },

    # Queue definitions
    task_default_queue="celery",
    task_queues={
        "celery": {"exchange": "celery", "routing_key": "celery"},
        "gpu": {"exchange": "gpu", "routing_key": "gpu"},
    },
)

# Setup logging
@celery_app.on_after_configure.connect
def setup_logging(sender, **kwargs):
    """Setup structured logging for Celery."""
    from app.core.logging import setup_logging
    setup_logging()


if __name__ == "__main__":
    celery_app.start()