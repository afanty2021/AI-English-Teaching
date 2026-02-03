"""
错题AI分析模型 - AI英语教学系统
定义错题分析的数据结构和AI输出格式
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MistakeAnalysisRequest(BaseModel):
    """错题分析请求"""
    question: str = Field(..., description="题目内容")
    wrong_answer: str = Field(..., description="学生的错误答案")
    correct_answer: str = Field(..., description="正确答案")
    mistake_type: str = Field(..., description="错题类型")
    topic: Optional[str] = Field(None, description="主题分类")
    difficulty_level: Optional[str] = Field(None, description="难度等级")
    mistake_count: int = Field(1, description="错误次数")
    student_level: Optional[str] = Field(None, description="学生英语水平（CEFR等级）")


class GrammarError(BaseModel):
    """语法错误详情"""
    error_type: str = Field(..., description="错误类型，如：时态错误、主谓不一致等")
    location: str = Field(..., description="错误位置")
    correction: str = Field(..., description="正确形式")
    explanation: str = Field(..., description="错误原因解释")


class VocabularyError(BaseModel):
    """词汇错误详情"""
    word: str = Field(..., description="错误的单词")
    correct_form: str = Field(..., description="正确形式")
    meaning: str = Field(..., description="单词含义")
    usage_example: str = Field(..., description="用法示例")
    common_mistake: bool = Field(False, description="是否为常见错误")


class ComprehensionIssue(BaseModel):
    """理解问题详情"""
    issue_type: str = Field(..., description="问题类型")
    misunderstanding: str = Field(..., description="误解内容")
    clarification: str = Field(..., description="正确理解")
    tips: str = Field(..., description="理解技巧")


class RootCause(BaseModel):
    """根本原因分析"""
    primary_cause: str = Field(..., description="主要原因")
    secondary_causes: List[str] = Field(default_factory=list, description="次要原因")
    knowledge_gaps: List[str] = Field(default_factory=list, description="知识盲点")


class LearningRecommendation(BaseModel):
    """学习建议"""
    priority: int = Field(..., ge=1, le=5, description="优先级（1-5，1最高）")
    category: str = Field(..., description="建议类别：语法、词汇、理解、练习等")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="详细建议")
    resources: List[str] = Field(default_factory=list, description="推荐学习资源")
    practice_exercises: List[str] = Field(default_factory=list, description="练习建议")
    estimated_time: Optional[str] = Field(None, description="预计学习时间")


class ReviewPlan(BaseModel):
    """复习计划"""
    review_frequency: str = Field(..., description="复习频率")
    next_review_days: List[int] = Field(..., description="建议复习日期间隔（天）")
    mastery_criteria: str = Field(..., description="掌握标准")
    review_method: str = Field(..., description="复习方法建议")


class MistakeAnalysisResponse(BaseModel):
    """错题AI分析响应"""
    # 基础分析
    mistake_category: str = Field(..., description="错误分类")
    severity: str = Field(..., description="严重程度：轻微、中等、严重")

    # 详细解析
    explanation: str = Field(..., description="错误原因详细解释")
    correct_approach: str = Field(..., description="正确解题思路/方法")

    # 具体错误分析（根据类型选择其一）
    grammar_errors: List[GrammarError] = Field(default_factory=list, description="语法错误详情")
    vocabulary_errors: List[VocabularyError] = Field(default_factory=list, description="词汇错误详情")
    comprehension_issues: List[ComprehensionIssue] = Field(default_factory=list, description="理解问题详情")

    # 根本原因
    root_cause: RootCause = Field(..., description="根本原因分析")

    # 知识点标签
    knowledge_points: List[str] = Field(default_factory=list, description="涉及的知识点")

    # 学习建议
    recommendations: List[LearningRecommendation] = Field(..., description="个性化学习建议")

    # 复习计划
    review_plan: ReviewPlan = Field(..., description="复习计划建议")

    # 鼓励语
    encouragement: str = Field(..., description="鼓励性话语")


class BatchMistakeAnalysisResponse(BaseModel):
    """批量错题分析响应"""
    results: List[MistakeAnalysisResponse] = Field(..., description="每个错题的分析结果")
    summary: str = Field(..., description="整体分析总结")
    common_patterns: List[str] = Field(default_factory=list, description="常见错误模式")
    overall_recommendations: List[str] = Field(default_factory=list, description="总体学习建议")
    priority_topics: List[str] = Field(default_factory=list, description="需要重点关注的话题")
