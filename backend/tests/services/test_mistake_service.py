"""
错题本服务测试

测试 MistakeService 的核心业务逻辑：
- 创建错题记录
- 从练习中收集错题
- 错题状态管理
- 错题统计
- 复习计划生成
"""
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models import Mistake, MistakeStatus, MistakeType
from app.services.mistake_service import MistakeService, get_mistake_service


class TestMistakeService:
    """错题本服务测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        session = AsyncMock()
        # 模拟 execute 返回结果
        session.execute.return_value = MagicMock(
            scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None))),
            scalar=MagicMock(return_value=None),
        )
        session.commit = MagicMock()
        session.refresh = MagicMock()
        return session

    @pytest.fixture
    def mistake_service(self, db_session):
        """创建错题服务实例"""
        return MistakeService(db_session)

    @pytest.fixture
    def sample_student_id(self):
        """示例学生ID"""
        return uuid.uuid4()

    @pytest.fixture
    def sample_practice_id(self):
        """示例练习ID"""
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_create_mistake_success(self, mistake_service, sample_student_id):
        """测试成功创建错题记录"""
        # 准备测试数据
        question = "What is the past tense of 'go'?"
        wrong_answer = "goed"
        correct_answer = "went"
        mistake_type = MistakeType.GRAMMAR

        # 执行测试
        result = await mistake_service.create_mistake(
            student_id=sample_student_id,
            question=question,
            wrong_answer=wrong_answer,
            correct_answer=correct_answer,
            mistake_type=mistake_type,
            explanation="Go is an irregular verb.",
            knowledge_points=["irregular_verbs", "past_tense"],
            topic="Grammar"
        )

        # 验证结果
        assert result is not None
        assert result.student_id == sample_student_id
        assert result.question == question
        assert result.wrong_answer == wrong_answer
        assert result.correct_answer == correct_answer
        assert result.mistake_type == MistakeType.GRAMMAR.value
        assert result.status == MistakeStatus.PENDING.value
        assert result.knowledge_points == ["irregular_verbs", "past_tense"]

    @pytest.mark.asyncio
    async def test_create_mistake_minimal_fields(self, mistake_service, sample_student_id):
        """测试使用最小必填字段创建错题"""
        result = await mistake_service.create_mistake(
            student_id=sample_student_id,
            question="Test question",
            wrong_answer="Wrong",
            correct_answer="Correct",
            mistake_type=MistakeType.VOCABULARY
        )

        assert result is not None
        assert result.explanation is None
        assert result.knowledge_points == []

    @pytest.mark.asyncio
    async def test_collect_mistakes_from_practice_empty(self, mistake_service, sample_student_id, sample_practice_id):
        """测试从练习中收集错题（无错题场景）"""
        # 模拟练习结果：全部正确
        practice_result = MagicMock()
        practice_result.id = sample_practice_id
        practice_result.student_id = sample_student_id
        practice_result.answers = [
            MagicMock(is_correct=True),
            MagicMock(is_correct=True),
            MagicMock(is_correct=True),
        ]

        # 模拟数据库查询返回空
        mistake_service.db.execute.return_value.scalars.return_value.all.return_value = []

        # 执行测试
        collected = await mistake_service.collect_mistakes_from_practice(practice_result)

        # 验证结果：没有收集到错题
        assert collected == []

    @pytest.mark.asyncio
    async def test_get_mistake_found(self, mistake_service, sample_student_id):
        """测试获取存在的错题"""
        mistake_id = uuid.uuid4()

        # 模拟数据库查询返回错题记录
        mock_mistake = MagicMock()
        mock_mistake.id = mistake_id
        mock_mistake.student_id = sample_student_id
        mock_mistake.status = MistakeStatus.PENDING.value

        mistake_service.db.execute.return_value.scalar.return_value = mock_mistake

        # 执行测试
        result = await mistake_service.get_mistake(mistake_id, sample_student_id)

        # 验证结果
        assert result is not None
        assert result.id == mistake_id

    @pytest.mark.asyncio
    async def test_get_mistake_not_found(self, mistake_service, sample_student_id):
        """测试获取不存在的错题"""
        mistake_id = uuid.uuid4()

        # 模拟数据库查询返回None
        mistake_service.db.execute.return_value.scalar.return_value = None

        # 执行测试
        result = await mistake_service.get_mistake(mistake_id, sample_student_id)

        # 验证结果
        assert result is None

    @pytest.mark.asyncio
    async def test_update_mistake_status_to_reviewing(self, mistake_service, sample_student_id):
        """测试更新错题状态为复习中"""
        mistake_id = uuid.uuid4()

        # 模拟数据库更新成功
        mock_mistake = MagicMock()
        mock_mistake.id = mistake_id
        mock_mistake.status = MistakeStatus.REVIEWING.value
        mistake_service.db.execute.return_value.scalar.return_value = mock_mistake

        # 执行测试
        result = await mistake_service.update_mistake_status(
            mistake_id=mistake_id,
            student_id=sample_student_id,
            new_status=MistakeStatus.REVIEWING
        )

        # 验证结果
        assert result is not None
        assert result.status == MistakeStatus.REVIEWING.value

    @pytest.mark.asyncio
    async def test_record_mistake_retry_success(self, mistake_service, sample_student_id):
        """测试记录错题重试（正确）"""
        mistake_id = uuid.uuid4()

        # 模拟错题记录
        mock_mistake = MagicMock()
        mock_mistake.id = mistake_id
        mock_mistake.mistake_count = 2
        mock_mistake.review_count = 1
        mock_mistake.mastery_level = 0.5
        mistake_service.db.execute.return_value.scalar.return_value = mock_mistake

        # 执行测试：重试正确
        result = await mistake_service.record_mistake_retry(
            mistake_id=mistake_id,
            student_id=sample_student_id,
            is_correct=True
        )

        # 验证结果
        assert result is not None
        assert result.review_count == 2  # 复习次数增加
        assert result.mastery_level > 0.5  # 掌握度提升

    @pytest.mark.asyncio
    async def test_record_mistake_retry_failed(self, mistake_service, sample_student_id):
        """测试记录错题重试（错误）"""
        mistake_id = uuid.uuid4()

        # 模拟错题记录
        mock_mistake = MagicMock()
        mock_mistake.id = mistake_id
        mock_mistake.mistake_count = 3
        mock_mistake.last_mistaken_at = datetime.utcnow()
        mistake_service.db.execute.return_value.scalar.return_value = mock_mistake

        # 执行测试：重试错误
        result = await mistake_service.record_mistake_retry(
            mistake_id=mistake_id,
            student_id=sample_student_id,
            is_correct=False
        )

        # 验证结果
        assert result is not None
        assert result.mistake_count == 4  # 错误次数增加

    @pytest.mark.asyncio
    async def test_get_mistake_statistics(self, mistake_service, sample_student_id):
        """测试获取错题统计数据"""
        # 模拟数据库聚合查询结果
        mock_stats = MagicMock()
        mock_stats.total_mistakes = 50
        mock_stats.pending_count = 20
        mock_stats.reviewing_count = 10
        mock_stats.mastered_count = 15
        mock_stats.ignored_count = 5

        mistake_service.db.execute.return_value.fetchone.return_value = mock_stats

        # 执行测试
        stats = await mistake_service.get_mistake_statistics(sample_student_id)

        # 验证结果
        assert stats is not None
        assert stats.total_mistakes == 50
        assert stats.pending_count == 20
        assert stats.reviewing_count == 10
        assert stats.mastered_count == 15
        assert stats.ignored_count == 5

    @pytest.mark.asyncio
    async def test_get_review_plan(self, mistake_service, sample_student_id):
        """测试获取复习计划"""
        now = datetime.utcnow()

        # 模拟返回待复习的错题列表
        mock_mistakes = [
            MagicMock(
                id=uuid.uuid4(),
                status=MistakeStatus.PENDING.value,
                next_review_at=now - timedelta(hours=1),  # 已过期
                priority_score=100
            ),
            MagicMock(
                id=uuid.uuid4(),
                status=MistakeStatus.PENDING.value,
                next_review_at=now + timedelta(hours=2),  # 未过期
                priority_score=80
            ),
        ]

        mistake_service.db.execute.return_value.scalars.return_value.all.return_value = mock_mistakes

        # 执行测试
        review_plan = await mistake_service.get_review_plan(sample_student_id)

        # 验证结果
        assert review_plan is not None
        assert len(review_plan.mistakes) == 2
        assert review_plan.total_count == 2
        assert review_plan.overdue_count == 1  # 1个已过期

    @pytest.mark.asyncio
    async def test_update_ai_analysis(self, mistake_service, sample_student_id):
        """测试更新AI分析结果"""
        mistake_id = uuid.uuid4()

        # 模拟错题记录
        mock_mistake = MagicMock()
        mock_mistake.id = mistake_id
        mistake_service.db.execute.return_value.scalar.return_value = mock_mistake

        # 准备AI分析数据
        ai_suggestion = "This is a common irregular verb."
        related_topics = ["irregular_verbs", "past_tense"]
        difficulty = "intermediate"

        # 执行测试
        result = await mistake_service.update_ai_analysis(
            mistake_id=mistake_id,
            student_id=sample_student_id,
            ai_suggestion=ai_suggestion,
            related_topics=related_topics,
            difficulty=difficulty
        )

        # 验证结果
        assert result is not None
        assert result.ai_suggestion == ai_suggestion
        assert result.related_topics == related_topics


class TestGetMistakeService:
    """测试 get_mistake_service 工厂函数"""

    def test_get_mistake_service_returns_service(self):
        """测试 get_mistake_service 返回正确的服务实例"""
        mock_db = MagicMock()
        service = get_mistake_service(mock_db)

        assert service is not None
        assert isinstance(service, MistakeService)
        assert service.db == mock_db
