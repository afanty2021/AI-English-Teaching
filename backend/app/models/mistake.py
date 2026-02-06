"""
错题本模型 - AI英语教学系统
记录学生在练习中的错误题目，支持错题复习和巩固
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.content import Content
    from app.models.practice import Practice


class MistakeStatus(str, PyEnum):
    """错题状态枚举"""
    PENDING = "pending"           # 待复习
    REVIEWING = "reviewing"       # 复习中
    MASTERED = "mastered"         # 已掌握
    IGNORED = "ignored"           # 已忽略


class MistakeType(str, PyEnum):
    """错题类型枚举"""
    GRAMMAR = "grammar"           # 语法错误
    VOCABULARY = "vocabulary"     # 词汇错误
    READING = "reading"           # 阅读理解错误
    LISTENING = "listening"       # 听力错误
    WRITING = "writing"           # 写作错误
    SPEAKING = "speaking"         # 口语错误
    PRONUNCIATION = "pronunciation"  # 发音错误
    COMPREHENSION = "comprehension"  # 理解错误


class Mistake(Base):
    """
    错题本模型

    记录学生在练习中的错误题目，支持以下功能：
    1. 自动收集错题（从练习记录中提取）
    2. 按知识点分类整理
    3. AI生成解析和建议
    4. 支持错题重做
    5. 追踪掌握程度
    """

    __tablename__ = "mistakes"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 关联的学生ID
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 关联的练习记录ID（可选，用于追溯）
    practice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practices.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 关联的内容ID（可选）
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 错题类型
    mistake_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 错题状态
    status: Mapped[str] = mapped_column(
        String(50),
        default=MistakeStatus.PENDING.value,
        index=True
    )

    # 题目内容
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # 学生错误答案
    wrong_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # 正确答案
    correct_answer: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # 错题解析（AI生成或教师添加）
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    # 知识点标签（JSON数组）
    knowledge_points: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 难度等级
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # 主题分类
    topic: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True  # 按知识点分类查询常用
    )

    # 错误次数
    mistake_count: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    # 复习次数
    review_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 最后复习时间
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # AI生成的学习建议
    ai_suggestion: Mapped[Optional[str]] = mapped_column(Text)

    # 是否需要AI深度分析
    needs_ai_analysis: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    # AI分析结果（JSON格式）
    ai_analysis: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 扩展元数据（JSON格式，存储题目选项、上下文等）
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 首次错误时间
    first_mistaken_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 最后更新时间
    last_mistaken_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
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

    # 关系 - 关联的学生
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="mistakes",
        foreign_keys=[student_id]
    )

    # 关系 - 关联的练习记录
    practice: Mapped[Optional["Practice"]] = relationship(
        "Practice",
        foreign_keys=[practice_id]
    )

    # 关系 - 关联的内容
    content: Mapped[Optional["Content"]] = relationship(
        "Content",
        foreign_keys=[content_id]
    )

    def __repr__(self) -> str:
        return (
            f"<Mistake(id={self.id}, student_id={self.student_id}, "
            f"type={self.mistake_type}, status={self.status}, "
            f"mistake_count={self.mistake_count})>"
        )

    @property
    def needs_review(self) -> bool:
        """是否需要复习（状态为待复习或复习中）"""
        return self.status in [
            MistakeStatus.PENDING.value,
            MistakeStatus.REVIEWING.value
        ]

    @property
    def is_mastered(self) -> bool:
        """是否已掌握"""
        return self.status == MistakeStatus.MASTERED.value

    @property
    def mastery_level(self) -> float:
        """
        掌握程度 (0-1)

        基于以下因素计算：
        - 复习次数
        - 错误次数趋势
        - 当前状态
        """
        if self.is_mastered:
            return 1.0

        # 基础分数：复习次数贡献
        base_score = min(self.review_count * 0.2, 0.6)

        # 状态加成
        if self.status == MistakeStatus.REVIEWING.value:
            base_score += 0.2

        return min(base_score, 1.0)
