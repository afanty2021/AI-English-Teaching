"""
知识图谱相关的Pydantic Schemas
定义知识图谱查询、诊断、更新等API请求和响应数据结构
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeGraphNode(BaseModel):
    """知识图谱节点"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="节点ID")
    type: str = Field(..., description="节点类型：vocabulary/grammar/reading/listening/speaking/writing")
    name: str = Field(..., description="节点名称")
    level: str = Field(..., description="难度等级：A1/A2/B1/B2/C1/C2")
    score: float = Field(..., ge=0, le=1, description="掌握程度：0-1")
    status: str = Field(default="learning", description="状态：mastered/learning/needs_practice")
    parent_nodes: List[str] = Field(default_factory=list, description="前置知识点")
    child_nodes: List[str] = Field(default_factory=list, description="后续知识点")


class KnowledgeGraphEdge(BaseModel):
    """知识图谱边"""
    model_config = ConfigDict(from_attributes=True)

    source: str = Field(..., description="源节点ID")
    target: str = Field(..., description="目标节点ID")
    relationship: str = Field(..., description="关系类型：prerequisite/similar/progress")
    strength: float = Field(default=0.5, ge=0, le=1, description="关系强度")


class KnowledgeGraphResponse(BaseModel):
    """知识图谱响应"""
    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID = Field(..., description="学生ID")
    nodes: List[KnowledgeGraphNode] = Field(..., description="知识节点列表")
    edges: List[KnowledgeGraphEdge] = Field(..., description="知识边列表")
    abilities: Dict[str, Any] = Field(..., description="能力评估")
    cefr_level: Optional[str] = Field(None, description="CEFR等级")
    exam_coverage: Dict[str, Any] = Field(default_factory=dict, description="考试覆盖度")
    ai_analysis: Dict[str, Any] = Field(default_factory=dict, description="AI分析结果")
    last_ai_analysis_at: Optional[datetime] = Field(None, description="最后AI分析时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class DiagnoseRequest(BaseModel):
    """学生诊断请求"""
    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID = Field(..., description="学生ID")
    practice_data: List[Dict[str, Any]] = Field(..., description="练习数据列表")
    force_reanalyze: bool = Field(default=False, description="是否强制重新分析")


class DiagnoseResponse(BaseModel):
    """学生诊断响应"""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="诊断是否成功")
    graph_id: Optional[uuid.UUID] = Field(None, description="知识图谱ID")
    cefr_level: Optional[str] = Field(None, description="CEFR等级")
    abilities: Dict[str, Any] = Field(default_factory=dict, description="能力评估")
    weak_points: List[str] = Field(default_factory=list, description="薄弱点列表")
    recommendations: List[str] = Field(default_factory=list, description="学习建议")
    analysis_summary: str = Field(..., description="分析总结")
    is_cached: bool = Field(default=False, description="是否使用缓存结果")


class UpdateKnowledgeGraphRequest(BaseModel):
    """更新知识图谱请求"""
    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID = Field(..., description="学生ID")
    practice_results: List[Dict[str, Any]] = Field(..., description="练习结果")


class UpdateKnowledgeGraphResponse(BaseModel):
    """更新知识图谱响应"""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="更新是否成功")
    updated_abilities: Dict[str, Any] = Field(default_factory=dict, description="更新的能力值")
    new_weak_points: List[str] = Field(default_factory=list, description="新识别的薄弱点")
    progress_summary: str = Field(..., description="进步总结")


class StudentAbility(BaseModel):
    """学生能力"""
    model_config = ConfigDict(from_attributes=True)

    vocabulary: float = Field(..., ge=0, le=1, description="词汇能力：0-1")
    grammar: float = Field(..., ge=0, le=1, description="语法能力：0-1")
    reading: float = Field(..., ge=0, le=1, description="阅读能力：0-1")
    listening: float = Field(..., ge=0, le=1, description="听力能力：0-1")
    speaking: float = Field(..., ge=0, le=1, description="口语能力：0-1")
    writing: float = Field(..., ge=0, le=1, description="写作能力：0-1")


class WeakPoint(BaseModel):
    """薄弱点"""
    model_config = ConfigDict(from_attributes=True)

    point: str = Field(..., description="知识点名称")
    type: str = Field(..., description="类型：vocabulary/grammar/skill")
    severity: float = Field(..., ge=0, le=1, description="严重程度：0-1")
    affected_areas: List[str] = Field(default_factory=list, description="影响的领域")
    recommendations: List[str] = Field(default_factory=list, description="改进建议")


class LearningRecommendation(BaseModel):
    """学习建议"""
    model_config = ConfigDict(from_attributes=True)

    category: str = Field(..., description="建议类别：vocabulary/grammar/reading/listening/speaking/writing")
    priority: str = Field(..., description="优先级：high/medium/low")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议描述")
    estimated_time: int = Field(..., description="预计时间（分钟）")
    resources: List[str] = Field(default_factory=list, description="推荐资源")


class KnowledgeGraphStats(BaseModel):
    """知识图谱统计"""
    model_config = ConfigDict(from_attributes=True)

    total_nodes: int = Field(..., description="总节点数")
    mastered_nodes: int = Field(..., description="已掌握节点数")
    learning_nodes: int = Field(..., description="学习中节点数")
    needs_practice_nodes: int = Field(..., description="需要练习节点数")
    coverage_rate: float = Field(..., ge=0, le=1, description="覆盖率")
    avg_score: float = Field(..., ge=0, le=1, description="平均得分")
    strongest_ability: str = Field(..., description="最强能力")
    weakest_ability: str = Field(..., description="最弱能力")
