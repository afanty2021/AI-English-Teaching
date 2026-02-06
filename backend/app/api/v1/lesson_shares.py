"""
教案分享 API 路由 - AI英语教学系统

提供教案分享相关的API端点。
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole
from app.schemas.lesson_share import (
    CreateShareRequest,
    CreateShareResponse,
    DuplicateLessonPlanRequest,
    DuplicateLessonPlanResponse,
    ShareListResponse,
    ShareResponse,
    ShareStatus,
)
from app.services.lesson_plan_service import get_lesson_plan_service, LessonPlanService
from app.services.lesson_plan_share_service import get_lesson_plan_share_service, LessonPlanShareService

router = APIRouter()


@router.post("/{lesson_plan_id}/share", response_model=CreateShareResponse, status_code=status.HTTP_201_CREATED)
async def share_lesson_plan(
    lesson_plan_id: uuid.UUID,
    request: CreateShareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    share_service: LessonPlanShareService = Depends(get_lesson_plan_share_service),
) -> CreateShareResponse:
    """
    分享教案给其他教师

    Args:
        lesson_plan_id: 教案ID
        request: 分享请求
        db: 数据库会话
        current_user: 当前用户
        share_service: 分享服务

    Returns:
        CreateShareResponse: 分享结果

    Raises:
        HTTPException: 如果用户不是教师或无权分享
    """
    # 验证用户权限
    if current_user.role != UserRole.TEACHER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能分享教案"
        )

    try:
        share = await share_service.create_share(
            db=db,
            lesson_plan_id=lesson_plan_id,
            shared_by_id=current_user.id,
            shared_to_id=request.shared_to,
            permission=request.permission,
            message=request.message,
            expires_days=request.expires_days,
        )

        return CreateShareResponse(
            share=share,
            message="分享已发送，等待对方接受"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分享失败: {str(e)}"
        )


@router.get("/shared", response_model=ShareListResponse)
async def get_shared_with_me(
    status: ShareStatus | None = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    share_service: LessonPlanShareService = Depends(get_lesson_plan_share_service),
) -> ShareListResponse:
    """
    获取分享给我的教案列表

    Args:
        status: 状态筛选
        page: 页码
        page_size: 每页大小
        db: 数据库会话
        current_user: 当前用户
        share_service: 分享服务

    Returns:
        ShareListResponse: 分享列表
    """
    try:
        shares, total = await share_service.get_shared_with_me(
            db=db,
            user_id=current_user.id,
            status=status,
            page=page,
            page_size=page_size,
        )

        return ShareListResponse(
            shares=shares,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享列表失败: {str(e)}"
        )


@router.get("/shared-by-me", response_model=ShareListResponse)
async def get_shared_by_me(
    status: ShareStatus | None = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    share_service: LessonPlanShareService = Depends(get_lesson_plan_share_service),
) -> ShareListResponse:
    """
    获取我分享的教案列表

    Args:
        status: 状态筛选
        page: 页码
        page_size: 每页大小
        db: 数据库会话
        current_user: 当前用户
        share_service: 分享服务

    Returns:
        ShareListResponse: 分享列表
    """
    try:
        shares, total = await share_service.get_shared_by_me(
            db=db,
            user_id=current_user.id,
            status=status,
            page=page,
            page_size=page_size,
        )

        return ShareListResponse(
            shares=shares,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享列表失败: {str(e)}"
        )


@router.put("/shared/{share_id}/accept", response_model=ShareResponse)
async def accept_share(
    share_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    share_service: LessonPlanShareService = Depends(get_lesson_plan_share_service),
) -> ShareResponse:
    """
    接受分享

    Args:
        share_id: 分享记录ID
        db: 数据库会话
        current_user: 当前用户
        share_service: 分享服务

    Returns:
        ShareResponse: 更新后的分享记录

    Raises:
        HTTPException: 如果分享不存在或无权操作
    """
    try:
        share = await share_service.accept_share(
            db=db,
            share_id=share_id,
            user_id=current_user.id,
        )

        return share

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"接受分享失败: {str(e)}"
        )


@router.put("/shared/{share_id}/reject", response_model=ShareResponse)
async def reject_share(
    share_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    share_service: LessonPlanShareService = Depends(get_lesson_plan_share_service),
) -> ShareResponse:
    """
    拒绝分享

    Args:
        share_id: 分享记录ID
        db: 数据库会话
        current_user: 当前用户
        share_service: 分享服务

    Returns:
        ShareResponse: 更新后的分享记录

    Raises:
        HTTPException: 如果分享不存在或无权操作
    """
    try:
        share = await share_service.reject_share(
            db=db,
            share_id=share_id,
            user_id=current_user.id,
        )

        return share

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"拒绝分享失败: {str(e)}"
        )


@router.delete("/shared/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_share(
    share_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    share_service: LessonPlanShareService = Depends(get_lesson_plan_share_service),
) -> None:
    """
    取消分享

    Args:
        share_id: 分享记录ID
        db: 数据库会话
        current_user: 当前用户
        share_service: 分享服务

    Raises:
        HTTPException: 如果分享不存在或无权操作
    """
    try:
        await share_service.cancel_share(
            db=db,
            share_id=share_id,
            user_id=current_user.id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消分享失败: {str(e)}"
        )


@router.get("/shared/statistics/overview")
async def get_share_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    share_service: LessonPlanShareService = Depends(get_lesson_plan_share_service),
):
    """
    获取分享统计概览

    返回当前用户的分享统计数据：
    - 待接受的分享数量
    - 总分享次数（我分享的）
    - 总接受次数（分享给我的）
    - 总拒绝次数
    - 接受率

    Args:
        db: 数据库会话
        current_user: 当前用户
        share_service: 分享服务

    Returns:
        分享统计数据
    """
    try:
        stats = await share_service.get_share_statistics(
            db=db,
            user_id=current_user.id,
        )
        return stats

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计失败: {str(e)}"
        )


@router.get("/notifications/pending")
async def get_pending_notifications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    share_service: LessonPlanShareService = Depends(get_lesson_plan_share_service),
):
    """
    获取待处理的通知

    返回当前用户的待处理分享通知（待接受的分享）。

    Args:
        db: 数据库会话
        current_user: 当前用户
        share_service: 分享服务

    Returns:
        待处理通知列表
    """
    try:
        notifications = await share_service.get_pending_notifications(
            db=db,
            user_id=current_user.id,
        )
        return {
            "notifications": notifications,
            "count": len(notifications)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知失败: {str(e)}"
        )
