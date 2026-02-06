"""
异步任务模型 - AI英语教学系统
用于存储PDF导出等异步任务的执行状态和结果
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AsyncTaskStatus(str, Enum):
    """异步任务状态枚举"""
    PENDING = "pending"       # 等待执行
    PROCESSING = "processing"  # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


class AsyncTaskType(str, Enum):
    """异步任务类型枚举"""
    REPORT_GENERATE = "report_generate"   # 报告生成
    REPORT_EXPORT = "report_export"     # 单个报告导出
    BATCH_EXPORT = "batch_export"       # 批量报告导出


class AsyncTask(Base):
    """
    异步任务模型

    用于跟踪后台任务的执行状态，如PDF报告导出、批量数据处理等。
    支持任务创建、进度更新、完成通知、失败重试等功能。
    """

    __tablename__ = "async_tasks"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # 关联用户ID（外键到users表）
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # 任务类型
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    # 任务状态
    status: Mapped[str] = mapped_column(
        String(20),
        default=AsyncTaskStatus.PENDING.value,
        nullable=False,
        index=True
    )

    # 进度百分比 (0-100)
    progress: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # 任务输入参数 (JSON)
    # 包含导出配置、目标学生列表等
    input_params: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # 任务结果URL (JSON)
    # 包含生成文件的下载链接
    result_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    # 结果详细信息 (JSON)
    # 包含批量导出的文件列表、错误详情等
    result_details: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # 错误信息
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # 重试次数
    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    # 最大重试次数
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False
    )

    # 优先级 (数字越大优先级越高)
    priority: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True
    )

    # Celery任务ID（用于关联Celery任务）
    celery_task_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 预计完成时间（用于进度显示）
    estimated_completion_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )

    # 关系 - 关联用户
    user: Mapped["User"] = relationship(
        "User",
        back_populates="async_tasks",
        foreign_keys=[user_id]
    )

    def __repr__(self) -> str:
        return f"<AsyncTask(id={self.id}, type={self.task_type}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """检查任务是否处于活动状态"""
        return self.status in (AsyncTaskStatus.PENDING.value, AsyncTaskStatus.PROCESSING.value)

    @property
    def can_retry(self) -> bool:
        """检查任务是否可重试"""
        return (
            self.status == AsyncTaskStatus.FAILED.value
            and self.retry_count < self.max_retries
        )

    @property
    def progress_percentage(self) -> int:
        """获取进度百分比"""
        return min(100, max(0, self.progress))

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress_percentage,
            "input_params": self.input_params,
            "result_url": self.result_url,
            "result_details": self.result_details,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "celery_task_id": self.celery_task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_completion_time": (
                self.estimated_completion_time.isoformat()
                if self.estimated_completion_time else None
            ),
        }

    def to_api_response(self) -> dict:
        """转换为API响应格式"""
        return {
            "id": str(self.id),
            "task_type": self.task_type,
            "status": self.status,
            "progress": self.progress_percentage,
            "message": self._get_status_message(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result_url": self.result_url,
            "error_message": self.error_message if self.status == AsyncTaskStatus.FAILED.value else None,
        }

    def _get_status_message(self) -> str:
        """获取状态描述消息"""
        messages = {
            AsyncTaskStatus.PENDING.value: "任务已创建，等待执行",
            AsyncTaskStatus.PROCESSING.value: f"正在处理... {self.progress_percentage}%",
            AsyncTaskStatus.COMPLETED.value: "任务已完成",
            AsyncTaskStatus.FAILED.value: f"任务失败: {self.error_message or '未知错误'}",
            AsyncTaskStatus.CANCELLED.value: "任务已取消",
        }
        return messages.get(self.status, "未知状态")
