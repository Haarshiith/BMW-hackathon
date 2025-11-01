from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
import re
from datetime import datetime, timedelta

from app.models.lesson_learned import LessonLearned
from app.schemas.solution_search import SearchResult, SearchSource

try:
    from langchain_openai import OpenAIEmbeddings
    from sklearn.metrics.pairwise import cosine_similarity

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class DatabaseSearchService:
    """Service for searching through existing lessons learned database using semantic similarity"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._embeddings = None

        # Initialize embeddings if available
        if LANGCHAIN_AVAILABLE:
            try:
                self._embeddings = OpenAIEmbeddings()
                print("✅ Database search initialized with semantic similarity")
            except Exception as e:
                print(
                    f"⚠️ Error initializing embeddings: {e}. Using fallback text search."
                )
                self._embeddings = None
        else:
            print("⚠️ Langchain not available. Using fallback text search.")

    async def search_similar_incidents(
        self,
        problem_description: str,
        department: str,
        severity: str,
        keywords: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Search for similar incidents in the database using semantic similarity

        Args:
            problem_description: The problem description to search for
            department: Department to filter by
            severity: Severity level to consider
            keywords: Optional keywords for enhanced search
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        try:
            print(
                f"🔍 Database search: '{problem_description[:50]}...' in {department}"
            )

            # Use semantic similarity if embeddings are available
            if self._embeddings:
                return await self._semantic_search(
                    problem_description, department, severity, keywords, limit
                )
            else:
                # Fallback to text-based search
                return await self._text_based_search(
                    problem_description, department, severity, keywords, limit
                )

        except Exception as e:
            print(f"Error in database search: {e}")
            return []

    async def get_relevant_solutions(
        self, keywords: List[str], department: Optional[str] = None, limit: int = 5
    ) -> List[SearchResult]:
        """
        Get relevant solutions based on keywords

        Args:
            keywords: List of keywords to search for
            department: Optional department filter
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        try:
            if not keywords:
                return []

            # Build keyword search query
            keyword_conditions = []
            for keyword in keywords:
                keyword_conditions.append(
                    or_(
                        LessonLearned.provided_solution.ilike(f"%{keyword}%"),
                        LessonLearned.problem_description.ilike(f"%{keyword}%"),
                        LessonLearned.commodity.ilike(f"%{keyword}%"),
                    )
                )

            query = select(LessonLearned)

            if keyword_conditions:
                query = query.where(or_(*keyword_conditions))

            if department:
                query = query.where(LessonLearned.department.ilike(f"%{department}%"))

            # Order by creation date (most recent first)
            query = query.order_by(LessonLearned.created_at.desc()).limit(limit)

            result = await self.db.execute(query)
            lessons = result.scalars().all()

            # Convert to SearchResult objects
            search_results = []
            for lesson in lessons:
                relevance_score = self._calculate_keyword_relevance(lesson, keywords)

                search_result = SearchResult(
                    source=SearchSource.database,
                    title=f"Solution: {lesson.commodity}",
                    description=f"Proven solution from {lesson.department}. {lesson.provided_solution[:200]}...",
                    relevance_score=relevance_score,
                    solution=lesson.provided_solution,
                    metadata={
                        "incident_id": lesson.id,
                        "department": lesson.department,
                        "severity": lesson.severity.value,
                        "commodity": lesson.commodity,
                        "problem_description": lesson.problem_description,
                        "created_at": lesson.created_at.isoformat(),
                        "reporter_name": lesson.reporter_name,
                    },
                )
                search_results.append(search_result)

            return search_results

        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []

    async def get_department_statistics(self, department: str) -> Dict[str, Any]:
        """
        Get statistics for a specific department

        Args:
            department: Department name

        Returns:
            Dictionary with department statistics
        """
        try:
            # Count total incidents
            total_query = select(func.count(LessonLearned.id)).where(
                LessonLearned.department.ilike(f"%{department}%")
            )
            total_result = await self.db.execute(total_query)
            total_incidents = total_result.scalar()

            # Count by severity
            severity_query = (
                select(LessonLearned.severity, func.count(LessonLearned.id))
                .where(LessonLearned.department.ilike(f"%{department}%"))
                .group_by(LessonLearned.severity)
            )

            severity_result = await self.db.execute(severity_query)
            severity_counts = {row[0].value: row[1] for row in severity_result}

            # Get recent incidents (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_query = select(func.count(LessonLearned.id)).where(
                and_(
                    LessonLearned.department.ilike(f"%{department}%"),
                    LessonLearned.created_at >= thirty_days_ago,
                )
            )
            recent_result = await self.db.execute(recent_query)
            recent_incidents = recent_result.scalar()

            return {
                "total_incidents": total_incidents,
                "severity_breakdown": severity_counts,
                "recent_incidents": recent_incidents,
                "department": department,
            }

        except Exception as e:
            print(f"Error getting department statistics: {e}")
            return {
                "total_incidents": 0,
                "severity_breakdown": {},
                "recent_incidents": 0,
                "department": department,
            }

    async def _semantic_search(
        self,
        problem_description: str,
        department: str,
        severity: str,
        keywords: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Perform semantic search using embeddings

        Args:
            problem_description: The problem description to search for
            department: Department to filter by
            severity: Severity level to consider
            keywords: Optional keywords for enhanced search
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects
        """
        try:
            print("   → Using semantic similarity search")

            # Get all lessons from the database (with department filter)
            # We need all fields for the SearchResult, so we fetch the full objects
            query = select(LessonLearned).where(
                LessonLearned.department.ilike(f"%{department}%")
            )

            result = await self.db.execute(query)
            all_lessons = result.scalars().all()

            if not all_lessons:
                print("   ← No lessons found in database")
                return []

            print(f"   → Found {len(all_lessons)} lessons in database")

            # Create searchable text for each lesson (only problem_description for similarity)
            lesson_texts = []
            for lesson in all_lessons:
                text = self._create_searchable_text(
                    lesson
                )  # Only uses problem_description
                lesson_texts.append(text)

            # Get embedding for the query
            query_text = problem_description
            if keywords:
                query_text += " " + " ".join(keywords)

            query_embedding = self._embeddings.embed_query(query_text)

            # Get embeddings for all lessons
            lesson_embeddings = self._embeddings.embed_documents(lesson_texts)

            # Calculate cosine similarities
            similarities = cosine_similarity([query_embedding], lesson_embeddings)[0]

            # Create results with similarity scores
            search_results = []
            for i, (lesson, similarity) in enumerate(zip(all_lessons, similarities)):
                # Apply minimum similarity threshold
                if similarity >= 0.3:
                    # Adjust score based on severity match and recency
                    adjusted_score = self._adjust_semantic_score(
                        similarity, lesson, severity
                    )

                    search_result = SearchResult(
                        source=SearchSource.database,
                        title=f"Similar Issue: {lesson.commodity}",
                        description=f"Found in {lesson.department} department. {lesson.problem_description[:200]}...",
                        relevance_score=adjusted_score,
                        solution=lesson.provided_solution,
                        metadata={
                            "incident_id": lesson.id,
                            "department": lesson.department,
                            "severity": lesson.severity.value,
                            "commodity": lesson.commodity,
                            "error_location": lesson.error_location,
                            "missed_detection": lesson.missed_detection,
                            "created_at": lesson.created_at.isoformat(),
                            "reporter_name": lesson.reporter_name,
                            "part_number": lesson.part_number,
                            "supplier": lesson.supplier,
                            "semantic_similarity": float(similarity),
                        },
                    )
                    search_results.append(search_result)

            # Sort by relevance score
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)

            print(f"   ← Semantic search returned {len(search_results)} results")
            return search_results[:limit]

        except Exception as e:
            print(f"   ❌ Error in semantic search: {e}")
            # Fallback to text search
            return await self._text_based_search(
                problem_description, department, severity, keywords, limit
            )

    async def _text_based_search(
        self,
        problem_description: str,
        department: str,
        severity: str,
        keywords: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Fallback text-based search (original implementation)
        """
        try:
            print("   → Using text-based search (fallback)")

            # Extract key terms from problem description
            search_terms = self._extract_search_terms(problem_description, keywords)

            # Build search query
            query = select(LessonLearned).where(
                LessonLearned.department.ilike(f"%{department}%")
            )

            # Add text search conditions (focus only on problem_description for better similarity)
            text_conditions = []
            for term in search_terms:
                text_conditions.append(
                    LessonLearned.problem_description.ilike(f"%{term}%")
                )

            if text_conditions:
                query = query.where(or_(*text_conditions))

            # Order by relevance (recent first, then by severity match)
            # Use a simpler ordering approach
            query = query.order_by(LessonLearned.created_at.desc()).limit(
                limit * 2
            )  # Get more results to filter by relevance

            result = await self.db.execute(query)
            lessons = result.scalars().all()

            # Convert to SearchResult objects
            search_results = []
            for lesson in lessons:
                relevance_score = self._calculate_relevance_score(
                    lesson, problem_description, search_terms, severity
                )

                # Only include results with reasonable relevance
                if relevance_score >= 0.3:
                    search_result = SearchResult(
                        source=SearchSource.database,
                        title=f"Similar Issue: {lesson.commodity}",
                        description=f"Found in {lesson.department} department. {lesson.problem_description[:200]}...",
                        relevance_score=relevance_score,
                        solution=lesson.provided_solution,
                        metadata={
                            "incident_id": lesson.id,
                            "department": lesson.department,
                            "severity": lesson.severity.value,
                            "commodity": lesson.commodity,
                            "error_location": lesson.error_location,
                            "missed_detection": lesson.missed_detection,
                            "created_at": lesson.created_at.isoformat(),
                            "reporter_name": lesson.reporter_name,
                            "part_number": lesson.part_number,
                            "supplier": lesson.supplier,
                        },
                    )
                    search_results.append(search_result)

            # Sort by relevance score
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)

            print(f"   ← Text search returned {len(search_results)} results")
            return search_results[:limit]

        except Exception as e:
            print(f"   ❌ Error in text-based search: {e}")
            return []

    def _extract_search_terms(
        self, problem_description: str, keywords: Optional[List[str]] = None
    ) -> List[str]:
        """
        Extract search terms from problem description and keywords

        Args:
            problem_description: The problem description text
            keywords: Optional additional keywords

        Returns:
            List of search terms
        """
        # Combine problem description and keywords
        text = problem_description.lower()
        if keywords:
            text += " " + " ".join(keywords).lower()

        # Remove common stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "this",
            "that",
            "these",
            "those",
        }

        # Extract words (alphanumeric only)
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text)

        # Filter out stop words and get unique terms
        search_terms = list(set([word for word in words if word not in stop_words]))

        # Limit to most relevant terms
        return search_terms[:10]

    def _calculate_relevance_score(
        self,
        lesson: LessonLearned,
        problem_description: str,
        search_terms: List[str],
        target_severity: str,
    ) -> float:
        """
        Calculate relevance score for a lesson (focused on problem_description similarity)

        Args:
            lesson: The lesson learned object
            problem_description: Original problem description
            search_terms: Extracted search terms
            target_severity: Target severity level

        Returns:
            Relevance score between 0.0 and 1.0
        """
        score = 0.0

        # Text similarity (60% weight) - focus only on problem_description
        text_similarity = 0.0
        if lesson.problem_description:
            field_lower = lesson.problem_description.lower()
            matches = sum(1 for term in search_terms if term in field_lower)
            text_similarity = matches / len(search_terms) if search_terms else 0

        score += text_similarity * 0.6

        # Severity match (20% weight)
        if lesson.severity.value == target_severity:
            score += 0.2

        # Recency (20% weight) - more recent = higher score
        days_old = (datetime.utcnow() - lesson.created_at).days
        recency_score = max(0, 1 - (days_old / 365))  # Decay over a year
        score += recency_score * 0.2

        # Solution quality (20% weight) - longer solutions are often better
        solution_length = (
            len(lesson.provided_solution) if lesson.provided_solution else 0
        )
        solution_score = min(solution_length / 500, 1.0)  # Normalize to 500 chars
        score += solution_score * 0.2

        return min(score, 1.0)

    def _calculate_keyword_relevance(
        self, lesson: LessonLearned, keywords: List[str]
    ) -> float:
        """
        Calculate relevance score based on keyword matches

        Args:
            lesson: The lesson learned object
            keywords: List of keywords

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not keywords:
            return 0.0

        # Check keyword matches in solution and problem description
        text_to_search = (
            f"{lesson.provided_solution} {lesson.problem_description}".lower()
        )

        matches = 0
        for keyword in keywords:
            if keyword.lower() in text_to_search:
                matches += 1

        return matches / len(keywords)

    def _create_searchable_text(self, lesson: LessonLearned) -> str:
        """
        Create searchable text from a lesson learned entry
        For solution search, we focus only on problem_description for better similarity matching

        Args:
            lesson: The lesson learned object

        Returns:
            Problem description text for semantic search
        """
        # For solution search, we only use problem_description to find similar problems
        return lesson.problem_description or ""

    def _adjust_semantic_score(
        self, base_similarity: float, lesson: LessonLearned, target_severity: str
    ) -> float:
        """
        Adjust semantic similarity score based on additional factors

        Args:
            base_similarity: Base cosine similarity score
            lesson: The lesson learned object
            target_severity: Target severity level

        Returns:
            Adjusted relevance score
        """
        score = base_similarity

        # Severity match bonus (10% boost)
        if lesson.severity.value == target_severity:
            score += 0.1

        # Recency bonus (5% boost for recent incidents)
        days_old = (datetime.utcnow() - lesson.created_at).days
        if days_old < 30:  # Less than 30 days old
            score += 0.05
        elif days_old < 90:  # Less than 90 days old
            score += 0.02

        # Solution quality bonus (5% boost for detailed solutions)
        if lesson.provided_solution and len(lesson.provided_solution) > 200:
            score += 0.05

        return min(score, 1.0)  # Cap at 1.0
