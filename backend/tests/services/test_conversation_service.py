"""
对话服务测试

测试 ConversationService 的核心业务逻辑：
- 创建对话会话
- 发送消息并获取AI回复
- 获取对话历史
- 对话反馈管理
"""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.conversation_service import ConversationService, get_conversation_service


class TestConversationService:
    """对话服务测试类"""

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
    def conversation_service(self, db_session):
        """创建对话服务实例"""
        return ConversationService(db_session)

    @pytest.fixture
    def sample_student_id(self):
        """示例学生ID"""
        return uuid.uuid4()

    @pytest.mark.asyncio
    async def test_create_conversation_success(self, conversation_service, sample_student_id):
        """测试成功创建对话会话"""
        # 准备测试数据
        title = "英语口语练习 - 日常对话"
        scenario = "在餐厅点餐"
        difficulty_level = "intermediate"

        # 模拟数据库保存
        mock_conversation = MagicMock()
        mock_conversation.id = uuid.uuid4()
        mock_conversation.student_id = sample_student_id
        mock_conversation.title = title
        conversation_service.db.add.return_value = mock_conversation

        # 执行测试
        result = await conversation_service.create_conversation(
            student_id=sample_student_id,
            title=title,
            scenario=scenario,
            difficulty_level=difficulty_level
        )

        # 验证结果
        assert result is not None
        assert result.student_id == sample_student_id
        assert result.title == title

    @pytest.mark.asyncio
    async def test_create_conversation_minimal_fields(self, conversation_service, sample_student_id):
        """测试使用最小必填字段创建对话"""
        mock_conversation = MagicMock()
        mock_conversation.id = uuid.uuid4()
        conversation_service.db.add.return_value = mock_conversation

        # 执行测试：只提供必填字段
        result = await conversation_service.create_conversation(
            student_id=sample_student_id,
            title="自由对话练习"
        )

        # 验证结果
        assert result is not None

    @pytest.mark.asyncio
    async def test_send_message_success(self, conversation_service, sample_student_id):
        """测试发送消息并获取AI回复"""
        conversation_id = uuid.uuid4()
        user_message = "Hello, how are you?"

        # 模拟数据库查询返回对话记录
        mock_conversation = MagicMock()
        mock_conversation.id = conversation_id
        mock_conversation.student_id = sample_student_id
        conversation_service.db.execute.return_value.scalar.return_value = mock_conversation

        # 模拟AI服务响应
        ai_response = "I'm doing well, thank you! How can I help you practice English today?"

        with patch('app.services.conversation_service.ai_service.chat_completion') as mock_chat:
            mock_chat.return_value = ai_response

            # 执行测试
            result = await conversation_service.send_message(
                conversation_id=conversation_id,
                student_id=sample_student_id,
                message=user_message
            )

            # 验证结果
            assert result is not None
            assert result.ai_response == ai_response

    @pytest.mark.asyncio
    async def test_send_message_conversation_not_found(self, conversation_service, sample_student_id):
        """测试发送消息到不存在的对话"""
        conversation_id = uuid.uuid4()

        # 模拟数据库查询返回None（对话不存在）
        conversation_service.db.execute.return_value.scalar.return_value = None

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="对话不存在"):
            await conversation_service.send_message(
                conversation_id=conversation_id,
                student_id=sample_student_id,
                message="Hello"
            )

    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, conversation_service, sample_student_id):
        """测试获取对话消息历史"""
        conversation_id = uuid.uuid4()

        # 模拟数据库查询返回消息列表
        mock_messages = [
            MagicMock(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role="user",
                content="Hello"
            ),
            MagicMock(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                role="assistant",
                content="Hi there!"
            ),
        ]

        conversation_service.db.execute.return_value.scalars.return_value.all.return_value = mock_messages

        # 执行测试
        messages = await conversation_service.get_conversation_messages(
            conversation_id=conversation_id,
            student_id=sample_student_id
        )

        # 验证结果
        assert messages is not None
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    @pytest.mark.asyncio
    async def test_submit_conversation_feedback(self, conversation_service, sample_student_id):
        """测试提交对话反馈"""
        conversation_id = uuid.uuid4()
        message_id = uuid.uuid4()
        rating = 5
        feedback = "Very helpful!"

        # 模拟数据库查询返回消息
        mock_message = MagicMock()
        mock_message.id = message_id
        mock_message.conversation_id = conversation_id
        conversation_service.db.execute.return_value.scalar.return_value = mock_message

        # 执行测试
        result = await conversation_service.submit_feedback(
            message_id=message_id,
            student_id=sample_student_id,
            rating=rating,
            feedback_text=feedback
        )

        # 验证结果
        assert result is not None
        assert result.rating == rating
        assert result.feedback_text == feedback

    @pytest.mark.asyncio
    async def test_get_conversation_statistics(self, conversation_service, sample_student_id):
        """测试获取对话统计数据"""
        conversation_id = uuid.uuid4()

        # 模拟数据库聚合查询
        mock_stats = MagicMock()
        mock_stats.total_messages = 20
        mock_stats.user_messages = 10
        mock_stats.assistant_messages = 10
        mock_stats.duration_seconds = 300

        conversation_service.db.execute.return_value.fetchone.return_value = mock_stats

        # 执行测试
        stats = await conversation_service.get_conversation_statistics(
            conversation_id=conversation_id,
            student_id=sample_student_id
        )

        # 验证结果
        assert stats is not None
        assert stats.total_messages == 20
        assert stats.duration_seconds == 300

    @pytest.mark.asyncio
    async def test_end_conversation(self, conversation_service, sample_student_id):
        """测试结束对话会话"""
        conversation_id = uuid.uuid4()

        # 模拟数据库查询返回对话
        mock_conversation = MagicMock()
        mock_conversation.id = conversation_id
        mock_conversation.student_id = sample_student_id
        mock_conversation.status = "active"
        conversation_service.db.execute.return_value.scalar.return_value = mock_conversation

        # 执行测试
        result = await conversation_service.end_conversation(
            conversation_id=conversation_id,
            student_id=sample_student_id
        )

        # 验证结果
        assert result is not None
        assert result.status == "ended"


class TestGetConversationService:
    """测试 get_conversation_service 工厂函数"""

    def test_get_conversation_service_returns_service(self):
        """测试 get_conversation_service 返回正确的服务实例"""
        mock_db = MagicMock()
        service = get_conversation_service(mock_db)

        assert service is not None
        assert isinstance(service, ConversationService)
        assert service.db == mock_db
