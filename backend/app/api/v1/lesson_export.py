"""
教案导出API v1
提供教案导出任务管理、模板管理等功能
"""
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole

router = APIRouter()


# 导出格式
EXPORT_FORMAT = {
    "word": "docx",
    "pdf": "pdf",
    "pptx": "pptx",
    "markdown": "md",
}

# 导出章节
EXPORT_SECTIONS = [
    "overview",
    "objectives",
    "vocabulary",
    "grammar",
    "structure",
    "materials",
    "exercises",
]


# ==================== 导出模板 ====================

class ExportTemplate:
    """导出模板"""
    TEMPLATES = [
        {
            "id": "standard",
            "name": "标准模板",
            "description": "标准教案导出格式",
            "preview_url": None,
            "format": "word",
            "is_default": True,
        },
        {
            "id": "detailed",
            "name": "详细模板",
            "description": "包含所有章节的详细格式",
            "preview_url": None,
            "format": "pdf",
            "is_default": False,
        },
        {
            "id": "simple",
            "name": "简洁模板",
            "description": "仅包含核心内容的简洁格式",
            "preview_url": None,
            "format": "markdown",
            "is_default": False,
        },
    ]


@router.get("/templates")
async def get_export_templates() -> Any:
    """
    获取导出模板列表

    Returns:
        dict: 导出模板列表
    """
    return {
        "templates": ExportTemplate.TEMPLATES,
    }


# ==================== 导出任务 ====================

class ExportTaskStatus:
    """导出任务状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# 内存中的任务存储（实际应使用数据库）
EXPORT_TASKS = {}


@router.post("/tasks")
async def create_export_task(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_id: str = Query(..., description="教案ID"),
    format: str = Query("word", description="导出格式"),
    sections: Optional[str] = Query(None, description="导出的章节（逗号分隔）"),
    include_teacher_notes: bool = Query(False, description="是否包含教师备注"),
    include_answers: bool = Query(False, description="是否包含答案"),
    language: str = Query("zh", description="导出语言"),
    include_page_numbers: bool = Query(True, description="是否包含页码"),
    include_toc: bool = Query(True, description="是否包含目录"),
) -> Any:
    """
    创建导出任务

    Args:
        db: 数据库会话
        current_user: 当前认证用户（需要是教师）
        lesson_id: 教案ID
        format: 导出格式
        sections: 导出的章节
        include_teacher_notes: 是否包含教师备注
        include_answers: 是否包含答案
        language: 导出语言
        include_page_numbers: 是否包含页码
        include_toc: 是否包含目录

    Returns:
        dict: 创建的任务信息
    """
    if current_user.role != UserRole.TEACHER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能创建导出任务"
        )

    # 验证格式
    if format not in EXPORT_FORMAT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的格式: {format}，支持的格式: {', '.join(EXPORT_FORMAT.keys())}"
        )

    # 解析章节
    if sections:
        selected_sections = [s.strip() for s in sections.split(",")]
    else:
        selected_sections = EXPORT_SECTIONS

    # 创建任务
    task_id = str(uuid.uuid4())
    task = {
        "id": task_id,
        "lesson_id": lesson_id,
        "lesson_title": f"教案-{lesson_id}",  # 实际应从数据库获取
        "format": format,
        "options": {
            "sections": selected_sections,
            "include_teacher_notes": include_teacher_notes,
            "include_answers": include_answers,
            "language": language,
            "include_page_numbers": include_page_numbers,
            "include_toc": include_toc,
        },
        "status": ExportTaskStatus.PENDING,
        "progress": 0,
        "error_message": None,
        "download_url": None,
        "created_at": datetime.utcnow().isoformat(),
        "completed_at": None,
    }
    EXPORT_TASKS[task_id] = task

    return {
        "task": {
            "id": task_id,
            "lesson_id": lesson_id,
            "lesson_title": task["lesson_title"],
            "format": format,
            "status": task["status"],
            "progress": task["progress"],
            "created_at": task["created_at"],
        }
    }


@router.post("/tasks/batch")
async def create_batch_export_tasks(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_ids: list = Query(..., description="教案ID列表"),
    format: str = Query("word", description="导出格式"),
    sections: Optional[str] = Query(None, description="导出的章节"),
) -> Any:
    """
    批量创建导出任务

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        lesson_ids: 教案ID列表
        format: 导出格式
        sections: 导出的章节

    Returns:
        dict: 创建的任务列表
    """
    if current_user.role != UserRole.TEACHER and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师才能创建导出任务"
        )

    tasks = []
    for lesson_id in lesson_ids:
        task_id = str(uuid.uuid4())
        task = {
            "id": task_id,
            "lesson_id": lesson_id,
            "lesson_title": f"教案-{lesson_id}",
            "format": format,
            "options": {
                "sections": [s.strip() for s in sections.split(",")] if sections else EXPORT_SECTIONS,
            },
            "status": ExportTaskStatus.PENDING,
            "progress": 0,
            "error_message": None,
            "download_url": None,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }
        EXPORT_TASKS[task_id] = task
        tasks.append(task)

    return {
        "tasks": [
            {
                "id": t["id"],
                "lesson_id": t["lesson_id"],
                "lesson_title": t["lesson_title"],
                "format": t["format"],
                "status": t["status"],
                "progress": t["progress"],
                "created_at": t["created_at"],
            }
            for t in tasks
        ],
        "total": len(tasks),
    }


@router.get("/tasks/{task_id}")
async def get_export_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取导出任务状态

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        dict: 任务信息
    """
    if task_id not in EXPORT_TASKS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    task = EXPORT_TASKS[task_id]
    return {
        "task": {
            "id": task["id"],
            "lesson_id": task["lesson_id"],
            "lesson_title": task["lesson_title"],
            "format": task["format"],
            "options": task["options"],
            "status": task["status"],
            "progress": task["progress"],
            "error_message": task["error_message"],
            "download_url": task["download_url"],
            "created_at": task["created_at"],
            "completed_at": task["completed_at"],
        }
    }


@router.get("/tasks")
async def get_export_tasks(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    lesson_id: Optional[str] = Query(None, description="教案ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    offset: int = Query(0, ge=0, description="跳过数量"),
) -> Any:
    """
    获取导出任务列表

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        lesson_id: 教案ID过滤
        status: 状态过滤
        limit: 返回数量
        offset: 跳过数量

    Returns:
        dict: 任务列表
    """
    tasks = list(EXPORT_TASKS.values())

    # 过滤
    if lesson_id:
        tasks = [t for t in tasks if t["lesson_id"] == lesson_id]
    if status:
        tasks = [t for t in tasks if t["status"] == status]

    # 排序
    tasks.sort(key=lambda x: x["created_at"], reverse=True)

    # 分页
    total = len(tasks)
    tasks = tasks[offset:offset + limit]

    return {
        "tasks": [
            {
                "id": t["id"],
                "lesson_id": t["lesson_id"],
                "lesson_title": t["lesson_title"],
                "format": t["format"],
                "status": t["status"],
                "progress": t["progress"],
                "error_message": t["error_message"],
                "download_url": t["download_url"],
                "created_at": t["created_at"],
                "completed_at": t["completed_at"],
            }
            for t in tasks
        ],
        "total": total,
    }


@router.post("/tasks/{task_id}/cancel")
async def cancel_export_task(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task_id: str,
) -> Any:
    """
    取消导出任务

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        task_id: 任务ID

    Returns:
        dict: 操作结果
    """
    if task_id not in EXPORT_TASKS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    task = EXPORT_TASKS[task_id]

    # 只有待处理或处理中的任务可以取消
    if task["status"] not in [ExportTaskStatus.PENDING, ExportTaskStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能取消待处理或处理中的任务"
        )

    task["status"] = ExportTaskStatus.FAILED
    task["error_message"] = "用户取消"
    task["completed_at"] = datetime.utcnow().isoformat()

    return {"message": "任务已取消"}


@router.delete("/tasks/{task_id}")
async def delete_export_task(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    task_id: str,
) -> Any:
    """
    删除导出任务

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        task_id: 任务ID

    Returns:
        dict: 操作结果
    """
    if task_id not in EXPORT_TASKS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 删除已完成或失败的任务
    task = EXPORT_TASKS[task_id]
    if task["status"] in [ExportTaskStatus.PENDING, ExportTaskStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能删除已完成或失败的任务"
        )

    del EXPORT_TASKS[task_id]
    return {"message": "任务已删除"}
