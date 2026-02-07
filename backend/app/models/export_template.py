"""
导出模板模型 - AI英语教学系统
支持教案导出模板管理，支持多种格式和自定义变量
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
    from app.models.export_task import ExportTask
    from app.models.organization import Organization
    from app.models.user import User


class TemplateFormat(str, PyEnum):
    """模板格式枚举"""
    WORD = "word"
    PDF = "pdf"
    PPTX = "pptx"
    MARKDOWN = "markdown"


class ExportTemplate(Base):
    """
    导出模板模型
    存储可复用的教案导出模板
    """

    __tablename__ = "export_templates"

    # 主键 - 使用PostgreSQL UUID
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 模板名称
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    # 模板描述
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 模板格式（使用String存储TemplateFormat枚举值）
    format: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    # 模板文件路径（相对于模板根目录）
    template_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    # 预览图片路径
    preview_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # 模板变量定义（JSON数组，定义可替换的变量）
    # 示例: [{"name": "title", "type": "text", "default": "", "required": true}]
    variables: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )

    # 是否为系统模板
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    # 是否激活
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    # 是否为默认模板
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # 创建者ID（系统模板为null）
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 所属组织ID（可选，用于组织内共享模板）
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # 使用次数统计
    usage_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False
    )

    # 创建时间
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # ==================== 关系 ====================

    # 关系 - 使用此模板的导出任务
    export_tasks: Mapped[list["ExportTask"]] = relationship(
        "ExportTask",
        back_populates="template",
        foreign_keys="ExportTask.template_id",
        cascade="all, delete-orphan"
    )

    # 关系 - 创建者
    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by]
    )

    # 关系 - 所属组织
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        foreign_keys=[organization_id]
    )

    def __repr__(self) -> str:
        return f"<ExportTemplate(id={self.id}, name={self.name}, format={self.format}, is_system={self.is_system})>"

    @property
    def is_public(self) -> bool:
        """是否为公共模板（系统模板或无组织限制）"""
        return self.is_system or self.organization_id is None

    @property
    def variable_names(self) -> list[str]:
        """获取所有变量名称"""
        return [var.get("name") for var in self.variables if isinstance(var, dict) and "name" in var]

    def get_variable(self, name: str) -> Optional[dict]:
        """获取指定变量的定义"""
        for var in self.variables:
            if isinstance(var, dict) and var.get("name") == name:
                return var
        return None

    def increment_usage(self) -> None:
        """增加使用次数"""
        self.usage_count += 1
