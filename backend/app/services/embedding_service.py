"""
向量嵌入服务 - AI英语教学系统
支持智谱AI、OpenAI等多种嵌入服务
"""
import asyncio
from typing import List, Optional, Dict, Any

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
    向量嵌入服务类
    支持多种AI提供商：智谱AI（主要）、OpenAI（备用）
    """

    def __init__(self, provider: Optional[str] = None):
        """
        初始化嵌入服务

        Args:
            provider: AI服务提供商 ("zhipuai", "openai", None=使用默认)
        """
        self.provider = provider or settings.AI_PROVIDER
        self.embedding_dim = settings.QDRANT_VECTOR_SIZE

        # 懒加载服务
        self._zhipuai_service = None
        self._openai_client = None

    def _get_zhipuai_service(self):
        """获取智谱AI服务"""
        if self._zhipuai_service is None:
            self._zhipuai_service = get_zhipuai_service()
        return self._zhipuai_service

    def _get_openai_client(self) -> AsyncOpenAI:
        """获取OpenAI客户端"""
        if self._openai_client is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API密钥未配置")
            self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

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
        为单个文本生成向量嵌入

        Args:
            text: 要生成向量的文本
            model: 使用的模型（可选）
            provider: AI服务提供商（可选，默认使用初始化时指定的提供商）

        Returns:
            List[float]: 向量嵌入（2048维 for 智谱AI）

        Raises:
            ValueError: 如果文本为空或API密钥未配置
            ConnectionError: 如果API调用失败
        """
        if not text or not text.strip():
            raise ValueError("文本不能为空")

        # 确定使用哪个提供商
        ai_provider = provider or self.provider

        if ai_provider == "zhipuai":
            # 使用智谱AI
            try:
                return await self._get_zhipuai_service().generate_embedding(text)
            except Exception as e:
                if provider == "zhipuai":  # 明确指定使用智谱AI，失败则抛出异常
                    raise
                # 否则降级到OpenAI
                print(f"智谱AI调用失败，降级到OpenAI: {e}")
                ai_provider = "openai"

        if ai_provider == "openai" and settings.OPENAI_API_KEY:
            # 使用OpenAI
            return await self._generate_openai_embedding(text, model)

        raise ValueError(f"没有可用的AI服务提供商（当前: {ai_provider}）")

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


    async def batch_generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = 100,
        model: Optional[str] = None,
        provider: Optional[str] = None
    ) -> List[List[float]]:
        """
        批量生成向量嵌入

        Args:
            texts: 要生成向量的文本列表
            batch_size: 每批处理的文本数量
            model: 使用的模型（可选）
            provider: AI服务提供商（可选）

        Returns:
            List[List[float]]: 向量嵌入列表

        Note:
            根据提供商选择最优批量处理策略
        """
        if not texts:
            return []

        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []

        # 确定使用哪个提供商
        ai_provider = provider or self.provider

        if ai_provider == "zhipuai":
            # 智谱AI支持原生批量请求
            try:
                return await self._get_zhipuai_service().batch_generate_embeddings(valid_texts)
            except Exception as e:
                if provider == "zhipuai":
                    raise
                print(f"智谱AI批量调用失败，使用OpenAI单条调用: {e}")
                # 降级到逐条处理
                ai_provider = "openai"

        if ai_provider == "openai":
            # OpenAI需要分批处理
            embeddings = []
            for i in range(0, len(valid_texts), batch_size):
                batch = valid_texts[i:i + batch_size]
                # 并发生成当前批次的向量
                batch_embeddings = await asyncio.gather(
                    *[self.generate_embedding(text, model, "openai") for text in batch],
                    return_exceptions=True
                )
                # 处理结果
                for emb in batch_embeddings:
                    if isinstance(emb, Exception):
                        # 对于失败的情况，使用零向量
                        print(f"Warning: {emb}")
                        embeddings.append([0.0] * self.embedding_dim)
                    else:
                        embeddings.append(emb)

            return embeddings

        raise ValueError(f"没有可用的AI服务提供商（当前: {ai_provider}）")

    async def generate_content_embedding(
        self,
        title: str,
        content_text: Optional[str] = None,
        description: Optional[str] = None,
        topic: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        exam_type: Optional[str] = None,
    ) -> List[float]:
        """
        为学习内容生成向量嵌入

        Args:
            title: 内容标题
            content_text: 内容正文
            description: 内容描述
            topic: 主题
            difficulty_level: 难度等级
            exam_type: 考试类型

        Returns:
            List[float]: 向量嵌入

        Note:
            组合多个字段生成更有意义的向量表示
        """
        # 构建用于生成向量的文本
        parts = [title]

        if description:
            parts.append(description)

        if topic:
            parts.append(f"主题: {topic}")

        if difficulty_level:
            parts.append(f"难度: {difficulty_level}")

        if exam_type:
            parts.append(f"考试: {exam_type}")

        # 添加内容正文（截取前2000字符以避免超出限制）
        if content_text:
            truncated_content = content_text[:2000]
            parts.append(truncated_content)

        # 组合所有部分
        combined_text = "\n\n".join(parts)

        return await self.generate_embedding(combined_text)

    async def generate_vocabulary_embedding(
        self,
        word: str,
        definitions: Optional[List[str]] = None,
        examples: Optional[List[str]] = None,
        english_definition: Optional[str] = None,
    ) -> List[float]:
        """
        为词汇生成向量嵌入

        Args:
            word: 单词
            definitions: 中文释义列表
            examples: 例句列表
            english_definition: 英文释义

        Returns:
            List[float]: 向量嵌入
        """
        parts = [word]

        if english_definition:
            parts.append(english_definition)

        if definitions:
            parts.append("释义: " + "; ".join(definitions[:3]))

        if examples:
            parts.append("例句: " + " ".join(examples[:2]))

        combined_text = "\n\n".join(parts)

        return await self.generate_embedding(combined_text)

    def get_embedding_dimension(self) -> int:
        """
        获取向量维度

        Returns:
            int: 向量维度（智谱AI: 2048, OpenAI: 1536）
        """
        return self.embedding_dim

    async def health_check(self) -> Dict[str, bool]:
        """
        健康检查：验证所有配置的AI服务连接

        Returns:
            Dict[str, bool]: 各服务的健康状态
        """
        health_status = {
            "zhipuai": False,
            "openai": False
        }

        # 检查智谱AI
        if settings.ZHIPUAI_API_KEY:
            try:
                zhipuai_service = self._get_zhipuai_service()
                health_status["zhipuai"] = await zhipuai_service.health_check()
            except Exception as e:
                print(f"智谱AI健康检查失败: {e}")

        # 检查OpenAI
        if settings.OPENAI_API_KEY:
            try:
                await self._generate_openai_embedding("test")
                health_status["openai"] = True
            except Exception as e:
                print(f"OpenAI健康检查失败: {e}")

        return health_status


# 创建全局单例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    获取嵌入服务单例

    Returns:
        EmbeddingService: 嵌入服务实例
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
