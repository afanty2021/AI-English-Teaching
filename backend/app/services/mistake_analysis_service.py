"""
错题AI分析服务 - AI英语教学系统
使用AI为错题生成详细解析和个性化学习建议
"""
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_service import get_ai_service
from app.services.mistake_analysis_schemas import (
    MistakeAnalysisRequest,
    MistakeAnalysisResponse,
    BatchMistakeAnalysisResponse,
)


class MistakeAnalysisService:
    """
    错题AI分析服务类

    核心功能：
    1. 单个错题AI分析
    2. 批量错题AI分析
    3. 生成个性化学习建议
    4. 识别常见错误模式
    5. 制定复习计划
    """

    def __init__(self, db: AsyncSession):
        """
        初始化错题AI分析服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.ai_service = get_ai_service()

    async def analyze_mistake(
        self,
        question: str,
        wrong_answer: str,
        correct_answer: str,
        mistake_type: str,
        topic: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        mistake_count: int = 1,
        student_level: Optional[str] = None,
    ) -> MistakeAnalysisResponse:
        """
        分析单个错题

        使用AI生成详细的错误解析和学习建议。

        Args:
            question: 题目内容
            wrong_answer: 学生的错误答案
            correct_answer: 正确答案
            mistake_type: 错题类型
            topic: 主题分类
            difficulty_level: 难度等级
            mistake_count: 错误次数
            student_level: 学生英语水平

        Returns:
            MistakeAnalysisResponse: AI分析结果
        """
        # 构建分析请求
        request_data = MistakeAnalysisRequest(
            question=question,
            wrong_answer=wrong_answer,
            correct_answer=correct_answer,
            mistake_type=mistake_type,
            topic=topic,
            difficulty_level=difficulty_level,
            mistake_count=mistake_count,
            student_level=student_level,
        )

        # 生成分析提示词
        prompt = self._build_analysis_prompt(request_data)

        # 调用AI获取分析结果
        try:
            response_content = await self.ai_service.generate_json(
                prompt=prompt,
                response_model=MistakeAnalysisResponse,
                temperature=0.7,  # 适中的创造性
            )
            return response_content

        except Exception as e:
            # 如果JSON模式失败，尝试文本模式然后手动解析
            print(f"JSON模式失败，尝试文本模式: {e}")
            return await self._analyze_with_text_mode(request_data)

    async def analyze_mistakes_batch(
        self,
        mistakes_data: List[Dict[str, Any]],
        student_level: Optional[str] = None,
    ) -> BatchMistakeAnalysisResponse:
        """
        批量分析错题

        对多个错题进行批量分析，识别常见错误模式。

        Args:
            mistakes_data: 错题数据列表，每个包含：
                - question: 题目
                - wrong_answer: 错误答案
                - correct_answer: 正确答案
                - mistake_type: 错题类型
                - topic: 主题（可选）
                - difficulty_level: 难度（可选）
                - mistake_count: 错误次数（可选）
            student_level: 学生英语水平

        Returns:
            BatchMistakeAnalysisResponse: 批量分析结果
        """
        # 逐个分析每个错题
        results = []
        for mistake_data in mistakes_data:
            try:
                result = await self.analyze_mistake(
                    question=mistake_data["question"],
                    wrong_answer=mistake_data["wrong_answer"],
                    correct_answer=mistake_data["correct_answer"],
                    mistake_type=mistake_data["mistake_type"],
                    topic=mistake_data.get("topic"),
                    difficulty_level=mistake_data.get("difficulty_level"),
                    mistake_count=mistake_data.get("mistake_count", 1),
                    student_level=student_level,
                )
                results.append(result)
            except Exception as e:
                print(f"分析错题失败: {e}")
                # 创建一个基础的分析结果
                results.append(self._create_fallback_analysis(mistake_data))

        # 生成整体总结
        summary_prompt = self._build_summary_prompt(results, student_level)
        summary = await self.ai_service.generate_text(
            prompt=summary_prompt,
            max_tokens=500,
        )

        # 识别常见错误模式
        common_patterns = await self._identify_common_patterns(results)

        # 生成总体建议
        overall_recommendations = await self._generate_overall_recommendations(
            results, common_patterns, student_level
        )

        # 识别需要重点关注的话题
        priority_topics = await self._identify_priority_topics(results)

        return BatchMistakeAnalysisResponse(
            results=results,
            summary=summary,
            common_patterns=common_patterns,
            overall_recommendations=overall_recommendations,
            priority_topics=priority_topics,
        )

    def _build_analysis_prompt(self, request: MistakeAnalysisRequest) -> str:
        """
        构建错题分析的提示词

        Args:
            request: 分析请求

        Returns:
            str: 完整的分析提示词
        """
        # 根据错题类型定制提示词
        type_specific_instructions = self._get_type_specific_instructions(request.mistake_type)

        prompt = f"""你是一位经验丰富的英语教学专家，擅长分析学生的英语错误并提供个性化学习建议。

请分析以下错题，提供详细的解析和建议：

## 题目信息
- **题目类型**: {self._get_mistake_type_name(request.mistake_type)}
- **题目**: {request.question}
- **学生答案**: {request.wrong_answer}
- **正确答案**: {request.correct_answer}
- **错误次数**: {request.mistake_count}次
{f"- **主题**: {request.topic}" if request.topic else ""}
{f"- **难度**: {request.difficulty_level}" if request.difficulty_level else ""}
{f"- **学生水平**: {request.student_level}" if request.student_level else ""}

## 分析要求

请以JSON格式返回详细的分析，包含以下内容：

1. **错误分类** (mistake_category): 对错误进行分类，如"时态使用错误"、"词汇搭配不当"等

2. **严重程度** (severity): "轻微"、"中等"或"严重"

3. **详细解释** (explanation): 清晰解释为什么学生答案错误，正确答案为什么对

4. **正确方法** (correct_approach): 解答此类题目的正确思路和方法

5. **{type_specific_instructions['analysis_field']}: {type_specific_instructions['analysis_instruction']}**

6. **根本原因分析** (root_cause):
   - primary_cause: 主要原因
   - secondary_causes: 次要原因列表
   - knowledge_gaps: 涉及的知识盲点

7. **知识点标签** (knowledge_points): 提取3-5个相关的知识点标签

8. **学习建议** (recommendations): 提供2-4条个性化学习建议，每条包含：
   - priority: 优先级(1-5)
   - category: 建议类别
   - title: 简短标题
   - description: 详细说明
   - resources: 推荐资源(可选)
   - practice_exercises: 练习建议(可选)
   - estimated_time: 预计学习时间(可选)

9. **复习计划** (review_plan):
   - review_frequency: 复习频率建议
   - next_review_days: 建议复习间隔天数列表
   - mastery_criteria: 掌握标准
   - review_method: 复习方法

10. **鼓励语** (encouragement): 一句鼓励学生的话

请确保分析准确、详细，建议具体可行。
"""

        return prompt

    def _get_type_specific_instructions(self, mistake_type: str) -> Dict[str, str]:
        """
        获取特定错题类型的分析指导

        Args:
            mistake_type: 错题类型

        Returns:
            Dict[str, str]: 分析字段名称和指导说明
        """
        instructions_map = {
            "grammar": {
                "analysis_field": "语法错误详情 (grammar_errors)",
                "analysis_instruction": "列出具体的语法错误，每项包含：error_type(错误类型)、location(位置)、correction(正确形式)、explanation(解释)"
            },
            "vocabulary": {
                "analysis_field": "词汇错误详情 (vocabulary_errors)",
                "analysis_instruction": "列出词汇错误，每项包含：word(单词)、correct_form(正确形式)、meaning(含义)、usage_example(用法示例)、common_mistake(是否常见错误)"
            },
            "reading": {
                "analysis_field": "理解问题详情 (comprehension_issues)",
                "analysis_instruction": "列出理解问题，每项包含：issue_type(问题类型)、misunderstanding(误解内容)、clarification(正确理解)、tips(理解技巧)"
            },
            "listening": {
                "analysis_field": "理解问题详情 (comprehension_issues)",
                "analysis_instruction": "列出听力理解问题，每项包含：issue_type(问题类型)、misunderstanding(误解内容)、clarification(正确理解)、tips(听力技巧)"
            },
            "writing": {
                "analysis_field": "语法错误详情 (grammar_errors)",
                "analysis_instruction": "列出写作中的错误，每项包含：error_type(错误类型)、location(位置)、correction(正确形式)、explanation(解释)"
            },
            "speaking": {
                "analysis_field": "理解问题详情 (comprehension_issues)",
                "analysis_instruction": "列出口语表达问题，每项包含：issue_type(问题类型)、misunderstanding(误解内容)、clarification(正确理解)、tips(口语技巧)"
            },
        }

        return instructions_map.get(
            mistake_type,
            {
                "analysis_field": "详细分析",
                "analysis_instruction": "提供详细的错误分析"
            }
        )

    def _get_mistake_type_name(self, mistake_type: str) -> str:
        """获取错题类型的中文名称"""
        type_names = {
            "grammar": "语法",
            "vocabulary": "词汇",
            "reading": "阅读理解",
            "listening": "听力理解",
            "writing": "写作",
            "speaking": "口语",
            "pronunciation": "发音",
            "comprehension": "理解",
        }
        return type_names.get(mistake_type, mistake_type)

    def _build_summary_prompt(
        self,
        results: List[MistakeAnalysisResponse],
        student_level: Optional[str],
    ) -> str:
        """构建批量分析的总结提示词"""
        mistakes_summary = "\n".join([
            f"{i+1}. [{r.mistake_category}] {r.explanation[:100]}..."
            for i, r in enumerate(results[:10])
        ])

        return f"""作为英语教学专家，请基于以下{len(results)}道错题的分析结果，提供简洁的总结：

{mistakes_summary}

{f"学生水平：{student_level}" if student_level else ""}

请提供：
1. 整体学习状况评估（1-2句话）
2. 最需要关注的2-3个问题领域
3. 给学生的学习建议（3条以内）

总结应该简洁、鼓励性、具有指导性。
"""

    async def _identify_common_patterns(
        self,
        results: List[MistakeAnalysisResponse],
    ) -> List[str]:
        """识别常见错误模式"""
        # 统计错误类别
        category_counts: Dict[str, int] = {}
        for result in results:
            category = result.mistake_category
            category_counts[category] = category_counts.get(category, 0) + 1

        # 找出出现频率高的模式
        common_patterns = []
        for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            if count >= 2:  # 至少出现2次
                common_patterns.append(f"{category}（{count}次）")

        return common_patterns[:5]  # 最多返回5个

    async def _generate_overall_recommendations(
        self,
        results: List[MistakeAnalysisResponse],
        common_patterns: List[str],
        student_level: Optional[str],
    ) -> List[str]:
        """生成总体学习建议"""
        recommendations = []

        # 基于常见模式生成建议
        if common_patterns:
            recommendations.append(f"重点关注：{', '.join(common_patterns[:3])}")

        # 收集高优先级建议
        high_priority_recs = set()
        for result in results:
            for rec in result.recommendations:
                if rec.priority <= 2:  # 高优先级
                    high_priority_recs.add(rec.category)

        if high_priority_recs:
            recommendations.append(f"加强练习：{', '.join(list(high_priority_recs)[:3])}")

        # 根据错误次数给出建议
        total_errors = sum(len(r.grammar_errors) or len(r.vocabulary_errors) or len(r.comprehension_issues) or 1
                           for r in results)
        if total_errors > len(results):
            recommendations.append("建议：先巩固基础，再做新题")

        recommendations.append("定期复习错题本，避免重复犯错")

        return recommendations[:5]

    async def _identify_priority_topics(
        self,
        results: List[MistakeAnalysisResponse],
    ) -> List[str]:
        """识别需要重点关注的话题"""
        # 收集所有知识点并统计
        topic_counts: Dict[str, int] = {}
        for result in results:
            for point in result.knowledge_points:
                topic_counts[point] = topic_counts.get(point, 0) + 1

        # 返回出现频率高的话题
        priority_topics = [
            topic for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1])
        ]

        return priority_topics[:5]

    async def _analyze_with_text_mode(
        self,
        request: MistakeAnalysisRequest,
    ) -> MistakeAnalysisResponse:
        """使用文本模式进行分析的备用方法"""
        prompt = self._build_analysis_prompt(request) + """

请以JSON格式返回结果，确保JSON格式正确。"""

        response_text = await self.ai_service.generate_text(
            prompt=prompt,
            max_tokens=2000,
        )

        # 尝试从响应中提取JSON
        try:
            # 尝试直接解析
            return MistakeAnalysisResponse.model_validate_json(response_text)
        except Exception:
            # 如果失败，尝试提取JSON部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return MistakeAnalysisResponse.model_validate_json(json_match.group())

        # 如果还是失败，返回基础分析
        return self._create_fallback_analysis({
            "question": request.question,
            "wrong_answer": request.wrong_answer,
            "correct_answer": request.correct_answer,
            "mistake_type": request.mistake_type,
        })

    def _create_fallback_analysis(self, mistake_data: Dict[str, Any]) -> MistakeAnalysisResponse:
        """创建备用基础分析（当AI分析失败时）"""
        from app.services.mistake_analysis_schemas import (
            RootCause,
            LearningRecommendation,
            ReviewPlan,
        )

        return MistakeAnalysisResponse(
            mistake_category="需要进一步分析",
            severity="中等",
            explanation=f"题目要求：{mistake_data['correct_answer']}\n"
                       f"你的答案：{mistake_data['wrong_answer']}\n"
                       f"建议：仔细比较正确答案和你的答案，理解其中的差异。",
            correct_approach=f"参考正确答案：{mistake_data['correct_answer']}",
            root_cause=RootCause(
                primary_cause="需要进一步分析",
                secondary_causes=["基础不牢固", "练习不足"],
                knowledge_gaps=[mistake_data.get("topic", "相关知识点")],
            ),
            knowledge_points=[mistake_data.get("topic", "基础")],
            recommendations=[
                LearningRecommendation(
                    priority=1,
                    category="复习巩固",
                    title="复习相关知识点",
                    description="建议重新学习相关知识点，多做类似练习",
                    practice_exercises=["完成5-10道类似题目"],
                )
            ],
            review_plan=ReviewPlan(
                review_frequency="每天复习",
                next_review_days=[1, 3, 7, 14],
                mastery_criteria="连续答对3次",
                review_method="重做错题 + 做新题",
            ),
            encouragement="继续努力，多练习就会进步！",
        )

    async def update_ai_analysis(
        self,
        mistake_id: str,
        ai_suggestion: str,
        ai_analysis: Dict[str, Any],
    ) -> Any:
        """
        更新错题的AI分析结果到数据库

        Args:
            mistake_id: 错题ID
            ai_suggestion: AI学习建议
            ai_analysis: AI分析详情

        Returns:
            更新后的错题对象
        """
        from app.models.mistake import Mistake

        import uuid

        mistake_uuid = uuid.UUID(mistake_id)
        query = select(Mistake).where(Mistake.id == mistake_uuid)
        result = await self.db.execute(query)
        mistake = result.scalar_one_or_none()

        if not mistake:
            raise ValueError(f"错题不存在: {mistake_id}")

        mistake.ai_suggestion = ai_suggestion
        mistake.ai_analysis = ai_analysis
        mistake.needs_ai_analysis = False

        await self.db.commit()
        await self.db.refresh(mistake)

        return mistake


# 创建服务工厂函数
def get_mistake_analysis_service(db: AsyncSession) -> MistakeAnalysisService:
    """
    获取错题AI分析服务实例

    Args:
        db: 数据库会话

    Returns:
        MistakeAnalysisService: 错题AI分析服务实例
    """
    return MistakeAnalysisService(db)
