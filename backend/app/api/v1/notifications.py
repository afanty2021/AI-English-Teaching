"""
通知偏好设置 API 路由

提供通知偏好设置的 CRUD 操作端点。
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.notification_preference import (
    NotificationPreferenceCreate,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.services.notification_preference_service import (
    get_notification_preference_service,
    NotificationPreferenceService,
)

router = APIRouter()


@router.get("/preferences", response_model=NotificationPreferenceResponse)
async def get_notification_preference(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(get_notification_preference_service),
) -> NotificationPreferenceResponse:
    """
    获取当前用户的通知偏好设置

    如果用户没有设置过通知偏好，将返回默认设置并自动创建记录。

    Args:
        db: 数据库会话
        current_user: 当前用户
        service: 通知偏好服务

    Returns:
        NotificationPreferenceResponse: 用户的通知偏好设置
    """
    try:
        preference = await service.get_or_create(db, user_id=current_user.id)
        return NotificationPreferenceResponse(
            id=str(preference.id),
            user_id=str(preference.user_id),
            enable_share_notifications=preference.enable_share_notifications,
            enable_comment_notifications=preference.enable_comment_notifications,
            enable_system_notifications=preference.enable_system_notifications,
            notify_via_websocket=preference.notify_via_websocket,
            notify_via_email=preference.notify_via_email,
            email_frequency=preference.email_frequency,
            quiet_hours_start=preference.quiet_hours_start,
            quiet_hours_end=preference.quiet_hours_end,
            created_at=preference.created_at.isoformat(),
            updated_at=preference.updated_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知偏好设置失败: {str(e)}"
        )


@router.put("/preferences", response_model=NotificationPreferenceResponse)
async def update_notification_preference(
    preference_data: NotificationPreferenceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(get_notification_preference_service),
) -> NotificationPreferenceResponse:
    """
    更新当前用户的通知偏好设置

    只更新提供的字段，未提供的字段保持不变。

    Args:
        preference_data: 要更新的通知偏好设置
        db: 数据库会话
        current_user: 当前用户
        service: 通知偏好服务

    Returns:
        NotificationPreferenceResponse: 更新后的通知偏好设置

    Raises:
        HTTPException: 如果更新失败
    """
    try:
        # 过滤掉 None 值
        update_data = {
            k: v for k, v in preference_data.model_dump().items()
            if v is not None
        }

        preference = await service.update(
            db=db,
            user_id=current_user.id,
            preference_data=update_data
        )

        return NotificationPreferenceResponse(
            id=str(preference.id),
            user_id=str(preference.user_id),
            enable_share_notifications=preference.enable_share_notifications,
            enable_comment_notifications=preference.enable_comment_notifications,
            enable_system_notifications=preference.enable_system_notifications,
            notify_via_websocket=preference.notify_via_websocket,
            notify_via_email=preference.notify_via_email,
            email_frequency=preference.email_frequency,
            quiet_hours_start=preference.quiet_hours_start,
            quiet_hours_end=preference.quiet_hours_end,
            created_at=preference.created_at.isoformat(),
            updated_at=preference.updated_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新通知偏好设置失败: {str(e)}"
        )


@router.post("/preferences/reset", response_model=NotificationPreferenceResponse)
async def reset_notification_preference(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(get_notification_preference_service),
) -> NotificationPreferenceResponse:
    """
    重置当前用户的通知偏好设置为默认值

    Args:
        db: 数据库会话
        current_user: 当前用户
        service: 通知偏好服务

    Returns:
        NotificationPreferenceResponse: 重置后的通知偏好设置
    """
    try:
        # 更新为默认值
        default_data = {
            "enable_share_notifications": True,
            "enable_comment_notifications": True,
            "enable_system_notifications": True,
            "notify_via_websocket": True,
            "notify_via_email": False,
            "email_frequency": "immediate",
            "quiet_hours_start": None,
            "quiet_hours_end": None,
        }

        preference = await service.update(
            db=db,
            user_id=current_user.id,
            preference_data=default_data
        )

        return NotificationPreferenceResponse(
            id=str(preference.id),
            user_id=str(preference.user_id),
            enable_share_notifications=preference.enable_share_notifications,
            enable_comment_notifications=preference.enable_comment_notifications,
            enable_system_notifications=preference.enable_system_notifications,
            notify_via_websocket=preference.notify_via_websocket,
            notify_via_email=preference.notify_via_email,
            email_frequency=preference.email_frequency,
            quiet_hours_start=preference.quiet_hours_start,
            quiet_hours_end=preference.quiet_hours_end,
            created_at=preference.created_at.isoformat(),
            updated_at=preference.updated_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置通知偏好设置失败: {str(e)}"
        )


@router.get("/preferences/check-quiet-hours")
async def check_quiet_hours_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: NotificationPreferenceService = Depends(get_notification_preference_service),
):
    """
    检查当前用户是否处于静默时段

    Args:
        db: 数据库会话
        current_user: 当前用户
        service: 通知偏好服务

    Returns:
        dict: 静默时段状态信息
    """
    try:
        in_quiet_hours = await service.is_in_quiet_hours(db, user_id=current_user.id)
        preference = await service.get(db, user_id=current_user.id)

        return {
            "in_quiet_hours": in_quiet_hours,
            "quiet_hours_configured": (
                preference is not None
                and preference.quiet_hours_start is not None
                and preference.quiet_hours_end is not None
            ),
            "quiet_hours_start": preference.quiet_hours_start if preference else None,
            "quiet_hours_end": preference.quiet_hours_end if preference else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检查静默时段状态失败: {str(e)}"
        )
