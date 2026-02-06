"""
用户相关的 Pydantic schemas
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """用户基础信息"""
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.STUDENT


class UserCreate(UserBase):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None


class UserInDB(UserBase):
    """数据库中的用户"""
    id: str
    username: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应"""
    id: str
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: list[UserResponse]
    total: int
    skip: int
    limit: int


class TeacherSummary(BaseModel):
    """教师摘要信息（用于分享时选择）"""
    id: str
    username: str
    full_name: Optional[str] = None
    email: EmailStr


class TeacherListResponse(BaseModel):
    """教师列表响应"""
    teachers: list[TeacherSummary]
    total: int
    page: int
    page_size: int
