"""
用户管理 API

提供用户搜索、查询等接口。
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserListResponse

router = APIRouter()


@router.get("/search", response_model=UserListResponse)
async def search_users(
    q: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    role: Optional[UserRole] = Query(None, description="角色筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> UserListResponse:
    """
    搜索用户

    支持按用户名、邮箱、姓名搜索，可按角色筛选。
    """
    # 构建查询条件
    conditions = []

    # 搜索条件：用户名、邮箱、姓名
    search_pattern = f"%{q}%"
    conditions.append(
        or_(
            User.username.ilike(search_pattern),
            User.email.ilike(search_pattern),
            User.full_name.ilike(search_pattern) if User.full_name is not None else False
        )
    )

    # 角色筛选
    if role:
        conditions.append(User.role == role)

    # 查询用户
    query = select(User).where(*conditions)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    users = result.scalars().all()

    # 获取总数
    count_query = select(func.count()).select_from(User).where(*conditions)
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
