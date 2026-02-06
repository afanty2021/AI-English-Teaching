"""
用户通知偏好设置模型

用户自定义通知行为和频率。
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class NotificationPreference(Base):
    """用户通知偏好设置模型"""

    __tablename__ = "notification_preferences"

    # 主键 - 使用PostgreSQL UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # 关联用户（一对一）
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True
    )

    # 通知类型偏好
    enable_share_notifications: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="是否启用分享通知"
    )
    enable_comment_notifications: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="是否启用评论通知"
    )
    enable_system_notifications: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="是否启用系统通知"
    )

    # 通知方式偏好
    notify_via_websocket: Mapped[bool] = mapped_column(
        nullable=False,
        default=True,
        comment="通过WebSocket实时通知"
    )
    notify_via_email: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        comment="通过邮件通知"
    )

    # 邮件通知频率
    email_frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="immediate",
        comment="邮件通知频率: immediate, hourly, daily, weekly, never"
    )

    # 通知时段（静默时段）
    quiet_hours_start: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="静默开始时间 (HH:MM)"
    )
    quiet_hours_end: Mapped[Optional[str]] = mapped_column(
        String(5),
        nullable=True,
        comment="静默结束时间 (HH:MM)"
    )

    # 创建和更新时间
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<NotificationPreference(user_id={self.user_id})>"
