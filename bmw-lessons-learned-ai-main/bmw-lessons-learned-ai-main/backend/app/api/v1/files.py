from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from app.services.file_upload_service import file_upload_service
from app.schemas.file_upload import (
    FileUploadResponse,
    MultipleFileUploadResponse,
    FileUploadRequest,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    summary="Upload a single file",
    description="Upload a single file (image or PDF) for lesson learned attachments",
)
async def upload_single_file(
    file: UploadFile = File(..., description="File to upload")
):
    """Upload a single file"""
    try:
        result = await file_upload_service.upload_single_file(file)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file upload: {str(e)}",
        )


@router.post(
    "/upload-multiple",
    response_model=MultipleFileUploadResponse,
    summary="Upload multiple files",
    description="Upload multiple files (images or PDFs) for lesson learned attachments",
)
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="Files to upload")
):
    """Upload multiple files"""
    try:
        result = await file_upload_service.upload_multiple_files(files)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in multiple file upload: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file upload: {str(e)}",
        )


@router.delete(
    "/{filename}", summary="Delete a file", description="Delete a file from storage"
)
async def delete_file(filename: str):
    """Delete a file"""
    try:
        success = await file_upload_service.delete_file(filename)

        if success:
            return {
                "message": f"File {filename} deleted successfully",
                "filename": filename,
                "deleted": True,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found or could not be deleted",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting file {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during file deletion: {str(e)}",
        )


@router.get(
    "/{filename}/info",
    summary="Get file information",
    description="Get information about a specific file",
)
async def get_file_info(filename: str):
    """Get file information"""
    try:
        file_info = await file_upload_service.get_file_info(filename)

        if file_info:
            return file_info
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting file info for {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting file information: {str(e)}",
        )


@router.get(
    "/config",
    response_model=FileUploadRequest,
    summary="Get upload configuration",
    description="Get current file upload configuration and limits",
)
async def get_upload_config():
    """Get upload configuration"""
    try:
        config = file_upload_service.get_upload_config()
        return config
    except Exception as e:
        logger.error(f"Error getting upload config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting upload configuration: {str(e)}",
        )
