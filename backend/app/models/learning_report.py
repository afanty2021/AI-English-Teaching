"""
学习报告模型 - AI英语教学系统
用于存储学生的学习报告快照和统计数据
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.student import Student


class LearningReport(Base):
    """
    学习报告模型
    存储学生的学习报告快照，包括统计数据、能力分析、错题分析等
    """

    __tablename__ = "learning_reports"

    # 主键 - 使用PostgreSQL UUID
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

    # 报告类型 (weekly, monthly, custom)
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 时间范围
    period_start: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )

    period_end: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True
    )

    # 统计数据快照 (JSON)
    # 包含: 总练习次数、总时长、平均正确率等
    statistics: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # 能力分析快照 (JSON)
    # 包含: 各项能力值、能力雷达图数据、趋势分析
    ability_analysis: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # 薄弱点分析 (JSON)
    # 包含: 薄弱知识点列表、高频错误类型、需要重点关注的内容
    weak_points: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # 学习建议 (JSON)
    # 包含: AI生成的学习建议、改进方向、推荐内容
    recommendations: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # 报告状态 (draft, completed, archived)
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False
    )

    # AI分析结果 (JSON)
    # 包含: AI生成的深度分析、个性化建议
    ai_insights: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # 报告标题（可选，用于显示）
    title: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    # 报告描述（可选）
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # 关系 - 关联的学生
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="learning_reports",
        foreign_keys=[student_id]
    )

    def __repr__(self) -> str:
        return f"<LearningReport(id={self.id}, student_id={self.student_id}, type={self.report_type})>"
