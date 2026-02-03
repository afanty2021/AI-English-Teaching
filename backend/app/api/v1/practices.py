"""
练习记录API v1
提供练习记录的创建、查询、更新等端点
"""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole
from app.models.practice import PracticeType, PracticeStatus
from app.services.practice_service import get_practice_service

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_practice(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    practice_data: dict,
) -> Any:
    """
    创建练习记录

    学生开始练习时创建记录，用于追踪学习进度。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        practice_data: 练习数据，包含：
            - practice_type: 练习类型 (reading, listening, writing, speaking, grammar, vocabulary, comprehensive)
            - content_id: 内容ID（可选）
            - total_questions: 题目总数
            - difficulty_level: 难度等级
            - topic: 主题分类

    Returns:
        dict: 创建的练习记录

    Raises:
        HTTPException 400: 数据格式错误
        HTTPException 403: 权限不足
    """
    # 权限检查：只有学生可以创建练习记录
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以创建练习记录"
        )

    # 验证必填字段
    required_fields = ["practice_type"]
    for field in required_fields:
        if field not in practice_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {field}"
            )

    # 验证练习类型
    try:
        practice_type = PracticeType(practice_data["practice_type"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的练习类型: {practice_data.get('practice_type')}"
        )

    # 获取学生ID
    student_id = current_user.student_profile.id

    # 创建练习记录
    service = get_practice_service(db)
    practice = await service.create_practice(
        student_id=student_id,
        practice_type=practice_type,
        content_id=practice_data.get("content_id"),
        total_questions=practice_data.get("total_questions"),
        difficulty_level=practice_data.get("difficulty_level"),
        topic=practice_data.get("topic"),
    )

    return {
        "id": str(practice.id),
        "student_id": str(practice.student_id),
        "practice_type": practice.practice_type,
        "status": practice.status,
        "started_at": practice.started_at.isoformat() if practice.started_at else None,
        "message": "练习记录创建成功"
    }


@router.get("/{practice_id}", response_model=dict)
async def get_practice(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    practice_id: uuid.UUID,
) -> Any:
    """
    获取练习详情

    返回指定练习记录的详细信息。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        practice_id: 练习记录ID

    Returns:
        dict: 练习记录详情

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 练习记录不存在
    """
    service = get_practice_service(db)

    try:
        practice = await service.get_practice(practice_id)

        # 权限检查：学生只能查看自己的练习
        if current_user.role == UserRole.STUDENT:
            if practice.student_id != current_user.student_profile.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查看其他学生的练习记录"
                )

        return {
            "id": str(practice.id),
            "student_id": str(practice.student_id),
            "content_id": str(practice.content_id) if practice.content_id else None,
            "practice_type": practice.practice_type,
            "status": practice.status,
            "total_questions": practice.total_questions,
            "completed_questions": practice.completed_questions,
            "correct_questions": practice.correct_questions,
            "score": practice.score,
            "correct_rate": practice.correct_rate,
            "difficulty_level": practice.difficulty_level,
            "topic": practice.topic,
            "time_spent": practice.time_spent,
            "progress_percentage": practice.progress_percentage,
            "started_at": practice.started_at.isoformat() if practice.started_at else None,
            "completed_at": practice.completed_at.isoformat() if practice.completed_at else None,
            "graph_updated": practice.graph_updated,
            "created_at": practice.created_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/students/{student_id}", response_model=dict)
async def list_student_practices(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    practice_type: PracticeType | None = Query(None, description="练习类型筛选"),
    status: PracticeStatus | None = Query(None, description="状态筛选"),
) -> Any:
    """
    获取学生的练习记录列表

    教师可以查看自己班级学生的练习，学生只能查看自己的练习。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        student_id: 学生ID
        skip: 跳过的记录数
        limit: 返回的记录数
        practice_type: 练习类型筛选
        status: 状态筛选

    Returns:
        dict: 练习记录列表和总数

    Raises:
        HTTPException 403: 权限不足
    """
    # 权限检查
    if current_user.role == UserRole.STUDENT:
        if current_user.student_profile.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他学生的练习记录"
            )

    service = get_practice_service(db)
    practices, total = await service.list_student_practices(
        student_id=student_id,
        practice_type=practice_type,
        status=status,
        limit=limit,
        offset=skip,
    )

    return {
        "total": total,
        "items": [
            {
                "id": str(p.id),
                "content_id": str(p.content_id) if p.content_id else None,
                "practice_type": p.practice_type,
                "status": p.status,
                "score": p.score,
                "correct_rate": p.correct_rate,
                "difficulty_level": p.difficulty_level,
                "topic": p.topic,
                "time_spent": p.time_spent,
                "progress_percentage": p.progress_percentage,
                "started_at": p.started_at.isoformat() if p.started_at else None,
                "completed_at": p.completed_at.isoformat() if p.completed_at else None,
                "created_at": p.created_at.isoformat(),
            }
            for p in practices
        ],
    }


@router.put("/{practice_id}", response_model=dict)
async def update_practice(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    practice_id: uuid.UUID,
    update_data: dict,
) -> Any:
    """
    更新练习进度

    更新练习的进度（已做题目数、正确数等）。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        practice_id: 练习记录ID
        update_data: 更新数据，包含：
            - completed_questions: 已完成题目数
            - correct_questions: 正确题目数
            - answers: 答案详情
            - time_spent: 累计耗时

    Returns:
        dict: 更新后的练习记录

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 练习记录不存在
    """
    # 权限检查：只有学生可以更新自己的练习
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以更新练习进度"
        )

    service = get_practice_service(db)

    try:
        practice = await service.update_practice_progress(
            practice_id=practice_id,
            completed_questions=update_data.get("completed_questions", 0),
            correct_questions=update_data.get("correct_questions", 0),
            answers=update_data.get("answers"),
            time_spent=update_data.get("time_spent"),
        )

        # 权限检查
        if practice.student_id != current_user.student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权更新其他学生的练习"
            )

        return {
            "id": str(practice.id),
            "status": practice.status,
            "completed_questions": practice.completed_questions,
            "correct_questions": practice.correct_questions,
            "correct_rate": practice.correct_rate,
            "score": practice.score,
            "progress_percentage": practice.progress_percentage,
            "message": "练习进度更新成功"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{practice_id}/complete", response_model=dict)
async def complete_practice(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    practice_id: uuid.UUID,
    completion_data: dict,
) -> Any:
    """
    完成练习并自动更新知识图谱

    标记练习为已完成，并使用规则引擎更新知识图谱（零成本）。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        practice_id: 练习记录ID
        completion_data: 完成数据，包含：
            - score: 最终得分（0-100）
            - answers: 完整答案
            - result_details: 结果详情
            - time_spent: 总耗时

    Returns:
        dict: 完成结果和知识图谱更新信息

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 练习记录不存在
    """
    # 权限检查：只有学生可以完成自己的练习
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以完成练习"
        )

    service = get_practice_service(db)

    try:
        result = await service.complete_practice(
            practice_id=practice_id,
            score=completion_data.get("score"),
            answers=completion_data.get("answers"),
            result_details=completion_data.get("result_details"),
            time_spent=completion_data.get("time_spent"),
        )

        practice = result["practice"]

        # 权限检查
        if practice.student_id != current_user.student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权完成其他学生的练习"
            )

        return {
            "practice_id": str(practice.id),
            "status": practice.status,
            "score": practice.score,
            "correct_rate": practice.correct_rate,
            "completed_at": practice.completed_at.isoformat() if practice.completed_at else None,
            "graph_updated": result["graph_updated"],
            "graph_update_result": result["graph_update_result"],
            "message": "练习完成，知识图谱已更新" if result["graph_updated"] else "练习完成，知识图谱更新失败"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/students/{student_id}/stats", response_model=dict)
async def get_student_practice_stats(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: uuid.UUID,
) -> Any:
    """
    获取学生练习统计

    返回学生的练习统计数据，包括总练习次数、平均分、完成率等。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        student_id: 学生ID

    Returns:
        dict: 练习统计数据

    Raises:
        HTTPException 403: 权限不足
    """
    # 权限检查
    if current_user.role == UserRole.STUDENT:
        if current_user.student_profile.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他学生的统计信息"
            )

    service = get_practice_service(db)
    stats = await service.get_student_practice_stats(student_id)

    return stats
