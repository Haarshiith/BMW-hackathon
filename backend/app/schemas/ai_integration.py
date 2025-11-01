from typing import List, Optional
from pydantic import BaseModel, Field, validator


class OpenAIRequest(BaseModel):
    """Schema for OpenAI API request"""

    commodity: str = Field(..., description="Commodity name")
    part_number: Optional[str] = Field(None, description="Part number")
    supplier: Optional[str] = Field(None, description="Supplier name")
    error_location: str = Field(..., description="Location where error occurred")
    problem_description: str = Field(..., description="Description of the problem")
    missed_detection: str = Field(..., description="How the detection was missed")
    provided_solution: str = Field(..., description="Solution that was provided")
    department: str = Field(..., description="Department name")
    severity: str = Field(..., description="Severity level")
    reporter_name: str = Field(
        ..., description="Name of the person reporting the issue"
    )

    def to_prompt_text(self) -> str:
        """Convert the request to a formatted prompt text for OpenAI"""
        prompt = f"""
Analyze the following quality issue and provide structured insights:

Commodity: {self.commodity}
Part Number: {self.part_number or 'Not specified'}
Supplier: {self.supplier or 'Not specified'}
Error Location: {self.error_location}
Problem Description: {self.problem_description}
Missed Detection: {self.missed_detection}
Provided Solution: {self.provided_solution}
Department: {self.department}
Severity: {self.severity}
Reporter: {self.reporter_name}

Please provide a JSON response with the following structure:
{{
    "lesson_summary": "Brief summary of the lesson learned",
    "lesson_detailed": "Detailed explanation of the lesson and its implications",
    "best_practice": ["List of best practices identified"],
    "preventive_actions": ["List of preventive actions recommended"]
}}
"""
        return prompt.strip()


class DepartmentSummaryRequest(BaseModel):
    """Schema for department summary request"""

    department: str = Field(..., min_length=1, description="Department name")
    lesson_summaries: List[str] = Field(
        ..., min_items=1, description="List of lesson summaries to analyze"
    )

    def to_prompt_text(self) -> str:
        """Convert the request to a formatted prompt text for OpenAI"""
        summaries_text = "\n".join(
            [f"{i+1}. {summary}" for i, summary in enumerate(self.lesson_summaries)]
        )

        prompt = f"""
You are an expert in quality management and continuous improvement. Analyze the following lesson summaries from the {self.department} department and provide a comprehensive department-level summary.

Lesson Summaries:
{summaries_text}

Please provide a JSON response with the following structure:
{{
    "consolidated_summary": "Comprehensive summary of all lessons learned in this department",
    "key_patterns": ["List of common patterns or recurring issues identified"],
    "top_recommendations": ["List of top recommendations for improvement"],
    "department_insights": "Additional insights specific to this department's challenges and opportunities"
}}
"""
        return prompt.strip()


class OpenAIResponse(BaseModel):
    """Schema for OpenAI API response"""

    lesson_summary: str = Field(..., description="Brief summary of the lesson learned")
    lesson_detailed: str = Field(..., description="Detailed explanation of the lesson")
    best_practice: List[str] = Field(
        ..., description="List of best practices identified"
    )
    preventive_actions: List[str] = Field(
        ..., description="List of preventive actions recommended"
    )

    @validator("best_practice")
    def validate_best_practice(cls, v):
        if not v or len(v) == 0:
            raise ValueError("best_practice must contain at least one item")
        return v

    @validator("preventive_actions")
    def validate_preventive_actions(cls, v):
        if not v or len(v) == 0:
            raise ValueError("preventive_actions must contain at least one item")
        return v


class DepartmentSummaryResponse(BaseModel):
    """Schema for department summary response from OpenAI"""

    consolidated_summary: str = Field(
        ..., description="Comprehensive summary of all lessons"
    )
    key_patterns: List[str] = Field(
        ..., description="List of common patterns identified"
    )
    top_recommendations: List[str] = Field(
        ..., description="List of top recommendations"
    )
    department_insights: str = Field(
        ..., description="Additional department-specific insights"
    )

    @validator("key_patterns")
    def validate_key_patterns(cls, v):
        if not v or len(v) == 0:
            raise ValueError("key_patterns must contain at least one item")
        return v

    @validator("top_recommendations")
    def validate_top_recommendations(cls, v):
        if not v or len(v) == 0:
            raise ValueError("top_recommendations must contain at least one item")
        return v


class AIProcessingStatus(BaseModel):
    """Schema for AI processing status"""

    status: str = Field(
        ..., description="Processing status (pending, processing, completed, failed)"
    )
    message: Optional[str] = Field(None, description="Status message")
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    error_details: Optional[str] = Field(
        None, description="Error details if processing failed"
    )
