"""
AI 服务门面（Facade）- AI英语教学系统

提供统一的AI服务入口，整合向量嵌入、对话和分析服务。
支持智谱AI（主要）和OpenAI（备用）。
"""
from typing import Any, Dict, List, Optional, TypeVar, Type

from pydantic import BaseModel

from app.core.config import settings
from app.services.ai.embedding_service import EmbeddingService, get_embedding_service
from app.services.ai.chat_service import ChatService, get_chat_service
from app.services.ai.analysis_service import AnalysisService, get_analysis_service


T = TypeVar('T', bound=BaseModel)


class AIService:
    """
    AI服务门面

    整合所有AI服务能力，提供统一的接口。
    这是应用层代码应该使用的服务类。
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        chat_service: Optional[ChatService] = None,
        analysis_service: Optional[AnalysisService] = None,
    ):
        """
        初始化AI服务

        Args:
            embedding_service: 向量嵌入服务实例
            chat_service: 对话服务实例
            analysis_service: 分析服务实例
        """
        self._embedding_service = embedding_service or get_embedding_service()
        self._chat_service = chat_service or get_chat_service()
        self._analysis_service = analysis_service or get_analysis_service()

    @property
    def embedding(self) -> EmbeddingService:
        """获取向量嵌入服务"""
        return self._embedding_service

    @property
    def chat(self) -> ChatService:
        """获取对话服务"""
        return self._chat_service

    @property
    def analysis(self) -> AnalysisService:
        """获取分析服务"""
        return self._analysis_service

    # ===== 向量嵌入方法 =====

    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> List[float]:
        """
        生成文本向量嵌入

        Args:
            text: 要生成向量的文本
            model: 使用的模型（可选）
            provider: AI服务提供商（可选）

        Returns:
            List[float]: 向量嵌入
        """
        return await self._embedding_service.generate_embedding(
            text=text,
            model=model,
            provider=provider
        )

    async def batch_generate_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> List[List[float]]:
        """
        批量生成向量嵌入

        Args:
            texts: 文本列表
            model: 使用的模型（可选）
            provider: AI服务提供商（可选）

        Returns:
            List[List[float]]: 向量嵌入列表
        """
        return await self._embedding_service.batch_generate_embeddings(
            texts=texts,
            model=model,
            provider=provider
        )

    # ===== 对话方法 =====

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None,
        provider: Optional[str] = None,
    ) -> str:
        """
        聊天完成（普通文本输出）

        Args:
            messages: 对话消息列表
            temperature: 温度参数（可选）
            max_tokens: 最大token数（可选）
            model: 使用的模型（可选）
            response_format: 响应格式（可选）
            provider: AI服务提供商（可选）

        Returns:
            str: AI生成的文本响应
        """
        return await self._chat_service.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            response_format=response_format,
            provider=provider
        )

    async def chat_completion_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[T],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> T:
        """
        聊天完成（结构化输出）

        Args:
            messages: 对话消息列表
            response_model: 响应的 Pydantic 模型类型
            temperature: 温度参数（可选）
            max_tokens: 最大token数（可选）
            model: 使用的模型（可选）

        Returns:
            T: 解析后的结构化数据对象
        """
        return await self._chat_service.chat_completion_structured(
            messages=messages,
            response_model=response_model,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model
        )

    # ===== 分析方法 =====

    async def analyze_student_assessment(
        self,
        student_info: Dict[str, Any],
        practice_data: List[Dict[str, Any]],
        target_exam: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        AI分析学生评估数据

        Args:
            student_info: 学生信息字典
            practice_data: 练习数据列表
            target_exam: 目标考试类型（可选）
            provider: AI服务提供商（可选）

        Returns:
            Dict[str, Any]: AI分析结果
        """
        return await self._analysis_service.analyze_student_assessment(
            student_info=student_info,
            practice_data=practice_data,
            target_exam=target_exam,
            provider=provider
        )

    # ===== 健康检查 =====

    async def health_check(self) -> Dict[str, bool]:
        """
        健康检查

        Returns:
            Dict[str, bool]: 各AI服务的健康状态
        """
        embedding_health = await self._embedding_service.health_check()
        chat_health = await self._chat_service.health_check()
        analysis_health = await self._analysis_service.health_check()

        return {
            "embedding": embedding_health,
            "chat": chat_health,
            "analysis": analysis_health,
        }


# 创建全局单例
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """
    获取AI服务单例

    Returns:
        AIService: AI服务实例
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


# 向后兼容：保持原有的导入路径
# 旧代码可以直接导入 AIService 和 get_ai_service 使用
__all__ = ["AIService", "get_ai_service"]
