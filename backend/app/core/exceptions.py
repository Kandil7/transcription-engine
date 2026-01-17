"""Custom exception classes for the Transcription Engine."""

from typing import Any, Dict, Optional


class TranscriptionEngineError(Exception):
    """Base exception class for Transcription Engine errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(TranscriptionEngineError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details={"field": field, **(details or {})}
        )


class FileProcessingError(TranscriptionEngineError):
    """Raised when file processing fails."""

    def __init__(self, message: str, file_path: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            status_code=400,
            details={"file_path": file_path, **(details or {})}
        )


class ModelError(TranscriptionEngineError):
    """Raised when AI model operations fail."""

    def __init__(self, message: str, model_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="MODEL_ERROR",
            status_code=500,
            details={"model_name": model_name, **(details or {})}
        )


class StorageError(TranscriptionEngineError):
    """Raised when storage operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            status_code=500,
            details={"operation": operation, **(details or {})}
        )


class DatabaseError(TranscriptionEngineError):
    """Raised when database operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details={"operation": operation, **(details or {})}
        )


class JobNotFoundError(TranscriptionEngineError):
    """Raised when a job is not found."""

    def __init__(self, job_id: str):
        super().__init__(
            message=f"Job with ID '{job_id}' not found",
            error_code="JOB_NOT_FOUND",
            status_code=404,
            details={"job_id": job_id}
        )


class JobProcessingError(TranscriptionEngineError):
    """Raised when job processing fails."""

    def __init__(self, job_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="JOB_PROCESSING_ERROR",
            status_code=500,
            details={"job_id": job_id, **(details or {})}
        )


class RateLimitError(TranscriptionEngineError):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details={"retry_after": retry_after}
        )


class AuthenticationError(TranscriptionEngineError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401
        )


class AuthorizationError(TranscriptionEngineError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403
        )


class ServiceUnavailableError(TranscriptionEngineError):
    """Raised when external services are unavailable."""

    def __init__(self, service_name: str, message: Optional[str] = None):
        super().__init__(
            message=message or f"Service '{service_name}' is currently unavailable",
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            details={"service": service_name}
        )


class ConfigurationError(TranscriptionEngineError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            status_code=500,
            details={"config_key": config_key}
        )