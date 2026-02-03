"""
组织模型 - AI英语教学系统
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.class_model import ClassInfo


class OrganizationType(str, PyEnum):
    """组织类型枚举"""
    SCHOOL = "school"
    TRAINING_CENTER = "training_center"
    INDIVIDUAL = "individual"


class Organization(Base):
    """
    组织模型
    表示教育培训机构、学校或其他组织
    """

    __tablename__ = "organizations"

    # 主键 - 使用PostgreSQL UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 组织名称
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    # 组织类型（使用String存储）
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=OrganizationType.INDIVIDUAL.value
    )

    # 设置（JSONB格式）
    settings: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 管理员用户ID
    admin_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True
    )

    # 是否激活
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
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

    # 关系 - 管理员用户
    admin_user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="organization_profile",
        foreign_keys="Organization.admin_user_id"
    )

    # 关系 - 该组织下的用户
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization",
        foreign_keys="User.organization_id"
    )

    # 关系 - 该组织下的教师
    teachers: Mapped[list["Teacher"]] = relationship(
        "Teacher",
        back_populates="organization",
        foreign_keys="Teacher.organization_id"
    )

    # 关系 - 该组织下的学生
    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="organization",
        foreign_keys="Student.organization_id"
    )

    # 关系 - 该组织下的班级
    classes: Mapped[list["ClassInfo"]] = relationship(
        "ClassInfo",
        back_populates="organization",
        foreign_keys="ClassInfo.organization_id"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, type={self.type})>"
