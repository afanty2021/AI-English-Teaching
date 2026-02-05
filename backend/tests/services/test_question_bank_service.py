"""
题库服务测试 - AI英语教学系统
测试 QuestionBankService 的各项功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
import uuid

from app.services.question_bank_service import QuestionBankService, get_question_bank_service
from app.models.question import QuestionBank, Question
from app.models import User, UserRole


@pytest.fixture
def db_session():
    """模拟数据库会话"""
    return MagicMock()


@pytest.fixture
def question_bank_service(db_session):
    """创建题库服务实例"""
    return QuestionBankService(db_session)


@pytest.fixture
def teacher_user():
    """创建教师用户"""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.role = UserRole.TEACHER
    return user


@pytest.fixture
def student_user():
    """创建学生用户"""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.role = UserRole.STUDENT
    return user


class TestQuestionBankService:
    """测试题库服务"""

    @pytest.mark.asyncio
    async def test_create_question_bank_success(self, db_session, teacher_user):
        """测试成功创建题库"""
        service = QuestionBankService(db_session)

        # Mock用户查询
        db_session.get = AsyncMock(return_value=teacher_user)

        # Mock commit
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()

        # 创建题库
        bank = await service.create_question_bank(
            name="A2 语法练习",
            practice_type="grammar",
            created_by=teacher_user.id,
            description="A2级别的语法题目",
            difficulty_level="A2",
            tags=["grammar", "a2"],
            is_public=True,
        )

        assert bank.name == "A2 语法练习"
        assert bank.practice_type == "grammar"
        assert bank.question_count == 0

    @pytest.mark.asyncio
    async def test_create_question_bank_student_forbidden(self, db_session, student_user):
        """测试学生不能创建题库"""
        service = QuestionBankService(db_session)

        # Mock用户查询
        db_session.get = AsyncMock(return_value=student_user)

        # 应该抛出异常
        with pytest.raises(ValueError, match="只有教师可以创建题库"):
            await service.create_question_bank(
                name="测试题库",
                practice_type="reading",
                created_by=student_user.id,
            )

    @pytest.mark.asyncio
    async def test_get_question_bank_not_found(self, db_session, question_bank_service):
        """测试获取不存在的题库"""
        fake_id = uuid.uuid4()

        # Mock查询返回None
        db_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None)))

        with pytest.raises(ValueError, match="题库不存在"):
            await question_bank_service.get_question_bank(fake_id)

    @pytest.mark.asyncio
    async def test_list_question_banks_filter_by_type(self, db_session, teacher_user):
        """测试按类型筛选题库"""
        service = QuestionBankService(db_session)

        # Mock查询返回结果
        mock_result = MagicMock()
        mock_result.scalars().all().return_value = []
        mock_result.scalar().return_value = 0
        db_session.execute = AsyncMock(return_value=mock_result)

        banks, total = await service.list_question_banks(
            user_id=teacher_user.id,
            practice_type="grammar",
        )

        assert isinstance(banks, list)
        assert total == 0


class TestGetQuestionBankService:
    """测试服务工厂函数"""

    def test_get_question_bank_service_singleton(self, db_session):
        """测试获取服务实例"""
        service = get_question_bank_service(db_session)

        assert service is not None
        assert isinstance(service, QuestionBankService)
        assert service.db == db_session
