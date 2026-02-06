"""
练习服务测试

测试 PracticeService 的核心业务逻辑：
- 创建练习会话
- 提交练习答案
- 计算练习成绩
- 生成练习报告
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.practice_service import PracticeService, get_practice_service


class TestPracticeService:
    """练习服务测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))),
            scalar=MagicMock(return_value=None),
        )
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.rollback = MagicMock()
        return session

    @pytest.fixture
    def practice_service(self, db_session):
        """创建练习服务实例"""
        return PracticeService(db_session)

    @pytest.fixture
    def sample_student_id(self):
        """示例学生ID"""
        return uuid.uuid4()

    @pytest.fixture
    def sample_content_id(self):
        """示例内容ID"""
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_create_practice_success(self, practice_service, sample_student_id, sample_content_id):
        """测试成功创建练习会话"""
        # 准备测试数据
        question_count = 10
        difficulty_level = "intermediate"
        topics = ["grammar", "vocabulary"]

        # 模拟内容查询
        mock_content = MagicMock()
        mock_content.id = sample_content_id
        practice_service.db.execute.return_value.scalars.return_value.first.return_value = mock_content

        # 执行测试
        result = await practice_service.create_practice(
            student_id=sample_student_id,
            content_id=sample_content_id,
            question_count=question_count,
            difficulty_level=difficulty_level,
            topics=topics
        )

        # 验证结果
        assert result is not None
        assert result.student_id == sample_student_id

    @pytest.mark.asyncio
    async def test_submit_answer_correct(self, practice_service, sample_student_id):
        """测试提交正确答案"""
        practice_id = uuid.uuid4()
        question_id = uuid.uuid4()

        # 模拟数据库查询返回练习和问题
        mock_practice = MagicMock()
        mock_practice.id = practice_id
        mock_practice.student_id = sample_student_id
        mock_practice.status = "in_progress"

        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.correct_answer = "Paris"
        mock_question.question_type = "multiple_choice"

        practice_service.db.execute.return_value.scalar.return_value = mock_practice

        # 执行测试：提交正确答案
        result = await practice_service.submit_answer(
            practice_id=practice_id,
            question_id=question_id,
            student_id=sample_student_id,
            answer="Paris",
            time_spent_seconds=30
        )

        # 验证结果
        assert result is not None
        assert result.is_correct is True
        assert result.time_spent_seconds == 30

    @pytest.mark.asyncio
    async def test_submit_answer_incorrect(self, practice_service, sample_student_id):
        """测试提交错误答案"""
        practice_id = uuid.uuid4()
        question_id = uuid.uuid4()

        # 模拟数据库查询
        mock_practice = MagicMock()
        mock_practice.id = practice_id
        mock_practice.student_id = sample_student_id

        mock_question = MagicMock()
        mock_question.id = question_id
        mock_question.correct_answer = "Paris"
        mock_question.question_type = "multiple_choice"

        practice_service.db.execute.return_value.scalar.return_value = mock_practice

        # 执行测试：提交错误答案
        result = await practice_service.submit_answer(
            practice_id=practice_id,
            question_id=question_id,
            student_id=sample_student_id,
            answer="London",
            time_spent_seconds=45
        )

        # 验证结果
        assert result is not None
        assert result.is_correct is False
        assert result.time_spent_seconds == 45

    @pytest.mark.asyncio
    async def test_calculate_practice_score(self, practice_service, sample_student_id):
        """测试计算练习成绩"""
        practice_id = uuid.uuid4()

        # 模拟数据库聚合查询
        mock_stats = MagicMock()
        mock_stats.total_questions = 10
        mock_stats.correct_answers = 8
        mock_stats.total_time = 600  # 10分钟

        practice_service.db.execute.return_value.fetchone.return_value = mock_stats

        # 执行测试
        score = await practice_service.calculate_practice_score(
            practice_id=practice_id,
            student_id=sample_student_id
        )

        # 验证结果
        assert score is not None
        assert score.total_questions == 10
        assert score.correct_answers == 8
        assert score.accuracy == 0.8  # 80%
        assert score.score == 80

    @pytest.mark.asyncio
    async def test_complete_practice(self, practice_service, sample_student_id):
        """测试完成练习会话"""
        practice_id = uuid.uuid4()

        # 模拟数据库查询返回练习
        mock_practice = MagicMock()
        mock_practice.id = practice_id
        mock_practice.student_id = sample_student_id
        mock_practice.status = "in_progress"

        practice_service.db.execute.return_value.scalar.return_value = mock_practice

        # 模拟计算成绩
        with patch.object(practice_service, 'calculate_practice_score') as mock_calc:
            mock_score = MagicMock()
            mock_score.score = 85
            mock_score.accuracy = 0.85
            mock_calc.return_value = mock_score

            # 执行测试
            result = await practice_service.complete_practice(
                practice_id=practice_id,
                student_id=sample_student_id
            )

            # 验证结果
            assert result is not None
            assert result.status == "completed"
            assert result.final_score == 85

    @pytest.mark.asyncio
    async def test_get_practice_report(self, practice_service, sample_student_id):
        """测试获取练习报告"""
        practice_id = uuid.uuid4()

        # 模拟数据库查询返回练习
        mock_practice = MagicMock()
        mock_practice.id = practice_id
        mock_practice.student_id = sample_student_id
        mock_practice.final_score = 85
        mock_practice.completed_at = datetime.utcnow()

        practice_service.db.execute.return_value.scalar.return_value = mock_practice

        # 模拟答案详情
        mock_answers = [
            MagicMock(id=uuid.uuid4(), is_correct=True),
            MagicMock(id=uuid.uuid4(), is_correct=False),
            MagicMock(id=uuid.uuid4(), is_correct=True),
        ]

        practice_service.db.execute.return_value.scalars.return_value.all.return_value = mock_answers

        # 执行测试
        report = await practice_service.get_practice_report(
            practice_id=practice_id,
            student_id=sample_student_id
        )

        # 验证结果
        assert report is not None
        assert report.final_score == 85
        assert len(report.answers) == 3
        assert report.correct_count == 2
        assert report.incorrect_count == 1

    @pytest.mark.asyncio
    async def test_get_recommended_content(self, practice_service, sample_student_id):
        """测试获取推荐练习内容"""
        # 模拟数据库查询返回推荐内容
        mock_contents = [
            MagicMock(id=uuid.uuid4(), title="Grammar Basics", difficulty="beginner"),
            MagicMock(id=uuid.uuid4(), title="Vocabulary Builder", difficulty="intermediate"),
        ]

        practice_service.db.execute.return_value.scalars.return_value.all.return_value = mock_contents

        # 执行测试
        recommendations = await practice_service.get_recommended_content(
            student_id=sample_student_id,
            limit=5
        )

        # 验证结果
        assert recommendations is not None
        assert len(recommendations) == 2
        assert recommendations[0].title == "Grammar Basics"

    @pytest.mark.asyncio
    async def test_create_practice_content_not_found(self, practice_service, sample_student_id):
        """测试创建练习时内容不存在"""
        content_id = uuid.uuid4()

        # 模拟数据库查询返回None
        practice_service.db.execute.return_value.scalars.return_value.first.return_value = None

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="内容不存在"):
            await practice_service.create_practice(
                student_id=sample_student_id,
                content_id=content_id,
                question_count=10
            )


class TestGetPracticeService:
    """测试 get_practice_service 工厂函数"""

    def test_get_practice_service_returns_service(self):
        """测试 get_practice_service 返回正确的服务实例"""
        mock_db = MagicMock()
        service = get_practice_service(mock_db)

        assert service is not None
        assert isinstance(service, PracticeService)
        assert service.db == mock_db
