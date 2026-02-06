"""
对话服务 - AI英语教学系统

提供AI对话完成功能，支持智谱AI和OpenAI。
"""
import json
from typing import Any, Dict, List, Optional, Type

from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.services.zhipu_service import get_zhipuai_service


class ChatService:
    """
    对话服务

    负责AI对话完成，支持普通文本和结构化JSON输出。
    """

    def __init__(self, provider: Optional[str] = None):
        """
        初始化对话服务

        Args:
            provider: AI服务提供商 ("zhipuai", "openai", None=使用默认)
        """
        self.provider = provider or settings.AI_PROVIDER
        self._openai_client: Optional[AsyncOpenAI] = None
        self._zhipuai_service = None

        # 从配置获取模型参数
        if self.provider == "zhipuai":
            self.model = settings.ZHIPUAI_MODEL
            self.temperature = settings.ZHIPUAI_TEMPERATURE
            self.max_tokens = settings.ZHIPUAI_MAX_TOKENS
        else:
            self.model = settings.OPENAI_MODEL
            self.temperature = settings.OPENAI_TEMPERATURE
            self.max_tokens = settings.OPENAI_MAX_TOKENS

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
            response_format: 响应格式，如 {"type": "json_object"}（可选）
            provider: AI服务提供商（可选）

        Returns:
            str: AI生成的文本响应

        Raises:
            ValueError: 如果消息列表为空
            ConnectionError: 如果API调用失败
        """
        if not messages:
            raise ValueError("消息列表不能为空")

        ai_provider = provider or self.provider

        # 使用智谱AI
        if ai_provider == "zhipuai":
            try:
                response = await self._get_zhipuai_service().chat_completion(
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens or self.max_tokens,
                    response_format=response_format
                )
                return response["choices"][0]["message"]["content"]
            except Exception as e:
                if provider == "zhipuai":
                    raise ConnectionError(f"智谱AI聊天完成失败: {str(e)}")
                print(f"智谱AI调用失败，降级到OpenAI: {e}")

        # 使用OpenAI
        return await self._openai_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            response_format=response_format
        )

    async def _openai_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """使用OpenAI进行聊天完成"""
        client = self._get_openai_client()
        chat_model = model or settings.OPENAI_MODEL

        try:
            params = {
                "model": chat_model,
                "messages": messages,
                "temperature": temperature or settings.OPENAI_TEMPERATURE,
                "max_tokens": max_tokens or settings.OPENAI_MAX_TOKENS,
            }

            if response_format:
                params["response_format"] = response_format

            response = await client.chat.completions.create(**params)
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ConnectionError(f"OpenAI聊天完成失败: {str(e)}")

    async def chat_completion_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: Type[BaseModel],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        model: Optional[str] = None,
    ) -> BaseModel:
        """
        聊天完成（结构化输出）

        使用 JSON mode 强制 AI 返回符合指定 Pydantic 模型的结构化数据

        Args:
            messages: 对话消息列表
            response_model: 响应的 Pydantic 模型类型
            temperature: 温度参数（可选）
            max_tokens: 最大token数（可选）
            model: 使用的模型（可选）

        Returns:
            BaseModel: 解析后的结构化数据对象

        Raises:
            ValueError: 如果消息列表为空或JSON解析失败
            ConnectionError: 如果API调用失败

        Example:
            class DiagnosisResult(BaseModel):
                cefr_level: str
                abilities: Dict[str, float]
                weak_points: List[str]

            result = await chat_service.chat_completion_structured(
                messages=[{"role": "user", "content": "..."}],
                response_model=DiagnosisResult
            )
        """
        # 在系统消息中添加JSON格式说明
        schema = response_model.model_json_schema()
        formatted_messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的英语教学分析助手。"
                    f"请严格按照以下JSON Schema格式返回响应：\n"
                    f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n\n"
                    "只返回JSON数据，不要包含任何其他文本。"
                )
            },
            *messages
        ]

        # 调用聊天完成，启用JSON mode
        response_text = await self.chat_completion(
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            model=model,
            response_format={"type": "json_object"}
        )

        # 解析JSON响应
        try:
            response_dict = json.loads(response_text)
            return response_model(**response_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}\n响应内容: {response_text}")
        except Exception as e:
            raise ValueError(f"响应模型验证失败: {str(e)}\n响应内容: {response_text}")

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
                await self._get_zhipuai_service().chat_completion(
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                health_status["zhipuai"] = True
            except Exception:
                health_status["zhipuai"] = False

        # 检查OpenAI
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                await self._openai_chat_completion(
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=10
                )
                health_status["openai"] = True
            except Exception:
                health_status["openai"] = False

        return health_status


# 创建全局单例
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """
    获取对话服务单例

    Returns:
        ChatService: 对话服务实例
    """
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
