"""
教案分享 API Schema - AI英语教学系统

定义教案分享相关的请求和响应数据结构。
"""
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SharePermission(str, Enum):
    """分享权限枚举"""
    VIEW = "view"      # 仅查看
    EDIT = "edit"      # 可编辑
    COPY = "copy"      # 可复制


class ShareStatus(str, Enum):
    """分享状态枚举"""
    PENDING = "pending"    # 待接受
    ACCEPTED = "accepted"  # 已接受
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"    # 已过期


# ==================== 请求 Schema ====================

class CreateShareRequest(BaseModel):
    """创建分享请求"""
    shared_to: uuid.UUID = Field(..., description="接收分享的教师ID")
    permission: SharePermission = Field(
        default=SharePermission.VIEW,
        description="分享权限"
    )
    message: str | None = Field(None, max_length=500, description="分享附言")
    expires_days: int | None = Field(
        None,
        ge=1,
        le=365,
        description="有效期（天数），不设置则永久有效"
    )


class UpdateShareStatusRequest(BaseModel):
    """更新分享状态请求"""
    status: ShareStatus = Field(..., description="新状态")


# ==================== 响应 Schema ====================

class UserSummary(BaseModel):
    """用户摘要信息"""
    id: uuid.UUID
    username: str
    full_name: str | None
    email: str

    class Config:
        from_attributes = True


class LessonPlanSummary(BaseModel):
    """教案摘要信息"""
    id: uuid.UUID
    title: str
    topic: str
    level: str
    duration: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShareResponse(BaseModel):
    """分享记录响应"""
    id: uuid.UUID
    lesson_plan: LessonPlanSummary
    shared_by: UserSummary
    shared_to: UserSummary
    permission: SharePermission
    status: ShareStatus
    message: str | None
    expires_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ShareListResponse(BaseModel):
    """分享列表响应"""
    shares: list[ShareResponse]
    total: int
    page: int
    page_size: int


class CreateShareResponse(BaseModel):
    """创建分享响应"""
    share: ShareResponse
    message: str = "分享已发送，等待对方接受"


# ==================== 复制相关 Schema ====================

class DuplicateLessonPlanRequest(BaseModel):
    """复制教案请求"""
    new_title: str | None = Field(None, max_length=255, description="新教案标题，不设置则自动添加副本标识")
    include_shares: bool = Field(
        default=False,
        description="是否同时复制分享记录（通常不复制）"
    )


class DuplicateLessonPlanResponse(BaseModel):
    """复制教案响应"""
    lesson_plan: LessonPlanSummary
    message: str = "教案已成功复制"


class CreateFromTemplateRequest(BaseModel):
    """从模板创建教案请求"""
    title: str = Field(..., max_length=255, description="教案标题")
    topic: str = Field(..., max_length=255, description="教学主题")
    level: str = Field(..., pattern=r'^(A1|A2|B1|B2|C1|C2)$', description="CEFR等级")
    duration: int = Field(default=45, ge=15, le=180, description="课程时长（分钟）")
    target_exam: str | None = Field(None, max_length=50, description="目标考试类型")
    additional_requirements: str | None = Field(
        None,
        max_length=1000,
        description="额外要求"
    )


class LessonPlanTemplateSummary(BaseModel):
    """教案模板摘要"""
    id: uuid.UUID
    name: str
    description: str | None
    level: str
    target_exam: str | None
    is_system: bool
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: list[LessonPlanTemplateSummary]
    total: int
    page: int
    page_size: int
