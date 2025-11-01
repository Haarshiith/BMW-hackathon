from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response schema"""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
    timestamp: str = Field(..., description="Error timestamp")


class SuccessResponse(BaseModel):
    """Standard success response schema"""

    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: str = Field(..., description="Response timestamp")


class HealthCheckResponse(BaseModel):
    """Health check response schema"""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    database_status: str = Field(..., description="Database connection status")
    uptime: str = Field(..., description="Service uptime")


class PaginationInfo(BaseModel):
    """Pagination information schema"""

    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class ListResponse(BaseModel):
    """Generic list response schema"""

    items: List[Any] = Field(..., description="List of items")
    pagination: PaginationInfo = Field(..., description="Pagination information")


class DepartmentListResponse(BaseModel):
    """Response schema for department list"""

    departments: List[str] = Field(..., description="List of unique departments")
    total_departments: int = Field(..., description="Total number of departments")


class ValidationErrorDetail(BaseModel):
    """Schema for validation error details"""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Value that failed validation")


class ValidationErrorResponse(BaseModel):
    """Schema for validation error response"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: List[ValidationErrorDetail] = Field(
        ..., description="List of validation errors"
    )
    timestamp: str = Field(..., description="Error timestamp")
