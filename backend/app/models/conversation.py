"""Conversation model for AI speaking practice sessions."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.attributes import flag_modified
import enum

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.student import Student


class ConversationScenario(str, enum.Enum):
    """Speaking practice scenarios."""
    DAILY_GREETING = "daily_greeting"
    ORDERING_FOOD = "ordering_food"
    ASKING_DIRECTIONS = "asking_directions"
    JOB_INTERVIEW = "job_interview"
    SHOPPING = "shopping"
    MAKING_APPOINTMENTS = "making_appointments"
    TRAVEL_PLANNING = "travel_planning"
    EMERGENCY_SITUATIONS = "emergency_situations"
    HOTEL_CHECK_IN = "hotel_check_in"
    DOCTOR_VISIT = "doctor_visit"
    BUSINESS_MEETING = "business_meeting"
    RESTAURANT_COMPLAINT = "restaurant_complaint"
    CASUAL_CONVERSATION = "casual_conversation"


class ConversationStatus(str, enum.Enum):
    """Conversation status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Conversation(Base):
    """
    Conversation model for AI speaking practice sessions.

    Attributes:
        id: Primary key
        student_id: Foreign key to student
        scenario: Conversation scenario type
        level: English proficiency level (A1-C2)
        status: Current status of the conversation
        messages: JSON array of conversation messages
        started_at: Conversation start timestamp
        completed_at: Conversation completion timestamp
        fluency_score: Final fluency score (0-100)
        vocabulary_score: Final vocabulary score (0-100)
        grammar_score: Final grammar score (0-100)
        overall_score: Final overall score (0-100)
        feedback: AI feedback on the conversation
        student: Relationship to Student model
    """

    __tablename__ = "conversations"

    # 主键 - 使用PostgreSQL UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 外键到students表
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    scenario: Mapped[ConversationScenario] = mapped_column(
        SQLEnum(ConversationScenario),
        nullable=False
    )

    level: Mapped[str] = mapped_column(String(10), nullable=False)  # A1, A2, B1, B2, C1, C2

    status: Mapped[ConversationStatus] = mapped_column(
        SQLEnum(ConversationStatus),
        default=ConversationStatus.ACTIVE,
        nullable=False
    )

    messages: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON string

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # Scoring fields
    fluency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vocabulary_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grammar_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Enhanced analysis fields (JSON stored as text)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    improvements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    grammar_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vocabulary_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array

    # Relationships
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="conversations"
    )

    def __repr__(self) -> str:
        return (
            f"<Conversation(id={self.id}, student_id={self.student_id}, "
            f"scenario={self.scenario}, status={self.status})>"
        )

    def to_dict(self) -> dict:
        """Convert conversation to dictionary."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "scenario": self.scenario.value if isinstance(self.scenario, ConversationScenario) else self.scenario,
            "level": self.level,
            "status": self.status.value if isinstance(self.status, ConversationStatus) else self.status,
            "messages": self.messages if isinstance(self.messages, list) else [],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "fluency_score": self.fluency_score,
            "vocabulary_score": self.vocabulary_score,
            "grammar_score": self.grammar_score,
            "overall_score": self.overall_score,
            "feedback": self.feedback
        }

    def add_message(self, role: str, content: str, metadata: Optional[dict] = None) -> None:
        """
        Add a message to the conversation.

        Args:
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata (timestamp, corrections, etc.)
        """
        import json

        messages = self.messages if isinstance(self.messages, list) else []
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {})
        })
        self.messages = json.dumps(messages)
        # 通知 SQLAlchemy 这个字段已修改（用于 JSON 字段）
        flag_modified(self, "messages")

    def get_messages(self) -> List[dict]:
        """Get conversation messages as a list."""
        import json
        return self.messages if isinstance(self.messages, list) else json.loads(self.messages or "[]")

    def get_recent_messages(self, limit: int = 10) -> List[dict]:
        """
        Get recent messages for context.

        Args:
            limit: Maximum number of recent messages to return

        Returns:
            List of recent messages
        """
        messages = self.get_messages()
        return messages[-limit:] if messages else []

    def calculate_duration_seconds(self) -> Optional[int]:
        """
        Calculate conversation duration in seconds.

        Returns:
            Duration in seconds, or None if conversation is not completed
        """
        if not self.completed_at or not self.started_at:
            return None
        return int((self.completed_at - self.started_at).total_seconds())
