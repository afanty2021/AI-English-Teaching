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


@router.get("/{lesson_plan_id}/export/{export_format}")
async def export_lesson_plan(
    lesson_plan_id: uuid.UUID,
    export_format: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_plan_service: LessonPlanService = Depends(get_lesson_plan_service),
):
    """
    导出教案文件

    支持导出为Word (.docx)、PowerPoint (.pptx) 或 PDF (.pdf) 格式。
    直接返回文件流供下载。

    Args:
        lesson_plan_id: 教案ID
        export_format: 导出格式 (docx/pptx/pdf)
        db: 数据库会话
        current_user: 当前用户
        lesson_plan_service: 教案服务

    Returns:
        FileResponse: 导出的文件

    Raises:
        HTTPException: 如果教案不存在、无权访问或格式不支持
    """
    from fastapi.responses import Response
    from app.services.export_service import ExportService

    # 验证导出格式
    valid_formats = ["docx", "pptx", "pdf"]
    if export_format not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的导出格式: {export_format}。支持的格式: {', '.join(valid_formats)}"
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
        export_service = ExportService()

        # 根据格式导出
        if export_format == "docx":
            file_content, file_name = await export_service.export_to_word(lesson_plan)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif export_format == "pptx":
            file_content, file_name = await export_service.export_to_ppt(lesson_plan)
            media_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        else:  # pdf
            file_content, file_name = await export_service.export_to_pdf(lesson_plan)
            media_type = "application/pdf"

        # 返回文件
        return Response(
            content=file_content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"'
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出教案失败: {str(e)}"
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
