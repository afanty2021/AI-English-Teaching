"""
导出模板API - AI英语教学系统
提供教案导出模板的CRUD接口
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.lesson_plan import LessonPlan
from app.models.user import User, UserRole
from app.services.content_renderer_service import ContentRendererService
from app.services.document_generators import (
    PDFDocumentGenerator,
    PPTXDocumentGenerator,
    WordDocumentGenerator,
)
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


@router.post("/{template_id}/preview", status_code=status.HTTP_200_OK)
async def preview_template(
    template_id: uuid.UUID,
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    预览模板效果

    使用指定模板和教案数据生成预览文档

    权限：所有认证用户（只能预览有权限访问的教案）

    Args:
        template_id: 模板ID
        lesson_id: 教案ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        Response: 预览文档（二进制内容）

    Raises:
        HTTPException: 模板不存在、教案不存在或无权限访问
    """
    from fastapi import HTTPException

    # 获取模板
    service = ExportTemplateService()
    template = await service.get_template(template_id, db)

    # 验证格式支持
    supported_formats = {"word", "pdf", "pptx", "markdown"}
    if template.format not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的预览格式: {template.format}",
        )

    # 获取教案数据
    result = await db.execute(
        select(LessonPlan).where(LessonPlan.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在",
        )

    # 权限检查：只能预览自己创建的教案或公开的教案
    is_owner = lesson.teacher_id == current_user.id
    is_public = lesson.is_public
    is_shared = lesson.is_shared

    if not (is_owner or is_public or is_shared):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此教案",
        )

    # 准备模板变量
    template_vars = {
        "teacher_name": current_user.username or current_user.full_name or "教师",
        "school": current_user.organization.name if current_user.organization else "",
        "date": lesson.created_at.strftime("%Y-%m-%d") if lesson.created_at else "",
    }

    # 生成预览文档
    try:
        generator = _get_document_generator(template.format)

        if template.format == "pdf":
            # PDF 生成器使用异步方法
            preview_bytes = await generator.generate_from_lesson_plan(lesson)
        elif template.format == "word":
            # Word 生成器需要处理数据结构
            content = _prepare_lesson_plan_content(lesson)
            preview_bytes = generator.generate(content, template_vars)
        elif template.format == "pptx":
            # PPTX 生成器需要处理数据结构
            content = _prepare_lesson_plan_content(lesson)
            preview_bytes = generator.generate(content, template_vars)
        else:  # markdown
            # Markdown 直接使用 ContentRendererService
            renderer = ContentRendererService(format="markdown")
            markdown_content = renderer.render_lesson_plan(lesson)
            preview_bytes = markdown_content.encode("utf-8")

        # 返回预览
        media_type = _get_media_type(template.format)
        filename = f"preview_{lesson.title}.{_get_extension(template.format)}"

        return Response(
            content=preview_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-Preview-Filename": filename,
                "X-Preview-Format": template.format,
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览生成失败: {str(e)}",
        )


def _get_document_generator(format: str):
    """
    获取对应格式的文档生成器

    Args:
        format: 文档格式

    Returns:
        文档生成器实例

    Raises:
        ValueError: 不支持的格式
    """
    generators = {
        "word": WordDocumentGenerator(),
        "pdf": PDFDocumentGenerator(),
        "pptx": PPTXDocumentGenerator(),
    }
    generator = generators.get(format)
    if generator is None:
        raise ValueError(f"不支持的格式: {format}")
    return generator


def _get_media_type(format: str) -> str:
    """
    获取格式的 MIME 类型

    Args:
        format: 文档格式

    Returns:
        MIME 类型字符串
    """
    media_types = {
        "word": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "markdown": "text/markdown",
    }
    return media_types.get(format, "application/octet-stream")


def _get_extension(format: str) -> str:
    """
    获取格式的文件扩展名

    Args:
        format: 文档格式

    Returns:
        文件扩展名
    """
    extensions = {
        "word": "docx",
        "pdf": "pdf",
        "pptx": "pptx",
        "markdown": "md",
    }
    return extensions.get(format, "bin")


def _prepare_lesson_plan_content(lesson: LessonPlan) -> Dict[str, Any]:
    """
    准备教案数据用于文档生成

    将 LessonPlan 模型转换为文档生成器需要的格式。

    Args:
        lesson: 教案模型实例

    Returns:
        Dict[str, Any]: 格式化后的教案内容
    """
    return {
        "title": lesson.title,
        "level": lesson.level,
        "topic": lesson.topic,
        "duration": lesson.duration,
        "target_exam": lesson.target_exam,
        "objectives": lesson.objectives or {},
        "vocabulary": lesson.vocabulary or {},
        "grammar_points": lesson.grammar_points or [],
        "teaching_structure": lesson.teaching_structure or {},
        "leveled_materials": lesson.leveled_materials or {},
        "exercises": lesson.exercises or {},
        "ppt_outline": lesson.ppt_outline or [],
        "resources": lesson.resources or {},
        "teaching_notes": lesson.teaching_notes,
    }
