"""
推荐系统相关模型 - AI英语教学系统
存储推荐反馈、历史记录和用户偏好
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RecommendationFeedback(Base):
    """
    推荐反馈模型
    记录用户对推荐内容的反馈，用于优化推荐算法
    """
    __tablename__ = "recommendation_feedback"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 用户ID
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 内容ID
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 反馈类型
    feedback_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="recommendation"
    )

    # 满意度评分 (1-5)
    satisfaction: Mapped[int] = mapped_column(
        Integer,
        nullable=True
    )

    # 反馈原因
    reason: Mapped[Optional[str]] = mapped_column(Text)

    # 是否已读/已处理
    is_processed: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<RecommendationFeedback(id={self.id}, user_id={self.user_id}, content_id={self.content_id})>"


class RecommendationHistory(Base):
    """
    推荐历史模型
    记录推荐内容的展示和完成情况
    """
    __tablename__ = "recommendation_history"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 用户ID
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 内容ID
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 内容类型
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    # 展示时间
    recommended_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 完成时间
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 满意度评分 (1-5)
    satisfaction: Mapped[Optional[int]] = mapped_column(Integer)

    # 反馈
    feedback: Mapped[Optional[str]] = mapped_column(Text)

    # 用时（秒）
    time_spent: Mapped[Optional[int]] = mapped_column(Integer)

    # 是否已删除
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<RecommendationHistory(id={self.id}, user_id={self.user_id}, content_id={self.content_id})>"


class RecommendationPreference(Base):
    """
    推荐偏好模型
    存储用户的个性化推荐偏好设置
    """
    __tablename__ = "recommendation_preferences"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 用户ID
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # 偏好主题
    preferred_topics: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 偏好的内容类型
    preferred_content_types: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 难度偏好
    difficulty_preference: Mapped[Optional[str]] = mapped_column(
        String(20)
    )

    # 每日学习时长偏好（分钟）
    study_time_preference: Mapped[Optional[int]] = mapped_column(Integer)

    # 是否接受所有推荐
    accept_all_recommendations: Mapped[bool] = mapped_column(
        default=True,
        nullable=False
    )

    # 静音时段（JSON格式）
    quiet_hours: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<RecommendationPreference(user_id={self.user_id})>"
