from typing import List, Dict
from pydantic import BaseModel, Field, validator


class FileUploadResponse(BaseModel):
    """Response schema for file upload"""

    filename: str = Field(..., description="Original filename")
    saved_filename: str = Field(..., description="Filename as saved on server")
    file_path: str = Field(..., description="Full path to saved file")
    file_size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    upload_successful: bool = Field(..., description="Whether upload was successful")


class MultipleFileUploadResponse(BaseModel):
    """Response schema for multiple file uploads"""

    successful_uploads: List[FileUploadResponse] = Field(
        ..., description="Successfully uploaded files"
    )
    failed_uploads: List[Dict[str, str]] = Field(
        ..., description="Failed uploads with error messages"
    )
    total_files: int = Field(..., description="Total number of files attempted")
    successful_count: int = Field(..., description="Number of successful uploads")
    failed_count: int = Field(..., description="Number of failed uploads")


class FileValidationError(BaseModel):
    """Schema for file validation errors"""

    filename: str = Field(..., description="Name of the file that failed validation")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for programmatic handling")


class FileUploadRequest(BaseModel):
    """Request schema for file upload validation"""

    max_file_size: int = Field(
        10485760, description="Maximum file size in bytes (default 10MB)"
    )
    allowed_types: List[str] = Field(
        default=["image/jpeg", "image/png", "application/pdf"],
        description="Allowed MIME types",
    )
    max_files: int = Field(
        5, ge=1, le=10, description="Maximum number of files allowed"
    )

    @validator("allowed_types")
    def validate_allowed_types(cls, v):
        valid_types = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "application/pdf",
            "text/plain",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        for file_type in v:
            if file_type not in valid_types:
                raise ValueError(
                    f"Invalid file type: {file_type}. Allowed types: {valid_types}"
                )
        return v
