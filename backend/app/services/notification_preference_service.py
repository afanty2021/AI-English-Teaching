"""
通知偏好设置服务

处理通知偏好设置的CRUD操作。
"""
import uuid
from typing import Optional

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import NotificationPreference


class NotificationPreferenceService:
    """通知偏好设置服务"""

    async def get_or_create(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> NotificationPreference:
        """
        获取用户的通知偏好设置，如果不存在则创建默认值

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            NotificationPreference: 用户的通知偏好设置
        """
        # 尝试查询现有记录
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        preference = result.scalar_one_or_none()

        # 如果不存在，创建新记录
        if preference is None:
            preference = NotificationPreference(
                user_id=user_id,
                enable_share_notifications=True,
                enable_comment_notifications=True,
                enable_system_notifications=True,
                notify_via_websocket=True,
                notify_via_email=False,
                email_frequency="immediate",
            )
            db.add(preference)
            await db.commit()
            await db.refresh(preference)

        return preference

    async def get(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> Optional[NotificationPreference]:
        """
        获取用户的通知偏好设置

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            Optional[NotificationPreference]: 用户的通知偏好设置，不存在返回 None
        """
        result = await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        preference_data: dict
    ) -> NotificationPreference:
        """
        更新用户的通知偏好设置

        Args:
            db: 数据库会话
            user_id: 用户ID
            preference_data: 要更新的字段数据

        Returns:
            NotificationPreference: 更新后的通知偏好设置

        Raises:
            ValueError: 如果用户偏好设置不存在
        """
        # 获取现有设置
        preference = await self.get(db, user_id)
        if preference is None:
            raise ValueError("通知偏好设置不存在")

        # 更新字段
        for field, value in preference_data.items():
            if hasattr(preference, field) and value is not None:
                setattr(preference, field, value)

        await db.commit()
        await db.refresh(preference)

        return preference

    async def is_in_quiet_hours(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> bool:
        """
        检查用户当前是否处于静默时段

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            bool: 是否处于静默时段
        """
        from datetime import datetime

        preference = await self.get(db, user_id)
        if preference is None:
            return False

        # 如果没有设置静默时段，返回 False
        if not preference.quiet_hours_start or not preference.quiet_hours_end:
            return False

        # 获取当前时间
        now = datetime.utcnow()
        current_time = now.strftime("%H:%M")

        # 检查是否在静默时段内
        start = preference.quiet_hours_start
        end = preference.quiet_hours_end

        if start <= end:
            # 静默时段在同一天内
            return start <= current_time <= end
        else:
            # 静默时段跨越午夜（如 22:00 到 08:00）
            return current_time >= start or current_time <= end

    async def should_send_websocket_notification(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> bool:
        """
        检查是否应该发送 WebSocket 通知

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            bool: 是否应该发送 WebSocket 通知
        """
        # 检查是否在静默时段
        if await self.is_in_quiet_hours(db, user_id):
            return False

        preference = await self.get(db, user_id)
        if preference is None:
            return True  # 默认启用

        return preference.notify_via_websocket

    async def should_send_email_notification(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> bool:
        """
        检查是否应该发送邮件通知

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            bool: 是否应该发送邮件通知
        """
        preference = await self.get(db, user_id)
        if preference is None:
            return False  # 默认不发送邮件

        # 如果禁用了邮件通知，返回 False
        if not preference.notify_via_email:
            return False

        # 如果邮件频率设置为 never，返回 False
        if preference.email_frequency == "never":
            return False

        # 检查是否在静默时段
        if await self.is_in_quiet_hours(db, user_id):
            return False

        return True

    async def get_email_frequency(
        self,
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> str:
        """
        获取用户的邮件通知频率设置

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            str: 邮件频率: immediate, hourly, daily, weekly, never
        """
        preference = await self.get(db, user_id)
        if preference is None:
            return "immediate"  # 默认立即发送

        return preference.email_frequency


# 服务依赖注入函数
async def get_notification_preference_service() -> NotificationPreferenceService:
    """
    获取通知偏好设置服务实例

    Returns:
        NotificationPreferenceService: 服务实例
    """
    return NotificationPreferenceService()
