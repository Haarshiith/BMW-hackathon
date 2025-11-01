from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.utils.database_utils import LessonLearnedRepository


async def get_lesson_repository(
    db: AsyncSession = Depends(get_db),
) -> LessonLearnedRepository:
    """Dependency to get lesson learned repository"""
    return LessonLearnedRepository(db)


async def get_lesson_by_id(
    lesson_id: int, repository: LessonLearnedRepository = Depends(get_lesson_repository)
):
    """Dependency to get a lesson by ID, raising 404 if not found"""
    lesson = await repository.get_by_id(lesson_id)
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with id {lesson_id} not found",
        )
    return lesson
