from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.openai_service import openai_service
from app.services.department_ai_cache_service import DepartmentAICacheService
from app.utils.database_utils import LessonLearnedRepository
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DepartmentAIService:
    """Service for AI analysis of department-level insights with caching"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = LessonLearnedRepository(db)
        self.cache_service = DepartmentAICacheService(db)
        self.openai_service = openai_service

    async def generate_department_summary(
        self, department: str, force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Generate AI-powered department summary with caching

        Args:
            department: Department name
            force_regenerate: Force regeneration even if cache is valid

        Returns:
            Dict containing department summary and insights
        """
        try:
            # Get all lessons for the department
            lessons = await self.repository.get_all(department=department, limit=1000)
            total_lessons = len(lessons)

            if not lessons:
                return {
                    "department": department,
                    "total_lessons": 0,
                    "consolidated_summary": f"No lessons learned found for {department} department.",
                    "key_patterns": [],
                    "top_recommendations": [],
                    "department_insights": f"No data available for {department} department analysis.",
                    "generated_at": datetime.utcnow().isoformat(),
                    "ai_generated": False,
                    "from_cache": False,
                }

            # Check cache validity
            is_valid, cached_summary = await self.cache_service.is_cache_valid(
                department, total_lessons
            )

            # Return cached summary if valid and not forcing regeneration
            if is_valid and not force_regenerate and cached_summary:
                logger.info(f"Returning cached summary for {department}")
                result = cached_summary.to_dict()
                result["from_cache"] = True
                return result

            # Generate new AI summary
            logger.info(
                f"Generating new AI summary for {department} (total lessons: {total_lessons})"
            )

            # Create lesson summaries from raw lesson data
            lesson_summaries = []
            for lesson in lessons:
                # Create a summary from the lesson data
                summary = f"Problem: {lesson.problem_description}. Solution: {lesson.provided_solution}. Severity: {lesson.severity.value}. Commodity: {lesson.commodity}."
                if lesson.supplier:
                    summary += f" Supplier: {lesson.supplier}."
                lesson_summaries.append(summary)

            # Generate AI-powered summary
            ai_summary = await self.openai_service.generate_department_summary(
                department, lesson_summaries
            )

            # Calculate severity breakdown
            severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
            for lesson in lessons:
                severity_counts[lesson.severity.value] += 1

            # Get unique commodities and suppliers
            commodities = list(set(lesson.commodity for lesson in lessons))
            suppliers = list(
                set(lesson.supplier for lesson in lessons if lesson.supplier)
            )

            summary_data = {
                "department": department,
                "total_lessons": total_lessons,
                "consolidated_summary": ai_summary.consolidated_summary,
                "key_patterns": ai_summary.key_patterns,
                "top_recommendations": ai_summary.top_recommendations,
                "department_insights": ai_summary.department_insights,
                "severity_breakdown": severity_counts,
                "unique_commodities": len(commodities),
                "unique_suppliers": len(suppliers),
                "top_commodities": commodities[:5],  # Top 5 commodities
                "top_suppliers": suppliers[:5],  # Top 5 suppliers
                "generated_at": datetime.utcnow().isoformat(),
                "ai_generated": True,
                "from_cache": False,
            }

            # Save to cache
            await self.cache_service.save_summary(
                department=department,
                summary_data=summary_data,
                total_lessons=total_lessons,
                ai_generated=True,
            )

            return summary_data

        except Exception as e:
            logger.error(f"Failed to generate department summary for {department}: {e}")

            # Check if we have a cached summary to return (even if stale)
            cached_summary = await self.cache_service.get_cached_summary(department)
            if cached_summary:
                logger.info(
                    f"Returning stale cached summary for {department} due to AI error"
                )
                result = cached_summary.to_dict()
                result["from_cache"] = True
                result["cache_stale"] = True
                result["error"] = f"Using cached data due to AI error: {str(e)}"
                return result

            # Return fallback summary if AI fails and no cache
            try:
                lessons = await self.repository.get_all(
                    department=department, limit=1000
                )
                total_lessons = len(lessons)

                return {
                    "department": department,
                    "total_lessons": total_lessons,
                    "consolidated_summary": f"Department {department} has {total_lessons} lessons learned. AI analysis is currently unavailable.",
                    "key_patterns": ["AI analysis temporarily unavailable"],
                    "top_recommendations": [
                        "Please try again later or contact support"
                    ],
                    "department_insights": f"Manual analysis required for {department} department due to AI service unavailability.",
                    "generated_at": datetime.utcnow().isoformat(),
                    "ai_generated": False,
                    "from_cache": False,
                    "error": str(e),
                }
            except Exception as fallback_error:
                logger.error(
                    f"Fallback department summary also failed: {fallback_error}"
                )
                raise

    async def get_department_insights(
        self, department: str, force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive department insights including AI analysis

        Args:
            department: Department name
            force_regenerate: Force regeneration of AI summary

        Returns:
            Dict containing comprehensive department insights
        """
        try:
            # Get basic department data
            lessons = await self.repository.get_all(department=department, limit=1000)

            if not lessons:
                return {
                    "department": department,
                    "total_lessons": 0,
                    "insights": "No lessons found for this department",
                    "ai_analysis_available": False,
                }

            # Get AI summary (with caching)
            ai_summary = await self.generate_department_summary(
                department, force_regenerate=force_regenerate
            )

            # Calculate additional metrics
            recent_lessons = [
                l for l in lessons if l.created_at.month == datetime.utcnow().month
            ]
            critical_lessons = [l for l in lessons if l.severity.value == "critical"]
            high_lessons = [l for l in lessons if l.severity.value == "high"]

            # Get trend data (last 6 months)
            six_months_ago = datetime.utcnow().replace(day=1)
            recent_trend = [l for l in lessons if l.created_at >= six_months_ago]

            return {
                "department": department,
                "total_lessons": len(lessons),
                "recent_lessons_this_month": len(recent_lessons),
                "critical_lessons": len(critical_lessons),
                "high_severity_lessons": len(high_lessons),
                "lessons_last_6_months": len(recent_trend),
                "ai_summary": ai_summary,
                "insights": {
                    "severity_distribution": {
                        "critical": len(critical_lessons),
                        "high": len(high_lessons),
                        "medium": len(
                            [l for l in lessons if l.severity.value == "medium"]
                        ),
                        "low": len([l for l in lessons if l.severity.value == "low"]),
                    },
                    "trend_analysis": {
                        "recent_activity": len(recent_lessons),
                        "six_month_trend": len(recent_trend),
                        "activity_level": (
                            "high"
                            if len(recent_lessons) > 5
                            else "moderate" if len(recent_lessons) > 2 else "low"
                        ),
                    },
                },
                "ai_analysis_available": ai_summary.get("ai_generated", False),
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get department insights for {department}: {e}")
            raise
