from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.deps import get_lesson_repository
from app.schemas import (
    OverallStatistics,
    SeverityStatistics,
    DepartmentStatistics,
    TrendStatistics,
    TrendData,
)
from app.utils.database_utils import LessonLearnedRepository
from datetime import datetime, timedelta
from collections import defaultdict, Counter

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get(
    "/overview",
    response_model=OverallStatistics,
    summary="Get overall statistics",
    description="Get comprehensive statistics across all lessons learned",
)
async def get_overall_statistics(
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Get overall statistics for all lessons learned"""
    try:
        # Get all lessons
        all_lessons = await repository.get_all(limit=10000)

        # Calculate total count
        total_lessons = len(all_lessons)

        # Calculate severity breakdown
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for lesson in all_lessons:
            severity_counts[lesson.severity.value] += 1

        severity_stats = SeverityStatistics(**severity_counts)

        # Calculate department breakdown
        dept_counts = defaultdict(
            lambda: {
                "count": 0,
                "severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            }
        )

        for lesson in all_lessons:
            dept = lesson.department
            dept_counts[dept]["count"] += 1
            dept_counts[dept]["severity"][lesson.severity.value] += 1

        department_stats = []
        for dept, data in dept_counts.items():
            dept_severity = SeverityStatistics(**data["severity"])
            department_stats.append(
                DepartmentStatistics(
                    department=dept,
                    count=data["count"],
                    severity_breakdown=dept_severity,
                )
            )

        # Sort departments by count
        department_stats.sort(key=lambda x: x.count, reverse=True)

        # Get most common commodities and suppliers
        commodity_counts = Counter(lesson.commodity for lesson in all_lessons)
        supplier_counts = Counter(
            lesson.supplier for lesson in all_lessons if lesson.supplier
        )

        most_common_commodities = [
            {"commodity": commodity, "count": count}
            for commodity, count in commodity_counts.most_common(10)
        ]

        most_common_suppliers = [
            {"supplier": supplier, "count": count}
            for supplier, count in supplier_counts.most_common(10)
        ]

        return OverallStatistics(
            total_lessons=total_lessons,
            by_severity=severity_stats,
            by_department=department_stats,
            most_common_commodities=most_common_commodities,
            most_common_suppliers=most_common_suppliers,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overall statistics: {str(e)}",
        )


@router.get(
    "/trends",
    response_model=TrendStatistics,
    summary="Get trend statistics",
    description="Get trend data for lessons learned over time",
)
async def get_trend_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Get trend statistics for lessons learned"""
    try:
        # Get all lessons
        all_lessons = await repository.get_all(limit=10000)

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Filter lessons within date range
        recent_lessons = [
            lesson
            for lesson in all_lessons
            if start_date <= lesson.created_at <= end_date
        ]

        # Group by date
        daily_counts = defaultdict(
            lambda: {
                "count": 0,
                "severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            }
        )

        for lesson in recent_lessons:
            date_str = lesson.created_at.date().isoformat()
            daily_counts[date_str]["count"] += 1
            daily_counts[date_str]["severity"][lesson.severity.value] += 1

        # Convert to trend data
        trends = []
        for date_str in sorted(daily_counts.keys()):
            data = daily_counts[date_str]
            severity_stats = SeverityStatistics(**data["severity"])
            trends.append(
                TrendData(
                    date=date_str,
                    count=data["count"],
                    severity_breakdown=severity_stats,
                )
            )

        # Calculate averages
        total_in_period = len(recent_lessons)
        average_per_day = total_in_period / days if days > 0 else 0

        return TrendStatistics(
            period=f"last_{days}_days",
            trends=trends,
            total_in_period=total_in_period,
            average_per_day=round(average_per_day, 2),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trend statistics: {str(e)}",
        )


@router.get(
    "/severity",
    response_model=SeverityStatistics,
    summary="Get severity statistics",
    description="Get breakdown of lessons by severity level",
)
async def get_severity_statistics(
    department: str = Query(None, description="Filter by department"),
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Get severity statistics"""
    try:
        # Get lessons (filtered by department if specified)
        lessons = await repository.get_all(department=department, limit=10000)

        # Calculate severity counts
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for lesson in lessons:
            severity_counts[lesson.severity.value] += 1

        return SeverityStatistics(**severity_counts)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get severity statistics: {str(e)}",
        )


@router.get(
    "/departments",
    response_model=List[DepartmentStatistics],
    summary="Get department statistics",
    description="Get statistics broken down by department",
)
async def get_department_statistics_list(
    repository: LessonLearnedRepository = Depends(get_lesson_repository),
):
    """Get statistics for all departments"""
    try:
        # Get all lessons
        all_lessons = await repository.get_all(limit=10000)

        # Group by department
        dept_counts = defaultdict(
            lambda: {
                "count": 0,
                "severity": {"low": 0, "medium": 0, "high": 0, "critical": 0},
            }
        )

        for lesson in all_lessons:
            dept = lesson.department
            dept_counts[dept]["count"] += 1
            dept_counts[dept]["severity"][lesson.severity.value] += 1

        # Convert to response format
        department_stats = []
        for dept, data in dept_counts.items():
            dept_severity = SeverityStatistics(**data["severity"])
            department_stats.append(
                DepartmentStatistics(
                    department=dept,
                    count=data["count"],
                    severity_breakdown=dept_severity,
                )
            )

        # Sort by count
        department_stats.sort(key=lambda x: x.count, reverse=True)

        return department_stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get department statistics: {str(e)}",
        )
