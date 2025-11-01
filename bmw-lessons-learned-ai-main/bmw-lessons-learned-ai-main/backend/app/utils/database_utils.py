from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc, func
from app.models.lesson_learned import LessonLearned, SeverityLevel


class LessonLearnedRepository:
    """Repository class for LessonLearned database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, lesson_data: Dict[str, Any]) -> LessonLearned:
        """Create a new lesson learned record"""
        lesson = LessonLearned(**lesson_data)
        self.db.add(lesson)
        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def get_by_id(self, lesson_id: int) -> Optional[LessonLearned]:
        """Get a lesson learned record by ID"""
        result = await self.db.execute(
            select(LessonLearned).where(LessonLearned.id == lesson_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 10,
        department: Optional[str] = None,
        severity: Optional[SeverityLevel] = None,
        commodity: Optional[str] = None,
        supplier: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[LessonLearned]:
        """Get all lesson learned records with filtering and pagination"""

        query = select(LessonLearned)

        # Apply filters
        filters = []

        if department:
            filters.append(LessonLearned.department.ilike(department))

        if severity:
            filters.append(LessonLearned.severity == severity)

        if commodity:
            filters.append(LessonLearned.commodity.ilike(f"%{commodity}%"))

        if supplier:
            filters.append(LessonLearned.supplier.ilike(f"%{supplier}%"))

        if search:
            search_filter = or_(
                LessonLearned.commodity.ilike(f"%{search}%"),
                LessonLearned.problem_description.ilike(f"%{search}%"),
                LessonLearned.error_location.ilike(f"%{search}%"),
                LessonLearned.department.ilike(f"%{search}%"),
            )
            filters.append(search_filter)

        if filters:
            query = query.where(and_(*filters))

        # Apply sorting
        sort_column = getattr(LessonLearned, sort_by, LessonLearned.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(
        self, lesson_id: int, update_data: Dict[str, Any]
    ) -> Optional[LessonLearned]:
        """Update a lesson learned record"""
        lesson = await self.get_by_id(lesson_id)
        if not lesson:
            return None

        for key, value in update_data.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)

        await self.db.commit()
        await self.db.refresh(lesson)
        return lesson

    async def delete(self, lesson_id: int) -> bool:
        """Delete a lesson learned record"""
        lesson = await self.get_by_id(lesson_id)
        if not lesson:
            return False

        await self.db.delete(lesson)
        await self.db.commit()
        return True

    async def get_departments(self) -> List[str]:
        """Get all unique departments"""
        result = await self.db.execute(select(LessonLearned.department).distinct())
        return [row[0] for row in result.fetchall()]

    async def get_lesson_summaries_by_department(self, department: str) -> List[str]:
        """Get all lesson summaries for a specific department"""
        result = await self.db.execute(
            select(LessonLearned.ai_analysis).where(
                and_(
                    LessonLearned.department == department,
                    LessonLearned.ai_analysis.isnot(None),
                )
            )
        )

        summaries = []
        for row in result.fetchall():
            if row[0] and "lesson_summary" in row[0]:
                summaries.append(row[0]["lesson_summary"])

        return summaries

    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about lessons learned"""
        # Total count
        total_result = await self.db.execute(select(LessonLearned.id))
        total_count = len(total_result.fetchall())

        # Count by severity
        severity_counts = {}
        for severity in SeverityLevel:
            result = await self.db.execute(
                select(LessonLearned.id).where(LessonLearned.severity == severity)
            )
            severity_counts[severity.value] = len(result.fetchall())

        # Count by department
        dept_result = await self.db.execute(
            select(LessonLearned.department, func.count(LessonLearned.id)).group_by(
                LessonLearned.department
            )
        )
        department_counts = {row[0]: row[1] for row in dept_result.fetchall()}

        return {
            "total_lessons": total_count,
            "by_severity": severity_counts,
            "by_department": department_counts,
        }
