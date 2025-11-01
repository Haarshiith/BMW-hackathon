import uuid
import aiofiles
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from pathlib import Path
from app.config import settings
from app.schemas.file_upload import (
    FileUploadResponse,
    MultipleFileUploadResponse,
    FileValidationError,
    FileUploadRequest,
)
import logging

logger = logging.getLogger(__name__)


class FileUploadService:
    """Service for handling file uploads and storage"""

    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.max_file_size = settings.max_file_size
        self.allowed_types = settings.allowed_file_types.split(",")

        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, file: UploadFile) -> Optional[FileValidationError]:
        """
        Validate a single file

        Args:
            file: UploadFile object to validate

        Returns:
            FileValidationError if validation fails, None if valid
        """
        # Check file size
        if hasattr(file, "size") and file.size and file.size > self.max_file_size:
            return FileValidationError(
                filename=file.filename or "unknown",
                error=f"File size {file.size} exceeds maximum allowed size {self.max_file_size} bytes",
                error_code="FILE_TOO_LARGE",
            )

        # Check file type
        if file.content_type not in self.allowed_types:
            return FileValidationError(
                filename=file.filename or "unknown",
                error=f"File type {file.content_type} is not allowed. Allowed types: {', '.join(self.allowed_types)}",
                error_code="INVALID_FILE_TYPE",
            )

        # Check filename
        if not file.filename or file.filename.strip() == "":
            return FileValidationError(
                filename="unknown",
                error="Filename is required",
                error_code="MISSING_FILENAME",
            )

        return None

    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to avoid conflicts

        Args:
            original_filename: Original filename

        Returns:
            Unique filename
        """
        # Get file extension
        file_extension = Path(original_filename).suffix

        # Generate unique filename with timestamp and UUID
        unique_id = str(uuid.uuid4())[:8]
        timestamp = int(uuid.uuid4().time_low)
        unique_filename = f"{timestamp}_{unique_id}{file_extension}"

        return unique_filename

    async def upload_single_file(self, file: UploadFile) -> FileUploadResponse:
        """
        Upload a single file

        Args:
            file: UploadFile object

        Returns:
            FileUploadResponse with upload details

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate file
            validation_error = self._validate_file(file)
            if validation_error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_error.error,
                )

            # Generate unique filename
            unique_filename = self._generate_unique_filename(file.filename)
            file_path = self.upload_dir / unique_filename

            # Read file content
            content = await file.read()

            # Check file size after reading
            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File size {len(content)} exceeds maximum allowed size {self.max_file_size} bytes",
                )

            # Write file to disk
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            # Get file size
            file_size = len(content)

            logger.info(
                f"Successfully uploaded file: {unique_filename} ({file_size} bytes)"
            )

            return FileUploadResponse(
                filename=file.filename,
                saved_filename=unique_filename,
                file_path=str(file_path),
                file_size=file_size,
                content_type=file.content_type,
                upload_successful=True,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}",
            )

    async def upload_multiple_files(
        self, files: List[UploadFile], max_files: int = 5
    ) -> MultipleFileUploadResponse:
        """
        Upload multiple files

        Args:
            files: List of UploadFile objects
            max_files: Maximum number of files allowed

        Returns:
            MultipleFileUploadResponse with upload results
        """
        try:
            # Check file count
            if len(files) > max_files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Too many files. Maximum allowed: {max_files}",
                )

            successful_uploads = []
            failed_uploads = []

            for file in files:
                try:
                    upload_result = await self.upload_single_file(file)
                    successful_uploads.append(upload_result)
                except HTTPException as e:
                    failed_uploads.append(
                        {"filename": file.filename or "unknown", "error": e.detail}
                    )
                except Exception as e:
                    failed_uploads.append(
                        {
                            "filename": file.filename or "unknown",
                            "error": f"Unexpected error: {str(e)}",
                        }
                    )

            return MultipleFileUploadResponse(
                successful_uploads=successful_uploads,
                failed_uploads=failed_uploads,
                total_files=len(files),
                successful_count=len(successful_uploads),
                failed_count=len(failed_uploads),
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to upload multiple files: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload files: {str(e)}",
            )

    async def delete_file(self, filename: str) -> bool:
        """
        Delete a file from storage

        Args:
            filename: Name of the file to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            file_path = self.upload_dir / filename

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Successfully deleted file: {filename}")
                return True
            else:
                logger.warning(f"File not found for deletion: {filename}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {e}")
            return False

    async def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file

        Args:
            filename: Name of the file

        Returns:
            File information dict or None if file doesn't exist
        """
        try:
            file_path = self.upload_dir / filename

            if not file_path.exists():
                return None

            stat = file_path.stat()

            return {
                "filename": filename,
                "file_path": str(file_path),
                "file_size": stat.st_size,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "exists": True,
            }

        except Exception as e:
            logger.error(f"Failed to get file info for {filename}: {e}")
            return None

    def get_upload_config(self) -> FileUploadRequest:
        """
        Get current upload configuration

        Returns:
            FileUploadRequest with current settings
        """
        return FileUploadRequest(
            max_file_size=self.max_file_size,
            allowed_types=self.allowed_types,
            max_files=5,
        )


# Global instance
file_upload_service = FileUploadService()
