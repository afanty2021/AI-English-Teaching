"""
认证服务
处理用户注册、登录、token生成等认证相关业务逻辑
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models import User, UserRole
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse


class AuthService:
    """
    认证服务类
    提供用户注册、登录、token生成等功能
    """

    @staticmethod
    async def register(
        db: AsyncSession,
        register_data: RegisterRequest
    ) -> AuthResponse:
        """
        用户注册

        Args:
            db: 数据库会话
            register_data: 注册请求数据

        Returns:
            AuthResponse: 认证响应，包含token和用户信息

        Raises:
            ValueError: 如果用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing_user = await db.execute(
            select(User).where(User.username == register_data.username)
        )
        if existing_user.scalar_one_or_none():
            raise ValueError("用户名已被使用")

        # 检查邮箱是否已存在
        existing_email = await db.execute(
            select(User).where(User.email == register_data.email)
        )
        if existing_email.scalar_one_or_none():
            raise ValueError("邮箱已被注册")

        # 根据角色设置用户角色
        role_map = {
            "student": UserRole.STUDENT,
            "teacher": UserRole.TEACHER,
        }
        user_role = role_map.get(register_data.role, UserRole.STUDENT)

        # 创建新用户
        user = User(
            username=register_data.username,
            email=str(register_data.email),
            password_hash=get_password_hash(register_data.password),
            full_name=register_data.full_name or register_data.username,
            phone=register_data.phone,
            role=user_role,
            is_active=True,
            is_superuser=False,
        )

        # 如果提供了组织名称，需要创建组织并关联
        organization = None
        if register_data.organization_name:
            from app.models import Organization

            # 检查组织名是否已存在
            existing_org = await db.execute(
                select(Organization).where(Organization.name == register_data.organization_name)
            )
            if existing_org.scalar_one_or_none():
                raise ValueError("组织名称已被使用")

            # 创建新组织
            organization = Organization(
                name=register_data.organization_name,
                type="training_center",
                is_active=True,
            )
            db.add(organization)
            await db.flush()  # 获取组织ID

            # 关联组织和用户
            user.organization_id = organization.id
            organization.admin_user_id = user.id

        db.add(user)
        await db.commit()
        await db.refresh(user)

        # 根据角色创建对应的 profile
        if register_data.role == "student":
            from app.models.student import Student

            student = Student(user_id=user.id)
            db.add(student)
            await db.commit()
        elif register_data.role == "teacher":
            from app.models.teacher import Teacher

            teacher = Teacher(user_id=user.id)
            db.add(teacher)
            await db.commit()

        # 生成token
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await db.commit()

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    @staticmethod
    async def login(
        db: AsyncSession,
        login_data: LoginRequest
    ) -> AuthResponse:
        """
        用户登录

        Args:
            db: 数据库会话
            login_data: 登录请求数据

        Returns:
            AuthResponse: 认证响应，包含token和用户信息

        Raises:
            ValueError: 如果用户名或密码错误
        """
        # 尝试通过用户名或邮箱查找用户
        user = await db.execute(
            select(User).where(
                (User.username == login_data.username) | (User.email == login_data.username)
            )
        )
        user = user.scalar_one_or_none()

        if not user:
            raise ValueError("用户名或密码错误")

        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            raise ValueError("用户名或密码错误")

        # 检查用户是否激活
        if not user.is_active:
            raise ValueError("账户已被禁用")

        # 生成token
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={"role": user.role}
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        await db.commit()

        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    @staticmethod
    async def refresh_token(
        db: AsyncSession,
        refresh_token: str
    ) -> dict:
        """
        刷新访问令牌

        Args:
            db: 数据库会话
            refresh_token: 刷新令牌

        Returns:
            dict: 包含新的access_token和refresh_token

        Raises:
            ValueError: 如果token无效或用户不存在
        """
        from app.core.security import decode_token

        # 解码refresh token
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("无效的刷新令牌")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("无效的刷新令牌")

        # 查找用户
        user = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = user.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        if not user.is_active:
            raise ValueError("账户已被禁用")

        # 生成新的token
        new_access_token = create_access_token(
            subject=str(user.id),
            additional_claims={"role": user.role}
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    @staticmethod
    async def get_current_user(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> UserResponse:
        """
        获取当前用户信息

        Args:
            db: 数据库会话
            user_id: 用户ID

        Returns:
            UserResponse: 用户信息

        Raises:
            ValueError: 如果用户不存在
        """
        user = await db.execute(
            select(User)
            .options(selectinload(User.organization))
            .where(User.id == user_id)
        )
        user = user.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        return UserResponse.model_validate(user)

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: uuid.UUID,
        old_password: str,
        new_password: str
    ) -> None:
        """
        修改密码

        Args:
            db: 数据库会话
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Raises:
            ValueError: 如果旧密码错误
        """
        user = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user.scalar_one_or_none()

        if not user:
            raise ValueError("用户不存在")

        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            raise ValueError("旧密码错误")

        # 更新密码
        user.password_hash = get_password_hash(new_password)
        await db.commit()
