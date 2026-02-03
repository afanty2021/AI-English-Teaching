"""Tests for SpeakingService."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.speaking_service import SpeakingService
from app.models.conversation import ConversationScenario, ConversationStatus
from app.models.student import Student


class TestSpeakingService:
    """Test suite for SpeakingService."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client."""
        client = Mock()
        client.chat = Mock()
        client.chat.completions = Mock()
        return client

    @pytest.fixture
    def speaking_service(self, mock_openai_client):
        """Create SpeakingService instance with mocked client."""
        return SpeakingService(openai_client=mock_openai_client)

    @pytest.fixture
    def mock_student(self, db_session):
        """Create mock student."""
        import uuid
        student = Student(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            current_cefr_level="B1"
        )
        db_session.add(student)
        db_session.commit()
        return student

    def test_create_conversation_success(
        self,
        speaking_service,
        mock_student,
        db_session
    ):
        """Test successful conversation creation."""
        conversation = speaking_service.create_conversation(
            student_id=str(mock_student.id),
            scenario=ConversationScenario.ORDERING_FOOD,
            level="B1"
        )

        assert conversation.id is not None
        assert conversation.student_id == str(mock_student.id)
        assert conversation.scenario == ConversationScenario.ORDERING_FOOD
        assert conversation.level == "B1"
        assert conversation.status == ConversationStatus.ACTIVE
        assert conversation.started_at is not None
        assert conversation.completed_at is None

    def test_create_conversation_invalid_student(self, speaking_service):
        """Test conversation creation with non-existent student."""
        with pytest.raises(ValueError, match="Student with id 999 not found"):
            speaking_service.create_conversation(
                student_id=999,
                scenario=ConversationScenario.DAILY_GREETING,
                level="A1"
            )

    def test_create_conversation_invalid_level(self, speaking_service, mock_student):
        """Test conversation creation with invalid level."""
        with pytest.raises(ValueError, match="Invalid level X3"):
            speaking_service.create_conversation(
                student_id=str(mock_student.id),
                scenario=ConversationScenario.DAILY_GREETING,
                level="X3"
            )

    def test_send_message_success(
        self,
        speaking_service,
        mock_openai_client,
        mock_student,
        db_session
    ):
        """Test successful message sending and AI response."""
        # Create conversation first
        conversation = speaking_service.create_conversation(
            student_id=str(mock_student.id),
            scenario=ConversationScenario.ORDERING_FOOD,
            level="B1"
        )

        # Mock AI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Hello! What would you like to order?"
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Send message
        response = speaking_service.send_message(
            conversation_id=conversation.id,
            user_message="Hi, I'd like to order lunch please."
        )

        assert response == "Hello! What would you like to order?"
        assert len(conversation.get_messages()) == 2  # user + assistant

    def test_send_message_conversation_not_found(self, speaking_service):
        """Test sending message to non-existent conversation."""
        with pytest.raises(ValueError, match="Conversation 999 not found"):
            speaking_service.send_message(
                conversation_id=999,
                user_message="Hello"
            )

    def test_send_message_conversation_not_active(
        self,
        speaking_service,
        mock_student,
        db_session
    ):
        """Test sending message to completed conversation."""
        # Create and complete conversation
        conversation = speaking_service.create_conversation(
            student_id=str(mock_student.id),
            scenario=ConversationScenario.DAILY_GREETING,
            level="A1"
        )
        conversation.status = ConversationStatus.COMPLETED
        db_session.commit()

        with pytest.raises(ValueError, match="is not active"):
            speaking_service.send_message(
                conversation_id=conversation.id,
                user_message="Hello"
            )

    def test_complete_conversation_success(
        self,
        speaking_service,
        mock_openai_client,
        mock_student,
        db_session
    ):
        """Test successful conversation completion with scoring."""
        # Create conversation
        conversation = speaking_service.create_conversation(
            student_id=str(mock_student.id),
            scenario=ConversationScenario.ORDERING_FOOD,
            level="B1"
        )

        # Add some messages
        conversation.add_message("user", "I would like to order a burger")
        conversation.add_message("assistant", "Sure! What would you like on it?")
        conversation.add_message("user", "Just cheese and lettuce, please")
        db_session.commit()

        # Mock scoring response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''{
            "fluency_score": 75.0,
            "vocabulary_score": 80.0,
            "grammar_score": 70.0,
            "overall_score": 75.0,
            "feedback": "Great job! Your vocabulary is appropriate for the level. Try to use more varied sentence structures."
        }'''
        mock_openai_client.chat.completions.create.return_value = mock_response

        # Complete conversation
        scores = speaking_service.complete_conversation(conversation.id)

        assert scores["fluency_score"] == 75.0
        assert scores["vocabulary_score"] == 80.0
        assert scores["grammar_score"] == 70.0
        assert scores["overall_score"] == 75.0
        assert "Great job!" in scores["feedback"]

        # Verify conversation status updated
        db_session.refresh(conversation)
        assert conversation.status == ConversationStatus.COMPLETED
        assert conversation.completed_at is not None
        assert conversation.overall_score == 75.0

    def test_complete_conversation_too_short(
        self,
        speaking_service,
        mock_student,
        db_session
    ):
        """Test completing conversation with too few messages."""
        # Create conversation
        conversation = speaking_service.create_conversation(
            student_id=str(mock_student.id),
            scenario=ConversationScenario.DAILY_GREETING,
            level="A1"
        )
        db_session.commit()

        # Complete without messages
        scores = speaking_service.complete_conversation(conversation.id)

        # Should return default scores
        assert scores["overall_score"] == 50.0
        assert "too short" in scores["feedback"].lower()

    def test_get_available_scenarios(self, speaking_service):
        """Test getting list of available scenarios."""
        scenarios = speaking_service.get_available_scenarios()

        assert len(scenarios) == 8
        scenario_ids = [s["id"] for s in scenarios]
        assert "daily_greeting" in scenario_ids
        assert "ordering_food" in scenario_ids
        assert "asking_directions" in scenario_ids
        assert "job_interview" in scenario_ids
        assert "shopping" in scenario_ids

    def test_get_system_prompt(self, speaking_service):
        """Test system prompt generation."""
        prompt = speaking_service._get_system_prompt(
            ConversationScenario.ORDERING_FOOD,
            "B1"
        )

        assert "Ordering Food" in prompt
        assert "restaurant" in prompt.lower()
        assert "B1" in prompt
        assert "Intermediate" in prompt

    def test_get_level_guidance(self, speaking_service):
        """Test level guidance generation."""
        a1_guidance = speaking_service._get_level_guidance("A1")
        assert "Beginner" in a1_guidance
        assert "simple words" in a1_guidance.lower()

        c1_guidance = speaking_service._get_level_guidance("C1")
        assert "Advanced" in c1_guidance
        assert "rich vocabulary" in c1_guidance.lower()

    def test_conversation_to_dict(self, mock_student, db_session):
        """Test Conversation.to_dict method."""
        conversation = Conversation(
            id=1,
            student_id=str(mock_student.id),
            scenario=ConversationScenario.DAILY_GREETING,
            level="A1",
            status=ConversationStatus.ACTIVE
        )
        conversation.add_message("user", "Hello")
        conversation.add_message("assistant", "Hi there!")

        conv_dict = conversation.to_dict()

        assert conv_dict["id"] == 1
        assert conv_dict["scenario"] == "daily_greeting"
        assert conv_dict["level"] == "A1"
        assert conv_dict["status"] == "active"
        assert len(conv_dict["messages"]) == 2

    def test_conversation_add_message(self, mock_student):
        """Test adding messages to conversation."""
        conversation = Conversation(
            id=1,
            student_id=str(mock_student.id),
            scenario=ConversationScenario.SHOPPING,
            level="B2",
            status=ConversationStatus.ACTIVE
        )

        conversation.add_message("user", "How much is this?")
        conversation.add_message("assistant", "It's $20.")

        messages = conversation.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "How much is this?"
        assert messages[1]["role"] == "assistant"
        assert "timestamp" in messages[0]

    def test_conversation_get_recent_messages(self, mock_student):
        """Test getting recent messages."""
        conversation = Conversation(
            id=1,
            student_id=str(mock_student.id),
            scenario=ConversationScenario.JOB_INTERVIEW,
            level="C1",
            status=ConversationStatus.ACTIVE
        )

        # Add 15 messages
        for i in range(15):
            conversation.add_message("user" if i % 2 == 0 else "assistant", f"Message {i}")

        recent = conversation.get_recent_messages(limit=10)
        assert len(recent) == 10
        assert recent[0]["content"] == "Message 5"  # Should start from message 5
        assert recent[-1]["content"] == "Message 14"

    def test_scenario_enum_values(self):
        """Test ConversationScenario enum values."""
        assert ConversationScenario.DAILY_GREETING.value == "daily_greeting"
        assert ConversationScenario.ORDERING_FOOD.value == "ordering_food"
        assert ConversationScenario.ASKING_DIRECTIONS.value == "asking_directions"
        assert ConversationScenario.JOB_INTERVIEW.value == "job_interview"
        assert ConversationScenario.SHOPPING.value == "shopping"
        assert ConversationScenario.MAKING_APPOINTMENTS.value == "making_appointments"
        assert ConversationScenario.TRAVEL_PLANNING.value == "travel_planning"
        assert ConversationScenario.EMERGENCY_SITUATIONS.value == "emergency_situations"
