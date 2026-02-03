"""
智谱AI服务封装
使用智谱AI的API进行对话和向量化
"""
import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    速率限制器
    使用令牌桶算法控制请求速率
    """

    def __init__(self, rate: float, per: float = 1.0):
        """
        初始化速率限制器

        Args:
            rate: 令牌数量
            per: 时间窗口（秒）
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """获取令牌，如果超过速率则等待"""
        async with self._lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current

            # 重新填充令牌
            self.allowance += time_passed * (self.rate / self.per)

            # 令牌不超过上限
            if self.allowance > self.rate:
                self.allowance = self.rate

            # 如果有令牌，消耗一个
            if self.allowance < 1.0:
                # 需要等待
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                await asyncio.sleep(sleep_time)
                self.allowance = 0.0
            else:
                self.allowance -= 1.0


class ZhipuAIService:
    """
    智谱AI服务类
    封装智谱AI的对话和向量化API

    包含速率限制功能，避免触发API并发限制
    """

    def __init__(self):
        """初始化智谱AI服务"""
        self.api_key: str = settings.ZHIPUAI_API_KEY
        self.base_url: str = settings.ZHIPUAI_BASE_URL
        self.model: str = settings.ZHIPUAI_MODEL
        self.embedding_model: str = settings.ZHIPUAI_EMBEDDING_MODEL
        self.temperature: float = settings.ZHIPUAI_TEMPERATURE
        self.max_tokens: int = settings.ZHIPUAI_MAX_TOKENS

        # HTTP客户端
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=60.0,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

        # 速率限制器配置
        # chat_completion: 限制为每秒3个请求（免费版限制较严格）
        self._chat_rate_limiter = RateLimiter(rate=3, per=1.0)
        # embedding: 限制为每秒5个请求
        self._embedding_rate_limiter = RateLimiter(rate=5, per=1.0)
        # 并发控制信号量
        self._concurrency_semaphore = asyncio.Semaphore(5)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stream: bool = False,
        response_format: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        聊天完成API调用

        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            top_p: top_p采样参数
            top_k: top_k采样参数
            stream: 是否流式输出
            response_format: 响应格式（支持JSON mode）
            timeout: 请求超时时间（秒），默认60秒

        Returns:
            API响应结果
        """
        if not self.api_key:
            raise ValueError("智谱AI API密钥未配置，请在.env中设置ZHIPUAI_API_KEY")

        # 速率限制和并发控制
        await self._chat_rate_limiter.acquire()

        async with self._concurrency_semaphore:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "top_p": top_p or settings.ZHIPUAI_TOP_P,
                "top_k": top_k or settings.ZHIPUAI_TOP_K,
                "stream": stream
            }

            # 添加JSON mode支持
            if response_format:
                payload["response_format"] = response_format

            try:
                logger.debug(f"调用智谱AI chat_completion: {len(messages)} 条消息")
                # 使用自定义超时或默认60秒
                request_timeout = timeout or 60.0
                response = await self.client.post(
                    "/chat/completions",
                    json=payload,
                    timeout=request_timeout
                )
                response.raise_for_status()
                result = response.json()

                # 处理响应：优先使用 content，如果为空则使用 reasoning_content
                choices = result.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    content = message.get("content", "")
                    reasoning_content = message.get("reasoning_content", "")

                    # 如果 content 为空但有 reasoning_content，使用 reasoning_content
                    if not content and reasoning_content:
                        result["choices"][0]["message"]["content"] = reasoning_content

                logger.debug(f"智谱AI chat_completion 成功")
                return result
            except httpx.HTTPStatusError as e:
                logger.error(f"智谱AI API错误: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"智谱AI调用失败: {e}")
                raise

    async def generate_embedding(
        self,
        text: str,
        encoding_type: str = "float"
    ) -> List[float]:
        """
        生成文本向量

        Args:
            text: 输入文本
            encoding_type: 编码类型

        Returns:
            向量列表（2048维）
        """
        if not self.api_key:
            raise ValueError("智谱AI API密钥未配置，请在.env中设置ZHIPUAI_API_KEY")

        # 速率限制和并发控制
        await self._embedding_rate_limiter.acquire()

        async with self._concurrency_semaphore:
            payload = {
                "model": self.embedding_model,
                "input": text,
                "encoding_type": encoding_type
            }

            try:
                logger.debug(f"调用智谱AI generate_embedding: {len(text)} 字符")
                response = await self.client.post(
                    "/embeddings",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                # 智谱AI返回格式: {"data": [{"embedding": [...]}]}
                logger.debug(f"智谱AI generate_embedding 成功")
                return result["data"][0]["embedding"]
            except httpx.HTTPStatusError as e:
                logger.error(f"智谱AI Embedding API错误: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"智谱AI Embedding调用失败: {e}")
                raise

    async def batch_generate_embeddings(
        self,
        texts: List[str],
        encoding_type: str = "float"
    ) -> List[List[float]]:
        """
        批量生成文本向量

        Args:
            texts: 输入文本列表
            encoding_type: 编码类型

        Returns:
            向量列表

        Note:
            批量请求只消耗一次速率限制配额，但会占用更多的令牌
        """
        if not self.api_key:
            raise ValueError("智谱AI API密钥未配置，请在.env中设置ZHIPUAI_API_KEY")

        # 批量请求也需要速率控制，但可以使用更高的配额
        await self._embedding_rate_limiter.acquire()

        async with self._concurrency_semaphore:
            # 智谱AI embedding-3支持批量请求
            payload = {
                "model": self.embedding_model,
                "input": texts,
                "encoding_type": encoding_type
            }

            try:
                logger.debug(f"调用智谱AI batch_generate_embeddings: {len(texts)} 个文本")
                response = await self.client.post(
                    "/embeddings",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()

                # 按顺序返回所有向量
                logger.debug(f"智谱AI batch_generate_embeddings 成功")
                return [item["embedding"] for item in result["data"]]
            except httpx.HTTPStatusError as e:
                logger.error(f"智谱AI Embedding API错误: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"智谱AI批量Embedding调用失败: {e}")
                raise

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            服务是否可用
        """
        try:
            # 尝试调用一个简单的对话
            await self.chat_completion([
                {"role": "user", "content": "hi"}
            ])
            return True
        except Exception:
            return False


# 全局服务实例
_zhipuai_service: Optional[ZhipuAIService] = None


def get_zhipuai_service() -> ZhipuAIService:
    """
    获取智谱AI服务实例（单例模式）

    Returns:
        ZhipuAIService实例
    """
    global _zhipuai_service
    if _zhipuai_service is None:
        _zhipuai_service = ZhipuAIService()
    return _zhipuai_service
