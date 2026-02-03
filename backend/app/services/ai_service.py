"""
AI 服务 - AI英语教学系统
支持智谱AI（主要）和OpenAI（备用）
使用智谱AI glm-4.7和embedding-3提供智能分析能力
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Type

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

T = TypeVar('T', bound=BaseModel)


class AIService:
    """
    AI服务类
    支持多种AI提供商：智谱AI（主要）、OpenAI（备用）
    使用智谱AI glm-4.7提供智能分析能力
    支持JSON mode用于结构化输出
    """

    def __init__(self, provider: Optional[str] = None):
        """
        初始化AI服务

        Args:
            provider: AI服务提供商 ("zhipuai", "openai", None=使用默认)
        """
        self.provider = provider or settings.AI_PROVIDER
        self._openai_client: Optional[AsyncOpenAI] = None
        self._zhipuai_service = None

        # 从配置获取模型参数
        if self.provider == "zhipuai":
            self.model = settings.ZHIPUAI_MODEL
            self.embedding_model = settings.ZHIPUAI_EMBEDDING_MODEL
            self.temperature = settings.ZHIPUAI_TEMPERATURE
            self.max_tokens = settings.ZHIPUAI_MAX_TOKENS
        else:
            self.model = settings.OPENAI_MODEL
            self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
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

    def _get_client_for_provider(self, provider: Optional[str] = None):
        """根据提供商获取对应的客户端"""
        ai_provider = provider or self.provider

        if ai_provider == "zhipuai":
            return self._get_zhipuai_service()
        elif ai_provider == "openai":
            return self._get_openai_client()
        else:
            raise ValueError(f"不支持的AI服务提供商: {ai_provider}")

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

        # 确定使用哪个提供商
        ai_provider = provider or self.provider

        if ai_provider == "zhipuai":
            # 使用智谱AI
            try:
                return await self._get_zhipuai_service().generate_embedding(text)
            except Exception as e:
                if provider == "zhipuai":  # 明确指定使用智谱AI
                    raise
                # 否则降级到OpenAI
                print(f"智谱AI调用失败，降级到OpenAI: {e}")

        # 尝试使用OpenAI
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            return await self._generate_openai_embedding(text, model)

        raise ValueError(f"没有可用的AI服务提供商（当前: {ai_provider}）")

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

        # 确定使用哪个提供商
        ai_provider = provider or self.provider

        if ai_provider == "zhipuai":
            try:
                return await self._get_zhipuai_service().batch_generate_embeddings(texts)
            except Exception as e:
                if provider == "zhipuai":
                    raise
                print(f"智谱AI批量调用失败，降级到OpenAI: {e}")

        # 使用OpenAI
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
        chat_model = model or self.model

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
        client = self._get_openai_client()
        chat_model = model or settings.OPENAI_MODEL

        try:
            params = {
                "model": chat_model,
                "messages": messages,
                "temperature": temperature or settings.OPENAI_TEMPERATURE,
                "max_tokens": max_tokens or settings.OPENAI_MAX_TOKENS,
            }

            # 如果指定了响应格式，添加到参数中
            if response_format:
                params["response_format"] = response_format

            response = await client.chat.completions.create(**params)
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ConnectionError(f"OpenAI聊天完成失败: {str(e)}")

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

        使用 JSON mode 强制 AI 返回符合指定 Pydantic 模型的结构化数据

        Args:
            messages: 对话消息列表
            response_model: 响应的 Pydantic 模型类型
            temperature: 温度参数（可选）
            max_tokens: 最大token数（可选）
            model: 使用的模型（可选）

        Returns:
            T: 解析后的结构化数据对象

        Raises:
            ValueError: 如果消息列表为空或JSON解析失败
            ConnectionError: 如果API调用失败

        Example:
            ```python
            class DiagnosisResult(BaseModel):
                cefr_level: str
                abilities: Dict[str, float]
                weak_points: List[str]

            result = await ai_service.chat_completion_structured(
                messages=[{"role": "user", "content": "..."}],
                response_model=DiagnosisResult
            )
            ```
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

    async def analyze_student_assessment(
        self,
        student_info: Dict[str, Any],
        practice_data: List[Dict[str, Any]],
        target_exam: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        AI分析学生评估数据

        这是核心功能，用于初始诊断和定期深度分析

        Args:
            student_info: 学生信息字典，包含：
                - id: 学生ID
                - name: 学生姓名
                - target_exam: 目标考试类型
                - target_score: 目标分数
                - current_cefr_level: 当前CEFR等级（如有）
            practice_data: 练习数据列表，每项包含：
                - content_id: 内容ID
                - topic: 主题
                - difficulty: 难度
                - score: 得分
                - correct_rate: 正确率
                - time_spent: 耗时
                - created_at: 完成时间
            target_exam: 目标考试类型（可选，覆盖student_info中的值）
            provider: AI服务提供商（可选）

        Returns:
            Dict[str, Any]: AI分析结果，包含：
                - cefr_level: 诊断的CEFR等级
                - abilities: 能力评估字典
                    - listening: 听力能力 (0-100)
                    - reading: 阅读能力 (0-100)
                    - speaking: 口语能力 (0-100)
                    - writing: 写作能力 (0-100)
                    - grammar: 语法能力 (0-100)
                    - vocabulary: 词汇能力 (0-100)
                - weak_points: 薄弱点列表
                    - topic: 主题
                    - reason: 原因分析
                - strong_points: 优势点列表
                - recommendations: 学习建议列表
                    - priority: 优先级 (high/medium/low)
                    - suggestion: 建议内容
                - exam_readiness: 考试准备度评估
                    - ready: 是否准备好
                    - gap: 差距分析
                - analysis_summary: 分析总结

        Raises:
            ValueError: 如果输入数据无效
            ConnectionError: 如果API调用失败
        """
        if not student_info:
            raise ValueError("学生信息不能为空")

        # 构建AI分析提示词
        prompt = self._build_analysis_prompt(
            student_info=student_info,
            practice_data=practice_data,
            target_exam=target_exam or student_info.get("target_exam")
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的英语教学分析专家，拥有20年的英语教学经验。"
                    "你需要基于学生的练习数据，进行全面的英语能力诊断分析。"
                    "分析结果需要客观、准确，并给出可操作的学习建议。"
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # 使用结构化输出
        response_text = await self.chat_completion(
            messages=messages,
            temperature=0.3,  # 降低温度以获得更一致的分析
            max_tokens=3000,
            response_format={"type": "json_object"},
            provider=provider
        )

        # 解析响应
        try:
            result = json.loads(response_text)
            # 添加元数据
            result["analyzed_at"] = datetime.utcnow().isoformat()
            result["analysis_version"] = "1.0"
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"AI分析结果解析失败: {str(e)}")

    def _build_analysis_prompt(
        self,
        student_info: Dict[str, Any],
        practice_data: List[Dict[str, Any]],
        target_exam: Optional[str] = None,
    ) -> str:
        """
        构建AI分析提示词

        Args:
            student_info: 学生信息
            practice_data: 练习数据
            target_exam: 目标考试

        Returns:
            str: 构建的提示词
        """
        prompt_parts = []

        # 学生信息部分
        prompt_parts.append("# 学生信息\n")
        prompt_parts.append(f"- 学生ID: {student_info.get('id', 'unknown')}")
        prompt_parts.append(f"- 姓名: {student_info.get('name', 'unknown')}")
        prompt_parts.append(f"- 当前CEFR等级: {student_info.get('current_cefr_level', '未评估')}")
        prompt_parts.append(f"- 目标考试: {target_exam or '未指定'}")
        prompt_parts.append(f"- 目标分数: {student_info.get('target_score', '未指定')}")
        prompt_parts.append(f"\n")

        # 练习数据部分
        if practice_data:
            prompt_parts.append("# 练习数据\n")
            prompt_parts.append(f"共完成 {len(practice_data)} 项练习\n\n")

            # 按主题分组统计
            topic_stats = {}
            for practice in practice_data:
                topic = practice.get("topic", "unknown")
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        "count": 0,
                        "total_score": 0,
                        "correct_count": 0,
                    }
                topic_stats[topic]["count"] += 1
                topic_stats[topic]["total_score"] += practice.get("score", 0)
                if practice.get("correct_rate", 0) >= 0.6:
                    topic_stats[topic]["correct_count"] += 1

            # 添加统计信息
            for topic, stats in topic_stats.items():
                avg_score = stats["total_score"] / stats["count"] if stats["count"] > 0 else 0
                accuracy = stats["correct_count"] / stats["count"] if stats["count"] > 0 else 0
                prompt_parts.append(
                    f"- {topic}: {stats['count']}项练习, "
                    f"平均分{avg_score:.1f}, 正确率{accuracy:.1%}"
                )

            prompt_parts.append("\n")

            # 最近5项练习详情
            prompt_parts.append("## 最近练习详情\n")
            recent_practices = sorted(
                practice_data,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )[:5]

            for i, practice in enumerate(recent_practices, 1):
                prompt_parts.append(
                    f"{i}. {practice.get('topic', 'unknown')} "
                    f"(难度: {practice.get('difficulty', 'unknown')}) "
                    f"- 得分: {practice.get('score', 0)}/100, "
                    f"正确率: {practice.get('correct_rate', 0):.1%}"
                )

            prompt_parts.append("\n")
        else:
            prompt_parts.append("# 练习数据\n暂无练习记录\n\n")

        # 分析要求
        prompt_parts.append("# 分析要求\n")
        prompt_parts.append("请基于以上数据，提供JSON格式的分析结果，包含以下字段：\n")
        prompt_parts.append("```json\n")
        prompt_parts.append("{\n")
        prompt_parts.append('  "cefr_level": "A1/B1/C1等",\n')
        prompt_parts.append('  "abilities": {\n')
        prompt_parts.append('    "listening": 0-100,\n')
        prompt_parts.append('    "reading": 0-100,\n')
        prompt_parts.append('    "speaking": 0-100,\n')
        prompt_parts.append('    "writing": 0-100,\n')
        prompt_parts.append('    "grammar": 0-100,\n')
        prompt_parts.append('    "vocabulary": 0-100\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "weak_points": [\n')
        prompt_parts.append('    {"topic": "主题", "reason": "原因分析"}\n')
        prompt_parts.append('  ],\n')
        prompt_parts.append('  "strong_points": ["优势点"],\n')
        prompt_parts.append('  "recommendations": [\n')
        prompt_parts.append('    {"priority": "high/medium/low", "suggestion": "建议内容"}\n')
        prompt_parts.append('  ],\n')
        prompt_parts.append('  "exam_readiness": {\n')
        prompt_parts.append('    "ready": true/false,\n')
        prompt_parts.append('    "gap": "差距描述"\n')
        prompt_parts.append('  },\n')
        prompt_parts.append('  "analysis_summary": "整体分析总结"\n')
        prompt_parts.append("}\n")
        prompt_parts.append("```\n")

        return "".join(prompt_parts)

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
        if settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            try:
                await self._generate_openai_embedding("test")
                health_status["openai"] = True
            except Exception as e:
                print(f"OpenAI健康检查失败: {e}")

        return health_status


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
