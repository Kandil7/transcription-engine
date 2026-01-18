"""URL download utilities for remote file fetching."""

import os
from typing import Optional
from urllib.parse import urlparse

import httpx
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


async def download_file_from_url(
    url: str,
    output_path: Optional[str] = None,
    max_size_mb: int = 500,
    timeout: int = 300
) -> str:
    """
    Download a file from a URL.

    Args:
        url: URL of the file to download
        output_path: Optional output path. If not provided, generates one from URL
        max_size_mb: Maximum file size in MB (default: 500MB)
        timeout: Request timeout in seconds (default: 300)

    Returns:
        Path to the downloaded file

    Raises:
        ValueError: If URL is invalid or file is too large
        httpx.HTTPError: If download fails
    """
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {url}")

        # Generate output path if not provided
        if not output_path:
            filename = os.path.basename(parsed.path) or f"download_{hash(url)}"
            # Ensure filename has extension
            if not os.path.splitext(filename)[1]:
                filename += ".mp3"  # Default extension
            
            os.makedirs(settings.upload_dir, exist_ok=True)
            output_path = os.path.join(settings.upload_dir, filename)

        logger.info("Downloading file from URL", url=url, output_path=output_path)

        # Download with streaming to handle large files
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()

                # Check content length
                content_length = response.headers.get("content-length")
                if content_length:
                    size_mb = int(content_length) / (1024 * 1024)
                    if size_mb > max_size_mb:
                        raise ValueError(
                            f"File too large: {size_mb:.2f}MB (max: {max_size_mb}MB)"
                        )

                # Download with size limit
                max_bytes = max_size_mb * 1024 * 1024
                downloaded = 0

                with open(output_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        downloaded += len(chunk)
                        if downloaded > max_bytes:
                            os.remove(output_path)
                            raise ValueError(
                                f"File exceeds maximum size: {max_size_mb}MB"
                            )
                        f.write(chunk)

        file_size_mb = downloaded / (1024 * 1024)
        logger.info(
            "File downloaded successfully",
            url=url,
            output_path=output_path,
            size_mb=f"{file_size_mb:.2f}"
        )

        return output_path

    except httpx.HTTPError as e:
        logger.error("HTTP error downloading file", url=url, error=str(e))
        raise
    except ValueError as e:
        logger.error("Validation error downloading file", url=url, error=str(e))
        raise
    except Exception as e:
        logger.error("Unexpected error downloading file", url=url, error=str(e))
        raise
