from typing import Optional
from pydantic import BaseModel, Field, validator
from app.models.lesson_learned import SeverityLevel


class LessonLearnedFilters(BaseModel):
    """Schema for filtering lessons learned"""

    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(10, ge=1, le=100, description="Number of items per page")
    department: Optional[str] = Field(None, description="Filter by department")
    severity: Optional[SeverityLevel] = Field(
        None, description="Filter by severity level"
    )
    commodity: Optional[str] = Field(None, description="Filter by commodity")
    supplier: Optional[str] = Field(None, description="Filter by supplier")
    search: Optional[str] = Field(None, min_length=1, description="Search term")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order (asc or desc)")

    @validator("sort_by")
    def validate_sort_by(cls, v):
        allowed_fields = [
            "created_at",
            "updated_at",
            "commodity",
            "department",
            "severity",
            "part_number",
            "supplier",
        ]
        if v not in allowed_fields:
            raise ValueError(f"sort_by must be one of: {', '.join(allowed_fields)}")
        return v

    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v.lower() not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v.lower()


class DepartmentFilters(BaseModel):
    """Schema for department-specific filters"""

    department: str = Field(..., min_length=1, description="Department name")
    include_ai_analysis: bool = Field(
        True, description="Include AI analysis in results"
    )


class StatisticsFilters(BaseModel):
    """Schema for statistics filters"""

    department: Optional[str] = Field(
        None, description="Filter statistics by department"
    )
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    severity: Optional[SeverityLevel] = Field(
        None, description="Filter by severity level"
    )
