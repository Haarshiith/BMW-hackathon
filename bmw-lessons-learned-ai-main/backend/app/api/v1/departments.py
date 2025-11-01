from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_lesson_repository
from app.schemas import (
    DepartmentListResponse,
    DepartmentSummaryResponse,
    SuccessResponse,
)
from app.utils.database_utils import LessonLearnedRepository
from app.services.department_ai_service import DepartmentAIService
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get(
    "/",
    response_model=DepartmentListResponse,
    summary="Get all departments",
    description="Retrieve a list of all unique departments",
)
async def get_departments(
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Get all unique departments"""
    try:
        departments = await repository.get_departments()
        return DepartmentListResponse(
            departments=departments, total_departments=len(departments)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve departments: {str(e)}",
        )


@router.get(
    "/{department}/lessons",
    response_model=List[dict],
    summary="Get lessons by department",
    description="Retrieve all lessons learned for a specific department",
)
async def get_department_lessons(
    department: str,
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Get all lessons for a specific department"""
    try:
        # Normalize department name to lowercase for consistency
        department = department.lower()
        lessons = await repository.get_all(department=department, limit=1000)

        # Convert to summary format
        lesson_summaries = []
        for lesson in lessons:
            lesson_summaries.append(
                {
                    "id": lesson.id,
                    "commodity": lesson.commodity,
                    "severity": lesson.severity,
                    "created_at": lesson.created_at,
                    "lesson_summary": (
                        lesson.ai_analysis.get("lesson_summary")
                        if lesson.ai_analysis
                        else None
                    ),
                }
            )

        return lesson_summaries

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lessons for department {department}: {str(e)}",
        )


@router.get(
    "/{department}/summary",
    response_model=dict,
    summary="Get department summary",
    description="Get an AI-powered consolidated summary of all lessons learned in a department",
)
async def get_department_summary(department: str, db: AsyncSession = Depends(get_db)):
    """Get an AI-powered consolidated summary for a department"""
    try:
        # Normalize department name to lowercase for consistency
        department = department.lower()
        ai_service = DepartmentAIService(db)
        summary = await ai_service.generate_department_summary(department)
        return summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary for department {department}: {str(e)}",
        )


@router.get(
    "/{department}/statistics",
    response_model=dict,
    summary="Get department statistics",
    description="Get statistics for a specific department",
)
async def get_department_statistics(
    department: str,
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Get statistics for a specific department"""
    try:
        # Normalize department name to lowercase for consistency
        department = department.lower()
        # Get all lessons for the department
        lessons = await repository.get_all(department=department, limit=1000)

        # Calculate statistics
        total_lessons = len(lessons)
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for lesson in lessons:
            severity_counts[lesson.severity.value] += 1

        # Get unique commodities and suppliers
        commodities = list(set(lesson.commodity for lesson in lessons))
        suppliers = list(set(lesson.supplier for lesson in lessons if lesson.supplier))

        return {
            "department": department,
            "total_lessons": total_lessons,
            "severity_breakdown": severity_counts,
            "unique_commodities": len(commodities),
            "unique_suppliers": len(suppliers),
            "commodities": commodities[:10],  # Top 10 commodities
            "suppliers": suppliers[:10],  # Top 10 suppliers
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics for department {department}: {str(e)}",
        )


@router.get(
    "/{department}/insights",
    response_model=dict,
    summary="Get department insights",
    description="Get comprehensive AI-powered insights for a department (with caching)",
)
async def get_department_insights(
    department: str, force_regenerate: bool = False, db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive AI-powered insights for a department

    Args:
        department: Department name
        force_regenerate: Force regeneration of AI summary even if cache is valid
        db: Database session
    """
    try:
        # Normalize department name to lowercase for consistency
        department = department.lower()
        ai_service = DepartmentAIService(db)
        insights = await ai_service.get_department_insights(
            department, force_regenerate=force_regenerate
        )
        return insights

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights for department {department}: {str(e)}",
        )


@router.post(
    "/{department}/regenerate-summary",
    response_model=dict,
    summary="Regenerate AI summary",
    description="Force regeneration of department AI summary",
)
async def regenerate_department_summary(
    department: str, db: AsyncSession = Depends(get_db)
):
    """Force regeneration of department AI summary"""
    try:
        # Normalize department name to lowercase for consistency
        department = department.lower()
        ai_service = DepartmentAIService(db)

        # Generate new summary with force_regenerate=True
        summary = await ai_service.generate_department_summary(
            department, force_regenerate=True
        )

        return {
            "message": f"AI summary regenerated for {department} department",
            "summary": summary,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate summary for department {department}: {str(e)}",
        )
