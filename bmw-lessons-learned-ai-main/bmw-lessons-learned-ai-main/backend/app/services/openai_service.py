import json
from typing import List
from openai import AsyncOpenAI
from app.config import settings
from app.schemas.ai_integration import (
    OpenAIRequest,
    OpenAIResponse,
    DepartmentSummaryRequest,
    DepartmentSummaryResponse,
)
import logging

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for OpenAI API integration"""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = "gpt-4.1"  # Can be changed to gpt-4 for better results

    async def analyze_lesson_learned(
        self, lesson_data: OpenAIRequest
    ) -> OpenAIResponse:
        """
        Analyze a lesson learned and generate AI insights

        Args:
            lesson_data: Lesson learned data to analyze

        Returns:
            OpenAIResponse: AI analysis results

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            # Generate prompt from lesson data
            prompt = lesson_data.to_prompt_text()

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in quality management and continuous improvement. Analyze quality issues and provide structured insights for manufacturing processes. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=2048,
                response_format={"type": "json_object"},
            )

            # Parse the response
            content = response.choices[0].message.content
            if not content:
                raise Exception("Empty response from OpenAI")

            # Parse JSON response
            try:
                ai_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI JSON response: {e}")
                logger.error(f"Raw response: {content}")
                raise Exception(f"Invalid JSON response from OpenAI: {e}")

            # Validate and create response
            ai_response = OpenAIResponse(**ai_data)

            logger.info(
                f"Successfully analyzed lesson for commodity: {lesson_data.commodity}"
            )
            return ai_response

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise Exception(f"AI analysis failed: {str(e)}")

    async def generate_department_summary(
        self, department: str, lesson_summaries: List[str]
    ) -> DepartmentSummaryResponse:
        """
        Generate a consolidated department summary from multiple lesson summaries

        Args:
            department: Department name
            lesson_summaries: List of lesson summaries to analyze

        Returns:
            DepartmentSummaryResponse: Consolidated department insights

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            # Create department summary request
            summary_request = DepartmentSummaryRequest(
                department=department, lesson_summaries=lesson_summaries
            )

            # Generate prompt
            prompt = summary_request.to_prompt_text()

            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in quality management and continuous improvement. Analyze multiple lesson summaries from a department and provide comprehensive insights. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,  # Slightly higher for more creative insights
                max_tokens=2048,
                response_format={"type": "json_object"},
            )

            # Parse the response
            content = response.choices[0].message.content
            if not content:
                raise Exception("Empty response from OpenAI")

            # Parse JSON response
            try:
                ai_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI JSON response: {e}")
                logger.error(f"Raw response: {content}")
                raise Exception(f"Invalid JSON response from OpenAI: {e}")

            # Validate and create response
            ai_response = DepartmentSummaryResponse(**ai_data)

            logger.info(f"Successfully generated department summary for: {department}")
            return ai_response

        except Exception as e:
            logger.error(f"OpenAI department summary failed: {e}")
            raise Exception(f"Department summary generation failed: {str(e)}")


# Global instance
openai_service = OpenAIService()
