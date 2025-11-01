from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.openai_service import openai_service
from app.schemas.ai_integration import OpenAIRequest, OpenAIResponse
from app.schemas.lesson_learned import LessonLearnedCreate
from app.models.lesson_learned import LessonLearned
from app.utils.database_utils import LessonLearnedRepository
import logging

logger = logging.getLogger(__name__)


class LessonAIService:
    """Service for AI analysis of lessons learned"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = LessonLearnedRepository(db)
        self.openai_service = openai_service

    async def create_lesson_with_ai_analysis(
        self, lesson_data: LessonLearnedCreate
    ) -> LessonLearned:
        """
        Create a lesson learned record with AI analysis

        Args:
            lesson_data: Lesson learned data

        Returns:
            LessonLearned: Created lesson with AI analysis
        """
        try:
            # First, create the lesson without AI analysis
            lesson_dict = lesson_data.model_dump()
            # Normalize department name to lowercase for consistency
            if "department" in lesson_dict:
                lesson_dict["department"] = lesson_dict["department"].lower()
            lesson = await self.repository.create(lesson_dict)

            # Generate AI analysis
            ai_analysis = await self._generate_ai_analysis(lesson_data)

            # Update lesson with AI analysis
            updated_lesson = await self.repository.update(
                lesson.id, {"ai_analysis": ai_analysis.model_dump()}
            )

            logger.info(f"Successfully created lesson {lesson.id} with AI analysis")
            return updated_lesson

        except Exception as e:
            logger.error(f"Failed to create lesson with AI analysis: {e}")
            # If AI analysis fails, still return the lesson without analysis
            if "lesson" in locals():
                logger.warning(
                    f"Returning lesson {lesson.id} without AI analysis due to error"
                )
                return lesson
            raise

    async def update_lesson_ai_analysis(
        self, lesson_id: int
    ) -> Optional[LessonLearned]:
        """
        Update AI analysis for an existing lesson

        Args:
            lesson_id: ID of the lesson to update

        Returns:
            LessonLearned: Updated lesson with new AI analysis
        """
        try:
            # Get existing lesson
            lesson = await self.repository.get_by_id(lesson_id)
            if not lesson:
                return None

            # Create OpenAI request from existing lesson data
            lesson_data = LessonLearnedCreate(
                commodity=lesson.commodity,
                part_number=lesson.part_number,
                supplier=lesson.supplier,
                error_location=lesson.error_location,
                problem_description=lesson.problem_description,
                missed_detection=lesson.missed_detection,
                provided_solution=lesson.provided_solution,
                department=lesson.department,
                severity=lesson.severity,
                reporter_name=lesson.reporter_name,
                attachments=lesson.attachments or [],
            )

            # Generate new AI analysis
            ai_analysis = await self._generate_ai_analysis(lesson_data)

            # Update lesson with new AI analysis
            updated_lesson = await self.repository.update(
                lesson_id, {"ai_analysis": ai_analysis.model_dump()}
            )

            logger.info(f"Successfully updated AI analysis for lesson {lesson_id}")
            return updated_lesson

        except Exception as e:
            logger.error(f"Failed to update AI analysis for lesson {lesson_id}: {e}")
            raise

    async def _generate_ai_analysis(
        self, lesson_data: LessonLearnedCreate
    ) -> OpenAIResponse:
        """
        Generate AI analysis for lesson data

        Args:
            lesson_data: Lesson learned data

        Returns:
            OpenAIResponse: AI analysis results
        """
        try:
            # Convert to OpenAI request format
            openai_request = OpenAIRequest(
                commodity=lesson_data.commodity,
                part_number=lesson_data.part_number,
                supplier=lesson_data.supplier,
                error_location=lesson_data.error_location,
                problem_description=lesson_data.problem_description,
                missed_detection=lesson_data.missed_detection,
                provided_solution=lesson_data.provided_solution,
                department=lesson_data.department,
                severity=lesson_data.severity.value,
                reporter_name=lesson_data.reporter_name,
            )

            # Get AI analysis
            ai_analysis = await self.openai_service.analyze_lesson_learned(
                openai_request
            )

            return ai_analysis

        except Exception as e:
            logger.error(f"Failed to generate AI analysis: {e}")
            raise

    async def get_lesson_with_ai_analysis(
        self, lesson_id: int
    ) -> Optional[LessonLearned]:
        """
        Get a lesson with AI analysis, generating it if not present

        Args:
            lesson_id: ID of the lesson

        Returns:
            LessonLearned: Lesson with AI analysis
        """
        try:
            lesson = await self.repository.get_by_id(lesson_id)
            if not lesson:
                return None

            # If AI analysis is missing, generate it
            if not lesson.ai_analysis:
                logger.info(
                    f"AI analysis missing for lesson {lesson_id}, generating..."
                )
                lesson = await self.update_lesson_ai_analysis(lesson_id)

            return lesson

        except Exception as e:
            logger.error(f"Failed to get lesson with AI analysis {lesson_id}: {e}")
            raise
