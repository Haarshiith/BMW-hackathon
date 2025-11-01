from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.lesson_ai_service import LessonAIService
from app.services.file_upload_service import file_upload_service
from app.schemas.lesson_learned import LessonLearnedResponse
from app.models.lesson_learned import SeverityLevel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lessons", tags=["lessons-with-files"])


@router.post(
    "/create-with-files",
    response_model=LessonLearnedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create lesson learned with file uploads",
    description="Create a new lesson learned record with file attachments and AI analysis",
)
async def create_lesson_with_files(
    # Required fields
    commodity: str = Form(..., description="Commodity name"),
    error_location: str = Form(..., description="Location where error occurred"),
    problem_description: str = Form(..., description="Description of the problem"),
    missed_detection: str = Form(..., description="How the detection was missed"),
    provided_solution: str = Form(..., description="Solution that was provided"),
    department: str = Form(..., description="Department name"),
    severity: str = Form(
        ..., description="Severity level (low, medium, high, critical)"
    ),
    reporter_name: str = Form(
        ..., description="Name of the person reporting the issue"
    ),
    # Optional fields
    part_number: Optional[str] = Form(None, description="Part number"),
    supplier: Optional[str] = Form(None, description="Supplier name"),
    # File uploads
    attachments: List[UploadFile] = File(
        default=[], description="Attachment files (images or PDFs)"
    ),
    # Database session
    db: AsyncSession = Depends(get_db),
):
    """Create a new lesson learned record with file attachments and AI analysis"""
    try:
        # Validate severity
        try:
            severity_enum = SeverityLevel(severity.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid severity level: {severity}. Must be one of: low, medium, high, critical",
            )

        # Upload files if provided
        uploaded_files = []
        if attachments:
            try:
                upload_result = await file_upload_service.upload_multiple_files(
                    attachments
                )

                if upload_result.failed_count > 0:
                    logger.warning(
                        f"Some files failed to upload: {upload_result.failed_uploads}"
                    )

                # Collect successfully uploaded filenames
                uploaded_files = [
                    upload.saved_filename for upload in upload_result.successful_uploads
                ]

            except Exception as e:
                logger.error(f"File upload failed: {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File upload failed: {str(e)}",
                )

        # Create lesson data
        from app.schemas.lesson_learned import LessonLearnedCreate

        lesson_data = LessonLearnedCreate(
            commodity=commodity,
            part_number=part_number,
            supplier=supplier,
            error_location=error_location,
            problem_description=problem_description,
            missed_detection=missed_detection,
            provided_solution=provided_solution,
            department=department,
            severity=severity_enum,
            reporter_name=reporter_name,
            attachments=uploaded_files,
        )

        # Create lesson with AI analysis
        ai_service = LessonAIService(db)
        lesson = await ai_service.create_lesson_with_ai_analysis(lesson_data)

        logger.info(
            f"Successfully created lesson {lesson.id} with {len(uploaded_files)} attachments"
        )

        return lesson

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create lesson with files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lesson: {str(e)}",
        )


@router.post(
    "/{lesson_id}/add-attachments",
    response_model=LessonLearnedResponse,
    summary="Add attachments to existing lesson",
    description="Add file attachments to an existing lesson learned record",
)
async def add_attachments_to_lesson(
    lesson_id: int,
    attachments: List[UploadFile] = File(..., description="Files to attach"),
    db: AsyncSession = Depends(get_db),
):
    """Add file attachments to an existing lesson learned record"""
    try:
        from app.utils.database_utils import LessonLearnedRepository

        repository = LessonLearnedRepository(db)

        # Check if lesson exists
        lesson = await repository.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson with id {lesson_id} not found",
            )

        # Upload new files
        upload_result = await file_upload_service.upload_multiple_files(attachments)

        if upload_result.failed_count > 0:
            logger.warning(
                f"Some files failed to upload: {upload_result.failed_uploads}"
            )

        # Get new filenames
        new_files = [
            upload.saved_filename for upload in upload_result.successful_uploads
        ]

        # Combine with existing attachments
        existing_attachments = lesson.attachments or []
        all_attachments = existing_attachments + new_files

        # Update lesson with new attachments
        updated_lesson = await repository.update(
            lesson_id, {"attachments": all_attachments}
        )

        logger.info(
            f"Successfully added {len(new_files)} attachments to lesson {lesson_id}"
        )

        return updated_lesson

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add attachments to lesson {lesson_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add attachments: {str(e)}",
        )


@router.delete(
    "/{lesson_id}/attachments/{filename}",
    response_model=LessonLearnedResponse,
    summary="Remove attachment from lesson",
    description="Remove a specific file attachment from a lesson learned record",
)
async def remove_attachment_from_lesson(
    lesson_id: int, filename: str, db: AsyncSession = Depends(get_db)
):
    """Remove a specific file attachment from a lesson learned record"""
    try:
        from app.utils.database_utils import LessonLearnedRepository

        repository = LessonLearnedRepository(db)

        # Check if lesson exists
        lesson = await repository.get_by_id(lesson_id)
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson with id {lesson_id} not found",
            )

        # Check if attachment exists
        existing_attachments = lesson.attachments or []
        if filename not in existing_attachments:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment {filename} not found in lesson {lesson_id}",
            )

        # Remove attachment from list
        updated_attachments = [att for att in existing_attachments if att != filename]

        # Update lesson
        updated_lesson = await repository.update(
            lesson_id, {"attachments": updated_attachments}
        )

        # Delete file from storage
        await file_upload_service.delete_file(filename)

        logger.info(
            f"Successfully removed attachment {filename} from lesson {lesson_id}"
        )

        return updated_lesson

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to remove attachment {filename} from lesson {lesson_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove attachment: {str(e)}",
        )
