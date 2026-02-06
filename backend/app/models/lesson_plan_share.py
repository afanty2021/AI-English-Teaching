"""
教案分享模型 - AI英语教学系统

支持教师间分享教案，包括权限控制、分享状态管理等功能。
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SharePermission(str, Enum):
    """分享权限枚举"""
    VIEW = "view"      # 仅查看
    EDIT = "edit"      # 可编辑
    COPY = "copy"      # 可复制


class ShareStatus(str, Enum):
    """分享状态枚举"""
    PENDING = "pending"    # 待接受
    ACCEPTED = "accepted"  # 已接受
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"    # 已过期


class LessonPlanShare(Base):
    """
    教案分享模型

    记录教师间分享教案的关系，包括分享者、接收者、权限等信息。
    """

    __tablename__ = "lesson_plan_shares"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 关联的教案ID（外键到lesson_plans表）
    lesson_plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lesson_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 分享者ID（外键到users表）
    shared_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    # 接收者ID（外键到users表）
    shared_to: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 分享权限
    permission: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SharePermission.VIEW.value
    )

    # 分享状态
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ShareStatus.PENDING.value,
        index=True
    )

    # 分享附言
    message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 过期时间（可选）
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 关系 - 关联的教案
    lesson_plan: Mapped["LessonPlan"] = relationship(
        "LessonPlan",
        back_populates="shares",
        foreign_keys=[lesson_plan_id]
    )

    # 关系 - 分享者
    sharer: Mapped["User"] = relationship(
        "User",
        back_populates="shares_given",
        foreign_keys=[shared_by]
    )

    # 关系 - 接收者
    recipient: Mapped["User"] = relationship(
        "User",
        back_populates="shares_received",
        foreign_keys=[shared_to]
    )

    def __repr__(self) -> str:
        return f"<LessonPlanShare(id={self.id}, lesson_plan={self.lesson_plan_id}, permission={self.permission}, status={self.status})>"

    def is_expired(self) -> bool:
        """检查分享是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def can_view(self) -> bool:
        """检查是否可以查看"""
        return self.status == ShareStatus.ACCEPTED.value and not self.is_expired()

    def can_edit(self) -> bool:
        """检查是否可以编辑"""
        return (
            self.status == ShareStatus.ACCEPTED.value
            and not self.is_expired()
            and self.permission in [SharePermission.EDIT.value, SharePermission.COPY.value]
        )

    def can_copy(self) -> bool:
        """检查是否可以复制"""
        return (
            self.status == ShareStatus.ACCEPTED.value
            and not self.is_expired()
            and self.permission == SharePermission.COPY.value
        )
