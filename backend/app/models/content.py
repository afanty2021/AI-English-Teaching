"""
内容模型 - AI英语教学系统
管理阅读、听力、视频等学习内容
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
    from app.models.practice import Practice


class ContentType(str, PyEnum):
    """内容类型枚举"""
    READING = "reading"       # 阅读材料
    LISTENING = "listening"   # 听力材料
    VIDEO = "video"           # 视频材料
    GRAMMAR = "grammar"       # 语法讲解
    VOCABULARY = "vocabulary" # 词汇学习
    WRITING = "writing"       # 写作指导


class DifficultyLevel(str, PyEnum):
    """难度等级枚举"""
    BEGINNER = "beginner"     # 初级
    ELEMENTARY = "elementary" # 基础
    INTERMEDIATE = "intermediate"  # 中级
    UPPER_INTERMEDIATE = "upper_intermediate"  # 中高级
    ADVANCED = "advanced"     # 高级
    PROFICIENT = "proficient" # 精通


class ExamType(str, PyEnum):
    """考试类型枚举"""
    IELTS = "ielts"           # 雅思
    TOEFL = "toefl"           # 托福
    CET4 = "cet4"             # 大学英语四级
    CET6 = "cet6"             # 大学英语六级
    GRE = "gre"               # GRE
    GMAT = "gmat"             # GMAT
    TOEIC = "toeic"           # 托业
    GENERAL = "general"       # 通用英语


class Content(Base):
    """
    内容模型
    存储阅读、听力、视频等学习内容
    """

    __tablename__ = "contents"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 内容标题
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    # 内容描述
    description: Mapped[Optional[str]] = mapped_column(Text)

    # 内容类型（使用String存储）
    content_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 难度等级（使用String存储）
    difficulty_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 考试类型（可为空，通用内容不限定考试，使用String存储）
    exam_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True
    )

    # 主题分类（如：科技、环境、教育等）
    topic: Mapped[Optional[str]] = mapped_column(
        String(100),
        index=True
    )

    # 标签（JSON数组）
    tags: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 内容正文/文本
    content_text: Mapped[Optional[str]] = mapped_column(Text)

    # 媒体URL（音频/视频链接）
    media_url: Mapped[Optional[str]] = mapped_column(String(500))

    # 媒体时长（秒）
    duration: Mapped[Optional[int]] = mapped_column(Integer)

    # 字数统计
    word_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Qdrant向量ID（用于关联向量搜索）
    vector_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
        index=True
    )

    # 向量嵌入文本（用于生成向量）
    embedding_text: Mapped[Optional[str]] = mapped_column(Text)

    # 知识点列表（JSON数组）
    knowledge_points: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 扩展元数据（JSONB格式）
    extra_metadata: Mapped[Optional[dict]] = mapped_column(
        JSON,
        default=dict
    )

    # 是否发布
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True
    )

    # 是否为精选内容
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True
    )

    # 排序权重
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 阅读次数
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 收藏次数
    favorite_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    # 创建者ID（可选）
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
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
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关系 - 内容词汇关联
    vocabularies: Mapped[list["Vocabulary"]] = relationship(
        "Vocabulary",
        secondary="content_vocabulary",
        back_populates="contents",
        lazy="selectin"
    )

    # 关系 - 创建者
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys="Content.created_by"
    )

    # 关系 - 练习记录
    practices: Mapped[list["Practice"]] = relationship(
        "Practice",
        back_populates="content",
        foreign_keys="Practice.content_id",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Content(id={self.id}, title={self.title}, type={self.content_type}, level={self.difficulty_level})>"


class Vocabulary(Base):
    """
    词汇模型
    存储单词、短语及其释义、例句等
    """

    __tablename__ = "vocabularies"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 单词/短语
    word: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    # 音标（IPA）
    phonetic: Mapped[Optional[str]] = mapped_column(String(100))

    # 词性（JSON数组，如：["n.", "v."]）
    part_of_speech: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 中文释义（JSON数组）
    definitions: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 英文释义
    english_definition: Mapped[Optional[str]] = mapped_column(Text)

    # 例句（JSON数组）
    examples: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 词根词缀
    etymology: Mapped[Optional[str]] = mapped_column(String(255))

    # 难度等级（使用String存储）
    difficulty_level: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # 频率等级（1-10，10为最高频）
    frequency_level: Mapped[Optional[int]] = mapped_column(Integer)

    # 相关词汇（JSON数组）
    related_words: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 同义词（JSON数组）
    synonyms: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 反义词（JSON数组）
    antonyms: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 搭配（JSON数组）
    collocations: Mapped[Optional[list]] = mapped_column(
        JSON,
        default=list
    )

    # 扩展信息（JSONB格式）
    extra_data: Mapped[Optional[dict]] = mapped_column(
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

    # 关系 - 内容词汇关联
    contents: Mapped[list["Content"]] = relationship(
        "Content",
        secondary="content_vocabulary",
        back_populates="vocabularies",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Vocabulary(id={self.id}, word={self.word})>"


# 内容与词汇的多对多关联表
class ContentVocabulary(Base):
    """
    内容与词汇关联表
    记录词汇在内容中的出现情况和学习要点
    """

    __tablename__ = "content_vocabulary"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # 内容ID
    content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 词汇ID
    vocabulary_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vocabularies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 在内容中的上下文句子
    context_sentence: Mapped[Optional[str]] = mapped_column(Text)

    # 上下文位置（JSON，记录句子在内容中的位置）
    context_position: Mapped[Optional[dict]] = mapped_column(JSON)

    # 是否为重点词汇
    is_key_vocabulary: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    # 是否为考点词汇
    is_exam_point: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    # 学习优先级（1-10）
    priority: Mapped[int] = mapped_column(
        Integer,
        default=5
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 关系
    content: Mapped["Content"] = relationship(
        "Content",
        backref="content_vocabularies"
    )

    vocabulary: Mapped["Vocabulary"] = relationship(
        "Vocabulary",
        backref="content_vocabularies"
    )

    def __repr__(self) -> str:
        return f"<ContentVocabulary(content_id={self.content_id}, vocabulary_id={self.vocabulary_id})>"
