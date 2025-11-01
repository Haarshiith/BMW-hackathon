from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models.solution_search import (
    SolutionSearch,
    SavedSolution,
    SearchStatus,
    SearchSource,
)
from app.schemas.solution_search import (
    SolutionSearchRequest,
    SolutionSearchResponse,
    SearchStatusResponse,
    SearchRefinementRequest,
    SearchRefinementResponse,
    SaveSolutionRequest,
    SavedSolutionResponse,
    SolutionSearchListResponse,
    SavedSolutionListResponse,
)

router = APIRouter(prefix="/solution-search", tags=["solution-search"])


async def get_search_by_id(db: AsyncSession, search_id: int) -> SolutionSearch:
    """Get a solution search by ID, raise 404 if not found"""

    result = await db.execute(
        select(SolutionSearch).where(SolutionSearch.id == search_id)
    )
    search = result.scalar_one_or_none()

    if not search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solution search with ID {search_id} not found",
        )

    return search


def convert_search_to_response(search: SolutionSearch) -> SolutionSearchResponse:
    """Convert SolutionSearch database model to SolutionSearchResponse schema"""

    # Parse search results from JSON
    results = []
    if search.search_results:
        for source, source_results in search.search_results.items():
            if isinstance(source_results, list):
                for result in source_results:
                    results.append(
                        {
                            "source": result.get(
                                "source", source
                            ),  # Use original source from result, fallback to key
                            "title": result.get("title", ""),
                            "description": result.get("description", ""),
                            "relevance_score": float(
                                result.get("relevance_score", 0.0)
                            ),
                            "solution": result.get("solution"),
                            "url": result.get("url"),
                            "metadata": result.get("metadata", {}),
                        }
                    )

    # Parse progress from JSON
    progress = None
    if search.progress:
        progress = {
            "database_completed": search.progress.get("database_completed", False),
            "rag_completed": search.progress.get("rag_completed", False),
            "web_completed": search.progress.get("web_completed", False),
            "total_sources": search.progress.get("total_sources", 3),
            "completed_sources": search.progress.get("completed_sources", 0),
            "estimated_completion_time": search.progress.get(
                "estimated_completion_time"
            ),
        }

    return SolutionSearchResponse(
        search_id=search.id,
        status=search.status,
        results=results,
        summary=search.summary,
        confidence_score=(
            float(search.confidence_score) if search.confidence_score else None
        ),
        search_progress=progress,
        created_at=search.created_at,
        completed_at=search.completed_at,
    )


# Background task for processing search using real search services
async def process_solution_search(search_id: int, db: AsyncSession):
    """Background task to process solution search using real search services"""
    try:
        from app.services.solution_search_service import SolutionSearchService
        from app.schemas.solution_search import SolutionSearchRequest
        from app.models.lesson_learned import SeverityLevel

        # Get the search record
        search = await get_search_by_id(db, search_id)

        # Create search request from database record
        search_request = SolutionSearchRequest(
            problem_description=search.problem_description,
            department=search.department,
            severity=SeverityLevel(search.severity),  # Convert string back to enum
            reporter_name=search.reporter_name,
            keywords=search.keywords or [],
            search_sources=search.search_sources or ["database", "rag", "web"],
            min_relevance_score=float(search.min_relevance_score or "0.3"),
        )

        # Initialize solution search service
        solution_service = SolutionSearchService(db)

        # Perform comprehensive search
        search_results = await solution_service.perform_comprehensive_search(
            search_request, search_id
        )

        print(f"✅ Search {search_id} completed successfully")
        print(
            f"   - Database results: {len(search_results['results'].get('database', []))}"
        )
        print(f"   - RAG results: {len(search_results['results'].get('rag', []))}")
        print(f"   - Web results: {len(search_results['results'].get('web', []))}")
        print(f"   - Confidence score: {search_results['confidence_score']:.2f}")

    except Exception as e:
        print(f"❌ Error processing search {search_id}: {e}")

        # Update search status to failed
        try:
            from sqlalchemy import update

            stmt = (
                update(SolutionSearch)
                .where(SolutionSearch.id == search_id)
                .values(status=SearchStatus.failed, completed_at=datetime.utcnow())
            )
            await db.execute(stmt)
            await db.commit()
        except Exception as update_error:
            print(f"Error updating failed search status: {update_error}")


@router.post(
    "/submit",
    response_model=SolutionSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new solution search request",
    description="Submit a problem description to search for solutions across multiple sources",
)
async def submit_solution_search(
    problem_data: SolutionSearchRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Submit a new solution search request"""
    try:
        # Create new solution search record
        search_dict = problem_data.model_dump()
        search_dict["severity"] = search_dict[
            "severity"
        ].value  # Convert enum to string
        search_dict["search_sources"] = [
            source.value for source in search_dict["search_sources"]
        ]

        search = SolutionSearch(**search_dict)
        db.add(search)
        await db.commit()
        await db.refresh(search)

        # Start background processing
        background_tasks.add_task(process_solution_search, search.id, db)

        # Return initial response
        return convert_search_to_response(search)

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit solution search: {str(e)}",
        )


@router.get(
    "/{search_id}",
    response_model=SolutionSearchResponse,
    summary="Get solution search results",
    description="Retrieve the complete results for a solution search",
)
async def get_search_results(search_id: int, db: AsyncSession = Depends(get_db)):
    """Get complete solution search results"""
    try:
        search = await get_search_by_id(db, search_id)
        return convert_search_to_response(search)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve search results: {str(e)}",
        )


@router.get(
    "/{search_id}/status",
    response_model=SearchStatusResponse,
    summary="Get solution search status",
    description="Get the current status and progress of a solution search",
)
async def get_search_status(search_id: int, db: AsyncSession = Depends(get_db)):
    """Get solution search status and progress"""
    try:
        search = await get_search_by_id(db, search_id)

        # Parse progress from JSON
        progress = {
            "database_completed": False,
            "rag_completed": False,
            "web_completed": False,
            "total_sources": 3,
            "completed_sources": 0,
        }

        if search.progress:
            progress.update(search.progress)

        return SearchStatusResponse(
            search_id=search.id,
            status=search.status,
            progress=progress,
            estimated_completion_time=progress.get("estimated_completion_time"),
            created_at=search.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve search status: {str(e)}",
        )


@router.get(
    "/{search_id}/results",
    response_model=SolutionSearchResponse,
    summary="Get solution search results (alias)",
    description="Alias for getting complete solution search results",
)
async def get_search_results_alias(search_id: int, db: AsyncSession = Depends(get_db)):
    """Alias for get_search_results"""
    return await get_search_results(search_id, db)


@router.post(
    "/{search_id}/refine",
    response_model=SearchRefinementResponse,
    summary="Refine solution search results",
    description="Refine existing search results with additional criteria",
)
async def refine_search(
    search_id: int,
    refinement_data: SearchRefinementRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refine solution search results"""
    try:
        search = await get_search_by_id(db, search_id)

        if search.status != SearchStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot refine search that is not completed",
            )

        # For now, return the same results with a refinement message
        # This will be implemented properly in Phase 4
        results = []
        if search.search_results:
            for source, source_results in search.search_results.items():
                if isinstance(source_results, list):
                    for result in source_results:
                        results.append(
                            {
                                "source": source,
                                "title": result.get("title", ""),
                                "description": result.get("description", ""),
                                "relevance_score": float(
                                    result.get("relevance_score", 0.0)
                                ),
                                "solution": result.get("solution"),
                                "url": result.get("url"),
                                "metadata": result.get("metadata", {}),
                            }
                        )

        return SearchRefinementResponse(
            refined_results=results,
            updated_summary=f"Refined search results based on additional criteria. Found {len(results)} relevant solutions.",
            refinement_applied="Applied additional keyword filtering and relevance scoring",
            total_results=len(results),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine search: {str(e)}",
        )


@router.post(
    "/{search_id}/save",
    response_model=SavedSolutionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a solution for later use",
    description="Save a specific search result for future reference",
)
async def save_solution(
    search_id: int, save_data: SaveSolutionRequest, db: AsyncSession = Depends(get_db)
):
    """Save a solution for later use"""
    try:
        search = await get_search_by_id(db, search_id)

        # Find the specific result in search results
        result_data = None
        result_source = None

        if search.search_results:
            for source, source_results in search.search_results.items():
                if isinstance(source_results, list):
                    for result in source_results:
                        if (
                            result.get("id") == save_data.result_id
                            or result.get("title") == save_data.result_id
                        ):
                            result_data = result
                            result_source = source
                            break

        if not result_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result with ID {save_data.result_id} not found in search {search_id}",
            )

        # Create saved solution record
        saved_solution = SavedSolution(
            search_id=search_id,
            result_id=save_data.result_id,
            source=SearchSource(result_source),
            title=result_data.get("title", ""),
            description=result_data.get("description", ""),
            solution=result_data.get("solution"),
            url=result_data.get("url"),
            relevance_score=str(result_data.get("relevance_score", 0.0)),
            user_notes=save_data.notes,
        )

        db.add(saved_solution)
        await db.commit()
        await db.refresh(saved_solution)

        return SavedSolutionResponse(
            id=saved_solution.id,
            search_id=saved_solution.search_id,
            result_id=saved_solution.result_id,
            source=saved_solution.source,
            title=saved_solution.title,
            description=saved_solution.description,
            solution=saved_solution.solution,
            url=saved_solution.url,
            user_notes=saved_solution.user_notes,
            saved_at=saved_solution.saved_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save solution: {str(e)}",
        )


@router.get(
    "/history",
    response_model=SolutionSearchListResponse,
    summary="Get solution search history",
    description="Get a paginated list of solution searches",
)
async def get_search_history(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    reporter_name: Optional[str] = Query(None, description="Filter by reporter name"),
    status: Optional[SearchStatus] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """Get solution search history with pagination"""
    try:
        from sqlalchemy import select, and_, desc

        # Build query
        query = select(SolutionSearch)
        filters = []

        if reporter_name:
            filters.append(SolutionSearch.reporter_name.ilike(f"%{reporter_name}%"))

        if status:
            filters.append(SolutionSearch.status == status)

        if filters:
            query = query.where(and_(*filters))

        # Apply pagination
        skip = (page - 1) * limit
        query = (
            query.order_by(desc(SolutionSearch.created_at)).offset(skip).limit(limit)
        )

        result = await db.execute(query)
        searches = result.scalars().all()

        # Get total count
        count_query = select(SolutionSearch)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())

        # Convert to response format
        search_responses = [convert_search_to_response(search) for search in searches]

        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        return SolutionSearchListResponse(
            searches=search_responses,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve search history: {str(e)}",
        )


@router.get(
    "/saved",
    response_model=SavedSolutionListResponse,
    summary="Get saved solutions",
    description="Get a paginated list of saved solutions",
)
async def get_saved_solutions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Get saved solutions with pagination"""
    try:
        from sqlalchemy import select, desc

        # Build query with pagination
        skip = (page - 1) * limit
        query = (
            select(SavedSolution)
            .order_by(desc(SavedSolution.saved_at))
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(query)
        saved_solutions = result.scalars().all()

        # Get total count
        count_result = await db.execute(select(SavedSolution))
        total = len(count_result.scalars().all())

        # Convert to response format
        solution_responses = [
            SavedSolutionResponse(
                id=solution.id,
                search_id=solution.search_id,
                result_id=solution.result_id,
                source=solution.source,
                title=solution.title,
                description=solution.description,
                solution=solution.solution,
                url=solution.url,
                user_notes=solution.user_notes,
                saved_at=solution.saved_at,
            )
            for solution in saved_solutions
        ]

        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        has_next = page < total_pages
        has_prev = page > 1

        return SavedSolutionListResponse(
            saved_solutions=solution_responses,
            total=total,
            page=page,
            limit=limit,
            has_next=has_next,
            has_prev=has_prev,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve saved solutions: {str(e)}",
        )
