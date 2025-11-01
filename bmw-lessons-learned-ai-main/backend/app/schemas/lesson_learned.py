from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from app.models.lesson_learned import SeverityLevel
from app.schemas.base import AIAnalysisResponse, TimestampMixin


class LessonLearnedBase(BaseModel):
    """Base schema for lesson learned data"""

    commodity: str = Field(
        ..., min_length=1, max_length=255, description="Commodity name"
    )
    part_number: Optional[str] = Field(
        None, max_length=100, description="Part number (optional)"
    )
    supplier: Optional[str] = Field(
        None, max_length=255, description="Supplier name (optional)"
    )
    error_location: str = Field(
        ..., min_length=1, description="Location where error occurred"
    )
    problem_description: str = Field(
        ..., min_length=1, description="Description of the problem"
    )
    missed_detection: str = Field(
        ..., min_length=1, description="How the detection was missed"
    )
    provided_solution: str = Field(
        ..., min_length=1, description="Solution that was provided"
    )
    department: str = Field(
        ..., min_length=1, max_length=100, description="Department name"
    )
    severity: SeverityLevel = Field(..., description="Severity level of the issue")
    reporter_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the person reporting the issue",
    )
    attachments: Optional[List[str]] = Field(
        default=[], description="List of attachment file paths"
    )

    @validator("attachments")
    def validate_attachments(cls, v):
        if v is None:
            return []
        return v


class LessonLearnedCreate(LessonLearnedBase):
    """Schema for creating a new lesson learned"""

    pass


class LessonLearnedUpdate(BaseModel):
    """Schema for updating a lesson learned"""

    commodity: Optional[str] = Field(None, min_length=1, max_length=255)
    part_number: Optional[str] = Field(None, max_length=100)
    supplier: Optional[str] = Field(None, max_length=255)
    error_location: Optional[str] = Field(None, min_length=1)
    problem_description: Optional[str] = Field(None, min_length=1)
    missed_detection: Optional[str] = Field(None, min_length=1)
    provided_solution: Optional[str] = Field(None, min_length=1)
    department: Optional[str] = Field(None, min_length=1, max_length=100)
    severity: Optional[SeverityLevel] = None
    reporter_name: Optional[str] = Field(None, min_length=1, max_length=100)
    attachments: Optional[List[str]] = None

    @validator("attachments")
    def validate_attachments(cls, v):
        if v is None:
            return []
        return v


class LessonLearnedResponse(LessonLearnedBase, TimestampMixin):
    """Schema for lesson learned response"""

    id: int
    ai_analysis: Optional[AIAnalysisResponse] = None

    class Config:
        from_attributes = True


class LessonLearnedWithAIAnalysis(LessonLearnedResponse):
    """Schema for lesson learned with AI analysis"""

    ai_analysis: AIAnalysisResponse

    class Config:
        from_attributes = True


class LessonLearnedListResponse(BaseModel):
    """Schema for paginated list of lessons learned"""

    items: List[LessonLearnedResponse]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool


class LessonLearnedSummary(BaseModel):
    """Schema for lesson learned summary (without full details)"""

    id: int
    commodity: str
    department: str
    severity: SeverityLevel
    created_at: datetime
    lesson_summary: Optional[str] = None  # From AI analysis

    class Config:
        from_attributes = True
