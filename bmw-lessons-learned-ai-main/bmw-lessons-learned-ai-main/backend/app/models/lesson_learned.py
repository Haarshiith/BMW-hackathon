from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON
from sqlalchemy.sql import func
from app.database import Base
import enum


class SeverityLevel(str, enum.Enum):
    """Severity levels for lessons learned"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LessonLearned(Base):
    """Main model for storing lessons learned data"""

    __tablename__ = "lessons_learned"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Required fields
    commodity = Column(String(255), nullable=False, index=True)
    error_location = Column(Text, nullable=False)
    problem_description = Column(Text, nullable=False)
    missed_detection = Column(Text, nullable=False)
    provided_solution = Column(Text, nullable=False)
    department = Column(String(100), nullable=False, index=True)
    severity = Column(Enum(SeverityLevel), nullable=False, index=True)
    reporter_name = Column(String(100), nullable=False, index=True)

    # Optional fields
    part_number = Column(String(100), nullable=True, index=True)
    supplier = Column(String(255), nullable=True, index=True)

    # File attachments (stored as JSON array of file paths)
    attachments = Column(JSON, nullable=True, default=list)

    # AI Analysis results (stored as JSON)
    ai_analysis = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<LessonLearned(id={self.id}, commodity='{self.commodity}', department='{self.department}')>"
