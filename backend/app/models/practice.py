"""
练习记录模型 - AI英语教学系统
记录学生完成练习的详细数据
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.content import Content


class PracticeStatus(str, PyEnum):
    """练习状态枚举"""
    IN_PROGRESS = "in_progress"   # 进行中
    COMPLETED = "completed"       # 已完成
    SKIPPED = "skipped"           # 已跳过
    EXPIRED = "expired"           # 已过期


class PracticeType(str, PyEnum):
    """练习类型枚举"""
    READING = "reading"           # 阅读练习
    LISTENING = "listening"       # 听力练习
    WRITING = "writing"           # 写作练习
    SPEAKING = "speaking"         # 口语练习
    GRAMMAR = "grammar"           # 语法练习
    VOCABULARY = "vocabulary"     # 词汇练习
    COMPREHENSIVE = "comprehensive"  # 综合练习


class Practice(Base):
    """
    练习记录模型
    记录学生完成练习的详细数据，用于追踪学习进度和更新知识图谱
    """

    __tablename__ = "practices"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 关联的学生ID（外键到students表）
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 关联的内容ID（外键到contents表，可选）
    content_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 练习类型（使用String存储）
    practice_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 练习状态（使用String存储）
    status: Mapped[str] = mapped_column(
        String(50),
        default=PracticeStatus.IN_PROGRESS,
        index=True
    )

    # 题目数量
    total_questions: Mapped[Optional[int]] = mapped_column(Integer)

    # 已完成题目数
    completed_questions: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 正确题目数
    correct_questions: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 得分（0-100）
    score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )

    # 正确率（0-1）
    correct_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )

    # 难度等级
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # 主题分类
    topic: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    # 耗时（秒）
    time_spent: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 开始时间
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 完成时间
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 答案详情（JSON格式）
    answers: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 练习结果详情（JSON格式）
    result_details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 知识图谱更新记录（JSON格式）
    graph_update: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 是否已更新知识图谱
    graph_updated: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    # 扩展元数据（JSON格式）
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
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
        back_populates="practices",
        foreign_keys=[student_id]
    )

    # 关系 - 关联的内容
    content: Mapped[Optional["Content"]] = relationship(
        "Content",
        back_populates="practices",
        foreign_keys=[content_id]
    )

    def __repr__(self) -> str:
        return (
            f"<Practice(id={self.id}, student_id={self.student_id}, "
            f"type={self.practice_type}, status={self.status}, "
            f"score={self.score})>"
        )

    @property
    def progress_percentage(self) -> float:
        """获取练习进度百分比"""
        if self.total_questions and self.total_questions > 0:
            return (self.completed_questions / self.total_questions) * 100
        return 0.0

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == PracticeStatus.COMPLETED

    @property
    def duration_seconds(self) -> Optional[int]:
        """获取练习时长（秒）"""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
