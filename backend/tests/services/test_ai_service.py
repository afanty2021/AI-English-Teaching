"""
AI 服务测试 - AI英语教学系统
测试 AIService 类的各项功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai_service import AIService, get_ai_service


class TestAIService:
    """AI服务测试类"""

    @pytest.fixture
    def ai_service(self):
        """创建AI服务实例"""
        return AIService()

    @pytest.fixture
    def mock_openai_client(self):
        """模拟OpenAI客户端"""
        with patch("app.services.ai_service.AsyncOpenAI") as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, ai_service, mock_openai_client):
        """测试成功生成向量嵌入"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        # 调用方法
        result = await ai_service.generate_embedding("test text")

        # 验证结果
        assert result == [0.1, 0.2, 0.3]
        mock_openai_client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, ai_service):
        """测试空文本抛出异常"""
        with pytest.raises(ValueError, match="文本不能为空"):
            await ai_service.generate_embedding("")

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings(self, ai_service, mock_openai_client):
        """测试批量生成向量嵌入"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2, 0.3]),
            MagicMock(embedding=[0.4, 0.5, 0.6]),
        ]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        # 调用方法
        result = await ai_service.batch_generate_embeddings(["text1", "text2"])

        # 验证结果
        assert len(result) == 2
        assert result[0] == [0.1, 0.2, 0.3]
        assert result[1] == [0.4, 0.5, 0.6]

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, ai_service, mock_openai_client):
        """测试聊天完成成功"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "AI response"
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # 调用方法
        messages = [{"role": "user", "content": "Hello"}]
        result = await ai_service.chat_completion(messages)

        # 验证结果
        assert result == "AI response"
        mock_openai_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_completion_with_json_format(self, ai_service, mock_openai_client):
        """测试使用JSON格式的聊天完成"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"key": "value"}'
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # 调用方法
        messages = [{"role": "user", "content": "Hello"}]
        result = await ai_service.chat_completion(
            messages=messages,
            response_format={"type": "json_object"}
        )

        # 验证结果
        assert result == '{"key": "value"}'

        # 验证调用了正确的参数
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args[1]["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_analyze_student_assessment(self, ai_service, mock_openai_client):
        """测试分析学生评估"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '''
        {
            "cefr_level": "B1",
            "abilities": {
                "listening": 75,
                "reading": 80,
                "speaking": 65,
                "writing": 70,
                "grammar": 72,
                "vocabulary": 68
            },
            "weak_points": [
                {"topic": "语法", "reason": "复杂句型掌握不足"}
            ],
            "strong_points": ["阅读理解"],
            "recommendations": [
                {"priority": "high", "suggestion": "加强语法练习"}
            ],
            "exam_readiness": {
                "ready": false,
                "gap": "需要提升综合能力"
            },
            "analysis_summary": "整体水平良好，需要针对性提升薄弱项"
        }
        '''
        mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # 准备测试数据
        student_info = {
            "id": "123",
            "name": "张三",
            "target_exam": "CET4",
            "target_score": 500,
        }
        practice_data = [
            {
                "content_id": "1",
                "topic": "阅读",
                "difficulty": "intermediate",
                "score": 80,
                "correct_rate": 0.85,
                "time_spent": 300,
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        # 调用方法
        result = await ai_service.analyze_student_assessment(
            student_info=student_info,
            practice_data=practice_data,
        )

        # 验证结果
        assert result["cefr_level"] == "B1"
        assert result["abilities"]["listening"] == 75
        assert len(result["weak_points"]) == 1
        assert result["weak_points"][0]["topic"] == "语法"
        assert len(result["recommendations"]) == 1
        assert result["recommendations"][0]["priority"] == "high"
        assert result["exam_readiness"]["ready"] is False
        assert "analyzed_at" in result
        assert result["analysis_version"] == "1.0"

    @pytest.mark.asyncio
    async def test_analyze_student_assessment_invalid_data(self, ai_service):
        """测试无效数据抛出异常"""
        with pytest.raises(ValueError, match="学生信息不能为空"):
            await ai_service.analyze_student_assessment(
                student_info={},
                practice_data=[],
            )

    def test_build_analysis_prompt(self, ai_service):
        """测试构建分析提示词"""
        student_info = {
            "id": "123",
            "name": "张三",
            "target_exam": "CET4",
            "target_score": 500,
            "current_cefr_level": "A2",
        }
        practice_data = [
            {
                "content_id": "1",
                "topic": "阅读",
                "difficulty": "intermediate",
                "score": 80,
                "correct_rate": 0.85,
                "time_spent": 300,
                "created_at": "2024-01-01T00:00:00",
            }
        ]

        prompt = ai_service._build_analysis_prompt(
            student_info=student_info,
            practice_data=practice_data,
            target_exam="CET4",
        )

        # 验证提示词包含关键信息
        assert "张三" in prompt
        assert "CET4" in prompt
        assert "阅读" in prompt
        assert "cefr_level" in prompt
        assert "abilities" in prompt

    @pytest.mark.asyncio
    async def test_health_check_success(self, ai_service, mock_openai_client):
        """测试健康检查成功"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        # 调用方法
        result = await ai_service.health_check()

        # 验证结果
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, ai_service, mock_openai_client):
        """测试健康检查失败"""
        # 模拟API失败
        mock_openai_client.embeddings.create = AsyncMock(side_effect=Exception("API error"))

        # 调用方法
        result = await ai_service.health_check()

        # 验证结果
        assert result is False


class TestGetAIService:
    """测试AI服务单例"""

    def test_get_ai_service_singleton(self):
        """测试获取单例"""
        service1 = get_ai_service()
        service2 = get_ai_service()

        # 验证返回同一个实例
        assert service1 is service2
