import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from app.schemas.solution_search import SearchResult, SearchSource

try:
    from langchain_community.vectorstores import Chroma
    from langchain_openai import OpenAIEmbeddings

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("Warning: langchain not available. RAG search will use fallback text search.")


class RAGSearchService:
    """Service for searching through RAG system (Excel files)"""

    def __init__(
        self,
        rag_directory: str = "rag",
        chroma_path: str = "rag/chroma",
        excel_file: str = "Challenge1.xlsx",
    ):
        self.rag_directory = Path(rag_directory)
        self.chroma_path = Path(chroma_path)
        self.excel_file = self.rag_directory / excel_file
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._cached_excel_data = {}
        self._cache_timestamp = None
        self._vector_db = None
        self._embeddings = None

        # Initialize vector database if langchain is available
        if LANGCHAIN_AVAILABLE:
            try:
                self._embeddings = OpenAIEmbeddings()
                if self.chroma_path.exists():
                    self._vector_db = Chroma(
                        persist_directory=str(self.chroma_path),
                        embedding_function=self._embeddings,
                    )
                    print(f"✅ Loaded ChromaDB from {self.chroma_path}")
                else:
                    print(
                        f"⚠️ ChromaDB not found at {self.chroma_path}. Using fallback text search."
                    )
            except Exception as e:
                print(
                    f"⚠️ Error initializing ChromaDB: {e}. Using fallback text search."
                )
                self._vector_db = None

    async def search_excel_data(
        self, query: str, department: Optional[str] = None, limit: int = 10
    ) -> List[SearchResult]:
        """
        Search through Excel data using vector similarity or text search

        Args:
            query: Search query
            department: Optional department filter (ignored for universal knowledge base)
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        try:
            print(
                f"🔍 RAG search called with query: '{query}', dept: '{department}', limit: {limit}"
            )
            print(f"   Vector DB available: {self._vector_db is not None}")
            print(f"   Pandas available: {PANDAS_AVAILABLE}")

            # Try vector search first if available
            if self._vector_db:
                print("   → Using vector search")
                results = await self._vector_search(query, limit)
                print(f"   ← Vector search returned {len(results)} results")
                return results
            else:
                # Fallback to text search
                print("   → Using text search")
                results = await self._text_search(query, department, limit)
                print(f"   ← Text search returned {len(results)} results")
                return results

        except Exception as e:
            print(f"❌ Error in RAG search: {e}")
            import traceback

            traceback.print_exc()
            return []

    async def get_similar_cases(
        self, problem_description: str, department: Optional[str] = None, limit: int = 5
    ) -> List[SearchResult]:
        """
        Find similar cases in the knowledge base

        Args:
            problem_description: Problem description to match
            department: Optional department filter
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        try:
            # Use the main search function with problem description
            return await self.search_excel_data(problem_description, department, limit)

        except Exception as e:
            print(f"Error finding similar cases: {e}")
            return []

    async def search_by_keywords(
        self, keywords: List[str], department: Optional[str] = None, limit: int = 5
    ) -> List[SearchResult]:
        """
        Search knowledge base by specific keywords

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

            # Combine keywords into search query
            query = " ".join(keywords)
            return await self.search_excel_data(query, department, limit)

        except Exception as e:
            print(f"Error in keyword search: {e}")
            return []

    async def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base

        Returns:
            Dictionary with knowledge base statistics
        """
        try:
            markdown_data = await self._load_markdown_data()

            total_files = len(markdown_data)
            total_documents = sum(len(docs) for docs in markdown_data.values())

            # Get file information
            file_info = []
            for file_path, docs in markdown_data.items():
                file_info.append(
                    {
                        "file_name": file_path.name,
                        "documents": len(docs),
                        "last_modified": (
                            file_path.stat().st_mtime if file_path.exists() else None
                        ),
                    }
                )

            return {
                "total_files": total_files,
                "total_documents": total_documents,
                "files": file_info,
                "rag_directory": str(self.rag_directory),
                "chroma_available": self._vector_db is not None,
            }

        except Exception as e:
            print(f"Error getting knowledge base stats: {e}")
            return {
                "total_files": 0,
                "total_documents": 0,
                "files": [],
                "rag_directory": str(self.rag_directory),
                "chroma_available": False,
            }

    async def _vector_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """
        Perform vector similarity search using ChromaDB

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        try:
            # Perform similarity search with relevance scores
            results = self._vector_db.similarity_search_with_relevance_scores(
                query, k=limit
            )

            search_results = []
            for doc, score in results:
                # Apply minimum relevance threshold
                if score < 0.3:
                    continue

                # Extract metadata
                metadata = doc.metadata
                source_file = metadata.get("source", "Unknown")

                # Note: Department filter is ignored in RAG search as knowledge base is universal

                # Extract title and description from content
                title, description, solution = self._parse_markdown_content(
                    doc.page_content
                )

                search_result = SearchResult(
                    source=SearchSource.rag,
                    title=f"Knowledge Base: {title}",
                    description=description,
                    relevance_score=float(score),
                    solution=solution,
                    metadata={
                        "file_path": source_file,
                        "source_type": "markdown_knowledge_base",
                        "department": self._extract_department_from_content(
                            doc.page_content
                        ),
                    },
                )
                search_results.append(search_result)

            return search_results

        except Exception as e:
            print(f"Error in vector search: {e}")
            return []

    async def _text_search(
        self, query: str, department: Optional[str] = None, limit: int = 10
    ) -> List[SearchResult]:
        """
        Perform fallback text search through Excel data

        Args:
            query: Search query
            department: Optional department filter (ignored for universal knowledge base)
            limit: Maximum number of results

        Returns:
            List of SearchResult objects
        """
        try:
            # Load Excel data
            excel_data = await self._load_excel_data()

            if not excel_data:
                return []

            search_results = []
            query_lower = query.lower()
            search_terms = self._extract_search_terms(query)

            for row_index, row_data in excel_data.items():
                # Convert row data to searchable text
                content = self._row_to_searchable_text(row_data)

                relevance_score = self._calculate_text_similarity(
                    content, query_lower, search_terms, department
                )

                if relevance_score >= 0.3:  # Minimum relevance threshold
                    title, description, solution = self._parse_excel_row(row_data)

                    search_result = SearchResult(
                        source=SearchSource.rag,
                        title=f"Knowledge Base: {title}",
                        description=description,
                        relevance_score=relevance_score,
                        solution=solution,
                        metadata={
                            "row_index": row_index,
                            "source_type": "excel_knowledge_base",
                            "department": self._extract_department_from_row(row_data),
                        },
                    )
                    search_results.append(search_result)

            # Sort by relevance and limit results
            search_results.sort(key=lambda x: x.relevance_score, reverse=True)
            return search_results[:limit]

        except Exception as e:
            print(f"Error in text search: {e}")
            return []

    async def _load_excel_data(self) -> Dict[int, Dict[str, Any]]:
        """
        Load Excel data from RAG directory

        Returns:
            Dictionary mapping row indices to row data dictionaries
        """
        try:
            if not PANDAS_AVAILABLE:
                print("Pandas not available. Cannot load Excel data.")
                return {}

            # Check if we need to reload data (cache for 5 minutes)
            import time

            current_time = time.time()
            if (
                self._cached_excel_data
                and self._cache_timestamp
                and (current_time - self._cache_timestamp) < 300
            ):
                return self._cached_excel_data

            excel_data = {}

            if not self.excel_file.exists():
                print(f"Excel file does not exist: {self.excel_file}")
                return excel_data

            # Load Excel file
            try:
                df = pd.read_excel(self.excel_file)
                print(f"Loaded Excel file with {len(df)} rows")

                # Process each row (skip header, so start from index 0)
                for index, row in df.iterrows():
                    # Convert row to dictionary, handling NaN values
                    row_dict = {}
                    for col, value in row.items():
                        if pd.isna(value):
                            row_dict[col] = ""
                        else:
                            row_dict[col] = str(value)

                    excel_data[index] = row_dict

                print(f"Processed {len(excel_data)} rows from Excel file")

            except Exception as e:
                print(f"Error reading Excel file: {e}")
                return {}

            # Cache the data
            self._cached_excel_data = excel_data
            self._cache_timestamp = current_time

            return excel_data

        except Exception as e:
            print(f"Error loading Excel data: {e}")
            return {}

    def _extract_search_terms(self, query: str) -> List[str]:
        """
        Extract search terms from query

        Args:
            query: Search query

        Returns:
            List of search terms
        """
        # Remove common stop words (English and German)
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
            "der",
            "die",
            "das",
            "und",
            "oder",
            "aber",
            "in",
            "auf",
            "an",
            "zu",
            "für",
            "von",
            "mit",
            "durch",
            "ist",
            "sind",
            "war",
            "waren",
            "sein",
            "haben",
            "hat",
            "wird",
            "würde",
            "könnte",
            "sollte",
            "kann",
            "muss",
            "diese",
            "diesen",
        }

        # Extract words (alphanumeric only, minimum 2 characters for German)
        words = re.findall(r"\b[a-zA-ZäöüßÄÖÜ]{2,}\b", query.lower())

        # Filter out stop words and get unique terms
        search_terms = list(set([word for word in words if word not in stop_words]))

        return search_terms[:10]  # Limit to 10 terms

    def _calculate_text_similarity(
        self,
        content: str,
        query: str,
        search_terms: List[str],
        department: Optional[str] = None,
    ) -> float:
        """
        Calculate text similarity score for markdown content

        Args:
            content: Markdown content
            query: Original query
            search_terms: Extracted search terms
            department: Optional department filter

        Returns:
            Similarity score between 0.0 and 1.0
        """
        score = 0.0
        content_lower = content.lower()
        query_lower = query.lower()

        # Note: Department filter is ignored in RAG search as knowledge base is universal

        # Direct query matching (highest priority)
        if query_lower in content_lower:
            score += 0.8

        # Check for key terms from the query
        key_terms = [
            "ece",
            "marking",
            "label",
            "present",
            "missing",
            "fehlt",
            "richtlinie",
        ]
        for term in key_terms:
            if term in query_lower and term in content_lower:
                score += 0.3

        # Text similarity based on search terms
        if search_terms:
            # Count term matches
            matches = sum(1 for term in search_terms if term in content_lower)
            if matches > 0:
                term_score = matches / len(search_terms)
                score += term_score * 0.4

            # Boost score for exact phrase matches
            phrase_matches = sum(
                1
                for term in search_terms
                if term in query_lower and term in content_lower
            )
            if phrase_matches > 0:
                phrase_boost = phrase_matches / len(search_terms) * 0.2
                score += phrase_boost

        # Boost score for longer, more detailed entries
        content_length = len(content)
        length_boost = min(content_length / 1000, 0.1)  # Normalize to 1000 chars
        score += length_boost

        # Cap the score at 1.0
        return min(score, 1.0)

    def _parse_markdown_content(self, content: str) -> Tuple[str, str, Optional[str]]:
        """
        Parse markdown content to extract title, description, and solution

        Args:
            content: Markdown content

        Returns:
            Tuple of (title, description, solution)
        """
        lines = content.split("\n")
        title = "Knowledge Base Entry"
        description = ""
        solution = None

        # Extract title from first heading
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break

        # Extract description from problem description or error context
        in_description = False
        description_parts = []

        for line in lines:
            line = line.strip()
            if line.startswith("**Problembeschreibung**:") or line.startswith(
                "**Fehlerort**"
            ):
                in_description = True
                description_parts.append(line)
            elif line.startswith("**") and in_description:
                break
            elif in_description and line:
                description_parts.append(line)

        if description_parts:
            description = " ".join(description_parts)[:300]

        # Extract solution from Maßnahmen section
        in_solution = False
        solution_parts = []

        for line in lines:
            line = line.strip()
            if "**Maßnahme" in line or "**Empfohlene Maßnahmen**" in line:
                in_solution = True
                solution_parts.append(line)
            elif line.startswith("**") and in_solution and "Maßnahme" not in line:
                break
            elif in_solution and line:
                solution_parts.append(line)

        if solution_parts:
            solution = " ".join(solution_parts)

        return title, description or "No description available", solution

    def _extract_department_from_content(self, content: str) -> Optional[str]:
        """
        Extract department information from markdown content

        Args:
            content: Markdown content

        Returns:
            Department name or None
        """
        # Look for department-related keywords in the content
        content_lower = content.lower()

        # Common department keywords
        dept_keywords = {
            "engineering": ["engineering", "entwicklung", "technik"],
            "quality": ["quality", "qualität", "qm"],
            "production": ["production", "produktion", "fertigung"],
            "supply chain": ["supply", "einkauf", "procurement"],
            "it": ["it", "information", "system"],
        }

        for dept, keywords in dept_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                return dept

        return None

    def _row_to_searchable_text(self, row_data: Dict[str, Any]) -> str:
        """
        Convert Excel row data to searchable text

        Args:
            row_data: Dictionary containing row data

        Returns:
            Combined text from all relevant fields
        """
        # Combine all text fields for searching
        text_parts = []

        # Key fields to include in search
        key_fields = [
            "Commodity",
            "Teilenummer",
            "Lieferant",
            "Fehlerort",
            "Fehlerart",
            "Problembeschreibung",
            "Auftreten Technisch",
            "Auftreten Systemisch",
            "Nicht-Entdecken Technisch",
            "Nicht-Entdecken Systemisch",
            "Maßnahme Auftreten Technisch",
            "Maßnahme Auftreten Systemisch",
            "Maßnahme Nicht-Entdecken Technisch",
            "Maßnahme Nicht-Entdecken Systemisch",
        ]

        for field in key_fields:
            if field in row_data and row_data[field]:
                text_parts.append(str(row_data[field]))

        return " ".join(text_parts)

    def _parse_excel_row(self, row_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Parse Excel row data to extract title, description, and solution

        Args:
            row_data: Dictionary containing row data

        Returns:
            Tuple of (title, description, solution)
        """
        # Create title from key fields
        title_parts = []
        if "Commodity" in row_data and row_data["Commodity"]:
            title_parts.append(str(row_data["Commodity"]))
        if "Fehlerort" in row_data and row_data["Fehlerort"]:
            title_parts.append(str(row_data["Fehlerort"]))
        if "Fehlerart" in row_data and row_data["Fehlerart"]:
            title_parts.append(str(row_data["Fehlerart"]))

        title = " - ".join(title_parts) if title_parts else "Knowledge Base Entry"

        # Create description from problem description
        description = ""
        if "Problembeschreibung" in row_data and row_data["Problembeschreibung"]:
            description = str(row_data["Problembeschreibung"])

        # Create solution from measures
        solution_parts = []
        measure_fields = [
            "Maßnahme Auftreten Technisch",
            "Maßnahme Auftreten Systemisch",
            "Maßnahme Nicht-Entdecken Technisch",
            "Maßnahme Nicht-Entdecken Systemisch",
        ]

        for field in measure_fields:
            if field in row_data and row_data[field]:
                solution_parts.append(str(row_data[field]))

        solution = " | ".join(solution_parts) if solution_parts else None

        return title, description, solution

    def _extract_department_from_row(self, row_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract department from Excel row data

        Args:
            row_data: Dictionary containing row data

        Returns:
            Department name or None
        """
        # Combine all text from the row
        all_text = self._row_to_searchable_text(row_data)
        return self._extract_department_from_content(all_text)
