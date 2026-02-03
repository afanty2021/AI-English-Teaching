"""
知识图谱模型 - AI英语教学系统
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class KnowledgeGraph(Base):
    """
    知识图谱模型
    存储学生的个性化学习知识图谱
    """

    __tablename__ = "knowledge_graphs"

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
        unique=True,
        index=True
    )

    # 图数据
    nodes: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=list
    )

    edges: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=list
    )

    # 能力概览
    abilities: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # CEFR等级
    cefr_level: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True
    )

    # 考试覆盖度
    exam_coverage: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # AI分析结果
    ai_analysis: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        default=dict
    )

    # 最后AI分析时间
    last_ai_analysis_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
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

    # 关系 - 关联的学生
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="knowledge_graph",
        foreign_keys=[student_id]
    )

    def __repr__(self) -> str:
        return f"<KnowledgeGraph(id={self.id}, student_id={self.student_id}, cefr_level={self.cefr_level})>"
