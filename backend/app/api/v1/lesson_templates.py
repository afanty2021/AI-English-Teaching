"""
教案模板API v1
提供教案模板的CRUD、应用、收藏等功能
"""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole, LessonPlanTemplate
from app.schemas.lesson_plan import (
    TemplateListResponse,
    TemplateDetailResponse,
    TemplateListItem,
    CreateTemplateRequest,
    UpdateTemplateRequest,
    TemplateQueryParams,
    ApplyTemplateResponse,
)

router = APIRouter()


# 官方模板分类
OFFICIAL_CATEGORIES = [
    {"key": "reading", "label": "阅读理解", "icon": "Reading"},
    {"key": "listening", "label": "听力训练", "icon": "Headset"},
    {"key": "speaking", "label": "口语会话", "icon": "Microphone"},
    {"key": "writing", "label": "写作指导", "icon": "Edit"},
    {"key": "grammar", "label": "语法讲解", "icon": "Grammar"},
    {"key": "vocabulary", "label": "词汇记忆", "icon": "Book"},
    {"key": "exam", "label": "考试备考", "icon": "Document"},
    {"key": "culture", "label": "文化拓展", "icon": "Clock"},
]


@router.get("/categories")
async def get_template_categories() -> Any:
    """
    获取官方模板分类

    Returns:
        list: 分类列表
    """
    return OFFICIAL_CATEGORIES


@router.get("", response_model=TemplateListResponse)
async def list_templates(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="分类过滤"),
    level: Optional[str] = Query(None, description="等级过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    is_public: Optional[bool] = Query(None, description="公开过滤"),
    is_official: Optional[bool] = Query(None, description="官方模板过滤"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向"),
) -> Any:
    """
    获取教案模板列表

    支持按分类、等级、搜索词等条件筛选，支持分页和排序。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        page: 页码
        page_size: 每页数量
        category: 分类过滤
        level: 等级过滤
        search: 搜索关键词
        is_public: 公开过滤
        is_official: 官方模板过滤
        sort_by: 排序字段
        sort_order: 排序方向

    Returns:
        TemplateListResponse: 模板列表
    """
    # 构建查询条件
    conditions = [LessonPlanTemplate.is_active == True]

    # 教师只能看到公开模板或自己创建的模板
    if current_user.role == UserRole.TEACHER:
        conditions.append(
            (LessonPlanTemplate.is_system == True) |
            (LessonPlanTemplate.created_by == current_user.id)
        )
    elif current_user.role != UserRole.ADMIN:
        # 非管理员只能看公开模板
        conditions.append(LessonPlanTemplate.is_system == True)

    if category:
        # 这里需要关联查询分类，简化为按名称模糊搜索
        pass

    if level:
        conditions.append(LessonPlanTemplate.level == level.upper())

    if search:
        from sqlalchemy import or_
        conditions.append(
            or_(
                LessonPlanTemplate.name.ilike(f"%{search}%"),
                LessonPlanTemplate.description.ilike(f"%{search}%")
            )
        )

    if is_public is not None:
        conditions.append(LessonPlanTemplate.is_system == is_public)

    if is_official is not None:
        conditions.append(LessonPlanTemplate.is_system == is_official)

    # 查询总数
    count_query = select(func.count(LessonPlanTemplate.id)).where(*conditions)
    total = await db.execute(count_query)
    total = total.scalar()

    # 构建排序
    sort_column = getattr(LessonPlanTemplate, sort_by, LessonPlanTemplate.created_at)
    if sort_order == "desc":
        sort_column = desc(sort_column)

    # 查询数据
    offset = (page - 1) * page_size
    query = (
        select(LessonPlanTemplate)
        .where(*conditions)
        .order_by(sort_column)
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    templates = result.scalars().all()

    # 转换为列表项
    items = []
    for t in templates:
        items.append(TemplateListItem(
            id=t.id,
            name=t.name,
            description=t.description,
            category_key="",
            category_label="",
            level=t.level,
            duration=45,  # 默认时长
            thumbnail_url=None,
            is_public=not t.is_system,
            is_official=t.is_system,
            usage_count=t.usage_count,
            rating=0.0,  # 默认评分
            created_at=t.created_at,
        ))

    return TemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{template_id}", response_model=TemplateDetailResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取模板详情

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        TemplateDetailResponse: 模板详情
    """
    template = await db.execute(
        select(LessonPlanTemplate).where(
            LessonPlanTemplate.id == template_id,
            LessonPlanTemplate.is_active == True
        )
    )
    template = template.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # 检查访问权限
    if (
        not template.is_system
        and template.created_by != current_user.id
        and current_user.role != UserRole.ADMIN
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此模板"
        )

    return TemplateDetailResponse(
        template={
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "level": template.level,
            "target_exam": template.target_exam,
            "template_structure": template.template_structure,
            "is_system": template.is_system,
            "usage_count": template.usage_count,
            "is_active": template.is_active,
            "created_by": template.created_by,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
        }
    )


@router.post("", response_model=TemplateDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    request: CreateTemplateRequest,
) -> Any:
    """
    创建教案模板

    教师可以创建自己的教案模板。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（需要是教师）
        request: 创建请求

    Returns:
        TemplateDetailResponse: 创建的模板详情
    """
    # 检查权限
    if current_user.role != UserRole.TEACHER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能创建模板"
        )

    # 创建模板
    template = LessonPlanTemplate(
        name=request.name,
        description=request.description,
        level=request.level.upper(),
        target_exam=request.target_exam,
        template_structure=request.structure.model_dump(),
        is_system=False,
        is_public=request.is_public,
        created_by=current_user.id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return TemplateDetailResponse(
        template={
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "level": template.level,
            "target_exam": template.target_exam,
            "template_structure": template.template_structure,
            "is_system": template.is_system,
            "usage_count": template.usage_count,
            "is_active": template.is_active,
            "created_by": template.created_by,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
        }
    )


@router.put("/{template_id}", response_model=TemplateDetailResponse)
async def update_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    request: UpdateTemplateRequest,
) -> Any:
    """
    更新教案模板

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        template_id: 模板ID
        request: 更新请求

    Returns:
        TemplateDetailResponse: 更新后的模板详情
    """
    template = await db.execute(
        select(LessonPlanTemplate).where(
            LessonPlanTemplate.id == template_id,
            LessonPlanTemplate.is_active == True
        )
    )
    template = template.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # 检查权限
    if template.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此模板"
        )

    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(template, field, value)

    await db.commit()
    await db.refresh(template)

    return TemplateDetailResponse(
        template={
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "level": template.level,
            "target_exam": template.target_exam,
            "template_structure": template.template_structure,
            "is_system": template.is_system,
            "usage_count": template.usage_count,
            "is_active": template.is_active,
            "created_by": template.created_by,
            "created_at": template.created_at,
            "updated_at": template.updated_at,
        }
    )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
) -> None:
    """
    删除教案模板

    软删除模板（将is_active设为False）。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        template_id: 模板ID
    """
    template = await db.execute(
        select(LessonPlanTemplate).where(
            LessonPlanTemplate.id == template_id,
            LessonPlanTemplate.is_active == True
        )
    )
    template = template.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # 检查权限
    if template.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此模板"
        )

    # 软删除
    template.is_active = False
    await db.commit()


@router.post("/{template_id}/duplicate", response_model=TemplateDetailResponse)
async def duplicate_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
) -> Any:
    """
    复制模板

    创建当前用户自己的模板副本。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        template_id: 源模板ID

    Returns:
        TemplateDetailResponse: 复制的模板详情
    """
    template = await db.execute(
        select(LessonPlanTemplate).where(
            LessonPlanTemplate.id == template_id,
            LessonPlanTemplate.is_active == True
        )
    )
    template = template.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # 创建副本
    new_template = LessonPlanTemplate(
        name=f"{template.name} (副本)",
        description=template.description,
        level=template.level,
        target_exam=template.target_exam,
        template_structure=template.template_structure,
        is_system=False,
        is_public=False,
        created_by=current_user.id,
    )
    db.add(new_template)
    await db.commit()
    await db.refresh(new_template)

    return TemplateDetailResponse(
        template={
            "id": new_template.id,
            "name": new_template.name,
            "description": new_template.description,
            "level": new_template.level,
            "target_exam": new_template.target_exam,
            "template_structure": new_template.template_structure,
            "is_system": new_template.is_system,
            "usage_count": new_template.usage_count,
            "is_active": new_template.is_active,
            "created_by": new_template.created_by,
            "created_at": new_template.created_at,
            "updated_at": new_template.updated_at,
        }
    )


@router.post("/{template_id}/apply", response_model=ApplyTemplateResponse)
async def apply_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    lesson_data: dict = None,
) -> Any:
    """
    应用模板

    基于模板生成教案。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（需要是教师）
        template_id: 模板ID
        lesson_data: 可选的教案数据

    Returns:
        ApplyTemplateResponse: 生成的教案
    """
    if current_user.role != UserRole.TEACHER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能应用模板"
        )

    template = await db.execute(
        select(LessonPlanTemplate).where(
            LessonPlanTemplate.id == template_id,
            LessonPlanTemplate.is_active == True
        )
    )
    template = template.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # 增加使用次数
    template.usage_count += 1
    await db.commit()

    # 基于模板生成教案数据
    lesson_plan_id = uuid.uuid4()
    lesson_plan_data = {
        "id": str(lesson_plan_id),
        "title": lesson_data.get("title", f"基于模板 {template.name} 的教案") if lesson_data else f"基于模板 {template.name} 的教案",
        "topic": lesson_data.get("topic", template.template_structure.get("sections", [{}])[0].get("label", "通用")) if lesson_data else "通用",
        "level": template.level,
        "duration": template.duration if hasattr(template, 'duration') else 45,
        "template_id": str(template_id),
        "template_structure": template.template_structure,
    }

    return ApplyTemplateResponse(
        lesson_plan_id=lesson_plan_id,
        lesson_plan=lesson_plan_data,
    )


@router.post("/{template_id}/favorite")
async def toggle_favorite_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
) -> Any:
    """
    收藏/取消收藏模板

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        template_id: 模板ID

    Returns:
        dict: 操作结果
    """
    # TODO: 实现收藏功能
    return {"favorited": True, "message": "收藏成功"}


@router.post("/{template_id}/rate")
async def rate_template(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    template_id: uuid.UUID,
    rating: int = Query(..., ge=1, le=5, description="评分 1-5"),
) -> Any:
    """
    评价模板

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        template_id: 模板ID
        rating: 评分

    Returns:
        dict: 评价结果
    """
    template = await db.execute(
        select(LessonPlanTemplate).where(
            LessonPlanTemplate.id == template_id,
            LessonPlanTemplate.is_active == True
        )
    )
    template = template.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # TODO: 实现评分功能（需要单独的评分表）
    return {"average_rating": rating, "message": "评价成功"}
