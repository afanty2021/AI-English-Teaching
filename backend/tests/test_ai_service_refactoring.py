"""
AI 服务重构测试 - AI英语教学系统

测试内容：
- EmbeddingService 向量嵌入服务
- ChatService 对话服务
- AnalysisService 分析服务
- AIService Facade 门面模式
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from app.services.ai.embedding_service import EmbeddingService, get_embedding_service
from app.services.ai.chat_service import ChatService, get_chat_service
from app.services.ai.analysis_service import AnalysisService, get_analysis_service
from app.services.ai_service import AIService, get_ai_service


class TestEmbeddingService:
    """向量嵌入服务测试"""

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self):
        """测试空文本校验"""
        service = EmbeddingService()
        with pytest.raises(ValueError, match="文本不能为空"):
            await service.generate_embedding("")

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings_empty_list(self):
        """测试空列表返回"""
        service = EmbeddingService()
        result = await service.batch_generate_embeddings([])
        assert result == []

    def test_embedding_service_singleton(self):
        """测试单例获取"""
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        assert service1 is service2


class TestChatService:
    """对话服务测试"""

    @pytest.mark.asyncio
    async def test_chat_completion_empty_messages(self):
        """测试空消息列表校验"""
        service = ChatService()
        with pytest.raises(ValueError, match="消息列表不能为空"):
            await service.chat_completion([])

    @pytest.mark.asyncio
    async def test_chat_completion_structured(self):
        """测试结构化输出"""
        from pydantic import BaseModel

        class MockResponse(BaseModel):
            name: str
            age: int

        # Mock OpenAI 客户端
        with patch.object(ChatService, '_get_openai_client') as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content='{"name": "test", "age": 25}'))]
                )
            )

            service = ChatService(provider="openai")
            result = await service.chat_completion_structured(
                messages=[{"role": "user", "content": "test"}],
                response_model=MockResponse
            )

            assert isinstance(result, MockResponse)
            assert result.name == "test"
            assert result.age == 25

    def test_chat_service_singleton(self):
        """测试单例获取"""
        service1 = get_chat_service()
        service2 = get_chat_service()
        assert service1 is service2


class TestAnalysisService:
    """分析服务测试"""

    @pytest.fixture
    def mock_chat_service(self):
        """模拟对话服务"""
        service = MagicMock(spec=ChatService)
        service.chat_completion = AsyncMock(return_value='{"cefr_level": "B2"}')
        return service

    @pytest.mark.asyncio
    async def test_analyze_student_assessment_empty_student_info(self):
        """测试空学生信息校验"""
        service = AnalysisService()
        with pytest.raises(ValueError, match="学生信息不能为空"):
            await service.analyze_student_assessment(
                student_info={},
                practice_data=[]
            )

    @pytest.mark.asyncio
    async def test_analyze_student_assessment(self, mock_chat_service):
        """测试学生评估分析"""
        service = AnalysisService(chat_service=mock_chat_service)

        student_info = {
            "id": "test-id",
            "name": "Test Student",
            "target_exam": "IELTS"
        }
        practice_data = [
            {
                "topic": "grammar",
                "score": 80,
                "correct_rate": 0.8,
                "difficulty": "medium"
            }
        ]

        result = await service.analyze_student_assessment(
            student_info=student_info,
            practice_data=practice_data
        )

        assert "analysis" in result
        assert "analyzed_at" in result
        assert "analysis_version" in result

    def test_analysis_service_singleton(self):
        """测试单例获取"""
        service1 = get_analysis_service()
        service2 = get_analysis_service()
        assert service1 is service2


class TestAIServiceFacade:
    """AI服务门面测试"""

    @pytest.fixture
    def mock_embedding_service(self):
        """模拟向量嵌入服务"""
        service = MagicMock(spec=EmbeddingService)
        service.generate_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        service.batch_generate_embeddings = AsyncMock(return_value=[[0.1], [0.2]])
        service.health_check = AsyncMock(return_value={"zhipuai": True})
        return service

    @pytest.fixture
    def mock_chat_service(self):
        """模拟对话服务"""
        service = MagicMock(spec=ChatService)
        service.chat_completion = AsyncMock(return_value="Hello!")
        service.health_check = AsyncMock(return_value={"zhipuai": True})
        return service

    @pytest.fixture
    def mock_analysis_service(self):
        """模拟分析服务"""
        service = MagicMock(spec=AnalysisService)
        service.analyze_student_assessment = AsyncMock(return_value={"analysis": {}})
        service.health_check = AsyncMock(return_value={"zhipuai": True})
        return service

    @pytest.mark.asyncio
    async def test_ai_service_delegates_to_embedding(
        self,
        mock_embedding_service
    ):
        """测试门面委托向量嵌入"""
        ai_service = AIService(
            embedding_service=mock_embedding_service,
            chat_service=self.mock_chat_service,
            analysis_service=self.mock_analysis_service
        )

        result = await ai_service.generate_embedding("test text")
        assert result == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_ai_service_delegates_to_chat(
        self,
        mock_chat_service
    ):
        """测试门面委托对话"""
        mock_analysis = MagicMock(spec=AnalysisService)
        ai_service = AIService(
            embedding_service=MagicMock(spec=EmbeddingService),
            chat_service=mock_chat_service,
            analysis_service=mock_analysis
        )

        result = await ai_service.chat_completion(
            messages=[{"role": "user", "content": "hello"}]
        )
        assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_ai_service_delegates_to_analysis(
        self,
        mock_analysis_service
    ):
        """测试门面委托分析"""
        ai_service = AIService(
            embedding_service=MagicMock(spec=EmbeddingService),
            chat_service=MagicMock(spec=ChatService),
            analysis_service=mock_analysis_service
        )

        result = await ai_service.analyze_student_assessment(
            student_info={"id": "test"},
            practice_data=[]
        )
        assert "analysis" in result

    def test_ai_service_properties(self):
        """测试门面属性访问"""
        ai_service = AIService()

        # 测试属性存在
        assert hasattr(ai_service, 'embedding')
        assert hasattr(ai_service, 'chat')
        assert hasattr(ai_service, 'analysis')

        # 测试属性类型
        assert isinstance(ai_service.embedding, EmbeddingService)
        assert isinstance(ai_service.chat, ChatService)
        assert isinstance(ai_service.analysis, AnalysisService)

    def test_ai_service_singleton(self):
        """测试单例获取"""
        service1 = get_ai_service()
        service2 = get_ai_service()
        assert service1 is service2


class TestAIServiceBackwardCompatibility:
    """向后兼容测试"""

    def test_import_path_compatibility(self):
        """测试导入路径兼容性"""
        # 旧代码导入方式应该仍然有效
        from app.services.ai_service import AIService, get_ai_service

        assert AIService is not None
        assert get_ai_service is not None

    def test_old_interface_still_works(self):
        """测试旧接口仍然工作"""
        # 旧代码使用的接口
        ai_service = AIService()

        # 检查主要方法仍然存在
        assert hasattr(ai_service, 'generate_embedding')
        assert hasattr(ai_service, 'batch_generate_embeddings')
        assert hasattr(ai_service, 'chat_completion')
        assert hasattr(ai_service, 'analyze_student_assessment')
        assert hasattr(ai_service, 'health_check')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
