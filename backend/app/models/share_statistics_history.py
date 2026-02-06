"""
分享统计历史数据模型

记录分享统计数据的变化趋势。
"""
import uuid
from datetime import datetime

from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class ShareStatisticsHistory(Base):
    """分享统计历史模型"""

    __tablename__ = "share_statistics_history"

    # 主键
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # 关联用户
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )

    # 统计数据快照
    pending_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    total_shared_by_me: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    total_shared_to_me: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    accepted_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    rejected_count: Mapped[int] = mapped_column(
        nullable=False,
        default=0
    )
    acceptance_rate: Mapped[float] = mapped_column(
        nullable=False,
        default=0.0
    )

    # 时间戳
    recorded_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow,
        index=True
    )

    def __repr__(self) -> str:
        return f"<ShareStatisticsHistory(user_id={self.user_id}, recorded_at={self.recorded_at})>"


# 复合索引
Index("ix_share_stats_history_user_date", "user_id", "recorded_at")
