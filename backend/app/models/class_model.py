"""
班级模型 - AI英语教学系统
实现教师与班级、学生与班级的关联管理
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.student import Student
    from app.models.teacher import Teacher
    from app.models.organization import Organization


class ClassInfo(Base):
    """
    班级模型
    实现教师-班级-学生的多对多关联
    """

    __tablename__ = "classes"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 班级名称
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    # 班级代码（唯一标识）
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    # 班级描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 年级
    grade: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # 学期
    semester: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # 所属组织ID
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 主教师ID（班主任）
    head_teacher_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 辅导教师ID列表（可能有多个）
    assistant_teacher_ids: Mapped[Optional[list]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=True
    )

    # 学生人数上限
    max_students: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    # 当前学生人数
    current_student_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 班级状态
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",  # active, archived, suspended
        index=True
    )

    # 开课日期
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 结课日期
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 扩展元数据（JSONB格式）
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

    # 关系 - 所属组织
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="classes",
        foreign_keys="ClassInfo.organization_id"
    )

    # 关系 - 主教师
    head_teacher: Mapped[Optional["Teacher"]] = relationship(
        "Teacher",
        foreign_keys="ClassInfo.head_teacher_id"
    )

    # 关系 - 班级学生关联
    class_students: Mapped[list["ClassStudent"]] = relationship(
        "ClassStudent",
        back_populates="class_info",
        foreign_keys="ClassStudent.class_id",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ClassInfo(id={self.id}, name={self.name}, code={self.code})>"


class ClassStudent(Base):
    """
    班级学生关联表
    记录学生加入班级的时间和状态
    """

    __tablename__ = "class_students"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # 班级ID
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 学生ID
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 入学状态
    enrollment_status: Mapped[str] = mapped_column(
        String(50),
        default="active",  # active, transferred, graduated
        index=True
    )

    # 入学日期
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # 毕业日期
    graduated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 备注
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # 关系 - 班级
    class_info: Mapped["ClassInfo"] = relationship(
        "ClassInfo",
        back_populates="class_students"
    )

    # 关系 - 学生
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="class_enrollments"
    )

    def __repr__(self) -> str:
        return f"<ClassStudent(class_id={self.class_id}, student_id={self.student_id})>"
