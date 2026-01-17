"""Monitoring and metrics setup."""

from typing import Callable

from prometheus_client import Counter, Gauge, Histogram
from structlog import get_logger

logger = get_logger(__name__)

# Metrics definitions
# Counters
jobs_processed_total = Counter(
    "transcription_jobs_processed_total",
    "Total number of jobs processed",
    ["status", "profile"]
)

jobs_processing_duration = Histogram(
    "transcription_jobs_processing_duration_seconds",
    "Time spent processing jobs",
    ["profile"]
)

# Gauges
active_jobs = Gauge(
    "transcription_active_jobs",
    "Number of currently active jobs"
)

gpu_memory_used = Gauge(
    "transcription_gpu_memory_used_mb",
    "GPU memory currently used in MB"
)

model_load_status = Gauge(
    "transcription_model_load_status",
    "Status of model loading (1=loaded, 0=not loaded)",
    ["model_type"]
)

# Histograms
api_request_duration = Histogram(
    "transcription_api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint", "status"]
)

transcription_duration = Histogram(
    "transcription_duration_seconds",
    "Time spent on transcription",
    ["model", "profile"]
)


def init_monitoring():
    """Initialize monitoring and metrics."""
    logger.info("Initializing monitoring")

    # Register metrics
    # They are automatically registered when imported

    # Set initial values
    model_load_status.labels(model_type="whisper").set(0)
    model_load_status.labels(model_type="translation").set(0)
    model_load_status.labels(model_type="summarization").set(0)

    logger.info("Monitoring initialized")


def track_job_metrics(status: str, profile: str, duration: float = None):
    """Track job processing metrics."""
    jobs_processed_total.labels(status=status, profile=profile).inc()

    if duration:
        jobs_processing_duration.labels(profile=profile).observe(duration)


def track_api_request(method: str, endpoint: str, status: int, duration: float):
    """Track API request metrics."""
    api_request_duration.labels(
        method=method,
        endpoint=endpoint,
        status=str(status)
    ).observe(duration)


def update_active_jobs(count: int):
    """Update active jobs gauge."""
    active_jobs.set(count)


def update_gpu_memory(used_mb: float):
    """Update GPU memory usage."""
    gpu_memory_used.set(used_mb)


def update_model_status(model_type: str, loaded: bool):
    """Update model load status."""
    model_load_status.labels(model_type=model_type).set(1 if loaded else 0)


def monitor_function(func: Callable) -> Callable:
    """Decorator to monitor function execution."""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            # Could add custom metrics here
            return result
        except Exception as e:
            duration = time.time() - start_time
            # Could add error metrics here
            raise

    return wrapper