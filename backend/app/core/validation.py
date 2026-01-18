"""Environment and configuration validation."""

import os
from typing import List, Optional

import asyncpg
import redis.asyncio as redis
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def _get_configuration_error():
    """Lazy import to avoid circular dependency."""
    from app.core.exceptions import ConfigurationError
    return ConfigurationError


async def validate_database_connection() -> bool:
    """Validate database connection."""
    try:
        # Parse database URL
        db_url = settings.database_url
        
        if db_url.startswith("postgresql"):
            # Extract connection details
            if "postgresql+asyncpg://" in db_url:
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
            elif "postgresql://" not in db_url:
                raise ValidationError("Invalid database URL format")
            
            # Parse URL
            import urllib.parse
            parsed = urllib.parse.urlparse(db_url)
            
            # Connect to database
            conn = await asyncpg.connect(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                user=parsed.username or "postgres",
                password=parsed.password or "",
                database=parsed.path.lstrip("/") or "postgres",
            )
            await conn.close()
            
            logger.info("Database connection validated successfully")
            return True
        else:
            # SQLite - just check if directory exists
            if db_url.startswith("sqlite"):
                db_path = db_url.replace("sqlite:///", "").replace("sqlite+aiosqlite:///", "")
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir, exist_ok=True)
                logger.info("SQLite database path validated")
                return True
            
            raise ValidationError(f"Unsupported database type: {db_url}")
            
    except Exception as e:
        logger.error("Database validation failed", error=str(e))
        raise ValidationError(f"Database connection failed: {str(e)}")


async def validate_redis_connection() -> bool:
    """Validate Redis connection."""
    try:
        redis_url = settings.redis_url or settings.celery_broker_url
        
        # Parse Redis URL
        import urllib.parse
        parsed = urllib.parse.urlparse(redis_url)
        
        # Connect to Redis
        r = redis.from_url(redis_url)
        await r.ping()
        await r.close()
        
        logger.info("Redis connection validated successfully")
        return True
        
    except Exception as e:
        logger.error("Redis validation failed", error=str(e))
        ConfigurationError = _get_configuration_error()
        raise ConfigurationError(f"Redis connection failed: {str(e)}")


def validate_storage_config() -> bool:
    """Validate storage configuration."""
    try:
        storage_type = settings.storage_type.lower()
        
        if storage_type == "local":
            # Check if upload directories exist and are writable
            upload_dir = settings.upload_dir
            processed_dir = settings.processed_dir
            
            os.makedirs(upload_dir, exist_ok=True)
            os.makedirs(processed_dir, exist_ok=True)
            
            # Test write permissions
            test_file = os.path.join(upload_dir, ".test_write")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                raise ValidationError(f"Cannot write to upload directory: {str(e)}")
            
            logger.info("Local storage validated successfully")
            return True
            
        elif storage_type == "minio":
            # Validate MinIO configuration
            ConfigurationError = _get_configuration_error()
            if not settings.minio_endpoint:
                raise ConfigurationError("MINIO_ENDPOINT is required when using MinIO storage")
            if not settings.minio_access_key:
                raise ConfigurationError("MINIO_ACCESS_KEY is required when using MinIO storage")
            if not settings.minio_secret_key:
                raise ConfigurationError("MINIO_SECRET_KEY is required when using MinIO storage")
            
            logger.info("MinIO storage configuration validated")
            return True
            
        elif storage_type == "s3":
            # Validate S3 configuration
            ConfigurationError = _get_configuration_error()
            if not settings.aws_access_key_id:
                raise ConfigurationError("AWS_ACCESS_KEY_ID is required when using S3 storage")
            if not settings.aws_secret_access_key:
                raise ConfigurationError("AWS_SECRET_ACCESS_KEY is required when using S3 storage")
            
            logger.info("S3 storage configuration validated")
            return True
            
        else:
            ConfigurationError = _get_configuration_error()
            raise ConfigurationError(f"Unsupported storage type: {storage_type}")
            
    except Exception as e:
        logger.error("Storage validation failed", error=str(e))
        ConfigurationError = _get_configuration_error()
        raise ConfigurationError(f"Storage validation failed: {str(e)}")


def validate_required_directories() -> bool:
    """Validate and create required directories."""
    try:
        directories = [
            settings.upload_dir,
            settings.processed_dir,
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            ConfigurationError = _get_configuration_error()
            if not os.path.isdir(directory):
                raise ConfigurationError(f"Directory does not exist and cannot be created: {directory}")
        
        logger.info("Required directories validated")
        return True
        
    except Exception as e:
        logger.error("Directory validation failed", error=str(e))
        ConfigurationError = _get_configuration_error()
        raise ConfigurationError(f"Directory validation failed: {str(e)}")


def validate_security_settings() -> bool:
    """Validate security-related settings."""
    try:
        ConfigurationError = _get_configuration_error()
        # Check secret key
        if settings.secret_key == "your-secret-key-here" and settings.environment.value == "production":
            logger.warning("Using default secret key in production - this is insecure!")
            raise ConfigurationError("SECRET_KEY must be changed in production")
        
        # Check debug mode
        if settings.debug and settings.environment.value == "production":
            logger.warning("Debug mode enabled in production - this is insecure!")
            raise ConfigurationError("Debug mode must be disabled in production")
        
        logger.info("Security settings validated")
        return True
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error("Security validation failed", error=str(e))
        raise ValidationError(f"Security validation failed: {str(e)}")


async def validate_all() -> List[str]:
    """
    Validate all configuration and connections.
    
    Returns:
        List of validation warnings (empty if all validations pass)
    """
    warnings = []
    
    ConfigurationError = _get_configuration_error()
    
    try:
        # Validate directories
        validate_required_directories()
    except ConfigurationError as e:
        warnings.append(f"Directory validation: {str(e)}")
    
    try:
        # Validate storage
        validate_storage_config()
    except ConfigurationError as e:
        warnings.append(f"Storage validation: {str(e)}")
    
    try:
        # Validate security
        validate_security_settings()
    except ConfigurationError as e:
        warnings.append(f"Security validation: {str(e)}")
    
    # Database and Redis validation are optional (warnings only)
    try:
        await validate_database_connection()
    except ConfigurationError as e:
        warnings.append(f"Database connection: {str(e)} (will retry on startup)")
    
    try:
        await validate_redis_connection()
    except ConfigurationError as e:
        warnings.append(f"Redis connection: {str(e)} (will retry on startup)")
    
    return warnings
