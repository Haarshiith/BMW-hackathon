# Import all schemas for easy access
from .base import (
    TimestampMixin,
    AIAnalysisBase,
    AIAnalysisResponse,
    DepartmentSummaryResponse
)

from .lesson_learned import (
    LessonLearnedBase,
    LessonLearnedCreate,
    LessonLearnedUpdate,
    LessonLearnedResponse,
    LessonLearnedWithAIAnalysis,
    LessonLearnedListResponse,
    LessonLearnedSummary
)

from .filters import (
    LessonLearnedFilters,
    DepartmentFilters,
    StatisticsFilters
)

from .statistics import (
    SeverityStatistics,
    DepartmentStatistics,
    OverallStatistics,
    TrendData,
    TrendStatistics
)

from .file_upload import (
    FileUploadResponse,
    MultipleFileUploadResponse,
    FileValidationError,
    FileUploadRequest
)

from .ai_integration import (
    OpenAIRequest,
    DepartmentSummaryRequest,
    OpenAIResponse,
    DepartmentSummaryResponse,
    AIProcessingStatus
)

from .solution_search import (
    SolutionSearchRequest,
    SolutionSearchResponse,
    SearchStatusResponse,
    SearchRefinementRequest,
    SearchRefinementResponse,
    SaveSolutionRequest,
    SavedSolutionResponse,
    SolutionSearchListResponse,
    SavedSolutionListResponse,
    SearchResult,
    SearchProgress
)

from .common import (
    ErrorResponse,
    SuccessResponse,
    HealthCheckResponse,
    PaginationInfo,
    ListResponse,
    DepartmentListResponse,
    ValidationErrorDetail,
    ValidationErrorResponse
)

__all__ = [
    # Base schemas
    "TimestampMixin",
    "AIAnalysisBase", 
    "AIAnalysisResponse",
    "DepartmentSummaryResponse",
    
    # Lesson learned schemas
    "LessonLearnedBase",
    "LessonLearnedCreate",
    "LessonLearnedUpdate", 
    "LessonLearnedResponse",
    "LessonLearnedWithAIAnalysis",
    "LessonLearnedListResponse",
    "LessonLearnedSummary",
    
    # Filter schemas
    "LessonLearnedFilters",
    "DepartmentFilters",
    "StatisticsFilters",
    
    # Statistics schemas
    "SeverityStatistics",
    "DepartmentStatistics", 
    "OverallStatistics",
    "TrendData",
    "TrendStatistics",
    
    # File upload schemas
    "FileUploadResponse",
    "MultipleFileUploadResponse",
    "FileValidationError",
    "FileUploadRequest",
    
    # AI integration schemas
    "OpenAIRequest",
    "DepartmentSummaryRequest",
    "OpenAIResponse",
    "DepartmentSummaryResponse",
    "AIProcessingStatus",
    
    # Solution search schemas
    "SolutionSearchRequest",
    "SolutionSearchResponse",
    "SearchStatusResponse",
    "SearchRefinementRequest",
    "SearchRefinementResponse",
    "SaveSolutionRequest",
    "SavedSolutionResponse",
    "SolutionSearchListResponse",
    "SavedSolutionListResponse",
    "SearchResult",
    "SearchProgress",
    
    # Common schemas
    "ErrorResponse",
    "SuccessResponse",
    "HealthCheckResponse",
    "PaginationInfo",
    "ListResponse",
    "DepartmentListResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse"
]
