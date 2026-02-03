"""
推荐相关的Pydantic Schemas
定义内容推荐、学生画像等数据结构
"""
import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, Field


class StudentProfile(BaseModel):
    """
    学生画像
    包含学习目标、能力评估、知识点掌握情况等
    """
    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID = Field(..., description="学生ID")
    target_exam: Optional[str] = Field(None, description="目标考试类型")
    target_score: Optional[int] = Field(None, description="目标分数")
    current_cefr_level: Optional[str] = Field(None, description="当前CEFR等级")

    # 能力评估（从知识图谱获取）
    abilities: Optional[dict] = Field(default_factory=dict, description="各维度能力评估")

    # 知识点掌握情况
    mastered_points: List[str] = Field(default_factory=list, description="已掌握的知识点")
    weak_points: List[str] = Field(default_factory=list, description="薄弱知识点")
    learning_points: List[str] = Field(default_factory=list, description="正在学习的知识点")

    # 学习偏好
    preferred_topics: List[str] = Field(default_factory=list, description="偏好主题")
    preferred_content_types: List[str] = Field(default_factory=list, description="偏好的内容类型")

    # 学习进度
    completed_content_count: int = Field(default=0, description="已完成内容数量")
    total_study_time: int = Field(default=0, description="总学习时长（分钟）")


class ReadingRecommendation(BaseModel):
    """
    阅读推荐
    """
    content_id: uuid.UUID = Field(..., description="内容ID")
    title: str = Field(..., description="标题")
    description: Optional[str] = Field(None, description="描述")
    difficulty_level: str = Field(..., description="难度等级")
    topic: Optional[str] = Field(None, description="主题")
    word_count: Optional[int] = Field(None, description="字数")
    estimated_time: Optional[int] = Field(None, description="预计阅读时间（分钟）")

    # 推荐理由
    reason: str = Field(..., description="推荐理由")

    # 相关知识点
    knowledge_points: List[str] = Field(default_factory=list, description="涉及的知识点")

    # 推荐分数
    score: float = Field(..., description="推荐分数")

    # i+1 信息
    i_plus_one_info: Optional[dict] = Field(None, description="i+1难度分析信息")


class ExerciseRecommendation(BaseModel):
    """
    练习题推荐
    """
    exercise_id: uuid.UUID = Field(..., description="练习题ID")
    title: str = Field(..., description="标题")
    question_type: str = Field(..., description="题目类型")
    difficulty_level: str = Field(..., description="难度等级")
    topic: Optional[str] = Field(None, description="主题")
    estimated_time: Optional[int] = Field(None, description="预计用时（分钟）")

    # 推荐理由
    reason: str = Field(..., description="推荐理由")

    # 考点
    exam_points: List[str] = Field(default_factory=list, description="考查的知识点")

    # 推荐分数
    score: float = Field(..., description="推荐分数")


class SpeakingRecommendation(BaseModel):
    """
    口语练习推荐
    """
    content_id: uuid.UUID = Field(..., description="内容ID")
    title: str = Field(..., description="标题")
    description: Optional[str] = Field(None, description="描述")
    difficulty_level: str = Field(..., description="难度等级")
    topic: Optional[str] = Field(None, description="主题")
    duration: Optional[int] = Field(None, description="时长（秒）")

    # 推荐理由
    reason: str = Field(..., description="推荐理由")

    # 练习类型
    practice_type: str = Field(..., description="练习类型（朗读/对话/演讲等）")

    # 推荐分数
    score: float = Field(..., description="推荐分数")


class DailyContentResponse(BaseModel):
    """
    每日内容推荐响应
    """
    model_config = ConfigDict(from_attributes=True)

    # 推荐日期
    date: datetime = Field(..., description="推荐日期")

    # 学生画像摘要
    student_profile_summary: dict = Field(..., description="学生画像摘要")

    # 阅读推荐
    reading_recommendations: List[ReadingRecommendation] = Field(
        default_factory=list,
        description="阅读材料推荐（3-5篇）"
    )

    # 练习推荐
    exercise_recommendations: List[ExerciseRecommendation] = Field(
        default_factory=list,
        description="练习题推荐（5-10题）"
    )

    # 口语推荐
    speaking_recommendations: List[SpeakingRecommendation] = Field(
        default_factory=list,
        description="口语练习推荐（1-3个）"
    )

    # 今日学习目标
    daily_goals: dict = Field(..., description="今日学习目标")

    # 推荐元信息
    total_recommendations: int = Field(..., description="总推荐数量")
    retrieval_strategy: str = Field(default="three_stage", description="召回策略")
    ai_reranked_count: int = Field(default=0, description="AI精排的内容数量")


class ContentDetailResponse(BaseModel):
    """
    内容详情响应
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="内容ID")
    title: str = Field(..., description="标题")
    description: Optional[str] = Field(None, description="描述")
    content_type: str = Field(..., description="内容类型")
    difficulty_level: str = Field(..., description="难度等级")
    exam_type: Optional[str] = Field(None, description="考试类型")
    topic: Optional[str] = Field(None, description="主题")
    tags: List[str] = Field(default_factory=list, description="标签")

    # 内容
    content_text: Optional[str] = Field(None, description="内容正文")
    media_url: Optional[str] = Field(None, description="媒体URL")
    duration: Optional[int] = Field(None, description="时长（秒）")
    word_count: Optional[int] = Field(None, description="字数")

    # 知识点
    knowledge_points: List[str] = Field(default_factory=list, description="知识点列表")

    # 相关词汇
    vocabularies: List[dict] = Field(default_factory=list, description="相关词汇")

    # 学习统计
    view_count: int = Field(default=0, description="阅读次数")
    favorite_count: int = Field(default=0, description="收藏次数")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class CompleteContentRequest(BaseModel):
    """
    标记内容完成请求
    """
    completion_time: int = Field(..., description="完成用时（秒）")
    score: Optional[int] = Field(None, description="得分（如果是练习题）")
    feedback: Optional[str] = Field(None, description="学习反馈")


class CompleteContentResponse(BaseModel):
    """
    标记内容完成响应
    """
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    earned_points: int = Field(default=0, description="获得的学习积分")
    updated_mastery: dict = Field(default_factory=dict, description="更新的知识点掌握度")


class RecommendationFilter(BaseModel):
    """
    推荐过滤条件
    """
    content_types: Optional[List[str]] = Field(None, description="内容类型过滤")
    difficulty_levels: Optional[List[str]] = Field(None, description="难度等级过滤")
    topics: Optional[List[str]] = Field(None, description="主题过滤")
    exam_types: Optional[List[str]] = Field(None, description="考试类型过滤")
    min_score: Optional[float] = Field(None, description="最低推荐分数")
    exclude_completed: bool = Field(default=True, description="排除已完成的内容")
    max_recommendations: int = Field(default=10, description="最大推荐数量")
