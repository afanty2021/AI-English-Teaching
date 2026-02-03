"""
教案相关的 Pydantic Schemas
定义教案生成请求、响应等数据结构
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==================== 基础模型 ====================

class VocabularyItem(BaseModel):
    """词汇项"""
    word: str = Field(..., description="单词")
    phonetic: Optional[str] = Field(None, description="音标")
    part_of_speech: str = Field(..., description="词性")
    meaning_cn: str = Field(..., description="中文释义")
    meaning_en: Optional[str] = Field(None, description="英文释义")
    example_sentence: str = Field(..., description="例句")
    example_translation: str = Field(..., description="例句翻译")
    collocations: List[str] = Field(default_factory=list, description="常用搭配")
    synonyms: List[str] = Field(default_factory=list, description="同义词")
    antonyms: List[str] = Field(default_factory=list, description="反义词")
    difficulty: str = Field(..., description="难度等级")


class GrammarPoint(BaseModel):
    """语法点"""
    name: str = Field(..., description="语法点名称")
    description: str = Field(..., description="语法描述")
    rule: str = Field(..., description="语法规则")
    examples: List[str] = Field(default_factory=list, description="例句")
    common_mistakes: List[str] = Field(default_factory=list, description="常见错误")
    practice_tips: List[str] = Field(default_factory=list, description="练习建议")


class TeachingStep(BaseModel):
    """教学步骤"""
    phase: str = Field(..., description="阶段名称 (warm-up/presentation/practice/production/homework)")
    title: str = Field(..., description="步骤标题")
    duration: int = Field(..., description="时长（分钟）")
    description: str = Field(..., description="步骤描述")
    activities: List[str] = Field(default_factory=list, description="活动列表")
    teacher_actions: List[str] = Field(default_factory=list, description="教师活动")
    student_actions: List[str] = Field(default_factory=list, description="学生活动")
    materials: List[str] = Field(default_factory=list, description="所需材料")


class LeveledMaterial(BaseModel):
    """分层材料"""
    level: str = Field(..., description="CEFR等级 (A1/A2/B1/B2/C1/C2)")
    title: str = Field(..., description="材料标题")
    content: str = Field(..., description="材料内容")
    word_count: int = Field(..., description="字数")
    vocabulary_list: List[VocabularyItem] = Field(default_factory=list, description="词汇表")
    comprehension_questions: List[str] = Field(default_factory=list, description="理解问题")
    difficulty_notes: str = Field(..., description="难度说明")


class ExerciseItem(BaseModel):
    """练习题"""
    id: str = Field(..., description="题目ID")
    type: str = Field(..., description="题型 (multiple_choice/fill_blank/matching/essay/speaking)")
    question: str = Field(..., description="题目")
    options: Optional[List[str]] = Field(None, description="选项（选择题）")
    correct_answer: str = Field(..., description="正确答案")
    explanation: str = Field(..., description="答案解析")
    points: int = Field(default=1, description="分值")
    difficulty: str = Field(..., description="难度")


class PPTSlide(BaseModel):
    """PPT幻灯片"""
    slide_number: int = Field(..., description="幻灯片编号")
    title: str = Field(..., description="幻灯片标题")
    content: List[str] = Field(default_factory=list, description="内容要点")
    notes: Optional[str] = Field(None, description="演讲者备注")
    layout: str = Field(default="title_content", description="布局类型")


# ==================== 请求模型 ====================

class GenerateLessonPlanRequest(BaseModel):
    """
    生成教案请求
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="教案标题"
    )
    topic: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="教学主题"
    )
    level: str = Field(
        ...,
        description="CEFR等级 (A1/A2/B1/B2/C1/C2)"
    )
    duration: int = Field(
        default=45,
        ge=15,
        le=180,
        description="课程时长（分钟）"
    )
    target_exam: Optional[str] = Field(
        None,
        description="目标考试类型 (IELTS/TOEFL/TOEIC等)"
    )
    student_count: Optional[int] = Field(
        None,
        ge=1,
        description="学生人数"
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="重点关注领域 (listening/speaking/reading/writing/grammar/vocabulary)"
    )
    learning_objectives: Optional[List[str]] = Field(
        None,
        description="自定义学习目标"
    )
    include_leveled_materials: bool = Field(
        default=True,
        description="是否包含分层阅读材料"
    )
    leveled_levels: List[str] = Field(
        default=["A1", "B1", "C1"],
        description="分层材料等级"
    )
    include_exercises: bool = Field(
        default=True,
        description="是否包含练习题"
    )
    exercise_count: int = Field(
        default=10,
        ge=1,
        le=50,
        description="练习题数量"
    )
    exercise_types: List[str] = Field(
        default_factory=lambda: ["multiple_choice", "fill_blank"],
        description="练习题型"
    )
    include_ppt: bool = Field(
        default=True,
        description="是否生成PPT大纲"
    )
    template_id: Optional[uuid.UUID] = Field(
        None,
        description="使用的模板ID"
    )
    additional_requirements: Optional[str] = Field(
        None,
        description="额外要求说明"
    )

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """验证CEFR等级"""
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"无效的CEFR等级，必须是: {', '.join(valid_levels)}")
        return v_upper

    @field_validator("target_exam")
    @classmethod
    def validate_exam(cls, v: Optional[str]) -> Optional[str]:
        """验证考试类型"""
        if v is None:
            return None
        valid_exams = ["IELTS", "TOEFL", "TOEIC", "CET4", "CET6", "GRE", "GMAT", "SAT"]
        v_upper = v.upper()
        if v_upper not in valid_exams:
            raise ValueError(f"无效的考试类型，必须是: {', '.join(valid_exams)}")
        return v_upper


class UpdateLessonPlanRequest(BaseModel):
    """
    更新教案请求
    """
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    topic: Optional[str] = Field(None, min_length=1, max_length=255)
    level: Optional[str] = Field(None)
    duration: Optional[int] = Field(None, ge=15, le=180)
    target_exam: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
    teaching_notes: Optional[str] = Field(None)
    resources: Optional[Dict[str, Any]] = Field(None)


class ExportLessonPlanRequest(BaseModel):
    """
    导出教案请求
    """
    export_format: str = Field(
        ...,
        description="导出格式 (pptx/docx/pdf)"
    )
    include_sections: List[str] = Field(
        default_factory=lambda: [
            "objectives", "vocabulary", "grammar", "structure", "materials", "exercises"
        ],
        description="包含的章节"
    )
    language: str = Field(
        default="zh",
        description="导出语言 (zh/en)"
    )


# ==================== 响应模型 ====================

class TeachingObjectives(BaseModel):
    """教学目标"""
    knowledge: List[str] = Field(default_factory=list, description="知识目标")
    skills: List[str] = Field(default_factory=list, description="技能目标")
    affective: List[str] = Field(default_factory=list, description="情感目标")
    cultural: List[str] = Field(default_factory=list, description="文化目标")


class LessonPlanObjectives(BaseModel):
    """教案教学目标（完整版）"""
    language_knowledge: List[str] = Field(default_factory=list, description="语言知识目标")
    language_skills: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="语言技能目标 (listening/speaking/reading/writing)"
    )
    learning_strategies: List[str] = Field(default_factory=list, description="学习策略")
    cultural_awareness: List[str] = Field(default_factory=list, description="文化意识")
    emotional_attitudes: List[str] = Field(default_factory=list, description="情感态度")


class LessonPlanStructure(BaseModel):
    """教案结构"""
    warm_up: Optional[TeachingStep] = Field(None, description="热身环节")
    presentation: Optional[TeachingStep] = Field(None, description="呈现环节")
    practice: List[TeachingStep] = Field(default_factory=list, description="练习环节")
    production: Optional[TeachingStep] = Field(None, description="产出环节")
    summary: Optional[TeachingStep] = Field(None, description="总结环节")
    homework: Optional[TeachingStep] = Field(None, description="作业环节")


class LessonPlanDetail(BaseModel):
    """教案详情"""
    # 基本信息
    id: uuid.UUID = Field(..., description="教案ID")
    title: str = Field(..., description="教案标题")
    topic: str = Field(..., description="教学主题")
    level: str = Field(..., description="CEFR等级")
    duration: int = Field(..., description="课程时长（分钟）")
    target_exam: Optional[str] = Field(None, description="目标考试")
    status: str = Field(..., description="教案状态")

    # 教学目标
    objectives: LessonPlanObjectives = Field(..., description="教学目标")

    # 核心词汇
    vocabulary: Dict[str, List[VocabularyItem]] = Field(
        default_factory=dict,
        description="核心词汇，按词性分组"
    )

    # 语法点
    grammar_points: List[GrammarPoint] = Field(default_factory=list, description="语法点")

    # 教学流程
    structure: LessonPlanStructure = Field(..., description="教学流程")

    # 分层材料
    leveled_materials: List[LeveledMaterial] = Field(default_factory=list, description="分层材料")

    # 练习题
    exercises: Dict[str, List[ExerciseItem]] = Field(
        default_factory=dict,
        description="练习题，按题型分组"
    )

    # PPT大纲
    ppt_outline: List[PPTSlide] = Field(default_factory=list, description="PPT大纲")

    # 额外资源
    resources: Dict[str, Any] = Field(default_factory=dict, description="额外资源")

    # 教学反思
    teaching_notes: Optional[str] = Field(None, description="教学反思")

    # 元数据
    generation_time_ms: Optional[int] = Field(None, description="生成耗时")
    last_generated_at: Optional[datetime] = Field(None, description="最后生成时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class LessonPlanSummary(BaseModel):
    """教案摘要（列表视图）"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="教案ID")
    title: str = Field(..., description="教案标题")
    topic: str = Field(..., description="教学主题")
    level: str = Field(..., description="CEFR等级")
    duration: int = Field(..., description="课程时长（分钟）")
    target_exam: Optional[str] = Field(None, description="目标考试")
    status: str = Field(..., description="教案状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class LessonPlanResponse(BaseModel):
    """教案响应"""
    lesson_plan: LessonPlanDetail = Field(..., description="教案详情")
    teacher_id: uuid.UUID = Field(..., description="教师ID")


class LessonPlanListResponse(BaseModel):
    """教案列表响应"""
    lesson_plans: List[LessonPlanSummary] = Field(..., description="教案列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页大小")


class LessonPlanExportResponse(BaseModel):
    """教案导出响应"""
    download_url: str = Field(..., description="下载链接")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小（字节）")
    expires_at: datetime = Field(..., description="链接过期时间")


# ==================== 模板相关 ====================

class CreateLessonPlanTemplateRequest(BaseModel):
    """创建教案模板请求"""
    name: str = Field(..., min_length=1, max_length=255, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    level: str = Field(..., description="适用等级")
    target_exam: Optional[str] = Field(None, description="目标考试")
    template_structure: Dict[str, Any] = Field(..., description="模板结构")


class UpdateLessonPlanTemplateRequest(BaseModel):
    """更新教案模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    level: Optional[str] = Field(None)
    target_exam: Optional[str] = Field(None)
    template_structure: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None)


class LessonPlanTemplateResponse(BaseModel):
    """教案模板响应"""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    level: str = Field(..., description="适用等级")
    target_exam: Optional[str] = Field(None, description="目标考试")
    template_structure: Dict[str, Any] = Field(..., description="模板结构")
    is_system: bool = Field(..., description="是否为系统模板")
    usage_count: int = Field(..., description="使用次数")
    is_active: bool = Field(..., description="是否活跃")
    created_by: Optional[uuid.UUID] = Field(None, description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class LessonPlanTemplateListResponse(BaseModel):
    """教案模板列表响应"""
    templates: List[LessonPlanTemplateResponse] = Field(..., description="模板列表")
    total: int = Field(..., description="总数")
