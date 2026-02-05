"""
练习会话API测试 - AI英语教学系统
测试练习会话的API端点
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from httpx import AsyncClient

from app.main import app
from app.models import UserRole
from app.models.question import Question, QuestionType, QuestionBank


@pytest.fixture
async def student_client(db):
    """创建学生测试客户端"""
    from app.main import get_db
    from app.api.deps import get_current_user

    student_id = uuid.uuid4()

    async def override_get_db():
        yield db

    async def override_get_current_user():
        user = MagicMock()
        user.id = student_id
        user.role = UserRole.STUDENT
        user.email = "student@example.com"
        user.username = "teststudent"
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def teacher_client(db):
    """创建教师测试客户端"""
    from app.main import get_db
    from app.api.deps import get_current_user

    async def override_get_db():
        yield db

    async def override_get_current_user():
        user = MagicMock()
        user.id = uuid.uuid4()
        user.role = UserRole.TEACHER
        user.email = "teacher@example.com"
        user.username = "testteacher"
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestPracticeSessionsAPI:
    """测试练习会话API"""

    @pytest.mark.asyncio
    async def test_start_practice_session_from_bank(self, student_client, db):
        """测试从题库开始练习"""
        from app.services.practice_session_service import get_practice_session_service

        bank_id = uuid.uuid4()

        # Mock service response
        mock_session = MagicMock()
        mock_session.id = uuid.uuid4()
        mock_session.title = "A2 语法练习"
        mock_session.status = "in_progress"
        mock_session.total_questions = 10
        mock_session.current_question_index = 0
        mock_session.question_count = 0
        mock_session.correct_count = 0
        mock_session.created_at = MagicMock()
        mock_session.created_at.isoformat = MagicMock(return_value="2024-01-01T00:00:00")

        mock_service = AsyncMock()
        mock_service.start_practice_session = AsyncMock(return_value=mock_session)

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_practice_session_service] = mock_get_service

        response = await student_client.post(
            "/api/v1/practice-sessions/",
            json={
                "question_source": "bank",
                "question_bank_id": str(bank_id),
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["total_questions"] == 10
        assert "message" in data

        app.dependency_overrides.pop(get_practice_session_service, None)

    @pytest.mark.asyncio
    async def test_start_practice_session_random(self, student_client, db):
        """测试随机题目开始练习"""
        from app.services.practice_session_service import get_practice_session_service

        # Mock service response
        mock_session = MagicMock()
        mock_session.id = uuid.uuid4()
        mock_session.title = "随机语法练习"
        mock_session.status = "in_progress"
        mock_session.total_questions = 10
        mock_session.current_question_index = 0
        mock_session.question_count = 0
        mock_session.correct_count = 0
        mock_session.created_at = MagicMock()
        mock_session.created_at.isoformat = MagicMock(return_value="2024-01-01T00:00:00")

        mock_service = AsyncMock()
        mock_service.start_practice_session = AsyncMock(return_value=mock_session)

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_practice_session_service] = mock_get_service

        response = await student_client.post(
            "/api/v1/practice-sessions/",
            json={
                "question_source": "random",
                "practice_type": "grammar",
                "difficulty_level": "A2",
                "count": 10,
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "in_progress"

        app.dependency_overrides.pop(get_practice_session_service, None)

    @pytest.mark.asyncio
    async def test_start_practice_session_missing_source(self, student_client):
        """测试缺少题目来源"""
        response = await student_client.post(
            "/api/v1/practice-sessions/",
            json={}
        )

        assert response.status_code == 400
        assert "缺少必填字段" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_start_practice_session_invalid_source(self, student_client):
        """测试无效的题目来源"""
        response = await student_client.post(
            "/api/v1/practice-sessions/",
            json={
                "question_source": "invalid",
            }
        )

        assert response.status_code == 400
        assert "无效的题目来源" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_current_question(self, student_client, db):
        """测试获取当前题目"""
        from app.services.practice_session_service import get_practice_session_service

        session_id = uuid.uuid4()

        # Mock service response
        mock_session = MagicMock()
        mock_session.student_id = uuid.uuid4()

        mock_question = MagicMock()
        mock_question.id = uuid.uuid4()
        mock_question.question_type = QuestionType.CHOICE
        mock_question.content_text = "What is the answer?"
        mock_question.difficulty_level = "A2"
        mock_question.topic = "grammar"
        mock_question.knowledge_points = ["present_tense"]
        mock_question.options = [{"key": "A", "content": "Option A"}]
        mock_question.order_index = 0
        mock_question.passage_content = None
        mock_question.audio_url = None

        mock_service = AsyncMock()
        mock_service.get_practice_session = AsyncMock(return_value=mock_session)
        mock_service.get_current_question = AsyncMock(
            return_value={
                "index": 0,
                "total": 10,
                "is_answered": False,
                "question": mock_question,
            }
        )

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_practice_session_service] = mock_get_service

        response = await student_client.get(f"/api/v1/practice-sessions/{session_id}/current")

        assert response.status_code == 200
        data = response.json()
        assert data["question_index"] == 0
        assert data["total_questions"] == 10
        assert not data["is_answered"]
        assert data["question"]["content_text"] == "What is the answer?"

        app.dependency_overrides.pop(get_practice_session_service, None)

    @pytest.mark.asyncio
    async def test_submit_answer(self, student_client, db):
        """测试提交答案"""
        from app.services.practice_session_service import get_practice_session_service

        session_id = uuid.uuid4()

        # Mock service response
        mock_session = MagicMock()
        mock_session.student_id = uuid.uuid4()

        mock_service = AsyncMock()
        mock_service.get_practice_session = AsyncMock(return_value=mock_session)
        mock_service.submit_answer = AsyncMock(
            return_value={
                "is_correct": True,
                "correct_answer": "A",
                "explanation": "Correct!",
                "current_question_index": 1,
                "correct_count": 1,
                "question_count": 1,
                "is_completed": False,
            }
        )

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_practice_session_service] = mock_get_service

        response = await student_client.post(
            f"/api/v1/practice-sessions/{session_id}/submit",
            json={"answer": "A"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["correct_answer"] == "A"
        assert not data["is_completed"]

        app.dependency_overrides.pop(get_practice_session_service, None)

    @pytest.mark.asyncio
    async def test_submit_answer_missing_answer(self, student_client):
        """测试缺少答案字段"""
        session_id = uuid.uuid4()

        response = await student_client.post(
            f"/api/v1/practice-sessions/{session_id}/submit",
            json={}
        )

        assert response.status_code == 400
        assert "缺少必填字段" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_navigate_next(self, student_client, db):
        """测试下一题"""
        from app.services.practice_session_service import get_practice_session_service

        session_id = uuid.uuid4()

        # Mock service response
        mock_session = MagicMock()
        mock_session.student_id = uuid.uuid4()

        mock_question = MagicMock()
        mock_question.id = uuid.uuid4()
        mock_question.question_type = QuestionType.CHOICE
        mock_question.content_text = "Next question"
        mock_question.difficulty_level = "A2"
        mock_question.topic = "grammar"
        mock_question.knowledge_points = []
        mock_question.options = []
        mock_question.order_index = 1
        mock_question.passage_content = None
        mock_question.audio_url = None

        mock_service = AsyncMock()
        mock_service.get_practice_session = AsyncMock(return_value=mock_session)
        mock_service.next_question = AsyncMock(
            return_value={
                "index": 1,
                "total": 10,
                "is_answered": False,
                "question": mock_question,
            }
        )

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_practice_session_service] = mock_get_service

        response = await student_client.post(
            f"/api/v1/practice-sessions/{session_id}/navigate",
            json={"direction": "next"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["question_index"] == 1
        assert data["question"]["content_text"] == "Next question"

        app.dependency_overrides.pop(get_practice_session_service, None)

    @pytest.mark.asyncio
    async def test_pause_session(self, student_client, db):
        """测试暂停会话"""
        from app.services.practice_session_service import get_practice_session_service

        session_id = uuid.uuid4()

        # Mock service response
        mock_session = MagicMock()
        mock_session.student_id = uuid.uuid4()

        mock_service = AsyncMock()
        mock_service.get_practice_session = AsyncMock(return_value=mock_session)
        mock_service.pause_session = AsyncMock()

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_practice_session_service] = mock_get_service

        response = await student_client.post(f"/api/v1/practice-sessions/{session_id}/pause")

        assert response.status_code == 200
        assert "message" in response.json()

        app.dependency_overrides.pop(get_practice_session_service, None)

    @pytest.mark.asyncio
    async def test_list_practice_sessions(self, student_client, db):
        """测试获取练习会话列表"""
        from app.services.practice_session_service import get_practice_session_service

        # Mock service response
        mock_sessions = []
        for i in range(3):
            session = MagicMock()
            session.id = uuid.uuid4()
            session.title = f"练习 {i+1}"
            session.status = "completed"
            session.total_questions = 10
            session.current_question_index = 10
            session.question_count = 10
            session.correct_count = 8
            session.progress_percentage = 100.0
            session.current_correct_rate = 0.8
            session.question_bank_id = None
            session.created_at = MagicMock()
            session.created_at.isoformat = MagicMock(return_value="2024-01-01T00:00:00")
            session.completed_at = MagicMock()
            session.completed_at.isoformat = MagicMock(return_value="2024-01-01T01:00:00")
            mock_sessions.append(session)

        mock_service = AsyncMock()
        mock_service.list_practice_sessions = AsyncMock(return_value=(mock_sessions, 3))

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_practice_session_service] = mock_get_service

        response = await student_client.get("/api/v1/practice-sessions/")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) == 3

        app.dependency_overrides.pop(get_practice_session_service, None)

    @pytest.mark.asyncio
    async def test_complete_session(self, student_client, db):
        """测试完成练习会话"""
        from app.services.practice_session_service import get_practice_session_service

        session_id = uuid.uuid4()
        practice_id = uuid.uuid4()

        # Mock service response
        mock_session = MagicMock()
        mock_session.student_id = uuid.uuid4()

        from datetime import datetime
        completed_at = datetime.now()

        mock_service = AsyncMock()
        mock_service.get_practice_session = AsyncMock(return_value=mock_session)
        mock_service.complete_session = AsyncMock(
            return_value={
                "practice_id": practice_id,
                "total_questions": 10,
                "answered_questions": 10,
                "correct_count": 8,
                "correct_rate": 0.8,
                "statistics": {
                    "by_type": {},
                    "by_difficulty": {},
                    "by_topic": {},
                },
                "wrong_questions": [],
                "completed_at": completed_at.isoformat(),
            }
        )

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_practice_session_service] = mock_get_service

        response = await student_client.post(f"/api/v1/practice-sessions/{session_id}/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["practice_id"] == str(practice_id)
        assert data["correct_count"] == 8
        assert data["correct_rate"] == 0.8

        app.dependency_overrides.pop(get_practice_session_service, None)
