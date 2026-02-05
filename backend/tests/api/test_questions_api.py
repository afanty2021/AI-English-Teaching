"""
题目API测试 - AI英语教学系统
测试题目管理的API端点
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from httpx import AsyncClient

from app.main import app
from app.models import UserRole
from app.models.question import Question, QuestionType


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


@pytest.fixture
async def student_client(db):
    """创建学生测试客户端"""
    from app.main import get_db
    from app.api.deps import get_current_user

    async def override_get_db():
        yield db

    async def override_get_current_user():
        user = MagicMock()
        user.id = uuid.uuid4()
        user.role = UserRole.STUDENT
        user.email = "student@example.com"
        user.username = "teststudent"
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


class TestQuestionsAPI:
    """测试题目API"""

    @pytest.mark.asyncio
    async def test_create_question_success(self, teacher_client, db):
        """测试成功创建题目"""
        from app.services.question_service import get_question_service

        # Mock service response
        mock_question = MagicMock()
        mock_question.id = uuid.uuid4()
        mock_question.question_type = QuestionType.CHOICE
        mock_question.content_text = "What is the correct answer?"
        mock_question.question_bank_id = None
        mock_question.difficulty_level = "A2"
        mock_question.topic = "grammar"
        mock_question.knowledge_points = ["present_tense"]
        mock_question.options = [{"key": "A", "content": "Option A"}]
        mock_question.correct_answer = {"key": "A"}
        mock_question.explanation = "This is the explanation"
        mock_question.order_index = 0
        mock_question.passage_content = None
        mock_question.audio_url = None
        mock_question.sample_answer = None
        mock_question.created_by = uuid.uuid4()
        mock_question.created_at = MagicMock()
        mock_question.created_at.isoformat = MagicMock(return_value="2024-01-01T00:00:00")

        mock_service = AsyncMock()
        mock_service.create_question = AsyncMock(return_value=mock_question)

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_question_service] = mock_get_service

        response = await teacher_client.post(
            "/api/v1/questions/",
            json={
                "question_type": "choice",
                "content_text": "What is the correct answer?",
                "difficulty_level": "A2",
                "topic": "grammar",
                "knowledge_points": ["present_tense"],
                "options": [{"key": "A", "content": "Option A"}],
                "correct_answer": {"key": "A"},
                "explanation": "This is the explanation",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["question_type"] == "choice"
        assert data["content_text"] == "What is the correct answer?"
        assert "message" in data

        app.dependency_overrides.pop(get_question_service, None)

    @pytest.mark.asyncio
    async def test_create_question_student_forbidden(self, student_client):
        """测试学生不能创建题目"""
        response = await student_client.post(
            "/api/v1/questions/",
            json={
                "question_type": "choice",
                "content_text": "Test question",
            }
        )

        assert response.status_code == 403
        assert "只有教师可以创建题目" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_question_missing_fields(self, teacher_client):
        """测试缺少必填字段"""
        response = await teacher_client.post(
            "/api/v1/questions/",
            json={
                "difficulty_level": "A2",
            }
        )

        assert response.status_code == 400
        assert "缺少必填字段" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_question_invalid_type(self, teacher_client):
        """测试无效的题目类型"""
        response = await teacher_client.post(
            "/api/v1/questions/",
            json={
                "question_type": "invalid_type",
                "content_text": "Test question",
            }
        )

        assert response.status_code == 400
        assert "无效的题目类型" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_questions(self, teacher_client, db):
        """测试获取题目列表"""
        from app.services.question_service import get_question_service

        # Mock service response
        mock_questions = []
        for i in range(3):
            question = MagicMock()
            question.id = uuid.uuid4()
            question.question_type = QuestionType.CHOICE
            question.content_text = f"Question {i+1}"
            question.question_bank_id = None
            question.difficulty_level = "A2"
            question.topic = "grammar"
            question.knowledge_points = []
            question.options = []
            question.has_audio = False
            question.is_active = True
            question.order_index = i
            question.created_by = uuid.uuid4()
            question.created_at = MagicMock()
            question.created_at.isoformat = MagicMock(return_value="2024-01-01T00:00:00")
            mock_questions.append(question)

        mock_service = AsyncMock()
        mock_service.list_questions = AsyncMock(return_value=(mock_questions, 3))

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_question_service] = mock_get_service

        response = await teacher_client.get("/api/v1/questions/")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) == 3

        app.dependency_overrides.pop(get_question_service, None)

    @pytest.mark.asyncio
    async def test_list_questions_with_filters(self, teacher_client, db):
        """测试带筛选条件的题目列表"""
        from app.services.question_service import get_question_service

        mock_service = AsyncMock()
        mock_service.list_questions = AsyncMock(return_value=([], 0))

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_question_service] = mock_get_service

        response = await teacher_client.get(
            "/api/v1/questions/",
            params={
                "question_type": "choice",
                "difficulty_level": "A2",
                "topic": "grammar",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

        app.dependency_overrides.pop(get_question_service, None)

    @pytest.mark.asyncio
    async def test_batch_create_questions(self, teacher_client, db):
        """测试批量创建题目"""
        from app.services.question_service import get_question_service

        # Mock service response
        mock_questions = []
        for i in range(2):
            question = MagicMock()
            question.id = uuid.uuid4()
            question.question_type = QuestionType.CHOICE
            question.content_text = f"Question {i+1}"
            question.question_bank_id = uuid.uuid4()
            question.order_index = i
            mock_questions.append(question)

        mock_service = AsyncMock()
        mock_service.batch_create_questions = AsyncMock(return_value=mock_questions)

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_question_service] = mock_get_service

        response = await teacher_client.post(
            "/api/v1/questions/batch",
            json={
                "questions": [
                    {
                        "question_type": "choice",
                        "content_text": "Question 1",
                    },
                    {
                        "question_type": "choice",
                        "content_text": "Question 2",
                    },
                ]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        app.dependency_overrides.pop(get_question_service, None)

    @pytest.mark.asyncio
    async def test_batch_create_questions_student_forbidden(self, student_client):
        """测试学生不能批量创建题目"""
        response = await student_client.post(
            "/api/v1/questions/batch",
            json={
                "questions": [
                    {
                        "question_type": "choice",
                        "content_text": "Question 1",
                    }
                ]
            }
        )

        assert response.status_code == 403
        assert "只有教师可以批量创建题目" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_batch_create_questions_empty_array(self, teacher_client):
        """测试空题目数组"""
        response = await teacher_client.post(
            "/api/v1/questions/batch",
            json={
                "questions": []
            }
        )

        assert response.status_code == 400
        assert "questions数组不能为空" in response.json()["detail"]
