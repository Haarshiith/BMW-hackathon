from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from app.models.solution_search import SearchStatus, SearchSource
from app.models.lesson_learned import SeverityLevel
from .base import TimestampMixin


# Request Schemas
class SolutionSearchRequest(BaseModel):
    problem_description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Detailed description of the problem",
    )
    department: str = Field(
        ..., min_length=1, max_length=100, description="Department name"
    )
    severity: SeverityLevel = Field(..., description="Severity level of the problem")
    reporter_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Name of the person reporting the problem",
    )
    keywords: Optional[List[str]] = Field(
        default=[], description="Optional keywords for search refinement"
    )
    search_sources: Optional[List[SearchSource]] = Field(
        default=[SearchSource.database, SearchSource.rag, SearchSource.web],
        description="Which sources to search",
    )
    min_relevance_score: Optional[float] = Field(
        default=0.3, ge=0.0, le=1.0, description="Minimum relevance score for results"
    )

    @validator("keywords")
    def validate_keywords(cls, v):
        if v is None:
            return []
        # Remove duplicates and limit to 20 keywords
        unique_keywords = list(dict.fromkeys(v))
        return unique_keywords[:20]

    @validator("search_sources")
    def validate_search_sources(cls, v):
        if v is None:
            return [SearchSource.database, SearchSource.rag, SearchSource.web]
        # Ensure we have at least one source
        if not v:
            return [SearchSource.database]
        return v


class SearchRefinementRequest(BaseModel):
    search_id: int = Field(..., description="ID of the search to refine")
    additional_keywords: Optional[List[str]] = Field(
        default=[], description="Additional keywords to include"
    )
    exclude_sources: Optional[List[SearchSource]] = Field(
        default=[], description="Sources to exclude from search"
    )
    min_relevance_score: Optional[float] = Field(
        default=0.3, ge=0.0, le=1.0, description="Minimum relevance score"
    )
    department_filter: Optional[str] = Field(
        default=None, description="Filter by specific department"
    )


class SaveSolutionRequest(BaseModel):
    result_id: str = Field(..., description="Identifier for the specific result")
    notes: Optional[str] = Field(
        default=None, max_length=500, description="User notes about the solution"
    )


# Response Schemas
class SearchResult(BaseModel):
    source: SearchSource = Field(..., description="Source of the result")
    title: str = Field(..., description="Title of the result")
    description: str = Field(..., description="Description of the result")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance score (0-1)"
    )
    solution: Optional[str] = Field(default=None, description="Suggested solution")
    url: Optional[str] = Field(default=None, description="External URL if applicable")
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Additional metadata"
    )

    class Config:
        use_enum_values = True


class SearchProgress(BaseModel):
    database_completed: bool = Field(
        ..., description="Whether database search is completed"
    )
    rag_completed: bool = Field(..., description="Whether RAG search is completed")
    web_completed: bool = Field(..., description="Whether web search is completed")
    total_sources: int = Field(..., description="Total number of search sources")
    completed_sources: int = Field(..., description="Number of completed sources")
    estimated_completion_time: Optional[int] = Field(
        default=None, description="Estimated time remaining in seconds"
    )


class SolutionSearchResponse(BaseModel):
    search_id: int = Field(..., description="Unique identifier for the search")
    status: SearchStatus = Field(..., description="Current status of the search")
    results: List[SearchResult] = Field(default=[], description="Search results")
    summary: Optional[str] = Field(
        default=None, description="AI-generated summary of findings"
    )
    confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Overall confidence score"
    )
    search_progress: Optional[SearchProgress] = Field(
        default=None, description="Current search progress"
    )
    created_at: datetime = Field(..., description="When the search was created")
    completed_at: Optional[datetime] = Field(
        default=None, description="When the search was completed"
    )

    class Config:
        use_enum_values = True


class SearchStatusResponse(BaseModel):
    search_id: int = Field(..., description="Unique identifier for the search")
    status: SearchStatus = Field(..., description="Current status of the search")
    progress: SearchProgress = Field(..., description="Current search progress")
    estimated_completion_time: Optional[int] = Field(
        default=None, description="Estimated time remaining in seconds"
    )
    created_at: datetime = Field(..., description="When the search was created")

    class Config:
        use_enum_values = True


class SearchRefinementResponse(BaseModel):
    refined_results: List[SearchResult] = Field(
        ..., description="Refined search results"
    )
    updated_summary: str = Field(..., description="Updated AI-generated summary")
    refinement_applied: str = Field(
        ..., description="Description of refinement applied"
    )
    total_results: int = Field(..., description="Total number of refined results")


class SavedSolutionResponse(BaseModel):
    id: int = Field(..., description="Unique identifier for the saved solution")
    search_id: int = Field(..., description="ID of the original search")
    result_id: str = Field(..., description="Identifier for the specific result")
    source: SearchSource = Field(..., description="Source of the solution")
    title: str = Field(..., description="Title of the solution")
    description: str = Field(..., description="Description of the solution")
    solution: Optional[str] = Field(default=None, description="Suggested solution")
    url: Optional[str] = Field(default=None, description="External URL if applicable")
    user_notes: Optional[str] = Field(default=None, description="User notes")
    saved_at: datetime = Field(..., description="When the solution was saved")

    class Config:
        use_enum_values = True


class SolutionSearchListResponse(BaseModel):
    searches: List[SolutionSearchResponse] = Field(
        ..., description="List of solution searches"
    )
    total: int = Field(..., description="Total number of searches")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


class SavedSolutionListResponse(BaseModel):
    saved_solutions: List[SavedSolutionResponse] = Field(
        ..., description="List of saved solutions"
    )
    total: int = Field(..., description="Total number of saved solutions")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")


# Database Model Schemas (for internal use)
class SolutionSearchBase(BaseModel):
    problem_description: str
    department: str
    severity: str
    reporter_name: str
    keywords: Optional[List[str]] = []
    search_sources: Optional[List[str]] = ["database", "rag", "web"]
    min_relevance_score: Optional[str] = "0.3"

    class Config:
        from_attributes = True


class SolutionSearchCreate(SolutionSearchBase):
    pass


class SolutionSearchUpdate(BaseModel):
    status: Optional[SearchStatus] = None
    search_results: Optional[Dict[str, Any]] = None
    confidence_score: Optional[str] = None
    summary: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None

    class Config:
        use_enum_values = True


class SolutionSearchInDB(SolutionSearchBase, TimestampMixin):
    id: int
    search_results: Optional[Dict[str, Any]] = {}
    status: SearchStatus
    confidence_score: Optional[str] = None
    summary: Optional[str] = None
    progress: Optional[Dict[str, Any]] = {}
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class SearchResultCacheBase(BaseModel):
    search_id: int
    source: SearchSource
    result_data: Dict[str, Any]
    relevance_score: Optional[str] = None
    result_count: int = 0
    search_query: Optional[str] = None
    search_duration: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class SearchResultCacheCreate(SearchResultCacheBase):
    pass


class SearchResultCacheInDB(SearchResultCacheBase, TimestampMixin):
    id: int

    class Config:
        from_attributes = True
        use_enum_values = True


class SavedSolutionBase(BaseModel):
    search_id: int
    result_id: str
    source: SearchSource
    title: str
    description: str
    solution: Optional[str] = None
    url: Optional[str] = None
    relevance_score: Optional[str] = None
    user_notes: Optional[str] = None
    is_helpful: Optional[str] = None

    class Config:
        from_attributes = True
        use_enum_values = True


class SavedSolutionCreate(SavedSolutionBase):
    pass


class SavedSolutionInDB(SavedSolutionBase, TimestampMixin):
    id: int
    saved_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True
