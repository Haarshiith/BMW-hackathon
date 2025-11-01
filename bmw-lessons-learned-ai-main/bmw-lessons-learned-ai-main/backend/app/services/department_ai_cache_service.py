from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.department_ai_cache import DepartmentAISummaryCache
import logging

logger = logging.getLogger(__name__)


class DepartmentAICacheService:
    """Service for managing department AI summary cache"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cached_summary(
        self, department: str
    ) -> Optional[DepartmentAISummaryCache]:
        """
        Get cached AI summary for a department

        Args:
            department: Department name

        Returns:
            Cached summary or None if not found
        """
        try:
            result = await self.db.execute(
                select(DepartmentAISummaryCache).where(
                    DepartmentAISummaryCache.department == department.lower()
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting cached summary for {department}: {e}")
            return None

    async def save_summary(
        self,
        department: str,
        summary_data: Dict[str, Any],
        total_lessons: int,
        ai_generated: bool = True,
    ) -> DepartmentAISummaryCache:
        """
        Save or update AI summary cache

        Args:
            department: Department name
            summary_data: AI summary data
            total_lessons: Number of lessons analyzed
            ai_generated: Whether the summary was AI-generated

        Returns:
            Updated cache entry
        """
        try:
            # Check if cache exists
            cache = await self.get_cached_summary(department)

            if cache:
                # Update existing cache
                cache.consolidated_summary = summary_data.get("consolidated_summary")
                cache.key_patterns = summary_data.get("key_patterns", [])
                cache.top_recommendations = summary_data.get("top_recommendations", [])
                cache.department_insights = summary_data.get("department_insights")
                cache.severity_breakdown = summary_data.get("severity_breakdown", {})
                cache.total_lessons_analyzed = total_lessons
                cache.unique_commodities = summary_data.get("unique_commodities", 0)
                cache.unique_suppliers = summary_data.get("unique_suppliers", 0)
                cache.top_commodities = summary_data.get("top_commodities", [])
                cache.top_suppliers = summary_data.get("top_suppliers", [])
                cache.last_updated = datetime.utcnow()
                cache.ai_generated = ai_generated

                logger.info(f"Updated cache for department {department}")
            else:
                # Create new cache entry
                cache = DepartmentAISummaryCache(
                    department=department.lower(),
                    consolidated_summary=summary_data.get("consolidated_summary"),
                    key_patterns=summary_data.get("key_patterns", []),
                    top_recommendations=summary_data.get("top_recommendations", []),
                    department_insights=summary_data.get("department_insights"),
                    severity_breakdown=summary_data.get("severity_breakdown", {}),
                    total_lessons_analyzed=total_lessons,
                    unique_commodities=summary_data.get("unique_commodities", 0),
                    unique_suppliers=summary_data.get("unique_suppliers", 0),
                    top_commodities=summary_data.get("top_commodities", []),
                    top_suppliers=summary_data.get("top_suppliers", []),
                    ai_generated=ai_generated,
                )
                self.db.add(cache)

                logger.info(f"Created new cache for department {department}")

            await self.db.commit()
            await self.db.refresh(cache)

            return cache

        except Exception as e:
            logger.error(f"Error saving cache for {department}: {e}")
            await self.db.rollback()
            raise

    async def is_cache_valid(
        self, department: str, current_lesson_count: int
    ) -> tuple[bool, Optional[DepartmentAISummaryCache]]:
        """
        Check if cached summary is still valid

        Args:
            department: Department name
            current_lesson_count: Current number of lessons in department

        Returns:
            Tuple of (is_valid, cache_entry)
        """
        cache = await self.get_cached_summary(department)

        if not cache:
            return False, None

        # Cache is valid if the lesson count hasn't changed
        is_valid = not cache.is_stale(current_lesson_count)

        return is_valid, cache

    async def invalidate_cache(self, department: str) -> bool:
        """
        Invalidate (delete) cached summary for a department

        Args:
            department: Department name

        Returns:
            True if cache was deleted, False otherwise
        """
        try:
            cache = await self.get_cached_summary(department)
            if cache:
                await self.db.delete(cache)
                await self.db.commit()
                logger.info(f"Invalidated cache for department {department}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error invalidating cache for {department}: {e}")
            await self.db.rollback()
            return False

    async def get_cache_status(
        self, department: str, current_lesson_count: int
    ) -> Dict[str, Any]:
        """
        Get cache status information

        Args:
            department: Department name
            current_lesson_count: Current number of lessons

        Returns:
            Dictionary with cache status information
        """
        is_valid, cache = await self.is_cache_valid(department, current_lesson_count)

        if not cache:
            return {
                "cache_exists": False,
                "cache_valid": False,
                "cache_stale": False,
                "lessons_analyzed": 0,
                "current_lessons": current_lesson_count,
                "last_generated": None,
            }

        return {
            "cache_exists": True,
            "cache_valid": is_valid,
            "cache_stale": not is_valid,
            "lessons_analyzed": cache.total_lessons_analyzed,
            "current_lessons": current_lesson_count,
            "last_generated": (
                cache.generated_at.isoformat() if cache.generated_at else None
            ),
            "ai_generated": cache.ai_generated,
        }
