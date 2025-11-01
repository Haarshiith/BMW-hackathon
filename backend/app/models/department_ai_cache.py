from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base


class DepartmentAISummaryCache(Base):
    """Model for caching department AI summaries"""

    __tablename__ = "department_ai_summary_cache"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Department identifier (unique)
    department = Column(String(100), unique=True, nullable=False, index=True)

    # AI-generated summary content
    consolidated_summary = Column(Text, nullable=True)
    key_patterns = Column(JSON, nullable=True)  # List of key patterns
    top_recommendations = Column(JSON, nullable=True)  # List of recommendations
    department_insights = Column(Text, nullable=True)

    # Statistics at the time of generation
    severity_breakdown = Column(
        JSON, nullable=True
    )  # {"low": 0, "medium": 0, "high": 0, "critical": 0}
    total_lessons_analyzed = Column(Integer, default=0, nullable=False)
    unique_commodities = Column(Integer, default=0)
    unique_suppliers = Column(Integer, default=0)
    top_commodities = Column(JSON, nullable=True)  # List of top commodities
    top_suppliers = Column(JSON, nullable=True)  # List of top suppliers

    # Metadata
    generated_at = Column(DateTime, default=func.now(), nullable=False)
    last_updated = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    ai_generated = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<DepartmentAISummaryCache(department='{self.department}', lessons={self.total_lessons_analyzed}, generated={self.generated_at})>"

    def to_dict(self):
        """Convert cache to dictionary"""
        return {
            "department": self.department,
            "consolidated_summary": self.consolidated_summary,
            "key_patterns": self.key_patterns or [],
            "top_recommendations": self.top_recommendations or [],
            "department_insights": self.department_insights,
            "severity_breakdown": self.severity_breakdown or {},
            "total_lessons": self.total_lessons_analyzed,
            "unique_commodities": self.unique_commodities,
            "unique_suppliers": self.unique_suppliers,
            "top_commodities": self.top_commodities or [],
            "top_suppliers": self.top_suppliers or [],
            "generated_at": (
                self.generated_at.isoformat() if self.generated_at else None
            ),
            "ai_generated": self.ai_generated,
        }

    def is_stale(self, current_lesson_count: int) -> bool:
        """
        Check if the cache is stale (needs regeneration)

        Args:
            current_lesson_count: Current number of lessons in the department

        Returns:
            True if cache is stale, False otherwise
        """
        # Cache is stale if there are more lessons than when it was generated
        return current_lesson_count > self.total_lessons_analyzed
