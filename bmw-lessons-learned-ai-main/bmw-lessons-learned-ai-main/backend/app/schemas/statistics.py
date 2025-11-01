from typing import Dict, Any, List
from pydantic import BaseModel, Field


class SeverityStatistics(BaseModel):
    """Statistics by severity level"""

    low: int = Field(0, description="Number of low severity lessons")
    medium: int = Field(0, description="Number of medium severity lessons")
    high: int = Field(0, description="Number of high severity lessons")
    critical: int = Field(0, description="Number of critical severity lessons")


class DepartmentStatistics(BaseModel):
    """Statistics by department"""

    department: str = Field(..., description="Department name")
    count: int = Field(..., description="Number of lessons in this department")
    severity_breakdown: SeverityStatistics = Field(
        ..., description="Severity breakdown for this department"
    )


class OverallStatistics(BaseModel):
    """Overall statistics response"""

    total_lessons: int = Field(..., description="Total number of lessons")
    by_severity: SeverityStatistics = Field(..., description="Breakdown by severity")
    by_department: List[DepartmentStatistics] = Field(
        ..., description="Breakdown by department"
    )
    most_common_commodities: List[Dict[str, Any]] = Field(
        ..., description="Most common commodities"
    )
    most_common_suppliers: List[Dict[str, Any]] = Field(
        ..., description="Most common suppliers"
    )


class TrendData(BaseModel):
    """Trend data for charts"""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    count: int = Field(..., description="Number of lessons on this date")
    severity_breakdown: SeverityStatistics = Field(
        ..., description="Severity breakdown for this date"
    )


class TrendStatistics(BaseModel):
    """Trend statistics response"""

    period: str = Field(..., description="Time period (e.g., 'last_30_days')")
    trends: List[TrendData] = Field(..., description="Trend data points")
    total_in_period: int = Field(..., description="Total lessons in the period")
    average_per_day: float = Field(..., description="Average lessons per day")
