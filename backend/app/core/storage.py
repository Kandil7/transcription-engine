"""Storage utilities for file management."""

import os
from typing import Optional

from minio import Minio
from structlog import get_logger

from app.config import settings

logger = get_logger(__name__)


class StorageClient:
    """Unified storage client supporting local and cloud storage."""

    def __init__(self):
        self.client: Optional[Minio] = None
        self.storage_type = settings.storage_type

        if self.storage_type == "minio":
            self.client = Minio(
                endpoint=settings.minio_endpoint or "localhost:9000",
                access_key=settings.minio_access_key or "minioadmin",
                secret_key=settings.minio_secret_key or "minioadmin",
                secure=settings.minio_secure,
            )
            self.bucket = settings.minio_bucket

        elif self.storage_type == "s3":
            self.client = Minio(
                endpoint=settings.aws_region + ".amazonaws.com",
                access_key=settings.aws_access_key_id,
                secret_key=settings.aws_secret_access_key,
                secure=True,
            )
            self.bucket = settings.s3_bucket

    async def upload_file(self, file_data: bytes, filename: str) -> str:
        """
        Upload file to storage.

        Args:
            file_data: File content as bytes
            filename: Filename to store as

        Returns:
            Storage path/URL for the uploaded file
        """
        try:
            if self.storage_type in ["minio", "s3"]:
                # Upload to MinIO/S3
                from io import BytesIO

                data_stream = BytesIO(file_data)
                self.client.put_object(
                    bucket_name=self.bucket,
                    object_name=filename,
                    data=data_stream,
                    length=len(file_data),
                )

                if self.storage_type == "minio":
                    return f"{settings.minio_endpoint}/{self.bucket}/{filename}"
                else:
                    return f"https://{self.bucket}.s3.{settings.aws_region}.amazonaws.com/{filename}"

            else:
                # Local storage
                os.makedirs(settings.upload_dir, exist_ok=True)
                file_path = os.path.join(settings.upload_dir, filename)

                with open(file_path, "wb") as f:
                    f.write(file_data)

                return file_path

        except Exception as e:
            logger.error("File upload failed", filename=filename, error=str(e))
            raise

    async def download_file(self, file_path: str) -> bytes:
        """
        Download file from storage.

        Args:
            file_path: Storage path/URL of the file

        Returns:
            File content as bytes
        """
        try:
            if self.storage_type in ["minio", "s3"]:
                # Download from MinIO/S3
                if self.storage_type == "minio":
                    object_name = file_path.split(f"/{self.bucket}/")[-1]
                else:
                    object_name = file_path.split(f"/{self.bucket}/")[-1]

                response = self.client.get_object(self.bucket, object_name)
                return response.read()

            else:
                # Local file
                with open(file_path, "rb") as f:
                    return f.read()

        except Exception as e:
            logger.error("File download failed", file_path=file_path, error=str(e))
            raise

    async def delete_file(self, file_path: str) -> None:
        """
        Delete file from storage.

        Args:
            file_path: Storage path/URL of the file
        """
        try:
            if self.storage_type in ["minio", "s3"]:
                # Delete from MinIO/S3
                if self.storage_type == "minio":
                    object_name = file_path.split(f"/{self.bucket}/")[-1]
                else:
                    object_name = file_path.split(f"/{self.bucket}/")[-1]

                self.client.remove_object(self.bucket, object_name)

            else:
                # Local file
                if os.path.exists(file_path):
                    os.remove(file_path)

        except Exception as e:
            logger.error("File deletion failed", file_path=file_path, error=str(e))
            raise

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            file_path: Storage path/URL of the file

        Returns:
            True if file exists, False otherwise
        """
        try:
            if self.storage_type in ["minio", "s3"]:
                # Check in MinIO/S3
                if self.storage_type == "minio":
                    object_name = file_path.split(f"/{self.bucket}/")[-1]
                else:
                    object_name = file_path.split(f"/{self.bucket}/")[-1]

                self.client.stat_object(self.bucket, object_name)
                return True

            else:
                # Local file
                return os.path.exists(file_path)

        except Exception:
            return False


# Global storage client instance
storage_client = StorageClient()


async def upload_file(file_data: bytes, filename: str) -> str:
    """Convenience function to upload file."""
    return await storage_client.upload_file(file_data, filename)


async def download_file(file_path: str) -> bytes:
    """Convenience function to download file."""
    return await storage_client.download_file(file_path)


async def delete_file(file_path: str) -> None:
    """Convenience function to delete file."""
    await storage_client.delete_file(file_path)


async def file_exists(file_path: str) -> bool:
    """Convenience function to check if file exists."""
    return await storage_client.file_exists(file_path)