"""
练习会话模型 - AI英语教学系统
记录学生的练习答题进度，支持断点续答
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.question import Question, QuestionBank
    from app.models.practice import Practice


class SessionStatus(str, PyEnum):
    """会话状态枚举"""
    IN_PROGRESS = "in_progress"  # 进行中
    PAUSED = "paused"            # 已暂停
    COMPLETED = "completed"      # 已完成
    ABANDONED = "abandoned"      # 已放弃


class PracticeSession(Base):
    """
    练习会话模型

    记录学生练习的答题进度，支持：
    1. 断点续答（暂停后可继续）
    2. 实时保存答案
    3. 追踪当前题目位置
    4. 完成后生成Practice记录

    与Practice模型的区别：
    - PracticeSession：记录答题过程（进度、当前题目）
    - Practice：记录练习结果（得分、正确率、知识图谱更新）
    """

    __tablename__ = "practice_sessions"

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
        index=True
    )

    # 关联的题库ID（可选，如果是随机练习则无题库）
    question_bank_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_banks.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 练习类型
    practice_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 会话状态
    status: Mapped[str] = mapped_column(
        String(50),
        default=SessionStatus.IN_PROGRESS.value,
        index=True
    )

    # 当前题目索引（0-based）
    current_question_index: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 当前正在作答的题目ID（外键，可选）
    current_question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 题目总数
    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    # 已作答的题目数（冗余字段，便于查询）
    answered_questions: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 正确的题目数（实时更新）
    correct_questions: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 答题记录（JSON格式）
    # 结构：{"question_id": {"answer": "...", "is_correct": true/false, "answered_at": "..."}}
    answers: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 题目ID列表（有序）
    # 结构：["uuid1", "uuid2", ...]
    question_ids: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 开始时间
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 完成时间
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 暂停时间
    paused_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 累计答题时间（秒）
    time_spent: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 最后活跃时间（用于自动暂停检测）
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # 是否已生成Practice记录
    practice_record_created: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    # 生成的Practice记录ID
    practice_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("practices.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 扩展元数据（JSON格式）
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

    # 关系 - 关联的学生
    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="practice_sessions",
        foreign_keys=[student_id]
    )

    # 关系 - 关联的题库
    question_bank: Mapped[Optional["QuestionBank"]] = relationship(
        "QuestionBank",
        back_populates="practice_sessions",
        foreign_keys=[question_bank_id]
    )

    # 关系 - 当前题目
    current_question: Mapped[Optional["Question"]] = relationship(
        "Question",
        foreign_keys=[current_question_id]
    )

    # 关系 - 生成的练习记录
    practice_record: Mapped[Optional["Practice"]] = relationship(
        "Practice",
        foreign_keys=[practice_record_id]
    )

    def __repr__(self) -> str:
        return (
            f"<PracticeSession(id={self.id}, student_id={self.student_id}, "
            f"type={self.practice_type}, status={self.status}, "
            f"progress={self.current_question_index}/{self.total_questions})>"
        )

    @property
    def is_active(self) -> bool:
        """会话是否活跃（进行中或已暂停）"""
        return self.status in [
            SessionStatus.IN_PROGRESS.value,
            SessionStatus.PAUSED.value
        ]

    @property
    def is_completed(self) -> bool:
        """会话是否已完成"""
        return self.status == SessionStatus.COMPLETED.value

    @property
    def is_paused(self) -> bool:
        """会话是否已暂停"""
        return self.status == SessionStatus.PAUSED.value

    @property
    def progress_percentage(self) -> float:
        """获取练习进度百分比"""
        if self.total_questions > 0:
            return (self.answered_questions / self.total_questions) * 100
        return 0.0

    @property
    def current_correct_rate(self) -> float:
        """
        获取当前正确率

        Returns:
            float: 正确率 (0-1)
        """
        if self.answered_questions > 0:
            return self.correct_questions / self.answered_questions
        return 0.0

    @property
    def remaining_questions(self) -> int:
        """剩余题目数"""
        return self.total_questions - self.answered_questions

    @property
    def can_resume(self) -> bool:
        """是否可以恢复（已暂停但未完成）"""
        return self.status == SessionStatus.PAUSED.value

    @property
    def duration_seconds(self) -> Optional[int]:
        """
        获取练习时长（秒）

        Returns:
            Optional[int]: 如果已完成返回实际时长，否则返回None
        """
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None

    @property
    def is_first_question(self) -> bool:
        """是否是第一题"""
        return self.current_question_index == 0

    @property
    def is_last_question(self) -> bool:
        """是否是最后一题"""
        return self.current_question_index >= self.total_questions - 1

    @property
    def current_question_number(self) -> int:
        """当前题号（从1开始）"""
        return self.current_question_index + 1

    @property
    def has_next_question(self) -> bool:
        """是否有下一题"""
        return self.current_question_index < self.total_questions - 1

    @property
    def has_previous_question(self) -> bool:
        """是否有上一题"""
        return self.current_question_index > 0

    def get_answer(self, question_id: uuid.UUID) -> Optional[dict]:
        """
        获取某题的答题记录

        Args:
            question_id: 题目ID

        Returns:
            Optional[dict]: 答题记录，如果未答题则返回None
        """
        question_id_str = str(question_id)
        return self.answers.get(question_id_str)

    def is_question_answered(self, question_id: uuid.UUID) -> bool:
        """
        检查某题是否已作答

        Args:
            question_id: 题目ID

        Returns:
            bool: 是否已作答
        """
        return str(question_id) in self.answers

    def get_question_id_at(self, index: int) -> Optional[uuid.UUID]:
        """
        获取指定索引的题目ID

        Args:
            index: 题目索引

        Returns:
            Optional[uuid.UUID]: 题目ID，如果索引无效则返回None
        """
        if 0 <= index < len(self.question_ids):
            return uuid.UUID(self.question_ids[index])
        return None

    def get_unanswered_question_ids(self) -> list[uuid.UUID]:
        """
        获取所有未作答的题目ID

        Returns:
            list[uuid.UUID]: 未作答的题目ID列表
        """
        answered_ids = set(self.answers.keys())
        unanswered = [
            uuid.UUID(qid) for qid in self.question_ids
            if qid not in answered_ids
        ]
        return unanswered

    def get_answered_question_ids(self) -> list[uuid.UUID]:
        """
        获取所有已作答的题目ID

        Returns:
            list[uuid.UUID]: 已作答的题目ID列表
        """
        return [uuid.UUID(qid) for qid in self.answers.keys()]

    def calculate_current_score(self) -> float:
        """
        计算当前得分（0-100）

        Returns:
            float: 当前得分
        """
        return self.current_correct_rate * 100
