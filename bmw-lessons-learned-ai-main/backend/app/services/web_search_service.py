import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import re

from app.schemas.solution_search import SearchResult, SearchSource
from app.config import settings


class WebSearchService:
    """Service for searching the web using OpenAI's web search tool"""

    def __init__(self):
        self.openai_client = None
        self._initialize_openai()
        self.rate_limit_delay = 1.0  # Delay between requests to avoid rate limiting
        self.last_request_time = 0

    def _initialize_openai(self):
        """Initialize OpenAI client"""
        try:
            from openai import OpenAI

            self.openai_client = OpenAI(api_key=settings.openai_api_key)
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            self.openai_client = None

    async def search_web_solutions(
        self,
        problem_description: str,
        department: str,
        severity: str,
        keywords: Optional[List[str]] = None,
        limit: int = 5,
    ) -> List[SearchResult]:
        """
        Search the web for solutions using OpenAI's web search

        Args:
            problem_description: Problem description to search for
            department: Department context
            severity: Severity level
            keywords: Optional additional keywords
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        try:
            if not self.openai_client:
                print("OpenAI client not initialized")
                return []

            # Rate limiting
            await self._rate_limit()

            # Construct search query
            search_query = self._construct_search_query(
                problem_description, department, severity, keywords
            )

            # Perform web search using OpenAI
            search_results = await self._perform_openai_web_search(search_query, limit)

            # Format results
            formatted_results = []
            for result in search_results:
                formatted_result = self._format_web_result(result, problem_description)
                if formatted_result:
                    print(
                        f"   → Web result: {formatted_result.title} | URL: {formatted_result.url}"
                    )
                    formatted_results.append(formatted_result)

            print(
                f"   ← Web search returned {len(formatted_results)} results with URLs"
            )
            return formatted_results[:limit]

        except Exception as e:
            print(f"Error in web search: {e}")
            return []

    async def search_industry_best_practices(
        self, problem_type: str, department: str, limit: int = 3
    ) -> List[SearchResult]:
        """
        Search for industry best practices related to the problem

        Args:
            problem_type: Type of problem
            department: Department context
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        try:
            if not self.openai_client:
                return []

            await self._rate_limit()

            # Construct best practices query with BMW context
            query = f"BMW automotive manufacturing best practices {problem_type} {department} quality control industry standards"

            search_results = await self._perform_openai_web_search(query, limit)

            formatted_results = []
            for result in search_results:
                formatted_result = self._format_web_result(
                    result, problem_type, is_best_practice=True
                )
                if formatted_result:
                    formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            print(f"Error searching best practices: {e}")
            return []

    async def search_similar_industry_cases(
        self, problem_description: str, industry: str = "manufacturing", limit: int = 3
    ) -> List[SearchResult]:
        """
        Search for similar cases in the industry

        Args:
            problem_description: Problem description
            industry: Industry context
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        try:
            if not self.openai_client:
                return []

            await self._rate_limit()

            # Construct case study query with BMW context
            query = f"BMW automotive {industry} case study solution {problem_description} problem resolution"

            search_results = await self._perform_openai_web_search(query, limit)

            formatted_results = []
            for result in search_results:
                formatted_result = self._format_web_result(
                    result, problem_description, is_case_study=True
                )
                if formatted_result:
                    formatted_results.append(formatted_result)

            return formatted_results

        except Exception as e:
            print(f"Error searching industry cases: {e}")
            return []

    def _construct_search_query(
        self,
        problem_description: str,
        department: str,
        severity: str,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """
        Construct an optimized search query for web search with BMW context

        Args:
            problem_description: Problem description
            department: Department context
            severity: Severity level
            keywords: Optional keywords

        Returns:
            Optimized search query with BMW context
        """
        # Base query components with BMW context
        query_parts = [
            "BMW automotive manufacturing",
            "quality issue solution",
            department,
            problem_description[:100],  # Limit description length
        ]

        # Add severity context
        if severity in ["critical", "high"]:
            query_parts.append("urgent resolution")

        # Add keywords if provided
        if keywords:
            query_parts.extend(keywords[:3])  # Limit to 3 keywords

        # Add BMW and automotive industry context
        query_parts.extend(
            [
                "BMW best practices",
                "automotive industry standards",
                "quality control",
                "manufacturing excellence",
            ]
        )

        # Join and clean the query
        query = " ".join(query_parts)

        # Remove extra whitespace and limit length
        query = re.sub(r"\s+", " ", query).strip()
        return query[:200]  # Limit total query length

    async def _perform_openai_web_search(
        self, query: str, limit: int
    ) -> List[Dict[str, Any]]:
        """
        Perform web search using OpenAI's web search tool

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search result dictionaries
        """
        try:
            # Use OpenAI's web search tool with BMW context
            response = self.openai_client.responses.create(
                model="gpt-4o",
                tools=[{"type": "web_search"}],
                input=f"Search for BMW automotive manufacturing solutions: {query}. Provide {limit} relevant sources with information about manufacturing quality issues and solutions.",
            )

            # Parse response according to OpenAI documentation
            results = []

            # The response.output contains the list of output items
            if hasattr(response, "output") and response.output:
                for item in response.output:
                    # Look for message items which contain the text and annotations
                    if (
                        item.type == "message"
                        and hasattr(item, "content")
                        and item.content
                    ):
                        for content_item in item.content:
                            if content_item.type == "output_text":
                                text = content_item.text
                                annotations = (
                                    getattr(content_item, "annotations", []) or []
                                )

                                # Extract URL citations from annotations
                                if annotations:
                                    for annotation in annotations[:limit]:
                                        if annotation.type == "url_citation":
                                            # Extract the cited text using start_index and end_index
                                            cited_text = ""
                                            if hasattr(
                                                annotation, "start_index"
                                            ) and hasattr(annotation, "end_index"):
                                                cited_text = text[
                                                    annotation.start_index : annotation.end_index
                                                ]

                                            # Clean up markdown citations from the text
                                            # Remove patterns like ([domain](url))

                                            cited_text = re.sub(
                                                r"\(\[.*?\]\(.*?\)\)", "", cited_text
                                            )
                                            # Remove standalone markdown links [text](url)
                                            cited_text = re.sub(
                                                r"\[([^\]]+)\]\([^\)]+\)",
                                                r"\1",
                                                cited_text,
                                            )
                                            # Clean up extra whitespace
                                            cited_text = " ".join(cited_text.split())

                                            # If cited_text is empty or too short, don't show AI intro text
                                            if (
                                                not cited_text
                                                or len(cited_text.strip()) < 50
                                            ):
                                                cited_text = ""

                                            result = {
                                                "title": annotation.title
                                                or "Web Search Result",
                                                "description": (
                                                    cited_text[:300]
                                                    if cited_text
                                                    else "Web search result - click to view full content"
                                                ),
                                                "url": annotation.url,
                                                "source": "web_search",
                                            }
                                            results.append(result)
                                            print(
                                                f"   ✓ Web result: {result['title'][:50]}... | URL: {result['url'][:50]}..."
                                            )
                                else:
                                    # If no annotations but we have text, create a general result
                                    results.append(
                                        {
                                            "title": "Web Search Results",
                                            "description": text[:500],
                                            "url": "",
                                            "source": "web_search",
                                        }
                                    )

            print(f"   → Extracted {len(results)} web search results")
            return results[:limit]

        except Exception as e:
            print(f"Error in OpenAI web search: {e}")
            import traceback

            traceback.print_exc()
            return []

    def _format_web_result(
        self,
        result: Dict[str, Any],
        original_query: str,
        is_best_practice: bool = False,
        is_case_study: bool = False,
    ) -> Optional[SearchResult]:
        """
        Format web search result into SearchResult object

        Args:
            result: Raw web search result
            original_query: Original search query
            is_best_practice: Whether this is a best practice result
            is_case_study: Whether this is a case study result

        Returns:
            Formatted SearchResult or None
        """
        try:
            title = result.get("title", "Web Search Result")
            description = result.get("description", "")
            url = result.get("url", "")

            # Calculate relevance score
            relevance_score = self._calculate_web_relevance(
                title, description, original_query, is_best_practice, is_case_study
            )

            # Only include results with reasonable relevance
            if relevance_score < 0.3:
                return None

            # Determine result type
            if is_best_practice:
                title = f"Best Practice: {title}"
            elif is_case_study:
                title = f"Case Study: {title}"

            return SearchResult(
                source=SearchSource.web,
                title=title,
                description=(
                    description[:300] if description else "No description available"
                ),
                relevance_score=relevance_score,
                solution=self._extract_solution_from_description(description),
                url=url,
                metadata={
                    "search_query": original_query,
                    "result_type": (
                        "best_practice"
                        if is_best_practice
                        else "case_study" if is_case_study else "general"
                    ),
                    "source_domain": self._extract_domain_from_url(url),
                    "search_timestamp": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            print(f"Error formatting web result: {e}")
            return None

    def _calculate_web_relevance(
        self,
        title: str,
        description: str,
        original_query: str,
        is_best_practice: bool = False,
        is_case_study: bool = False,
    ) -> float:
        """
        Calculate relevance score for web search result

        Args:
            title: Result title
            description: Result description
            original_query: Original search query
            is_best_practice: Whether this is a best practice result
            is_case_study: Whether this is a case study result

        Returns:
            Relevance score between 0.0 and 1.0
        """
        score = 0.0

        # Combine title and description for analysis
        text = f"{title} {description}".lower()
        query_lower = original_query.lower()

        # Extract query terms
        query_terms = re.findall(r"\b[a-zA-Z]{3,}\b", query_lower)

        # Calculate term matches
        if query_terms:
            matches = sum(1 for term in query_terms if term in text)
            term_score = matches / len(query_terms)
            score += term_score * 0.6

        # Boost for BMW and automotive terms
        bmw_terms = [
            "bmw",
            "automotive",
            "manufacturing",
            "quality",
            "control",
            "production",
            "process",
            "defect",
            "issue",
            "problem",
            "solution",
            "fix",
            "improvement",
            "automobile",
            "vehicle",
        ]

        bmw_matches = sum(1 for term in bmw_terms if term in text)
        bmw_boost = min(bmw_matches / len(bmw_terms), 0.4)
        score += bmw_boost

        # Extra boost for BMW-specific content
        if "bmw" in text:
            score += 0.1

        # Boost for result type
        if is_best_practice:
            score += 0.1
        elif is_case_study:
            score += 0.15

        # Boost for longer, more detailed content
        content_length = len(text)
        length_boost = min(content_length / 1000, 0.1)
        score += length_boost

        return min(score, 1.0)

    def _extract_solution_from_description(self, description: str) -> Optional[str]:
        """
        Extract solution information from description

        Args:
            description: Result description

        Returns:
            Extracted solution or None
        """
        if not description:
            return None

        # Look for solution indicators
        solution_indicators = [
            "solution:",
            "fix:",
            "resolution:",
            "action:",
            "recommendation:",
            "best practice:",
            "should:",
            "must:",
            "need to:",
            "implement:",
        ]

        description_lower = description.lower()

        for indicator in solution_indicators:
            if indicator in description_lower:
                # Extract text after the indicator
                start_idx = description_lower.find(indicator) + len(indicator)
                solution_text = description[start_idx:].strip()

                # Take first sentence or up to 200 characters
                sentences = solution_text.split(".")
                if sentences:
                    return sentences[0].strip()[:200]

        # If no clear solution indicator, return first part of description
        return description[:200] if len(description) > 50 else None

    def _extract_domain_from_url(self, url: str) -> Optional[str]:
        """
        Extract domain from URL

        Args:
            url: URL string

        Returns:
            Domain name or None
        """
        if not url:
            return None

        try:
            # Simple domain extraction
            if "://" in url:
                domain = url.split("://")[1].split("/")[0]
                return domain
            return None
        except:
            return None

    async def _rate_limit(self):
        """Implement rate limiting to avoid API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()
