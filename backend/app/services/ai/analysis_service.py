"""
分析服务 - AI英语教学系统

提供学生评估数据分析能力，生成诊断报告和学习建议。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.ai.chat_service import ChatService, get_chat_service


class AnalysisService:
    """
    分析服务

    负责学生评估数据的AI分析，包括能力诊断、薄弱点识别和学习建议生成。
    """

    def __init__(self, chat_service: Optional[ChatService] = None):
        """
        初始化分析服务

        Args:
            chat_service: 对话服务实例（可选，默认使用单例）
        """
        self._chat_service = chat_service or get_chat_service()

    @property
    def chat_service(self) -> ChatService:
        """获取对话服务"""
        return self._chat_service

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
        response_text = await self._chat_service.chat_completion(
            messages=messages,
            temperature=0.3,  # 降低温度以获得更一致的分析
            max_tokens=3000,
            response_format={"type": "json_object"},
            provider=provider
        )

        # 解析响应
        try:
            result = {"analysis": json.loads(response_text)}
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
        健康检查

        Returns:
            Dict[str, bool]: 依赖服务的健康状态
        """
        return await self._chat_service.health_check()


# 创建全局单例
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    """
    获取分析服务单例

    Returns:
        AnalysisService: 分析服务实例
    """
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AnalysisService()
    return _analysis_service


# 需要导入 json 模块
import json
