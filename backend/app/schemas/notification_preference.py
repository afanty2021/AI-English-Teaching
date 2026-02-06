"""
通知偏好设置 Pydantic Schema

定义通知偏好相关的请求和响应模型。
"""
from datetime import time
from typing import Optional

from pydantic import BaseModel, Field


class NotificationPreferenceBase(BaseModel):
    """通知偏好设置基础模型"""
    # 通知类型开关
    enable_share_notifications: bool = Field(
        default=True,
        description="是否启用分享通知"
    )
    enable_comment_notifications: bool = Field(
        default=True,
        description="是否启用评论通知"
    )
    enable_system_notifications: bool = Field(
        default=True,
        description="是否启用系统通知"
    )

    # 通知方式
    notify_via_websocket: bool = Field(
        default=True,
        description="是否通过 WebSocket 实时通知"
    )
    notify_via_email: bool = Field(
        default=False,
        description="是否通过邮件通知"
    )

    # 邮件频率: immediate(立即), hourly(每小时), daily(每天), weekly(每周), never(从不)
    email_frequency: str = Field(
        default="immediate",
        description="邮件通知频率"
    )

    # 静默时段
    quiet_hours_start: Optional[str] = Field(
        default=None,
        description="静默开始时间 (HH:MM格式)",
        max_length=5
    )
    quiet_hours_end: Optional[str] = Field(
        default=None,
        description="静默结束时间 (HH:MM格式)",
        max_length=5
    )


class NotificationPreferenceCreate(NotificationPreferenceBase):
    """创建通知偏好设置请求"""
    pass


class NotificationPreferenceUpdate(BaseModel):
    """更新通知偏好设置请求（部分更新）"""
    # 通知类型开关（可选）
    enable_share_notifications: Optional[bool] = Field(
        default=None,
        description="是否启用分享通知"
    )
    enable_comment_notifications: Optional[bool] = Field(
        default=None,
        description="是否启用评论通知"
    )
    enable_system_notifications: Optional[bool] = Field(
        default=None,
        description="是否启用系统通知"
    )

    # 通知方式（可选）
    notify_via_websocket: Optional[bool] = Field(
        default=None,
        description="是否通过 WebSocket 实时通知"
    )
    notify_via_email: Optional[bool] = Field(
        default=None,
        description="是否通过邮件通知"
    )

    # 邮件频率（可选）
    email_frequency: Optional[str] = Field(
        default=None,
        description="邮件通知频率: immediate, hourly, daily, weekly, never"
    )

    # 静默时段（可选）
    quiet_hours_start: Optional[str] = Field(
        default=None,
        description="静默开始时间 (HH:MM格式)",
        max_length=5
    )
    quiet_hours_end: Optional[str] = Field(
        default=None,
        description="静默结束时间 (HH:MM格式)",
        max_length=5
    )


class NotificationPreferenceResponse(NotificationPreferenceBase):
    """通知偏好设置响应模型"""
    id: str
    user_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
