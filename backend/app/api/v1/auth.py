"""
认证API v1
提供用户注册、登录、token刷新等认证相关端点
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.schemas.auth import (
    AuthResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    *,
    db: AsyncSession = Depends(get_db),
    register_data: RegisterRequest,
) -> Any:
    """
    用户注册

    创建新用户账户，支持个人注册和组织注册。
    如果提供organization_name，会自动创建组织并将用户设为组织管理员。

    Args:
        db: 数据库会话
        register_data: 注册请求数据

    Returns:
        AuthResponse: 包含access_token、refresh_token和用户信息

    Raises:
        HTTPException 400: 用户名或邮箱已存在
    """
    try:
        result = await AuthService.register(db=db, register_data=register_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# 速率限制依赖
async def check_login_rate_limit(
    login_data: LoginRequest,
    request: Request,
) -> None:
    """
    检查登录请求是否超过速率限制

    Args:
        login_data: 登录请求数据
        request: FastAPI请求对象

    Raises:
        HTTPException 429: 超过登录尝试次数限制
    """
    from app.core.rate_limiter import get_rate_limiter
    from datetime import timedelta

    limiter = get_rate_limiter()

    # 使用用户名/IP作为标识符
    identifier = login_data.username

    # 检查速率限制
    allowed, remaining, reset_seconds = await limiter.check_rate_limit(
        identifier=identifier,
        limit=5,  # 每分钟最多5次
        window=timedelta(minutes=1),
        endpoint="login"
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录尝试过于频繁，请 {reset_seconds} 秒后重试",
            headers={
                "X-RateLimit-Limit": "5",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_seconds),
                "Retry-After": str(reset_seconds),
            }
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    *,
    db: AsyncSession = Depends(get_db),
    login_data: LoginRequest,
    request: Request,
) -> Any:
    """
    用户登录

    支持使用用户名或邮箱登录。
    包含速率限制：每分钟最多5次尝试，超出后需要等待。

    Args:
        db: 数据库会话
        login_data: 登录请求数据
        request: FastAPI请求对象（用于速率限制）

    Returns:
        AuthResponse: 包含access_token、refresh_token和用户信息

    Raises:
        HTTPException 401: 用户名或密码错误
        HTTPException 403: 账户已被禁用
        HTTPException 429: 超过登录尝试次数限制
    """
    # 先检查速率限制
    await check_login_rate_limit(login_data, request)

    try:
        result = await AuthService.login(db=db, login_data=login_data)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    *,
    db: AsyncSession = Depends(get_db),
    token_data: RefreshTokenRequest,
) -> Any:
    """
    刷新访问令牌

    使用refresh_token获取新的access_token和refresh_token。

    Args:
        db: 数据库会话
        token_data: 包含refresh_token的请求数据

    Returns:
        TokenResponse: 包含新的access_token和refresh_token

    Raises:
        HTTPException 401: refresh_token无效或过期
    """
    try:
        result = await AuthService.refresh_token(
            db=db,
            refresh_token=token_data.refresh_token
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取当前用户信息

    需要在Authorization header中提供Bearer token。

    Args:
        current_user: 当前认证用户

    Returns:
        UserResponse: 当前用户信息

    Raises:
        HTTPException 401: 未提供token或token无效
    """
    return UserResponse.model_validate(current_user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    *,
    db: AsyncSession = Depends(get_db),
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    修改密码

    需要提供旧密码进行验证。

    Args:
        db: 数据库会话
        password_data: 包含旧密码和新密码的请求数据
        current_user: 当前认证用户

    Returns:
        None

    Raises:
        HTTPException 400: 旧密码错误
    """
    try:
        await AuthService.change_password(
            db=db,
            user_id=current_user.id,
            old_password=password_data.old_password,
            new_password=password_data.new_password,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    用户登出

    将当前 Token 加入黑名单，实现服务端主动注销。
    客户端应删除存储的 token。

    Args:
        credentials: HTTP Bearer credentials
        current_user: 当前认证用户

    Returns:
        None

    Raises:
        HTTPException 500: 服务端错误
    """
    from app.core.security import get_token_jti
    from app.core.token_blacklist import get_token_blacklist

    token = credentials.credentials
    jti = get_token_jti(token)

    if jti:
        blacklist = get_token_blacklist()
        await blacklist.add_to_blacklist(
            jti=jti,
            user_id=str(current_user.id),
            reason="logout"
        )


@router.get("/verify-token", response_model=UserResponse)
async def verify_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """
    验证token有效性

    验证提供的access_token是否有效并返回用户信息。

    Args:
        credentials: HTTP Bearer credentials
        db: 数据库会话

    Returns:
        UserResponse: 用户信息

    Raises:
        HTTPException 401: token无效
    """
    from app.core.security import verify_token

    token = credentials.credentials
    user_id = verify_token(token, token_type="access")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_info = await AuthService.get_current_user(
        db=db,
        user_id=user_id
    )

    return user_info
