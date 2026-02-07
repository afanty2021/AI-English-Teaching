"""
导出模板API - AI英语教学系统
提供教案导出模板的CRUD接口
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User, UserRole
from app.services.template_service import (
    ExportTemplateService,
    TemplateCreateRequest,
    TemplateResponse,
    TemplateUpdateRequest,
)

router = APIRouter()


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    format: Optional[str] = Query(None, description="按格式过滤"),
    is_system: Optional[bool] = Query(None, description="是否为系统模板"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TemplateResponse]:
    """
    列出导出模板

    权限：所有认证用户

    Args:
        format: 按格式过滤
        is_system: 是否为系统模板
        is_active: 是否激活
        db: 数据库会话
        current_user: 当前用户

    Returns:
        模板列表
    """
    service = ExportTemplateService()

    # 获取用户的组织ID
    organization_id = current_user.organization_id if current_user.organization else None

    templates = await service.list_templates(
        format_filter=format,
        is_system=is_system,
        is_active=is_active,
        organization_id=organization_id,
        db=db,
    )

    return templates


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    """
    创建导出模板

    权限：教师和管理员

    Args:
        template_data: 模板创建请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        创建的模板
    """
    # 权限检查
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.ORGANIZATION_ADMIN]:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限",
        )

    service = ExportTemplateService()

    # 添加组织ID
    template_dict = template_data.model_dump()
    if current_user.organization:
        template_dict["organization_id"] = current_user.organization_id

    template = await service.create_template(
        template_dict,
        current_user.id,
        db,
    )

    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    """
    获取模板详情

    权限：所有认证用户

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        模板详情
    """
    service = ExportTemplateService()
    template = await service.get_template(template_id, db)
    return template


@router.get("/default/{format}", response_model=Optional[TemplateResponse])
async def get_default_template(
    format: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Optional[TemplateResponse]:
    """
    获取指定格式的默认模板

    权限：所有认证用户

    Args:
        format: 模板格式
        db: 数据库会话
        current_user: 当前用户

    Returns:
        默认模板，如果不存在则返回null
    """
    service = ExportTemplateService()
    template = await service.get_default_template(format, db)
    return template


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    update_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    """
    更新模板

    权限：模板创建者、组织管理员或超级管理员

    Args:
        template_id: 模板ID
        update_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        更新后的模板
    """
    from fastapi import HTTPException

    service = ExportTemplateService()
    template = await service.get_template(template_id, db)

    # 权限检查
    is_creator = template.created_by == current_user.id
    is_org_admin = current_user.role == UserRole.ORGANIZATION_ADMIN and template.organization_id == current_user.organization_id
    is_superuser = current_user.is_superuser

    if not (is_creator or is_org_admin or is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此模板",
        )

    updated_template = await service.update_template(template_id, update_data, db)
    return updated_template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    删除模板（软删除）

    权限：模板创建者、组织管理员或超级管理员

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户
    """
    from fastapi import HTTPException

    service = ExportTemplateService()
    template = await service.get_template(template_id, db)

    # 权限检查
    is_creator = template.created_by == current_user.id
    is_org_admin = current_user.role == UserRole.ORGANIZATION_ADMIN and template.organization_id == current_user.organization_id
    is_superuser = current_user.is_superuser

    if not (is_creator or is_org_admin or is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此模板",
        )

    await service.delete_template(template_id, db)


@router.post("/{template_id}/set-default", response_model=TemplateResponse)
async def set_default_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    """
    设置默认模板

    权限：组织管理员或超级管理员

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        更新后的模板
    """
    from fastapi import HTTPException

    # 权限检查
    if current_user.role not in [UserRole.ADMIN, UserRole.ORGANIZATION_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )

    service = ExportTemplateService()
    template = await service.set_default_template(template_id, db)
    return template


@router.post("/{template_id}/validate", response_model=Dict[str, Any])
async def validate_template_variables(
    template_id: uuid.UUID,
    variables: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    验证模板变量

    权限：所有认证用户

    Args:
        template_id: 模板ID
        variables: 提供的变量
        db: 数据库会话
        current_user: 当前用户

    Returns:
        验证结果
    """
    service = ExportTemplateService()
    is_valid, missing_vars = await service.validate_template_variables(
        template_id, variables, db
    )

    return {
        "is_valid": is_valid,
        "missing_variables": missing_vars,
    }


@router.post("/{template_id}/clone", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def clone_template(
    template_id: uuid.UUID,
    new_name: str = Query(..., description="新模板名称"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    """
    克隆模板

    权限：教师和管理员

    Args:
        template_id: 原模板ID
        new_name: 新模板名称
        db: 数据库会话
        current_user: 当前用户

    Returns:
        新模板
    """
    from fastapi import HTTPException

    # 权限检查
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN, UserRole.ORGANIZATION_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限",
        )

    service = ExportTemplateService()
    new_template = await service.clone_template(
        template_id, new_name, current_user.id, db
    )
    return new_template


@router.post("/{template_id}/usage", status_code=status.HTTP_200_OK)
async def increment_template_usage(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """
    增加模板使用次数

    权限：所有认证用户

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        操作结果
    """
    service = ExportTemplateService()
    await service.increment_usage(template_id, db)
    return {"message": "使用次数已更新"}
