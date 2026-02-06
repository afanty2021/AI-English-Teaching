"""
学生模型 - AI英语教学系统
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation
    from app.models.practice import Practice
    from app.models.class_model import ClassStudent
    from app.models.mistake import Mistake
    from app.models.learning_report import LearningReport
    from app.models.practice_session import PracticeSession


class Student(Base):
    """
    学生模型
    扩展用户信息，添加学生特定字段
    包含AI英语教学系统所需的学习目标和考试目标字段
    """

    __tablename__ = "students"

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

    # 学号
    student_no: Mapped[Optional[str]] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
        index=True
    )

    # 年级
    grade: Mapped[Optional[str]] = mapped_column(String(50))

    # 班级ID
    class_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True
    )

    # 家长ID列表（可能有多个家长）
    parent_ids: Mapped[Optional[list]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=True
    )

    # === AI英语教学系统特有字段 ===

    # 目标考试类型（CET4, CET6, IELTS, TOEFL, GAOKAO等）
    target_exam: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True  # 按目标考试筛选学生常用
    )

    # 目标分数
    target_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    # 学习目标描述
    study_goal: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 当前CEFR等级（由知识图谱诊断得出）
    current_cefr_level: Mapped[Optional[str]] = mapped_column(
        String(10),
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
        back_populates="student_profile",
        foreign_keys=[user_id]
    )

    # 关系 - 所属组织
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        back_populates="students",
        foreign_keys="Student.organization_id"
    )

    # 关系 - 知识图谱
    knowledge_graph: Mapped[Optional["KnowledgeGraph"]] = relationship(
        "KnowledgeGraph",
        back_populates="student",
        uselist=False,
        foreign_keys="KnowledgeGraph.student_id"
    )

    # 关系 - AI口语对话会话
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="student",
        foreign_keys="Conversation.student_id",
        cascade="all, delete-orphan"
    )

    # 关系 - 练习记录
    practices: Mapped[list["Practice"]] = relationship(
        "Practice",
        back_populates="student",
        foreign_keys="Practice.student_id",
        cascade="all, delete-orphan",
        order_by="desc(Practice.created_at)"
    )

    # 关系 - 班级入学记录
    class_enrollments: Mapped[list["ClassStudent"]] = relationship(
        "ClassStudent",
        back_populates="student",
        foreign_keys="ClassStudent.student_id",
        cascade="all, delete-orphan"
    )

    # 关系 - 错题本
    mistakes: Mapped[list["Mistake"]] = relationship(
        "Mistake",
        back_populates="student",
        foreign_keys="Mistake.student_id",
        cascade="all, delete-orphan",
        order_by="desc(Mistake.last_mistaken_at)"
    )

    # 关系 - 学习报告
    learning_reports: Mapped[list["LearningReport"]] = relationship(
        "LearningReport",
        back_populates="student",
        foreign_keys="LearningReport.student_id",
        cascade="all, delete-orphan",
        order_by="desc(LearningReport.created_at)"
    )

    # 关系 - 练习会话（答题进度）
    practice_sessions: Mapped[list["PracticeSession"]] = relationship(
        "PracticeSession",
        back_populates="student",
        foreign_keys="PracticeSession.student_id",
        cascade="all, delete-orphan",
        order_by="desc(PracticeSession.created_at)"
    )

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_no={self.student_no}, target_exam={self.target_exam})>"

    @property
    def level(self) -> Optional[str]:
        """获取当前CEFR等级（提供level属性访问以兼容性）"""
        return self.current_cefr_level

    @property
    def learning_goals(self) -> list:
        """获取学习目标（提供learning_goals属性访问以兼容性）"""
        # 可以从study_goal解析或返回默认值
        if self.study_goal:
            return [self.study_goal]
        return []

    @property
    def interests(self) -> list:
        """获取兴趣（提供interests属性访问以兼容性）"""
        # 返回默认值或从其他字段解析
        return []
