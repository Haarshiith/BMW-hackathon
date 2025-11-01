from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.solution_search import (
    SolutionSearchRequest,
    SearchResult,
    SearchStatus,
)
from app.models.solution_search import SolutionSearch, SearchResultCache
from app.services.database_search_service import DatabaseSearchService
from app.services.rag_search_service import RAGSearchService
from app.services.web_search_service import WebSearchService


class SolutionSearchService:
    """Master service for coordinating solution searches across all sources"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.database_service = DatabaseSearchService(db)
        self.rag_service = RAGSearchService()
        self.web_service = WebSearchService()

    async def perform_comprehensive_search(
        self, search_request: SolutionSearchRequest, search_id: int
    ) -> Dict[str, Any]:
        """
        Perform comprehensive search across all sources

        Args:
            search_request: The search request
            search_id: ID of the search record

        Returns:
            Dictionary with search results and metadata
        """
        try:
            # Update search status to searching
            await self._update_search_status(search_id, SearchStatus.searching)

            # Initialize progress tracking
            progress = {
                "database_completed": False,
                "rag_completed": False,
                "web_completed": False,
                "total_sources": 3,
                "completed_sources": 0,
            }

            all_results = {}
            search_errors = {}

            # Run searches in parallel for better performance
            search_tasks = []

            # Database search
            if "database" in search_request.search_sources:
                task = self._run_database_search(search_request, search_id)
                search_tasks.append(("database", task))

            # RAG search
            if "rag" in search_request.search_sources:
                task = self._run_rag_search(search_request, search_id)
                search_tasks.append(("rag", task))

            # Web search
            if "web" in search_request.search_sources:
                task = self._run_web_search(search_request, search_id)
                search_tasks.append(("web", task))

            # Execute searches with progress tracking
            for source_name, task in search_tasks:
                try:
                    results = await task
                    all_results[source_name] = results
                    progress[f"{source_name}_completed"] = True
                    progress["completed_sources"] += 1

                    # Update progress in database
                    await self._update_search_progress(search_id, progress)

                except Exception as e:
                    print(f"Error in {source_name} search: {e}")
                    search_errors[source_name] = str(e)
                    progress[f"{source_name}_completed"] = True
                    progress["completed_sources"] += 1
                    await self._update_search_progress(search_id, progress)

            # Rank and filter results
            ranked_results = await self.rank_and_filter_results(
                all_results, search_request, search_id
            )

            # Generate AI summary
            summary = await self.generate_solution_summary(
                ranked_results, search_request
            )

            # Calculate overall confidence score
            confidence_score = self._calculate_confidence_score(ranked_results)

            # Update search with final results
            final_results = {
                "database": [
                    result.model_dump() for result in ranked_results.get("database", [])
                ],
                "rag": [
                    result.model_dump() for result in ranked_results.get("rag", [])
                ],
                "web": [
                    result.model_dump() for result in ranked_results.get("web", [])
                ],
            }

            await self._update_search_results(
                search_id, final_results, summary, confidence_score, progress
            )

            return {
                "search_id": search_id,
                "results": ranked_results,
                "summary": summary,
                "confidence_score": confidence_score,
                "errors": search_errors,
                "progress": progress,
            }

        except Exception as e:
            print(f"Error in comprehensive search: {e}")
            await self._update_search_status(search_id, SearchStatus.failed)
            raise

    async def _run_database_search(
        self, search_request: SolutionSearchRequest, search_id: int
    ) -> List[SearchResult]:
        """Run database search and cache results"""
        try:
            # Perform database search
            results = await self.database_service.search_similar_incidents(
                problem_description=search_request.problem_description,
                department=search_request.department,
                severity=search_request.severity.value,
                keywords=search_request.keywords,
                limit=10,
            )

            # Cache results
            await self._cache_search_results(search_id, "database", results)

            return results

        except Exception as e:
            print(f"Database search error: {e}")
            return []

    async def _run_rag_search(
        self, search_request: SolutionSearchRequest, search_id: int
    ) -> List[SearchResult]:
        """Run RAG search and cache results"""
        try:
            # Perform RAG search
            results = await self.rag_service.search_excel_data(
                query=search_request.problem_description,
                department=search_request.department,
                limit=8,
            )

            # Cache results
            await self._cache_search_results(search_id, "rag", results)

            return results

        except Exception as e:
            print(f"RAG search error: {e}")
            return []

    async def _run_web_search(
        self, search_request: SolutionSearchRequest, search_id: int
    ) -> List[SearchResult]:
        """Run web search and cache results"""
        try:
            # Perform web search
            results = await self.web_service.search_web_solutions(
                problem_description=search_request.problem_description,
                department=search_request.department,
                severity=search_request.severity.value,
                keywords=search_request.keywords,
                limit=5,
            )

            # Cache results
            await self._cache_search_results(search_id, "web", results)

            return results

        except Exception as e:
            print(f"Web search error: {e}")
            return []

    async def rank_and_filter_results(
        self,
        all_results: Dict[str, List[SearchResult]],
        search_request: SolutionSearchRequest,
        search_id: int,
    ) -> Dict[str, List[SearchResult]]:
        """
        Rank and filter results from all sources

        Args:
            all_results: Results from all search sources
            search_request: Original search request
            search_id: Search ID for logging

        Returns:
            Ranked and filtered results
        """
        try:
            ranked_results = {}

            for source, results in all_results.items():
                if not results:
                    ranked_results[source] = []
                    continue

                # Apply minimum relevance filter
                filtered_results = [
                    result
                    for result in results
                    if result.relevance_score >= search_request.min_relevance_score
                ]

                # Sort by relevance score
                filtered_results.sort(key=lambda x: x.relevance_score, reverse=True)

                # Limit results per source
                max_results_per_source = {"database": 8, "rag": 6, "web": 4}

                limit = max_results_per_source.get(source, 5)
                ranked_results[source] = filtered_results[:limit]

            return ranked_results

        except Exception as e:
            print(f"Error ranking results: {e}")
            return all_results

    async def generate_solution_summary(
        self,
        ranked_results: Dict[str, List[SearchResult]],
        search_request: SolutionSearchRequest,
    ) -> str:
        """
        Generate AI-powered summary of search results

        Args:
            ranked_results: Ranked results from all sources
            search_request: Original search request

        Returns:
            AI-generated summary
        """
        try:
            # Count results by source
            total_results = sum(len(results) for results in ranked_results.values())

            if total_results == 0:
                return f"No relevant solutions found for your {search_request.severity.value} severity issue in {search_request.department} department. Consider refining your search criteria or consulting with domain experts."

            # Create summary based on results
            summary_parts = []

            # Database results summary
            db_results = ranked_results.get("database", [])
            if db_results:
                summary_parts.append(
                    f"Found {len(db_results)} similar incidents in our internal database with proven solutions."
                )

            # RAG results summary
            rag_results = ranked_results.get("rag", [])
            if rag_results:
                summary_parts.append(
                    f"Located {len(rag_results)} relevant entries in our knowledge base."
                )

            # Web results summary
            web_results = ranked_results.get("web", [])
            if web_results:
                summary_parts.append(
                    f"Identified {len(web_results)} industry best practices and external solutions."
                )

            # Combine summary parts
            base_summary = f"Search completed for your {search_request.severity.value} severity issue in {search_request.department} department. "
            base_summary += " ".join(summary_parts)

            # Add confidence indicator
            if total_results >= 5:
                base_summary += " High confidence in the provided solutions."
            elif total_results >= 2:
                base_summary += " Moderate confidence in the provided solutions."
            else:
                base_summary += (
                    " Limited results available - consider additional research."
                )

            return base_summary

        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Search completed for your {search_request.severity.value} severity issue in {search_request.department} department. Results are available for review."

    def _calculate_confidence_score(
        self, ranked_results: Dict[str, List[SearchResult]]
    ) -> float:
        """
        Calculate overall confidence score for the search results

        Args:
            ranked_results: Ranked results from all sources

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            if not ranked_results:
                return 0.0

            # Calculate weighted confidence based on source reliability and result quality
            source_weights = {
                "database": 0.5,  # Highest weight - internal data
                "rag": 0.3,  # Medium weight - knowledge base
                "web": 0.2,  # Lower weight - external sources
            }

            total_confidence = 0.0
            total_weight = 0.0

            for source, results in ranked_results.items():
                if not results:
                    continue

                # Calculate average relevance for this source
                avg_relevance = sum(result.relevance_score for result in results) / len(
                    results
                )

                # Weight by source reliability
                source_weight = source_weights.get(source, 0.1)
                weighted_confidence = avg_relevance * source_weight

                total_confidence += weighted_confidence
                total_weight += source_weight

            # Normalize confidence score
            if total_weight > 0:
                confidence = total_confidence / total_weight
            else:
                confidence = 0.0

            # Boost confidence if we have results from multiple sources
            source_count = len(
                [source for source, results in ranked_results.items() if results]
            )
            if source_count > 1:
                confidence *= 1.1  # 10% boost for multi-source results

            return min(confidence, 1.0)

        except Exception as e:
            print(f"Error calculating confidence score: {e}")
            return 0.0

    async def _update_search_status(self, search_id: int, status: SearchStatus):
        """Update search status in database"""
        try:
            from sqlalchemy import select, update

            stmt = (
                update(SolutionSearch)
                .where(SolutionSearch.id == search_id)
                .values(status=status)
            )

            await self.db.execute(stmt)
            await self.db.commit()

        except Exception as e:
            print(f"Error updating search status: {e}")

    async def _update_search_progress(self, search_id: int, progress: Dict[str, Any]):
        """Update search progress in database"""
        try:
            from sqlalchemy import update

            stmt = (
                update(SolutionSearch)
                .where(SolutionSearch.id == search_id)
                .values(progress=progress)
            )

            await self.db.execute(stmt)
            await self.db.commit()

        except Exception as e:
            print(f"Error updating search progress: {e}")

    async def _update_search_results(
        self,
        search_id: int,
        results: Dict[str, Any],
        summary: str,
        confidence_score: float,
        progress: Dict[str, Any],
    ):
        """Update search with final results"""
        try:
            from sqlalchemy import update

            stmt = (
                update(SolutionSearch)
                .where(SolutionSearch.id == search_id)
                .values(
                    search_results=results,
                    summary=summary,
                    confidence_score=str(confidence_score),
                    status=SearchStatus.completed,
                    completed_at=datetime.utcnow(),
                    progress=progress,
                )
            )

            await self.db.execute(stmt)
            await self.db.commit()

        except Exception as e:
            print(f"Error updating search results: {e}")

    async def _cache_search_results(
        self, search_id: int, source: str, results: List[SearchResult]
    ):
        """Cache search results in database"""
        try:
            # Create cache entry
            cache_entry = SearchResultCache(
                search_id=search_id,
                source=source,
                result_data=[result.model_dump() for result in results],
                result_count=len(results),
                relevance_score=(
                    str(
                        sum(result.relevance_score for result in results) / len(results)
                    )
                    if results
                    else "0.0"
                ),
            )

            self.db.add(cache_entry)
            await self.db.commit()

        except Exception as e:
            print(f"Error caching search results: {e}")

    async def get_search_statistics(self) -> Dict[str, Any]:
        """Get statistics about solution searches"""
        try:
            from sqlalchemy import select, func

            # Total searches
            total_query = select(func.count(SolutionSearch.id))
            total_result = await self.db.execute(total_query)
            total_searches = total_result.scalar()

            # Searches by status
            status_query = select(
                SolutionSearch.status, func.count(SolutionSearch.id)
            ).group_by(SolutionSearch.status)

            status_result = await self.db.execute(status_query)
            status_counts = {row[0].value: row[1] for row in status_result}

            # Searches by department
            dept_query = select(
                SolutionSearch.department, func.count(SolutionSearch.id)
            ).group_by(SolutionSearch.department)

            dept_result = await self.db.execute(dept_query)
            dept_counts = {row[0]: row[1] for row in dept_result}

            return {
                "total_searches": total_searches,
                "status_breakdown": status_counts,
                "department_breakdown": dept_counts,
            }

        except Exception as e:
            print(f"Error getting search statistics: {e}")
            return {
                "total_searches": 0,
                "status_breakdown": {},
                "department_breakdown": {},
            }
