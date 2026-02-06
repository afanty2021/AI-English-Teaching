"""
向量嵌入服务 - AI英语教学系统

提供文本向量嵌入生成功能，支持智谱AI和OpenAI。
"""
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.services.zhipu_service import get_zhipuai_service


class EmbeddingService:
    """
    向量嵌入服务

    负责生成文本的向量表示，用于相似度搜索和内容推荐。
    支持智谱AI（主要）和OpenAI（备用）。
    """

    def __init__(self, provider: Optional[str] = None):
        """
        初始化向量嵌入服务

        Args:
            provider: AI服务提供商 ("zhipuai", "openai", None=使用默认)
        """
        self.provider = provider or settings.AI_PROVIDER
        self._openai_client: Optional[AsyncOpenAI] = None
        self._zhipuai_service = None

        # 从配置获取模型参数
        if self.provider == "zhipuai":
            self.embedding_model = settings.ZHIPUAI_EMBEDDING_MODEL
        else:
            self.embedding_model = settings.OPENAI_EMBEDDING_MODEL

    def _get_openai_client(self) -> AsyncOpenAI:
        """获取OpenAI客户端（懒加载）"""
        if self._openai_client is None:
            if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "your_openai_api_key_here":
                raise ValueError("OpenAI API密钥未配置")
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

    def _get_zhipuai_service(self):
        """获取智谱AI服务"""
        if self._zhipuai_service is None:
            self._zhipuai_service = get_zhipuai_service()
        return self._zhipuai_service

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
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
            List[float]: 向量嵌入（智谱AI: 2048维, OpenAI: 1536维）

        Raises:
            ValueError: 如果文本为空
            ConnectionError: 如果API调用失败
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        ai_provider = provider or self.provider

        # 尝试智谱AI
        if ai_provider == "zhipuai":
            try:
                return await self._get_zhipuai_service().generate_embedding(text)
            except Exception as e:
                if provider == "zhipuai":  # 明确指定使用智谱AI
                    raise
                print(f"智谱AI调用失败，降级到OpenAI: {e}")

        # 尝试OpenAI
        return await self._generate_openai_embedding(text, model)

    async def _generate_openai_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """使用OpenAI生成向量"""
        client = self._get_openai_client()
        embedding_model = model or settings.OPENAI_EMBEDDING_MODEL

        try:
            response = await client.embeddings.create(
                model=embedding_model,
                input=text,
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            raise ConnectionError(f"OpenAI生成向量失败: {str(e)}")

    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
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
        if not texts:
            return []

        ai_provider = provider or self.provider

        # 尝试智谱AI
        if ai_provider == "zhipuai":
            try:
                return await self._get_zhipuai_service().batch_generate_embeddings(texts)
            except Exception as e:
                if provider == "zhipuai":
                    raise
                print(f"智谱AI批量调用失败，降级到OpenAI: {e}")

        # 使用OpenAI批量生成
        return await self._batch_generate_openai_embeddings(texts, model)

    async def _batch_generate_openai_embeddings(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[List[float]]:
        """使用OpenAI批量生成向量"""
        client = self._get_openai_client()
        embedding_model = model or settings.OPENAI_EMBEDDING_MODEL

        try:
            response = await client.embeddings.create(
                model=embedding_model,
                input=texts,
                encoding_format="float"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise ConnectionError(f"批量生成向量失败: {str(e)}")

    async def health_check(self) -> Dict[str, bool]:
        """
        健康检查

        Returns:
            Dict[str, bool]: 各服务的健康状态
        """
        health_status: Dict[str, bool] = {}

        # 检查智谱AI
        if settings.ZHIPUAI_API_KEY:
            try:
                await self._get_zhipuai_service().generate_embedding("test")
                health_status["zhipuai"] = True
            except Exception:
                health_status["zhipuai"] = False

        # 检查OpenAI
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                await self._generate_openai_embedding("test")
                health_status["openai"] = True
            except Exception:
                health_status["openai"] = False

        return health_status


# 创建全局单例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    获取向量嵌入服务单例

    Returns:
        EmbeddingService: 向量嵌入服务实例
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
