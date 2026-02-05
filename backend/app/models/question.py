"""
题目模型 - AI英语教学系统
定义题目、题库的数据结构
"""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.practice_session import PracticeSession


class QuestionType(str, PyEnum):
    """题目类型枚举"""
    CHOICE = "choice"                              # 选择题
    FILL_BLANK = "fill_blank"                      # 填空题
    READING_COMPREHENSION = "reading_comprehension"  # 阅读理解
    WRITING = "writing"                            # 写作题
    SPEAKING = "speaking"                          # 口语题
    LISTENING = "listening"                        # 听力题
    TRANSLATION = "translation"                    # 翻译题


class CEFRLevel(str, PyEnum):
    """
    CEFR 难度等级枚举

    CEFR（欧洲语言共同参考框架）是国际通用的语言等级标准：
    - A 级：基础使用者（Basic User）
    - B 级：独立使用者（Independent User）
    - C 级：熟练使用者（Proficient User）
    """
    A1 = "A1"  # 初级入门 - Breakthrough
    A2 = "A2"  # 初级进阶 - Waystage
    B1 = "B1"  # 中级入门 - Threshold
    B2 = "B2"  # 中级进阶 - Vantage
    C1 = "C1"  # 高级入门 - Effective Operational Proficiency
    C2 = "C2"  # 高级精通 - Mastery


class Question(Base):
    """
    题目模型

    支持以下功能：
    1. 多种题型（选择、填空、阅读理解等）
    2. 难度等级标识（CEFR标准）
    3. 知识点标签
    4. 题目解析
    5. 组织到题库中
    """

    __tablename__ = "questions"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 题目类型
    question_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 题目内容
    content_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # 难度等级（CEFR标准：A1-C2）
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        index=True
    )

    # 主题分类（如：weather, shopping, grammar等）
    topic: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    # 知识点标签（JSON数组，如：["present tense", "vocabulary"]）
    knowledge_points: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 选项（JSON数组，仅选择题使用）
    # 格式：[{"id": "A", "text": "选项内容"}, ...]
    options: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 正确答案
    # - 选择题：选项ID，如 "A" 或 ["A", "B"]（多选）
    # - 填空题：答案字符串或数组（多个空）
    # - 阅读理解：JSON对象，如 {"1": "A", "2": "B"}
    correct_answer: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 题目解析
    explanation: Mapped[Optional[str]] = mapped_column(Text)

    # 所属题库ID（外键）
    question_bank_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_banks.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # 创建者ID（外键到users表）
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True
    )

    # 是否启用
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True
    )

    # 在题库中的排序序号
    order_index: Mapped[Optional[int]] = mapped_column(Integer)

    # 阅读理解题目的文章内容（仅阅读理解题型）
    passage_content: Mapped[Optional[str]] = mapped_column(Text)

    # 听力题目的音频URL（仅听力题型）
    audio_url: Mapped[Optional[str]] = mapped_column(String(500))

    # 口语题目的参考答案示例
    sample_answer: Mapped[Optional[str]] = mapped_column(Text)

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

    # 关系 - 创建者
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by]
    )

    # 关系 - 所属题库
    question_bank: Mapped["QuestionBank"] = relationship(
        "QuestionBank",
        back_populates="questions",
        foreign_keys=[question_bank_id]
    )

    # 关系 - 练习会话中的题目记录
    session_questions: Mapped[list["PracticeSession"]] = relationship(
        "PracticeSession",
        foreign_keys="PracticeSession.current_question_id",
        back_populates="current_question"
    )

    def __repr__(self) -> str:
        return (
            f"<Question(id={self.id}, type={self.question_type}, "
            f"difficulty={self.difficulty_level}, topic={self.topic})>"
        )

    @property
    def is_choice_question(self) -> bool:
        """是否为选择题"""
        return self.question_type == QuestionType.CHOICE.value

    @property
    def is_fill_blank_question(self) -> bool:
        """是否为填空题"""
        return self.question_type == QuestionType.FILL_BLANK.value

    @property
    def is_reading_comprehension(self) -> bool:
        """是否为阅读理解题"""
        return self.question_type == QuestionType.READING_COMPREHENSION.value

    @property
    def has_audio(self) -> bool:
        """是否包含音频"""
        return bool(self.audio_url)

    @property
    def answer_type(self) -> str:
        """
        答案类型

        Returns:
            str: "single" (单选), "multiple" (多选), "text" (文本), "complex" (复杂)
        """
        if self.is_choice_question:
            # 检查是否是多选
            if isinstance(self.correct_answer, list):
                return "multiple"
            return "single"
        elif self.is_reading_comprehension:
            return "complex"
        return "text"


class QuestionBank(Base):
    """
    题库模型

    题库是题目的组织单位，教师可以：
    1. 创建题库（按类型、难度、主题分类）
    2. 向题库添加题目
    3. 设置题库为公开/私有
    4. 将题库分配给学生练习
    """

    __tablename__ = "question_banks"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 题库名称
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    # 题库描述
    description: Mapped[Optional[str]] = mapped_column(Text)

    # 练习类型（与PracticeType对应）
    practice_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 主要难度等级
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        index=True
    )

    # 标签（JSON数组）
    tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 创建者ID（外键到users表）
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 是否公开（其他教师可见/可复用）
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True
    )

    # 题目数量（冗余字段，便于查询）
    question_count: Mapped[int] = mapped_column(
        Integer,
        default=0
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

    # 关系 - 创建者
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by]
    )

    # 关系 - 题库中的题目
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="question_bank",
        foreign_keys="Question.question_bank_id",
        order_by="Question.order_index",
        cascade="all, delete-orphan"
    )

    # 关系 - 使用此题库的练习会话
    practice_sessions: Mapped[list["PracticeSession"]] = relationship(
        "PracticeSession",
        back_populates="question_bank",
        foreign_keys="PracticeSession.question_bank_id"
    )

    def __repr__(self) -> str:
        return (
            f"<QuestionBank(id={self.id}, name={self.name}, "
            f"type={self.practice_type}, questions={self.question_count})>"
        )

    @property
    def is_empty(self) -> bool:
        """题库是否为空"""
        return self.question_count == 0

    @property
    def question_levels(self) -> list:
        """题库包含的难度等级列表"""
        levels = set(q.difficulty_level for q in self.questions if q.difficulty_level)
        return sorted(list(levels))
