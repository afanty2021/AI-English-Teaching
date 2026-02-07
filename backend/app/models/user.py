"""
用户模型 - AI英语教学系统
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.async_task import AsyncTask
    from app.models.export_task import ExportTask
    from app.models.lesson_plan import LessonPlan
    from app.models.lesson_plan_share import LessonPlanShare


class UserRole(str, PyEnum):
    """用户角色枚举"""
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    ORGANIZATION_ADMIN = "organization_admin"


class User(Base):
    """
    用户模型
    存储所有用户的基础信息
    """

    __tablename__ = "users"

    # 主键 - 使用PostgreSQL UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 用户名
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    # 邮箱
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    # 密码哈希
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # 用户角色（使用String存储，值为UserRole枚举值）
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=UserRole.STUDENT.value
    )

    # 是否激活
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # 是否为超级管理员
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # 真实姓名
    full_name: Mapped[Optional[str]] = mapped_column(String(100))

    # 电话号码
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    # 头像URL
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255))

    # 扩展信息（JSONB格式）
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 所属组织ID（可选）
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 最后登录时间
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

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

    # 关系 - 所属组织
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="users",
        foreign_keys="User.organization_id"
    )

    # 关系 - 如果该用户是学生
    student_profile: Mapped[Optional["Student"]] = relationship(
        "Student",
        back_populates="user",
        uselist=False,
        foreign_keys="Student.user_id"
    )

    # 关系 - 如果该用户是教师
    teacher_profile: Mapped[Optional["Teacher"]] = relationship(
        "Teacher",
        back_populates="user",
        uselist=False,
        foreign_keys="Teacher.user_id"
    )

    # 关系 - 如果该用户是组织管理员
    organization_profile: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="admin_user",
        uselist=False,
        foreign_keys="Organization.admin_user_id"
    )

    # 关系 - 如果该用户是教师，创建的教案
    lesson_plans: Mapped[list["LessonPlan"]] = relationship(
        "LessonPlan",
        back_populates="teacher",
        foreign_keys="LessonPlan.teacher_id",
        cascade="all, delete-orphan"
    )

    # ==================== 分享相关关系 ====================

    # 关系 - 我给出的教案分享
    shares_given: Mapped[list["LessonPlanShare"]] = relationship(
        "LessonPlanShare",
        back_populates="sharer",
        foreign_keys="LessonPlanShare.shared_by",
        cascade="all, delete-orphan"
    )

    # 关系 - 我收到的教案分享
    shares_received: Mapped[list["LessonPlanShare"]] = relationship(
        "LessonPlanShare",
        back_populates="recipient",
        foreign_keys="LessonPlanShare.shared_to",
        cascade="all, delete-orphan"
    )

    # 关系 - 异步任务
    async_tasks: Mapped[list["AsyncTask"]] = relationship(
        "AsyncTask",
        back_populates="user",
        foreign_keys="AsyncTask.user_id",
        cascade="all, delete-orphan"
    )

    # 关系 - 导出任务
    export_tasks: Mapped[list["ExportTask"]] = relationship(
        "ExportTask",
        back_populates="creator",
        foreign_keys="ExportTask.created_by",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"

    def set_password(self, password: str) -> None:
        """设置密码哈希"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        """验证密码"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, self.password_hash)
