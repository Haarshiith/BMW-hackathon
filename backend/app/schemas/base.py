from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""

    created_at: datetime
    updated_at: datetime


class AIAnalysisBase(BaseModel):
    """Base schema for AI analysis results"""

    lesson_summary: str = Field(..., description="Brief summary of the lesson learned")
    lesson_detailed: str = Field(..., description="Detailed explanation of the lesson")
    best_practice: List[str] = Field(
        ..., description="List of best practices identified"
    )
    preventive_actions: List[str] = Field(
        ..., description="List of preventive actions recommended"
    )


class AIAnalysisResponse(AIAnalysisBase):
    """Response schema for AI analysis"""

    pass


class DepartmentSummaryResponse(BaseModel):
    """Response schema for department-level summary"""

    department: str
    total_lessons: int
    consolidated_summary: str
    key_patterns: List[str]
    top_recommendations: List[str]
    generated_at: datetime
