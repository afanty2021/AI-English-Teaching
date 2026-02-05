"""
题库API测试 - AI英语教学系统
测试题库管理的API端点
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid
from httpx import AsyncClient

from app.main import app
from app.models import User, UserRole
from app.models.question import QuestionBank


@pytest.fixture
async def client(db):
    """创建测试客户端"""
    from app.main import get_db
    from app.api.deps import get_current_user

    # Override dependencies
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


class TestQuestionBanksAPI:
    """测试题库API"""

    @pytest.mark.asyncio
    async def test_create_question_bank_success(self, client, db):
        """测试成功创建题库"""
        # Mock service response
        from app.services.question_bank_service import get_question_bank_service

        mock_bank = MagicMock()
        mock_bank.id = uuid.uuid4()
        mock_bank.name = "A2 语法练习"
        mock_bank.description = "A2级别的语法题目"
        mock_bank.practice_type = "grammar"
        mock_bank.difficulty_level = "A2"
        mock_bank.tags = ["grammar", "a2"]
        mock_bank.is_public = False
        mock_bank.question_count = 0
        mock_bank.created_by = uuid.uuid4()
        mock_bank.created_at = MagicMock()
        mock_bank.created_at.isoformat = MagicMock(return_value="2024-01-01T00:00:00")

        mock_service = AsyncMock()
        mock_service.create_question_bank = AsyncMock(return_value=mock_bank)

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_question_bank_service] = mock_get_service

        response = await client.post(
            "/api/v1/question-banks/",
            json={
                "name": "A2 语法练习",
                "practice_type": "grammar",
                "description": "A2级别的语法题目",
                "difficulty_level": "A2",
                "tags": ["grammar", "a2"],
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "A2 语法练习"
        assert data["practice_type"] == "grammar"
        assert "message" in data

        app.dependency_overrides.pop(get_question_bank_service, None)

    @pytest.mark.asyncio
    async def test_create_question_bank_student_forbidden(self, student_client):
        """测试学生不能创建题库"""
        response = await student_client.post(
            "/api/v1/question-banks/",
            json={
                "name": "测试题库",
                "practice_type": "reading",
            }
        )

        assert response.status_code == 403
        assert "只有教师可以创建题库" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_question_bank_missing_fields(self, client):
        """测试缺少必填字段"""
        response = await client.post(
            "/api/v1/question-banks/",
            json={
                "description": "没有名称和类型",
            }
        )

        assert response.status_code == 400
        assert "缺少必填字段" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_question_bank_invalid_type(self, client):
        """测试无效的练习类型"""
        response = await client.post(
            "/api/v1/question-banks/",
            json={
                "name": "测试题库",
                "practice_type": "invalid_type",
            }
        )

        assert response.status_code == 400
        assert "无效的练习类型" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_question_banks(self, client, db):
        """测试获取题库列表"""
        from app.services.question_bank_service import get_question_bank_service

        # Mock service response
        mock_banks = []
        for i in range(3):
            bank = MagicMock()
            bank.id = uuid.uuid4()
            bank.name = f"题库 {i+1}"
            bank.description = f"描述 {i+1}"
            bank.practice_type = "grammar"
            bank.difficulty_level = "A2"
            bank.tags = []
            bank.is_public = True
            bank.question_count = i * 10
            bank.created_by = uuid.uuid4()
            bank.created_at = MagicMock()
            bank.created_at.isoformat = MagicMock(return_value="2024-01-01T00:00:00")
            mock_banks.append(bank)

        mock_service = AsyncMock()
        mock_service.list_question_banks = AsyncMock(return_value=(mock_banks, 3))

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_question_bank_service] = mock_get_service

        response = await client.get("/api/v1/question-banks/")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert len(data["items"]) == 3

        app.dependency_overrides.pop(get_question_bank_service, None)

    @pytest.mark.asyncio
    async def test_list_question_banks_with_filters(self, client, db):
        """测试带筛选条件的题库列表"""
        from app.services.question_bank_service import get_question_bank_service

        mock_service = AsyncMock()
        mock_service.list_question_banks = AsyncMock(return_value=([], 0))

        async def mock_get_service(db):
            return mock_service

        app.dependency_overrides[get_question_bank_service] = mock_get_service

        response = await client.get(
            "/api/v1/question-banks/",
            params={
                "practice_type": "grammar",
                "difficulty_level": "A2",
                "is_public": True,
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

        app.dependency_overrides.pop(get_question_bank_service, None)
