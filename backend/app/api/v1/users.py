"""
用户管理 API

提供用户搜索、查询等接口。
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserListResponse
from app.services.user_search_cache_service import get_user_search_cache_service, UserSearchCacheService

router = APIRouter()


@router.get("/search", response_model=UserListResponse)
async def search_users(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    role: Optional[UserRole] = Query(None, description="角色筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    cache_service: UserSearchCacheService = Depends(get_user_search_cache_service)
) -> UserListResponse:
    """
    搜索用户（支持缓存）

    支持按用户名、邮箱、姓名搜索，可按角色筛选。
    热门搜索结果会被缓存5分钟。
    """
    # 使用缓存服务搜索
    users_data = await cache_service.search_and_cache(
        db=db,
        query=q,
        role=role,
        limit=limit
    )

    # 转换为响应格式
    users = [
        UserResponse(
            id=user_data["id"],
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=user_data.get("is_active", True),
            created_at=user_data.get("created_at"),
            updated_at=user_data.get("updated_at")
        )
        for user_data in users_data
    ]

    return UserListResponse(
        users=users,
        total=len(users),
        skip=skip,
        limit=limit
    )


@router.get("/search/hot")
async def get_hot_searches(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    cache_service: UserSearchCacheService = Depends(get_user_search_cache_service),
    current_user: User = Depends(get_current_user)
):
    """
    获取热门搜索查询

    返回最近搜索次数最多的关键词。
    """
    hot_queries = await cache_service.get_hot_queries(limit=limit)
    return {"queries": hot_queries, "count": len(hot_queries)}


@router.get("/teachers", response_model=UserListResponse)
async def list_teachers(
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserListResponse:
    """
    获取教师列表

    返回所有教师角色的用户，用于分享教案时选择接收教师。
    """
    # 只查询教师角色
    query = select(User).where(User.role == UserRole.TEACHER)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    # 获取总数
    count_query = select(func.count()).select_from(User).where(User.role == UserRole.TEACHER)
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return UserListResponse(
        users=[UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None,
            updated_at=user.updated_at.isoformat() if user.updated_at else None
        ) for user in users],
        total=total,
        skip=skip,
        limit=limit
    )
