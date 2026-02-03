"""
教师模型 - AI英语教学系统
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.class_model import ClassInfo


class Teacher(Base):
    """
    教师模型
    扩展用户信息，添加教师特定字段
    """

    __tablename__ = "teachers"

    # 主键 - 使用PostgreSQL UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 关联的用户ID（外键到users表）
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    # 专业领域（如reading, writing, speaking, grammar等）
    specialization: Mapped[Optional[list]] = mapped_column(
        ARRAY(String(100)),
        nullable=True
    )

    # 资格信息（JSON格式）
    qualification: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 个人简介
    bio: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 所属组织ID（外键到organizations表）
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
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

    # 关系 - 关联的用户
    user: Mapped["User"] = relationship(
        "User",
        back_populates="teacher_profile",
        foreign_keys=[user_id]
    )

    # 关系 - 所属组织
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="teachers",
        foreign_keys="Teacher.organization_id"
    )

    # 关系 - 教授的班级（作为主教师）
    taught_classes: Mapped[list["ClassInfo"]] = relationship(
        "ClassInfo",
        back_populates="head_teacher",
        foreign_keys="ClassInfo.head_teacher_id"
    )

    def __repr__(self) -> str:
        return f"<Teacher(id={self.id}, user_id={self.user_id})>"
