"""Tests for Conversation API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.models.conversation import ConversationScenario, ConversationStatus
from app.models.student import Student
from app.models.user import User


class TestConversationAPI:
    """Test suite for Conversation API endpoints."""

    @pytest.fixture
    def client(self, db_session):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def test_user(self, db_session):
        """Create test user."""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def test_student(self, db_session, test_user):
        """Create test student."""
        student = Student(
            id=1,
            user_id=test_user.id,
            level="B1",
            learning_goals=["Speaking", "Listening"],
            interests=["Travel", "Technology"]
        )
        db_session.add(student)
        db_session.commit()
        return student

    @pytest.fixture
    def auth_headers(self, client, test_user):
        """Get authentication headers."""
        # Create access token
        from app.core.security import create_access_token
        token = create_access_token(data={"sub": test_user.username})
        return {"Authorization": f"Bearer {token}"}

    def test_create_conversation_success(
        self,
        client,
        auth_headers,
        test_student
    ):
        """Test successful conversation creation."""
        response = client.post(
            "/api/v1/conversations",
            json={
                "scenario": "ordering_food",
                "level": "B1"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["scenario"] == "ordering_food"
        assert data["level"] == "B1"
        assert data["status"] == "active"
        assert data["message_count"] == 0
        assert "id" in data
        assert "started_at" in data

    def test_create_conversation_invalid_level(
        self,
        client,
        auth_headers
    ):
        """Test conversation creation with invalid level."""
        response = client.post(
            "/api/v1/conversations",
            json={
                "scenario": "daily_greeting",
                "level": "X5"
            },
            headers=auth_headers
        )

        assert response.status_code == 422  # Validation error

    def test_create_conversation_no_student_profile(
        self,
        client,
        auth_headers
    ):
        """Test conversation creation without student profile."""
        # Delete student profile
        pass  # Implementation depends on test setup

    def test_send_message_success(
        self,
        client,
        auth_headers,
        test_student,
        db_session
    ):
        """Test sending message successfully."""
        # Create conversation first
        from app.services.speaking_service import SpeakingService
        service = SpeakingService()
        conversation = service.create_conversation(
            student_id=test_student.id,
            scenario=ConversationScenario.DAILY_GREETING,
            level="A1"
        )

        # Mock OpenAI response
        with patch("app.services.speaking_service.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Hello! Nice to meet you!"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            response = client.post(
                f"/api/v1/conversations/{conversation.id}/message",
                json={"message": "Hello, how are you?"},
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["role"] == "assistant"
            assert "Hello! Nice to meet you!" in data["content"]

    def test_send_message_conversation_not_found(
        self,
        client,
        auth_headers
    ):
        """Test sending message to non-existent conversation."""
        response = client.post(
            "/api/v1/conversations/999/message",
            json={"message": "Hello"},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_complete_conversation_success(
        self,
        client,
        auth_headers,
        test_student,
        db_session
    ):
        """Test completing conversation successfully."""
        from app.services.speaking_service import SpeakingService
        service = SpeakingService()
        conversation = service.create_conversation(
            student_id=test_student.id,
            scenario=ConversationScenario.ORDERING_FOOD,
            level="B1"
        )

        # Add messages
        conversation.add_message("user", "I want a burger")
        conversation.add_message("assistant", "Sure, what toppings?")
        db_session.commit()

        # Mock scoring response
        with patch("app.services.speaking_service.OpenAI") as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '''{
                "fluency_score": 70.0,
                "vocabulary_score": 75.0,
                "grammar_score": 65.0,
                "overall_score": 70.0,
                "feedback": "Good effort! Keep practicing."
            }'''
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            response = client.post(
                f"/api/v1/conversations/{conversation.id}/complete",
                headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["scores"]["overall_score"] == 70.0
            assert data["scores"]["feedback"] is not None
            assert "completed_at" in data

    def test_get_conversation_details(
        self,
        client,
        auth_headers,
        test_student,
        db_session
    ):
        """Test getting conversation details."""
        from app.services.speaking_service import SpeakingService
        service = SpeakingService()
        conversation = service.create_conversation(
            student_id=test_student.id,
            scenario=ConversationScenario.SHOPPING,
            level="B2"
        )

        # Add messages
        conversation.add_message("user", "How much is this shirt?")
        conversation.add_message("assistant", "It's $25.")
        db_session.commit()

        response = client.get(
            f"/api/v1/conversations/{conversation.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation.id
        assert data["scenario"] == "shopping"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"

    def test_list_conversations(
        self,
        client,
        auth_headers,
        test_student,
        db_session
    ):
        """Test listing conversations."""
        from app.services.speaking_service import SpeakingService
        service = SpeakingService()

        # Create multiple conversations
        service.create_conversation(
            student_id=test_student.id,
            scenario=ConversationScenario.DAILY_GREETING,
            level="A1"
        )
        service.create_conversation(
            student_id=test_student.id,
            scenario=ConversationScenario.ORDERING_FOOD,
            level="B1"
        )

        response = client.get(
            "/api/v1/conversations",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_available_scenarios(
        self,
        client,
        auth_headers
    ):
        """Test getting available scenarios."""
        response = client.get(
            "/api/v1/conversations/scenarios/available",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert len(data["scenarios"]) == 8

        scenario_ids = [s["id"] for s in data["scenarios"]]
        assert "daily_greeting" in scenario_ids
        assert "ordering_food" in scenario_ids
        assert "job_interview" in scenario_ids

    def test_delete_conversation(
        self,
        client,
        auth_headers,
        test_student,
        db_session
    ):
        """Test deleting a completed conversation."""
        from app.services.speaking_service import SpeakingService
        service = SpeakingService()
        conversation = service.create_conversation(
            student_id=test_student.id,
            scenario=ConversationScenario.DAILY_GREETING,
            level="A1"
        )

        # Complete it first
        conversation.status = ConversationStatus.COMPLETED
        db_session.commit()

        response = client.delete(
            f"/api/v1/conversations/{conversation.id}",
            headers=auth_headers
        )

        assert response.status_code == 204

    def test_delete_active_conversation_fails(
        self,
        client,
        auth_headers,
        test_student,
        db_session
    ):
        """Test that deleting active conversation is not allowed."""
        from app.services.speaking_service import SpeakingService
        service = SpeakingService()
        conversation = service.create_conversation(
            student_id=test_student.id,
            scenario=ConversationScenario.DAILY_GREETING,
            level="A1"
        )

        response = client.delete(
            f"/api/v1/conversations/{conversation.id}",
            headers=auth_headers
        )

        assert response.status_code == 400
