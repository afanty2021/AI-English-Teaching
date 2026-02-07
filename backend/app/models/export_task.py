"""
导出任务模型 - AI英语教学系统
支持教案导出任务管理，支持多种格式（Word、PDF、PPTX、Markdown）
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
    from app.models.export_template import ExportTemplate
    from app.models.lesson_plan import LessonPlan
    from app.models.user import User


class TaskStatus(str, PyEnum):
    """导出任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, PyEnum):
    """导出格式枚举"""
    WORD = "word"
    PDF = "pdf"
    PPTX = "pptx"
    MARKDOWN = "markdown"


class ExportTask(Base):
    """
    导出任务模型
    存储教案导出任务的执行状态和结果
    """

    __tablename__ = "export_tasks"

    # 主键 - 使用PostgreSQL UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 关联的教案ID（外键到lesson_plans表）
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lesson_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 使用的模板ID（可选，外键到export_templates表）
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("export_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 创建者ID（外键到users表）
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 导出格式（使用String存储ExportFormat枚举值）
    format: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # 任务状态（使用String存储TaskStatus枚举值）
    status: Mapped[str] = mapped_column(
        String(20),
        default=TaskStatus.PENDING.value,
        nullable=False,
        index=True
    )

    # 导出进度（0-100）
    progress: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    # 导出选项（JSON格式，存储导出配置）
    options: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False
    )

    # 导出文件路径
    file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # 文件大小（字节）
    file_size: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )

    # 下载URL
    download_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 错误代码
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 开始处理时间
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 完成时间
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # ==================== 关系 ====================

    # 关系 - 关联的教案
    lesson: Mapped["LessonPlan"] = relationship(
        "LessonPlan",
        back_populates="export_tasks",
        foreign_keys=[lesson_id]
    )

    # 关系 - 使用的模板
    template: Mapped[Optional["ExportTemplate"]] = relationship(
        "ExportTemplate",
        back_populates="export_tasks",
        foreign_keys=[template_id]
    )

    # 关系 - 创建者
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="export_tasks",
        foreign_keys=[created_by]
    )

    def __repr__(self) -> str:
        return f"<ExportTask(id={self.id}, lesson_id={self.lesson_id}, format={self.format}, status={self.status})>"

    @property
    def is_processing(self) -> bool:
        """是否正在处理中"""
        return self.status == TaskStatus.PROCESSING.value

    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == TaskStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        """是否失败"""
        return self.status == TaskStatus.FAILED.value

    @property
    def can_be_cancelled(self) -> bool:
        """是否可以被取消"""
        return self.status in [TaskStatus.PENDING.value, TaskStatus.PROCESSING.value]
