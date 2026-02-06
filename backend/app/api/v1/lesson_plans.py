"""
教案 API 路由 - AI英语教学系统
提供教案生成、查询、更新、删除和导出功能
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole
from app.schemas.lesson_plan import (
    ExportLessonPlanRequest,
    GenerateLessonPlanRequest,
    LessonPlanDetail,
    LessonPlanExportResponse,
    LessonPlanListResponse,
    LessonPlanObjectives,
    LessonPlanResponse,
    LessonPlanSummary,
    UpdateLessonPlanRequest,
)
from app.schemas.lesson_share import (
    CreateFromTemplateRequest,
    DuplicateLessonPlanRequest,
    DuplicateLessonPlanResponse,
    TemplateListResponse,
)
from app.services.lesson_plan_service import get_lesson_plan_service, LessonPlanService

router = APIRouter()


@router.post("/", response_model=LessonPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson_plan(
    request: GenerateLessonPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> LessonPlanResponse:
    """
    生成新教案

    使用AI根据教师的请求生成完整的教案，包括：
    - 教学目标
    - 核心词汇
    - 语法点
    - 教学流程
    - 分层阅读材料
    - 练习题
    - PPT大纲

    Args:
        request: 生成教案请求
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        LessonPlanResponse: 生成的教案

    Raises:
        HTTPException: 如果用户不是教师或生成失败
    """
    # 验证用户权限
    if current_user.role != UserRole.TEACHER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能创建教案"
        )

    try:
        # 生成教案
        lesson_plan = await lesson_plan_service.generate_lesson_plan(
            db=db,
            teacher_id=current_user.id,
            request=request,
        )

        # 转换为响应格式
        return _convert_to_response(lesson_plan)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI服务暂时不可用: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"教案生成失败: {str(e)}"
        )


@router.get("/", response_model=LessonPlanListResponse)
async def list_lesson_plans(
    status: Optional[str] = Query(None, description="按状态筛选"),
    level: Optional[str] = Query(None, description="按等级筛选"),
    target_exam: Optional[str] = Query(None, description="按考试类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> LessonPlanListResponse:
    """
    列出教案

    支持按状态、等级、考试类型筛选，支持分页。

    Args:
        status: 状态筛选
        level: 等级筛选
        target_exam: 考试类型筛选
        page: 页码
        page_size: 每页大小
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        LessonPlanListResponse: 教案列表
    """
    # 教师只能查看自己的教案，管理员可以查看所有
    teacher_id = current_user.id if current_user.role == UserRole.TEACHER else None

    # 如果是超级管理员，可以查看所有教案
    if current_user.is_superuser:
        teacher_id = None

    try:
        lesson_plans, total = await lesson_plan_service.list_lesson_plans(
            db=db,
            teacher_id=teacher_id,
            status=status,
            level=level,
            target_exam=target_exam,
            page=page,
            page_size=page_size,
        )

        return LessonPlanListResponse(
            lesson_plans=[_convert_to_summary(lp) for lp in lesson_plans],
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取教案列表失败: {str(e)}"
        )


@router.get("/{lesson_plan_id}", response_model=LessonPlanResponse)
async def get_lesson_plan(
    lesson_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> LessonPlanResponse:
    """
    获取教案详情

    Args:
        lesson_plan_id: 教案ID
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        LessonPlanResponse: 教案详情

    Raises:
        HTTPException: 如果教案不存在或无权访问
    """
    lesson_plan = await lesson_plan_service.get_lesson_plan(db, lesson_plan_id)

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 检查权限：教师只能查看自己的教案，管理员可以查看所有
    if (
        current_user.role == UserRole.TEACHER
        and not current_user.is_superuser
        and lesson_plan.teacher_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此教案"
        )

    return _convert_to_response(lesson_plan)


@router.put("/{lesson_plan_id}", response_model=LessonPlanResponse)
async def update_lesson_plan(
    lesson_plan_id: uuid.UUID,
    request: UpdateLessonPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> LessonPlanResponse:
    """
    更新教案

    只能更新教案的基本信息和教学反思，不能修改AI生成的内容。

    Args:
        lesson_plan_id: 教案ID
        request: 更新请求
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        LessonPlanResponse: 更新后的教案

    Raises:
        HTTPException: 如果教案不存在或无权修改
    """
    lesson_plan = await lesson_plan_service.get_lesson_plan(db, lesson_plan_id)

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 只有教案的创建者或管理员可以更新
    if (
        lesson_plan.teacher_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权修改此教案"
        )

    # 构建更新字典
    updates = request.model_dump(exclude_unset=True)

    try:
        updated_plan = await lesson_plan_service.update_lesson_plan(
            db=db,
            lesson_plan_id=lesson_plan_id,
            updates=updates,
        )

        if not updated_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="教案不存在"
            )

        return _convert_to_response(updated_plan)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新教案失败: {str(e)}"
        )


@router.delete("/{lesson_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson_plan(
    lesson_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> None:
    """
    删除教案

    Args:
        lesson_plan_id: 教案ID
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Raises:
        HTTPException: 如果教案不存在或无权删除
    """
    lesson_plan = await lesson_plan_service.get_lesson_plan(db, lesson_plan_id)

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 只有教案的创建者或管理员可以删除
    if (
        lesson_plan.teacher_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除此教案"
        )

    try:
        success = await lesson_plan_service.delete_lesson_plan(
            db=db,
            lesson_plan_id=lesson_plan_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="教案不存在"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除教案失败: {str(e)}"
        )


@router.get("/{lesson_plan_id}/export/pdf")
async def export_lesson_plan_pdf(
    lesson_plan_id: uuid.UUID,
    include_objectives: bool = Query(True, description="是否包含教学目标"),
    include_structure: bool = Query(True, description="是否包含教学流程"),
    include_vocabulary: bool = Query(True, description="是否包含词汇表"),
    include_grammar: bool = Query(True, description="是否包含语法点"),
    include_materials: bool = Query(True, description="是否包含分层材料"),
    include_exercises: bool = Query(True, description="是否包含练习题"),
    include_ppt_outline: bool = Query(True, description="是否包含PPT大纲"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
):
    """
    导出教案为PDF格式

    支持自定义导出内容，提供灵活的导出选项。

    Args:
        lesson_plan_id: 教案ID
        include_objectives: 是否包含教学目标
        include_structure: 是否包含教学流程
        include_vocabulary: 是否包含词汇表
        include_grammar: 是否包含语法点
        include_materials: 是否包含分层材料
        include_exercises: 是否包含练习题
        include_ppt_outline: 是否包含PPT大纲
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        FileResponse: PDF文件

    Raises:
        HTTPException: 如果教案不存在或无权访问
    """
    from fastapi.responses import Response
    from app.services.lesson_plan_export_service import get_lesson_plan_export_service

    # 获取教案
    lesson_plan = await lesson_plan_service.get_lesson_plan(db, lesson_plan_id)

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 检查权限
    if (
        current_user.role == UserRole.TEACHER
        and not current_user.is_superuser
        and lesson_plan.teacher_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权导出此教案"
        )

    try:
        # 准备导出选项
        options = {
            'include_objectives': include_objectives,
            'include_structure': include_structure,
            'include_vocabulary': include_vocabulary,
            'include_grammar': include_grammar,
            'include_materials': include_materials,
            'include_exercises': include_exercises,
            'include_ppt_outline': include_ppt_outline,
        }

        # 准备教师信息
        teacher = {
            'username': current_user.username,
            'email': current_user.email,
        }

        # 准备教案数据
        lesson_plan_data = lesson_plan.__dict__.copy()

        # 使用导出服务
        export_service = get_lesson_plan_export_service()
        pdf_content = await export_service.export_as_pdf(
            lesson_plan=lesson_plan_data,
            teacher=teacher,
            options=options
        )

        # 生成文件名
        file_name = f"教案-{lesson_plan.title}-{lesson_plan.level}.pdf"

        # 返回PDF文件
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF导出失败: {str(e)}"
        )


@router.get("/{lesson_plan_id}/export/markdown")
async def export_lesson_plan_markdown(
    lesson_plan_id: uuid.UUID,
    include_objectives: bool = Query(True, description="是否包含教学目标"),
    include_structure: bool = Query(True, description="是否包含教学流程"),
    include_vocabulary: bool = Query(True, description="是否包含词汇表"),
    include_grammar: bool = Query(True, description="是否包含语法点"),
    include_materials: bool = Query(True, description="是否包含分层材料"),
    include_exercises: bool = Query(True, description="是否包含练习题"),
    include_ppt_outline: bool = Query(True, description="是否包含PPT大纲"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
):
    """
    导出教案为Markdown格式

    支持自定义导出内容，提供灵活的导出选项。

    Args:
        lesson_plan_id: 教案ID
        include_objectives: 是否包含教学目标
        include_structure: 是否包含教学流程
        include_vocabulary: 是否包含词汇表
        include_grammar: 是否包含语法点
        include_materials: 是否包含分层材料
        include_exercises: 是否包含练习题
        include_ppt_outline: 是否包含PPT大纲
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        Markdown文本

    Raises:
        HTTPException: 如果教案不存在或无权访问
    """
    from fastapi.responses import Response

    # 获取教案
    lesson_plan = await lesson_plan_service.get_lesson_plan(db, lesson_plan_id)

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 检查权限
    if (
        current_user.role == UserRole.TEACHER
        and not current_user.is_superuser
        and lesson_plan.teacher_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权导出此教案"
        )

    try:
        # 准备导出选项
        options = {
            'include_objectives': include_objectives,
            'include_structure': include_structure,
            'include_vocabulary': include_vocabulary,
            'include_grammar': include_grammar,
            'include_materials': include_materials,
            'include_exercises': include_exercises,
            'include_ppt_outline': include_ppt_outline,
        }

        # 准备教师信息
        teacher = {
            'username': current_user.username,
            'email': current_user.email,
        }

        # 准备教案数据
        lesson_plan_data = lesson_plan.__dict__.copy()

        # 使用导出服务
        export_service = get_lesson_plan_export_service()
        markdown_content = await export_service.export_as_markdown(
            lesson_plan=lesson_plan_data,
            teacher=teacher,
            options=options
        )

        # 返回Markdown内容
        return Response(
            content=markdown_content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="教案-{lesson_plan.title}-{lesson_plan.level}.md"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Markdown导出失败: {str(e)}"
        )


@router.get("/{lesson_plan_id}/export/ppt")
async def export_lesson_plan_ppt(
    lesson_plan_id: uuid.UUID,
    color_scheme: str = Query("default", description="PPT配色方案"),
    include_slide_numbers: bool = Query(True, description="是否包含幻灯片编号"),
    include_notes: bool = Query(True, description="是否包含演讲者备注"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
):
    """
    导出教案为PPT格式

    支持自定义PPT样式和选项。

    Args:
        lesson_plan_id: 教案ID
        color_scheme: PPT配色方案 (default/blue/green/purple)
        include_slide_numbers: 是否包含幻灯片编号
        include_notes: 是否包含演讲者备注
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        FileResponse: PPTX文件

    Raises:
        HTTPException: 如果教案不存在或无权访问
    """
    from fastapi.responses import Response
    from app.services.ppt_export_service import get_ppt_export_service

    # 验证配色方案
    valid_schemes = ["default", "blue", "green", "purple"]
    if color_scheme not in valid_schemes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的配色方案: {color_scheme}。支持的方案: {', '.join(valid_schemes)}"
        )

    # 获取教案
    lesson_plan = await lesson_plan_service.get_lesson_plan(db, lesson_plan_id)

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 检查权限
    if (
        current_user.role == UserRole.TEACHER
        and not current_user.is_superuser
        and lesson_plan.teacher_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权导出此教案"
        )

    try:
        # 准备导出选项
        options = {
            'color_scheme': color_scheme,
            'include_slide_numbers': include_slide_numbers,
            'include_notes': include_notes,
        }

        # 准备教案数据
        lesson_plan_data = lesson_plan.__dict__.copy()

        # 使用PPT导出服务
        ppt_service = get_ppt_export_service(color_scheme)
        ppt_content = await ppt_service.export_as_pptx(
            lesson_plan=lesson_plan_data,
            options=options
        )

        # 生成文件名
        file_name = f"教案PPT-{lesson_plan.title}-{lesson_plan.level}.pptx"

        # 返回PPTX文件
        return Response(
            content=ppt_content,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PPT导出失败: {str(e)}"
        )


@router.get("/{lesson_plan_id}/ppt/preview")
async def preview_lesson_plan_ppt(
    lesson_plan_id: uuid.UUID,
    color_scheme: str = Query("default", description="PPT配色方案"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
):
    """
    预览教案PPT

    以HTML格式返回PPT预览，支持在线查看。

    Args:
        lesson_plan_id: 教案ID
        color_scheme: PPT配色方案
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        HTML格式的PPT预览

    Raises:
        HTTPException: 如果教案不存在或无权访问
    """
    from fastapi.responses import Response

    # 获取教案
    lesson_plan = await lesson_plan_service.get_lesson_plan(db, lesson_plan_id)

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 检查权限
    if (
        current_user.role == UserRole.TEACHER
        and not current_user.is_superuser
        and lesson_plan.teacher_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权预览此教案"
        )

    try:
        # 准备教案数据
        lesson_plan_data = lesson_plan.__dict__.copy()

        # 使用PPT导出服务生成HTML
        ppt_service = get_ppt_export_service(color_scheme)
        html_content = await ppt_service.export_as_html(
            lesson_plan=lesson_plan_data
        )

        # 返回HTML预览
        return Response(
            content=html_content,
            media_type="text/html"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PPT预览失败: {str(e)}"
        )


@router.post("/{lesson_plan_id}/regenerate", response_model=LessonPlanResponse)
async def regenerate_lesson_plan(
    lesson_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> LessonPlanResponse:
    """
    重新生成教案

    使用相同参数重新生成教案内容。

    Args:
        lesson_plan_id: 教案ID
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        LessonPlanResponse: 重新生成的教案

    Raises:
        HTTPException: 如果教案不存在或无权访问
    """
    lesson_plan = await lesson_plan_service.get_lesson_plan(db, lesson_plan_id)

    if not lesson_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="教案不存在"
        )

    # 只有教案的创建者或管理员可以重新生成
    if (
        lesson_plan.teacher_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权重新生成此教案"
        )

    try:
        # 从原教案的AI参数构建请求
        original_params = lesson_plan.ai_generation_params or {}
        request = GenerateLessonPlanRequest(**original_params)

        # 重新生成
        new_lesson_plan = await lesson_plan_service.generate_lesson_plan(
            db=db,
            teacher_id=current_user.id,
            request=request,
        )

        return _convert_to_response(new_lesson_plan)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI服务暂时不可用: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新生成教案失败: {str(e)}"
        )


@router.post("/{lesson_plan_id}/duplicate", response_model=LessonPlanResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_lesson_plan(
    lesson_plan_id: uuid.UUID,
    request: DuplicateLessonPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> LessonPlanResponse:
    """
    复制教案

    创建原教案的副本，所有内容完全复制。

    Args:
        lesson_plan_id: 原教案ID
        request: 复制请求
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        LessonPlanResponse: 复制后的新教案

    Raises:
        HTTPException: 如果教案不存在或无权复制
    """
    # 验证用户权限
    if current_user.role != UserRole.TEACHER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能复制教案"
        )

    try:
        new_plan = await lesson_plan_service.duplicate_lesson_plan(
            db=db,
            lesson_plan_id=lesson_plan_id,
            teacher_id=current_user.id,
            new_title=request.new_title,
        )

        return _convert_to_response(new_plan)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"复制教案失败: {str(e)}"
        )


@router.get("/templates", response_model=TemplateListResponse)
async def get_templates(
    level: str | None = Query(None, description="按等级筛选"),
    target_exam: str | None = Query(None, description="按考试类型筛选"),
    is_system: bool | None = Query(None, description="是否仅系统模板"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> TemplateListResponse:
    """
    获取教案模板列表

    支持按等级、考试类型、是否系统模板筛选，支持分页。

    Args:
        level: 等级筛选
        target_exam: 考试类型筛选
        is_system: 是否系统模板筛选
        page: 页码
        page_size: 每页大小
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        TemplateListResponse: 模板列表
    """
    try:
        templates, total = await lesson_plan_service.get_templates(
            db=db,
            level=level,
            target_exam=target_exam,
            is_system=is_system,
            page=page,
            page_size=page_size,
        )

        # 转换为响应格式
        template_summaries = [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "level": t.level,
                "target_exam": t.target_exam,
                "is_system": t.is_system,
                "usage_count": t.usage_count,
                "created_at": t.created_at,
            }
            for t in templates
        ]

        return TemplateListResponse(
            templates=template_summaries,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取模板列表失败: {str(e)}"
        )


@router.post("/from-template/{template_id}", response_model=LessonPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_from_template(
    template_id: uuid.UUID,
    request: CreateFromTemplateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
) -> LessonPlanResponse:
    """
    从模板创建教案

    基于教案模板快速创建新教案，模板提供基础结构和内容。

    Args:
        template_id: 模板ID
        request: 创建请求
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        LessonPlanResponse: 创建的教案

    Raises:
        HTTPException: 如果模板不存在或无权创建
    """
    # 验证用户权限
    if current_user.role != UserRole.TEACHER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能创建教案"
        )

    try:
        new_plan = await lesson_plan_service.create_from_template(
            db=db,
            template_id=template_id,
            teacher_id=current_user.id,
            title=request.title,
            topic=request.topic,
            level=request.level,
            duration=request.duration,
            target_exam=request.target_exam,
            additional_requirements=request.additional_requirements,
        )

        return _convert_to_response(new_plan)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"从模板创建教案失败: {str(e)}"
        )


# ==================== 辅助函数 ====================

def _convert_to_response(lesson_plan) -> LessonPlanResponse:
    """将LessonPlan模型转换为响应格式"""
    # 构建教学目标
    objectives_data = lesson_plan.objectives or {}
    objectives = LessonPlanObjectives(
        language_knowledge=objectives_data.get("language_knowledge", []),
        language_skills=objectives_data.get("language_skills", {}),
        learning_strategies=objectives_data.get("learning_strategies", []),
        cultural_awareness=objectives_data.get("cultural_awareness", []),
        emotional_attitudes=objectives_data.get("emotional_attitudes", []),
    )

    # 构建词汇
    vocabulary = lesson_plan.vocabulary or {}

    # 构建语法点
    grammar_points = lesson_plan.grammar_points or []

    # 构建教学流程
    structure = lesson_plan.teaching_structure or {}

    # 构建分层材料
    leveled_materials = lesson_plan.leveled_materials if isinstance(lesson_plan.leveled_materials, list) else []

    # 构建练习题
    exercises = lesson_plan.exercises or {}

    # 构建PPT大纲 - 确保是列表
    ppt_outline = lesson_plan.ppt_outline if isinstance(lesson_plan.ppt_outline, list) else []

    # 构建资源
    resources = lesson_plan.resources or {}

    # 构建详情
    detail = LessonPlanDetail(
        id=lesson_plan.id,
        title=lesson_plan.title,
        topic=lesson_plan.topic,
        level=lesson_plan.level,
        duration=lesson_plan.duration,
        target_exam=lesson_plan.target_exam,
        status=lesson_plan.status,
        objectives=objectives,
        vocabulary=vocabulary,
        grammar_points=grammar_points,
        structure=structure,
        leveled_materials=leveled_materials,
        exercises=exercises,
        ppt_outline=ppt_outline,
        resources=resources,
        teaching_notes=lesson_plan.teaching_notes,
        generation_time_ms=lesson_plan.generation_time_ms,
        last_generated_at=lesson_plan.last_generated_at,
        created_at=lesson_plan.created_at,
        updated_at=lesson_plan.updated_at,
    )

    return LessonPlanResponse(
        lesson_plan=detail,
        teacher_id=lesson_plan.teacher_id,
    )


def _convert_to_summary(lesson_plan) -> LessonPlanSummary:
    """将LessonPlan模型转换为摘要格式"""
    return LessonPlanSummary(
        id=lesson_plan.id,
        title=lesson_plan.title,
        topic=lesson_plan.topic,
        level=lesson_plan.level,
        duration=lesson_plan.duration,
        target_exam=lesson_plan.target_exam,
        status=lesson_plan.status,
        created_at=lesson_plan.created_at,
        updated_at=lesson_plan.updated_at,
    )
