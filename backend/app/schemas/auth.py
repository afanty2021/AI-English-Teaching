"""
认证相关的Pydantic Schemas
定义用户注册、登录、认证响应等数据结构
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """
    用户注册请求
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="用户名"
    )
    email: EmailStr = Field(
        ...,
        description="邮箱地址"
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="密码"
    )
    confirm_password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="确认密码"
    )
    role: str = Field(
        ...,
        description="角色（student 或 teacher）"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="真实姓名"
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="电话号码"
    )
    organization_name: Optional[str] = Field(
        None,
        max_length=255,
        description="组织名称（教师注册时可选）"
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """验证角色"""
        if v not in ["student", "teacher"]:
            raise ValueError("角色必须是 student 或 teacher")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str, info) -> str:
        """验证确认密码"""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("用户名只能包含字母、数字、下划线和连字符")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        验证密码强度

        要求：
        - 至少 8 位
        - 包含大写字母
        - 包含小写字母
        - 包含数字
        - 包含特殊字符
        """
        import re

        if len(v) < 8:
            raise ValueError("密码长度至少 8 位")

        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")

        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含至少一个小写字母")

        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含至少一个数字")

        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("密码必须包含至少一个特殊字符")

        return v


class LoginRequest(BaseModel):
    """
    用户登录请求
    """
    username: str = Field(
        ...,
        description="用户名或邮箱"
    )
    password: str = Field(
        ...,
        description="密码"
    )


class TokenResponse(BaseModel):
    """
    Token响应
    """
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")


class UserResponse(BaseModel):
    """
    用户信息响应
    """
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="真实姓名")
    phone: Optional[str] = Field(None, description="电话号码")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    role: str = Field(..., description="用户角色")
    is_active: bool = Field(..., description="是否激活")
    is_superuser: bool = Field(..., description="是否超级管理员")
    organization_id: Optional[uuid.UUID] = Field(None, description="所属组织ID")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class AuthResponse(BaseModel):
    """
    认证响应（登录/注册成功后返回）
    """
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: UserResponse = Field(..., description="用户信息")


class RefreshTokenRequest(BaseModel):
    """
    刷新Token请求
    """
    refresh_token: str = Field(..., description="刷新令牌")


class ChangePasswordRequest(BaseModel):
    """
    修改密码请求
    """
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="新密码"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        验证新密码强度

        要求：
        - 至少 8 位
        - 包含大写字母
        - 包含小写字母
        - 包含数字
        - 包含特殊字符
        """
        import re

        if len(v) < 8:
            raise ValueError("密码长度至少 8 位")

        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")

        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含至少一个小写字母")

        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含至少一个数字")

        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("密码必须包含至少一个特殊字符")

        return v


class PasswordResetRequest(BaseModel):
    """
    密码重置请求
    """
    email: EmailStr = Field(..., description="邮箱地址")


class PasswordResetConfirm(BaseModel):
    """
    密码重置确认
    """
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="新密码"
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        验证新密码强度

        要求：
        - 至少 8 位
        - 包含大写字母
        - 包含小写字母
        - 包含数字
        - 包含特殊字符
        """
        import re

        if len(v) < 8:
            raise ValueError("密码长度至少 8 位")

        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含至少一个大写字母")

        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含至少一个小写字母")

        if not re.search(r"[0-9]", v):
            raise ValueError("密码必须包含至少一个数字")

        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v):
            raise ValueError("密码必须包含至少一个特殊字符")

        return v
