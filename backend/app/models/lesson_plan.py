"""
教案模型 - AI英语教学系统
支持AI生成的完整教案，包括教学目标、词汇、语法、分层材料等
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LessonPlan(Base):
    """
    教案模型
    存储AI生成的完整教案内容
    """

    __tablename__ = "lesson_plans"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 关联的教师ID（外键到users表，角色为teacher）
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 教案基本信息
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    topic: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    # CEFR等级
    level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True
    )

    # 课程时长（分钟）
    duration: Mapped[int] = mapped_column(
        nullable=False,
        default=45
    )

    # 目标考试类型
    target_exam: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # 教案状态
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True
    )

    # AI生成参数
    ai_generation_params: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 教学目标
    objectives: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 核心词汇
    vocabulary: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 语法点
    grammar_points: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 教学流程
    teaching_structure: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 分层阅读材料
    leveled_materials: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 练习题
    exercises: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # PPT大纲
    ppt_outline: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 额外资源和素材
    resources: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 教学反思
    teaching_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # AI生成耗时（毫秒）
    generation_time_ms: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )

    # 最后生成时间
    last_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # ==================== 分享相关字段 ====================

    # 是否已分享给其他教师
    is_shared: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        index=True
    )

    # 是否公开（所有教师可见）
    is_public: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    # 分享计数
    share_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    # 分支来源（基于哪个教案复制）
    forked_from: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # 分支计数（被复制次数）
    fork_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    # ==================== 时间戳 ====================

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ==================== 关系 ====================

    # 关系 - 关联的教师
    teacher: Mapped["User"] = relationship(
        "User",
        back_populates="lesson_plans",
        foreign_keys=[teacher_id]
    )

    # 关系 - 分享记录
    shares: Mapped[list["LessonPlanShare"]] = relationship(
        "LessonPlanShare",
        back_populates="lesson_plan",
        foreign_keys="LessonPlanShare.lesson_plan_id",
        cascade="all, delete-orphan"
    )

    # 关系 - 分支来源教案（自引用）
    original_plan: Mapped[Optional["LessonPlan"]] = relationship(
        "LessonPlan",
        remote_side=[id],
        foreign_keys=[forked_from],
        back_populates="forked_plans"
    )

    # 关系 - 分支出的教案
    forked_plans: Mapped[list["LessonPlan"]] = relationship(
        "LessonPlan",
        remote_side=[forked_from],
        foreign_keys=[forked_from],
        back_populates="original_plan"
    )

    def __repr__(self) -> str:
        return f"<LessonPlan(id={self.id}, title={self.title}, level={self.level}, topic={self.topic})>"


class LessonPlanTemplate(Base):
    """
    教案模板模型
    存储可复用的教案模板
    """

    __tablename__ = "lesson_plan_templates"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 模板名称
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # 模板描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 适用等级
    level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True
    )

    # 目标考试
    target_exam: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # 模板结构
    template_structure: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    # 是否为系统模板
    is_system: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    # 使用次数
    usage_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    # 是否活跃
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True
    )

    # 创建者ID（系统模板为null）
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<LessonPlanTemplate(id={self.id}, name={self.name}, level={self.level})>"
