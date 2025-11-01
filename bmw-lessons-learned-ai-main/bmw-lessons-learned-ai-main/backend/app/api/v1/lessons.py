from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_lesson_repository, get_lesson_by_id
from app.schemas import (
    LessonLearnedCreate,
    LessonLearnedUpdate,
    LessonLearnedResponse,
    LessonLearnedListResponse,
    PaginationInfo,
    SuccessResponse,
)
from app.utils.database_utils import LessonLearnedRepository
from app.models.lesson_learned import LessonLearned
from app.services.lesson_ai_service import LessonAIService
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post(
    "/",
    response_model=LessonLearnedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lesson learned",
    description="Create a new lesson learned record with AI analysis",
)
async def create_lesson(
    lesson_data: LessonLearnedCreate, db: AsyncSession = Depends(get_db)
):
    """Create a new lesson learned record with AI analysis"""
    try:
        ai_service = LessonAIService(db)
        lesson = await ai_service.create_lesson_with_ai_analysis(lesson_data)
        return lesson
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lesson: {str(e)}",
        )


@router.get(
    "/{lesson_id}",
    response_model=LessonLearnedResponse,
    summary="Get a lesson learned by ID",
    description="Retrieve a specific lesson learned record by its ID",
)
async def get_lesson(lesson: LessonLearned = Depends(get_lesson_by_id)):
    """Get a lesson learned record by ID"""
    return lesson


@router.get(
    "/",
    response_model=LessonLearnedListResponse,
    summary="Get all lessons learned",
    description="Retrieve a paginated list of lessons learned with optional filtering and search",
)
async def get_lessons(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    department: str = Query(None, description="Filter by department"),
    severity: str = Query(None, description="Filter by severity level"),
    commodity: str = Query(None, description="Filter by commodity"),
    supplier: str = Query(None, description="Filter by supplier"),
    search: str = Query(None, description="Search term"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Get all lessons learned with filtering, pagination, and search"""
    try:
        # Normalize department name to lowercase for consistency
        if department:
            department = department.lower()

        # Calculate skip for pagination
        skip = (page - 1) * limit

        # Get lessons with filters
        lessons = await repository.get_all(
            skip=skip,
            limit=limit,
            department=department,
            severity=severity,
            commodity=commodity,
            supplier=supplier,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Get total count for pagination with the same filters
        total_lessons = await repository.get_all(
            limit=10000,  # Get a large number to count all
            department=department,
            severity=severity,
            commodity=commodity,
            supplier=supplier,
            search=search,
        )
        total = len(total_lessons)

        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        pagination = PaginationInfo(
            page=page,
            limit=limit,
            total=total,
            pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

        return LessonLearnedListResponse(
            items=lessons,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lessons: {str(e)}",
        )


@router.put(
    "/{lesson_id}",
    response_model=LessonLearnedResponse,
    summary="Update a lesson learned",
    description="Update an existing lesson learned record",
)
async def update_lesson(
    lesson_id: int,
    lesson_update: LessonLearnedUpdate,
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Update a lesson learned record"""
    try:
        # Check if lesson exists
        existing_lesson = await repository.get_by_id(lesson_id)
        if not existing_lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson with id {lesson_id} not found",
            )

        # Update lesson
        update_data = lesson_update.model_dump(exclude_unset=True)
        updated_lesson = await repository.update(lesson_id, update_data)

        if not updated_lesson:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update lesson",
            )

        return updated_lesson

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update lesson: {str(e)}",
        )


@router.delete(
    "/{lesson_id}",
    response_model=SuccessResponse,
    summary="Delete a lesson learned",
    description="Delete a lesson learned record by its ID",
)
async def delete_lesson(
    lesson_id: int, repository: LessonLearnedRepository = Depends(get_lesson_repository)
):
    """Delete a lesson learned record"""
    try:
        # Check if lesson exists
        existing_lesson = await repository.get_by_id(lesson_id)
        if not existing_lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson with id {lesson_id} not found",
            )

        # Delete lesson
        success = await repository.delete(lesson_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete lesson",
            )

        return SuccessResponse(
            message=f"Lesson with id {lesson_id} deleted successfully",
            data={"deleted_id": lesson_id},
            timestamp=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lesson: {str(e)}",
        )


@router.get(
    "/{lesson_id}/summary",
    response_model=dict,
    summary="Get lesson summary",
    description="Get a summary of a specific lesson learned",
)
async def get_lesson_summary(lesson: LessonLearned = Depends(get_lesson_by_id)):
    """Get a summary of a lesson learned"""
    return {
        "id": lesson.id,
        "commodity": lesson.commodity,
        "department": lesson.department,
        "severity": lesson.severity,
        "lesson_summary": (
            lesson.ai_analysis.get("lesson_summary") if lesson.ai_analysis else None
        ),
        "created_at": lesson.created_at,
    }


@router.post(
    "/{lesson_id}/regenerate-ai",
    response_model=LessonLearnedResponse,
    summary="Regenerate AI analysis",
    description="Regenerate AI analysis for an existing lesson learned",
)
async def regenerate_ai_analysis(lesson_id: int, db: AsyncSession = Depends(get_db)):
    """Regenerate AI analysis for a lesson learned"""
    try:
        ai_service = LessonAIService(db)
        updated_lesson = await ai_service.update_lesson_ai_analysis(lesson_id)

        if not updated_lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lesson with id {lesson_id} not found",
            )

        return updated_lesson

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate AI analysis: {str(e)}",
        )
