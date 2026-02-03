"""Conversation schemas for request/response validation."""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ConversationScenario(str, Enum):
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


class ConversationStatus(str, Enum):
    """Conversation status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class MessageSchema(BaseModel):
    """Schema for a conversation message."""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp (ISO format)")


class CreateConversationRequest(BaseModel):
    """Request schema for creating a new conversation."""
    scenario: ConversationScenario = Field(
        ...,
        description="Conversation scenario type"
    )
    level: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="English proficiency level (A1-C2)"
    )

    @field_validator('level')
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate that level is in correct format."""
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid level '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v.upper()

    model_config = {
        "json_schema_extra": {
            "example": {
                "scenario": "ordering_food",
                "level": "B1"
            }
        }
    }


class SendMessageRequest(BaseModel):
    """Request schema for sending a message in conversation."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="User's message content"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "I would like to order a cheeseburger, please."
            }
        }
    }


class ConversationScores(BaseModel):
    """Schema for conversation scores - Enhanced with detailed analysis."""
    fluency_score: Optional[float] = Field(None, description="Fluency score (0-100)")
    vocabulary_score: Optional[float] = Field(None, description="Vocabulary score (0-100)")
    grammar_score: Optional[float] = Field(None, description="Grammar score (0-100)")
    overall_score: Optional[float] = Field(None, description="Overall score (0-100)")
    feedback: Optional[str] = Field(None, description="AI feedback on performance")
    strengths: List[str] = Field(default_factory=list, description="Student's strengths in this conversation")
    improvements: List[str] = Field(default_factory=list, description="Areas for improvement")
    grammar_notes: Optional[str] = Field(None, description="Specific grammar observations")
    vocabulary_notes: Optional[str] = Field(None, description="Vocabulary usage observations")
    recommendations: List[str] = Field(default_factory=list, description="Learning recommendations")


class ConversationResponse(BaseModel):
    """Response schema for conversation summary."""
    id: str = Field(..., description="Conversation ID (UUID)")
    student_id: str = Field(..., description="Student ID (UUID)")
    scenario: str = Field(..., description="Conversation scenario")
    level: str = Field(..., description="Student's level")
    status: str = Field(..., description="Conversation status")
    message_count: int = Field(..., description="Number of messages in conversation")
    started_at: datetime = Field(..., description="Conversation start time")
    completed_at: Optional[datetime] = Field(None, description="Conversation completion time")

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    """Response schema for detailed conversation information."""
    id: str = Field(..., description="Conversation ID (UUID)")
    student_id: str = Field(..., description="Student ID (UUID)")
    scenario: str = Field(..., description="Conversation scenario")
    level: str = Field(..., description="Student's level")
    status: str = Field(..., description="Conversation status")
    messages: List[MessageSchema] = Field(default_factory=list, description="Conversation messages")
    started_at: datetime = Field(..., description="Conversation start time")
    completed_at: Optional[datetime] = Field(None, description="Conversation completion time")
    scores: Optional[ConversationScores] = Field(None, description="Conversation scores (if completed)")

    model_config = {"from_attributes": True}


class SendMessageResponse(BaseModel):
    """Response schema for sending a message."""
    message_id: Optional[str] = Field(None, description="Message ID")
    role: str = Field(..., description="Message role")
    content: str = Field(..., description="AI response content")
    timestamp: str = Field(..., description="Response timestamp")


class CompleteConversationResponse(BaseModel):
    """Response schema for completing a conversation."""
    conversation_id: str = Field(..., description="Conversation ID (UUID)")
    status: str = Field(..., description="Final status")
    completed_at: datetime = Field(..., description="Completion timestamp")
    scores: ConversationScores = Field(..., description="Performance scores")
    message_count: int = Field(..., description="Total number of messages")
    duration_seconds: Optional[int] = Field(None, description="Conversation duration in seconds")


class ScenarioInfo(BaseModel):
    """Schema for scenario information."""
    id: str = Field(..., description="Scenario ID")
    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")
    context: str = Field(..., description="Scenario context")


class ScenariosListResponse(BaseModel):
    """Response schema for list of available scenarios."""
    scenarios: List[ScenarioInfo] = Field(..., description="List of available scenarios")


class MessageListResponse(BaseModel):
    """Response schema for conversation messages."""
    conversation_id: str = Field(..., description="Conversation ID (UUID)")
    messages: List[MessageSchema] = Field(..., description="List of messages")
    total_count: int = Field(..., description="Total number of messages")
