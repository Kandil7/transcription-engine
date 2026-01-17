"""Logging configuration."""

import logging
import sys
from typing import Optional

from structlog import configure, get_logger, stdlib, write_to_loguru
from structlog.contextvars import merge_contextvars

logger = get_logger(__name__)


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Optional[str] = None
):
    """
    Setup structured logging with structlog.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_type: Log format (json, console)
        log_file: Optional log file path
    """
    # Convert string level to logging level
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    log_level = level_map.get(level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Configure structlog
    shared_processors = [
        merge_contextvars,
        stdlib.add_log_level,
        stdlib.add_logger_name,
        stdlib.PositionalArgumentsFormatter(),
    ]

    if format_type == "json":
        # JSON format for production
        shared_processors.extend([
            stdlib.ExtraAdder(),
            write_to_loguru,
        ])
    else:
        # Human-readable format for development
        shared_processors.extend([
            stdlib.ExtraAdder(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ])

    configure(
        processors=shared_processors,
        wrapper_class=stdlib.BoundLogger,
        logger_factory=stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure loguru for output
    import loguru

    loguru.logger.remove()  # Remove default handler

    if format_type == "json":
        loguru.logger.add(
            sys.stdout,
            format="{message}",
            level=log_level,
            serialize=True,  # JSON format
        )
    else:
        loguru.logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
        )

    # Add file handler if specified
    if log_file:
        loguru.logger.add(
            log_file,
            rotation="10 MB",
            retention="1 week",
            level=log_level,
            serialize=format_type == "json",
        )

    logger.info("Logging configured", level=level, format=format_type, log_file=log_file)