"""
API依赖注入模块
提供数据库会话、用户认证、权限验证等FastAPI依赖
"""
import uuid
from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token, get_token_jti, get_token_version, decode_token
from app.core.token_blacklist import get_token_blacklist
from app.models import User, UserRole
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# HTTP Bearer 安全方案
security = HTTPBearer(auto_error=False)


async def check_token_not_revoked(
    token: str,
    user_id: str
) -> tuple[bool, str]:
    """
    检查 Token 是否已被撤销

    Args:
        token: JWT token 字符串
        user_id: 用户 ID

    Returns:
        tuple: (是否有效, 错误信息)
    """
    try:
        blacklist = get_token_blacklist()

        # 检查 JTI 是否在黑名单中
        jti = get_token_jti(token)
        if jti and await blacklist.is_revoked(jti):
            return False, "Token 已被撤销"

        # 检查 Token 版本（用于密码修改后的撤销）
        token_version = get_token_version(token)
        if token_version:
            is_valid = await blacklist.check_token_version(user_id, token_version)
            if not is_valid:
                return False, "Token 版本已过期，请重新登录"

        return True, ""
    except Exception:
        # 如果 Redis 不可用，降级处理（允许请求通过）
        return True, ""


async def validate_token(
    credentials: Optional[HTTPAuthorizationCredentials],
    token_type: str = "access"
) -> str:
    """
    验证 Token 并返回用户 ID

    Args:
        credentials: HTTP Bearer credentials
        token_type: 期望的 token 类型

    Returns:
        str: 用户 ID

    Raises:
        HTTPException: Token 无效
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    user_id = verify_token(token, token_type=token_type)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查 Token 是否被撤销
    is_valid, error_msg = await check_token_not_revoked(token, user_id)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话依赖注入

    Yields:
        AsyncSession: 异步数据库会话

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    from app.db.session_manager import get_db as _get_db

    async for session in _get_db():
        yield session


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    获取当前用户（可选认证）

    Args:
        credentials: HTTP Bearer credentials（可选）
        db: 数据库会话

    Returns:
        User对象，如果未提供token或token无效则返回None

    Example:
        @app.get("/public-content")
        async def get_public_content(user: Optional[User] = Depends(get_current_user_optional)):
            if user:
                return {"message": f"Hello {user.username}"}
            return {"message": "Hello guest"}
    """
    if credentials is None:
        return None

    try:
        user_id = await validate_token(credentials)
    except HTTPException:
        return None

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return None

    # 查询用户 - 根据角色预加载不同的关联数据
    # 首先获取用户基本信息以确定角色
    temp_result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    temp_user = temp_result.scalar_one_or_none()

    if temp_user is None:
        return None

    # 根据角色构建查询选项
    from sqlalchemy.orm import selectinload

    if temp_user.role == UserRole.STUDENT.value:
        options = [selectinload(User.organization), selectinload(User.student_profile)]
    elif temp_user.role == UserRole.TEACHER.value:
        options = [selectinload(User.organization), selectinload(User.teacher_profile)]
    else:
        options = [selectinload(User.organization)]

    # 重新查询用户并预加载关联数据
    result = await db.execute(
        select(User)
        .options(*options)
        .where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前认证用户

    Args:
        credentials: HTTP Bearer credentials（必需）
        db: 数据库会话

    Returns:
        User对象

    Raises:
        HTTPException: 如果未提供token或token无效

    Example:
        @app.get("/protected")
        async def protected_endpoint(user: User = Depends(get_current_user)):
            return {"message": f"Hello {user.username}"}
    """
    user_id = await validate_token(credentials)

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户 - 根据角色预加载不同的关联数据
    # 首先获取用户基本信息以确定角色
    temp_result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    temp_user = temp_result.scalar_one_or_none()

    if temp_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 根据角色构建查询选项
    from sqlalchemy.orm import selectinload

    if temp_user.role == UserRole.STUDENT.value:
        # 学生需要预加载 student_profile
        options = [selectinload(User.organization), selectinload(User.student_profile)]
    elif temp_user.role == UserRole.TEACHER.value:
        # 教师需要预加载 teacher_profile
        options = [selectinload(User.organization), selectinload(User.teacher_profile)]
    else:
        options = [selectinload(User.organization)]

    # 重新查询用户并预加载关联数据
    result = await db.execute(
        select(User)
        .options(*options)
        .where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前激活用户

    Args:
        current_user: 当前用户

    Returns:
        激活的User对象

    Raises:
        HTTPException: 如果用户未激活
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户未激活"
        )
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前超级管理员

    Args:
        current_user: 当前用户

    Returns:
        超级管理员User对象

    Raises:
        HTTPException: 如果用户不是超级管理员
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )
    return current_user


async def get_current_teacher(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前教师用户

    验证用户必须是教师或超级管理员

    Args:
        current_user: 当前用户

    Returns:
        教师User对象

    Raises:
        HTTPException: 如果用户不是教师
    """
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限"
        )
    return current_user


async def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前学生用户

    验证用户必须是学生，并预加载学生档案

    Args:
        credentials: HTTP Bearer credentials（必需）
        db: 数据库会话

    Returns:
        学生User对象（已预加载student_profile）

    Raises:
        HTTPException: 如果用户不是学生
    """
    user_id = await validate_token(credentials)

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户并预加载学生档案
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.organization),
            selectinload(User.student_profile),
        )
        .where(User.id == user_uuid)
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )

    if user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要学生权限"
        )

    return user


async def get_current_organization_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前组织管理员

    验证用户必须是组织管理员或超级管理员

    Args:
        current_user: 当前用户

    Returns:
        组织管理员User对象

    Raises:
        HTTPException: 如果用户不是组织管理员
    """
    if current_user.role not in [UserRole.ORGANIZATION_ADMIN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要组织管理员权限"
        )
    return current_user
