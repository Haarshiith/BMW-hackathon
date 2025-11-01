from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class SearchStatus(str, enum.Enum):
    searching = "searching"
    completed = "completed"
    failed = "failed"


class SearchSource(str, enum.Enum):
    database = "database"
    rag = "rag"
    web = "web"


class SolutionSearch(Base):
    __tablename__ = "solution_searches"

    id = Column(Integer, primary_key=True, index=True)
    problem_description = Column(Text, nullable=False)
    department = Column(String(100), nullable=False, index=True)
    severity = Column(
        String(20), nullable=False, index=True
    )  # Using string instead of enum for flexibility
    reporter_name = Column(String(100), nullable=False, index=True)
    keywords = Column(JSON, nullable=True, default=[])  # Store extracted keywords

    # Search configuration
    search_sources = Column(JSON, nullable=True, default=["database", "rag", "web"])
    min_relevance_score = Column(String(10), nullable=True, default="0.3")

    # Results and status
    search_results = Column(JSON, nullable=True, default={})
    status = Column(
        Enum(SearchStatus), nullable=False, default=SearchStatus.searching, index=True
    )
    confidence_score = Column(String(10), nullable=True)  # Overall confidence score
    summary = Column(Text, nullable=True)  # AI-generated summary

    # Progress tracking
    progress = Column(
        JSON,
        nullable=True,
        default={
            "database_completed": False,
            "rag_completed": False,
            "web_completed": False,
            "total_sources": 3,
            "completed_sources": 0,
        },
    )

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    result_cache = relationship(
        "SearchResultCache", back_populates="search", cascade="all, delete-orphan"
    )


class SearchResultCache(Base):
    __tablename__ = "search_result_cache"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(
        Integer, ForeignKey("solution_searches.id"), nullable=False, index=True
    )
    source = Column(Enum(SearchSource), nullable=False, index=True)

    # Result data
    result_data = Column(JSON, nullable=False)  # Store the actual search results
    relevance_score = Column(
        String(10), nullable=True
    )  # Overall relevance for this source
    result_count = Column(Integer, nullable=False, default=0)  # Number of results found

    # Metadata
    search_query = Column(Text, nullable=True)  # The actual query used
    search_duration = Column(String(20), nullable=True)  # How long the search took
    error_message = Column(Text, nullable=True)  # If search failed

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    search = relationship("SolutionSearch", back_populates="result_cache")


class SavedSolution(Base):
    __tablename__ = "saved_solutions"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(
        Integer, ForeignKey("solution_searches.id"), nullable=False, index=True
    )
    result_id = Column(
        String(100), nullable=False, index=True
    )  # Identifier for the specific result
    source = Column(Enum(SearchSource), nullable=False, index=True)

    # Solution data
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    solution = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    relevance_score = Column(String(10), nullable=True)

    # User notes
    user_notes = Column(Text, nullable=True)
    is_helpful = Column(String(10), nullable=True)  # "yes", "no", "maybe"

    # Timestamps
    saved_at = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    search = relationship("SolutionSearch")
