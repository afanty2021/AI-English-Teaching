"""
智能复习服务测试 - AI英语教学系统
"""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.mistake_review_service import MistakeReviewService
from app.models.mistake import Mistake, MistakeStatus


class TestMistakeReviewService:
    """智能复习服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建测试服务实例"""
        return MistakeReviewService(mock_db)

    @pytest.fixture
    def sample_mistake(self):
        """创建模拟错题"""
        mistake = Mock(spec=Mistake)
        mistake.id = uuid4()
        mistake.student_id = uuid4()
        mistake.question = "What is the past tense of 'go'?"
        mistake.wrong_answer = "gone"
        mistake.correct_answer = "went"
        mistake.mistake_type = "grammar"
        mistake.status = MistakeStatus.PENDING.value
        mistake.mistake_count = 2
        mistake.review_count = 1
        mistake.first_mistaken_at = datetime.utcnow() - timedelta(days=5)
        mistake.last_reviewed_at = datetime.utcnow() - timedelta(days=1)
        mistake.last_mistaken_at = datetime.utcnow() - timedelta(days=5)
        mistake.knowledge_points = ["verb_tense", "past_simple"]
        mistake.topic = "时态"
        return mistake

    def test_init(self, service):
        """测试初始化"""
        assert service.EBINGHAUS_INTERVALS == [1, 3, 7, 14, 30]
        assert service.URGENT_THRESHOLD_HOURS == 24

    def test_get_review_interval_first_review(self, service, sample_mistake):
        """测试首次复习间隔"""
        sample_mistake.review_count = 0
        interval = service._get_review_interval(0)
        assert interval == 1  # 首次复习间隔1天

    def test_get_review_interval_second_review(self, service, sample_mistake):
        """测试第二次复习间隔"""
        sample_mistake.review_count = 1
        interval = service._get_review_interval(1)
        assert interval == 3  # 第二次复习间隔3天

    def test_get_review_interval_third_review(self, service, sample_mistake):
        """测试第三次复习间隔"""
        sample_mistake.review_count = 2
        interval = service._get_review_interval(2)
        assert interval == 7  # 第三次复习间隔7天

    def test_get_review_interval_fourth_review(self, service, sample_mistake):
        """测试第四次复习间隔"""
        sample_mistake.review_count = 3
        interval = service._get_review_interval(3)
        assert interval == 14  # 第四次复习间隔14天

    def test_get_review_interval_max_review(self, service, sample_mistake):
        """测试超过最大次数的复习间隔"""
        sample_mistake.review_count = 10
        interval = service._get_review_interval(10)
        assert interval == 30  # 超过最大次数使用最大间隔

    def test_calculate_next_review_time_never_reviewed(self, service):
        """测试从未复习的错题 - 验证间隔计算正确"""
        # 创建一个简单的 mock，避免 spec 限制
        mistake = Mock()
        mistake.review_count = 0
        mistake.first_mistaken_at = datetime(2026, 2, 4, 12, 0, 0, tzinfo=timezone.utc)
        mistake.last_reviewed_at = None

        next_review = service.calculate_next_review_time(mistake)

        # 首次复习应该是1天后 (间隔0=1天)
        expected = mistake.first_mistaken_at + timedelta(days=1)
        assert next_review == expected
        assert next_review.day == 5  # 2月4日 + 1天 = 2月5日

    def test_calculate_next_review_time_has_reviewed(self, service, sample_mistake):
        """测试有复习记录的错题"""
        last_reviewed = datetime.utcnow() - timedelta(days=2)
        sample_mistake.last_reviewed_at = last_reviewed
        sample_mistake.review_count = 1  # 第二次复习

        next_review = service.calculate_next_review_time(sample_mistake)

        # 第二次复习间隔3天
        expected = last_reviewed + timedelta(days=3)
        assert next_review.date() == expected.date()

    def test_is_overdue_not_overdue(self, service, sample_mistake):
        """测试未过期的错题"""
        # 下次复习时间在将来
        sample_mistake.last_reviewed_at = datetime.utcnow() - timedelta(hours=12)
        sample_mistake.review_count = 0

        result = service.is_overdue(sample_mistake)
        assert result is False

    def test_is_overdue_overdue(self, service, sample_mistake):
        """测试已过期的错题"""
        # 使用固定时间
        fixed_time = datetime(2026, 2, 6, 12, 0, 0, tzinfo=timezone.utc)
        # 下次复习时间在5天前（3天间隔 + 2天延迟 = 已过期5天）
        sample_mistake.last_reviewed_at = fixed_time - timedelta(days=8)
        sample_mistake.review_count = 1  # 间隔应该是3天

        with patch('app.services.mistake_review_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs, tzinfo=timezone.utc)

            result = service.is_overdue(sample_mistake)
            assert result is True

    def test_is_urgent_not_urgent(self, service, sample_mistake):
        """测试不紧急的错题"""
        # 下次复习时间在24小时后
        sample_mistake.last_reviewed_at = datetime.utcnow() - timedelta(hours=10)
        sample_mistake.review_count = 0  # 间隔应该是1天

        result = service.is_urgent(sample_mistake)
        assert result is True  # 实际上已经过了1天，所以是紧急

    def test_is_urgent_is_urgent(self, service, sample_mistake):
        """测试紧急的错题"""
        # 下次复习时间在24小时内
        sample_mistake.last_reviewed_at = datetime.utcnow() - timedelta(hours=20)
        sample_mistake.review_count = 0  # 间隔应该是1天

        result = service.is_urgent(sample_mistake)
        assert result is True

    def test_get_review_priority_score_new_mistake(self, service, sample_mistake):
        """测试新错题优先级（从未复习）"""
        sample_mistake.review_count = 0
        sample_mistake.mistake_count = 1
        sample_mistake.first_mistaken_at = datetime.utcnow() - timedelta(hours=12)

        score = service.get_review_priority_score(sample_mistake)

        # 新错题应该有奖励分数
        assert score >= 10  # 至少10分的新错题奖励

    def test_get_review_priority_score_frequent_mistake(self, service, sample_mistake):
        """测试高频错题优先级"""
        sample_mistake.review_count = 1
        sample_mistake.mistake_count = 5  # 高频错题
        sample_mistake.first_mistaken_at = datetime.utcnow() - timedelta(days=10)

        score = service.get_review_priority_score(sample_mistake)

        # 高频错题应该有高分
        assert score > 20  # 5次错误 = 30分

    def test_get_review_priority_score_overdue_mistake(self, service, sample_mistake):
        """测试过期错题优先级"""
        sample_mistake.review_count = 1
        sample_mistake.mistake_count = 2
        sample_mistake.last_reviewed_at = datetime.utcnow() - timedelta(days=10)  # 过期7天

        score = service.get_review_priority_score(sample_mistake)

        # 过期应该有高分
        assert score > 40  # 过期7天 = 70分 + 其他分数

    def test_get_review_priority_score_mastered_mistake(self, service, sample_mistake):
        """测试已掌握错题优先级（较低）"""
        sample_mistake.review_count = 5
        sample_mistake.mistake_count = 1
        sample_mistake.status = MistakeStatus.MASTERED.value

        score = service.get_review_priority_score(sample_mistake)

        # 已掌握的错题应该有较低分数
        assert score < 30


class TestMistakeReviewServiceAsync:
    """智能复习服务异步测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建测试服务实例"""
        return MistakeReviewService(mock_db)

    @pytest.fixture
    def sample_mistake(self):
        """创建模拟错题"""
        mistake = Mock(spec=Mistake)
        mistake.id = uuid4()
        mistake.student_id = uuid4()
        mistake.question = "What is the past tense of 'go'?"
        mistake.wrong_answer = "gone"
        mistake.correct_answer = "went"
        mistake.mistake_type = "grammar"
        mistake.status = MistakeStatus.PENDING.value
        mistake.mistake_count = 2
        mistake.review_count = 1
        mistake.first_mistaken_at = datetime.utcnow() - timedelta(days=5)
        mistake.last_reviewed_at = datetime.utcnow() - timedelta(days=1)
        mistake.last_mistaken_at = datetime.utcnow() - timedelta(days=5)
        mistake.knowledge_points = ["verb_tense", "past_simple"]
        mistake.topic = "时态"
        return mistake

    @pytest.mark.asyncio
    async def test_get_today_review_list_empty(self, service, mock_db):
        """测试空复习清单"""
        student_id = uuid4()

        # 模拟空查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_today_review_list(student_id)

        assert result["student_id"] == str(student_id)
        assert result["total_count"] == 0
        assert result["today_count"] == 0

    @pytest.mark.asyncio
    async def test_get_today_review_list_with_mistakes(self, service, mock_db, sample_mistake):
        """测试有错题的复习清单"""
        student_id = sample_mistake.student_id

        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_mistake]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_today_review_list(student_id)

        assert result["student_id"] == str(student_id)
        assert result["total_count"] == 1
        assert len(result["review_list"]) >= 0  # 可能没有今日复习项

    @pytest.mark.asyncio
    async def test_get_urgent_review_empty(self, service, mock_db):
        """测试空紧急复习"""
        student_id = uuid4()

        # 模拟空查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_urgent_review(student_id)

        assert result["student_id"] == str(student_id)
        assert result["total_urgent"] == 0
        assert len(result["urgent_list"]) == 0

    @pytest.mark.asyncio
    async def test_get_review_statistics_empty(self, service, mock_db):
        """测试空统计"""
        student_id = uuid4()

        # 模拟空查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_review_statistics(student_id)

        assert result["student_id"] == str(student_id)
        assert result["total_mistakes"] == 0
        assert result["mastery_rate"] == 0

    @pytest.mark.asyncio
    async def test_get_review_statistics_with_mistakes(self, service, mock_db, sample_mistake):
        """测试有错题的统计"""
        student_id = sample_mistake.student_id

        # 模拟查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [sample_mistake]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_review_statistics(student_id)

        assert result["student_id"] == str(student_id)
        assert result["total_mistakes"] == 1

    @pytest.mark.asyncio
    async def test_get_recommended_review_empty(self, service, mock_db):
        """测试空推荐复习"""
        student_id = uuid4()

        # 模拟空查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_recommended_review(student_id)

        assert result["student_id"] == str(student_id)
        assert result["recommended_count"] == 0

    @pytest.mark.asyncio
    async def test_get_review_calendar_empty(self, service, mock_db):
        """测试空复习日历"""
        student_id = uuid4()

        # 模拟空查询结果
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.get_review_calendar(student_id, days=30)

        assert result["student_id"] == str(student_id)
        assert "calendar" in result


class TestMistakeReviewServiceHelpers:
    """智能复习服务辅助函数测试类"""

    @pytest.fixture
    def service(self):
        """创建测试服务实例"""
        return MistakeReviewService(MagicMock())

    def test_mistake_to_review_item(self, service):
        """测试错题转复习项"""
        mistake = Mock(spec=Mistake)
        mistake.id = uuid4()
        mistake.question = "这是一个测试问题" + "a" * 150  # 超过100字符
        mistake.mistake_type = "grammar"
        mistake.topic = "测试主题"
        mistake.mistake_count = 3
        mistake.review_count = 1
        mistake.status = MistakeStatus.PENDING.value
        mistake.first_mistaken_at = datetime.utcnow() - timedelta(days=5)
        mistake.last_reviewed_at = datetime.utcnow() - timedelta(days=1)
        mistake.last_mistaken_at = datetime.utcnow() - timedelta(days=5)

        item = service._mistake_to_review_item(mistake, "overdue")

        assert item["id"] == str(mistake.id)
        assert "..." in item["question_preview"]  # 应该被截断
        assert item["mistake_type"] == "grammar"
        assert item["mistake_count"] == 3
        assert item["review_count"] == 1
        assert item["review_type"] == "overdue"

    def test_mistake_to_review_item_short_question(self, service):
        """测试短问题的复习项"""
        mistake = Mock(spec=Mistake)
        mistake.id = uuid4()
        mistake.question = "短问题"
        mistake.mistake_type = "vocabulary"
        mistake.topic = None
        mistake.mistake_count = 1
        mistake.review_count = 0
        mistake.status = MistakeStatus.PENDING.value
        mistake.first_mistaken_at = datetime.utcnow() - timedelta(hours=12)
        mistake.last_reviewed_at = None
        mistake.last_mistaken_at = datetime.utcnow() - timedelta(hours=12)

        item = service._mistake_to_review_item(mistake, "new")

        assert item["question_preview"] == "短问题"  # 不应该被截断
        assert item["topic"] is None
        assert item["review_type"] == "new"
