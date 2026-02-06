"""
错题本API v1
提供错题的创建、查询、更新、复习等端点
"""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole
from app.models.mistake import MistakeStatus, MistakeType
from app.services.mistake_service import get_mistake_service
from app.services.mistake_analysis_service import get_mistake_analysis_service
from app.services.mistake_export_service import get_mistake_export_service
from app.services.mistake_review_service import get_mistake_review_service

router = APIRouter()


def get_current_student_id(current_user: User) -> str:
    """
    获取当前学生ID的辅助函数

    Args:
        current_user: 当前认证用户

    Returns:
        str: 学生ID

    Raises:
        HTTPException: 如果用户不是学生或学生档案不存在
    """
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以执行此操作"
        )

    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    return str(current_user.student_profile.id)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_mistake(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mistake_data: dict,
) -> Any:
    """
    创建错题记录

    学生或教师可以手动添加错题到错题本。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        mistake_data: 错题数据，包含：
            - question: 题目内容
            - wrong_answer: 错误答案
            - correct_answer: 正确答案
            - mistake_type: 错题类型 (grammar, vocabulary, reading, listening, writing, speaking, pronunciation, comprehension)
            - practice_id: 关联练习ID（可选）
            - content_id: 关联内容ID（可选）
            - explanation: 错题解析（可选）
            - knowledge_points: 知识点列表（可选）
            - difficulty_level: 难度等级（可选）
            - topic: 主题分类（可选）

    Returns:
        dict: 创建的错题记录

    Raises:
        HTTPException 400: 数据格式错误
        HTTPException 403: 权限不足
    """
    # 权限检查：学生和教师都可以创建错题
    if current_user.role not in [UserRole.STUDENT, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )

    # 验证必填字段
    required_fields = ["question", "wrong_answer", "correct_answer", "mistake_type"]
    for field in required_fields:
        if field not in mistake_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {field}"
            )

    # 验证错题类型
    try:
        mistake_type = MistakeType(mistake_data["mistake_type"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的错题类型: {mistake_data.get('mistake_type')}"
        )

    # 获取学生ID
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生档案不存在，请先完善个人信息"
            )
        student_id = current_user.student_profile.id
    else:
        # 教师需要指定学生ID
        if "student_id" not in mistake_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="教师创建错题需要指定student_id"
            )
        try:
            student_id = uuid.UUID(mistake_data["student_id"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的student_id格式"
            )

    # 创建错题记录
    service = get_mistake_service(db)
    mistake = await service.create_mistake(
        student_id=student_id,
        question=mistake_data["question"],
        wrong_answer=mistake_data["wrong_answer"],
        correct_answer=mistake_data["correct_answer"],
        mistake_type=mistake_type,
        practice_id=mistake_data.get("practice_id"),
        content_id=mistake_data.get("content_id"),
        explanation=mistake_data.get("explanation"),
        knowledge_points=mistake_data.get("knowledge_points"),
        difficulty_level=mistake_data.get("difficulty_level"),
        topic=mistake_data.get("topic"),
        extra_metadata=mistake_data.get("extra_metadata"),
    )

    return {
        "id": str(mistake.id),
        "student_id": str(mistake.student_id),
        "mistake_type": mistake.mistake_type,
        "status": mistake.status,
        "question": mistake.question,
        "created_at": mistake.created_at.isoformat(),
        "message": "错题记录创建成功"
    }


@router.post("/collect/{practice_id}", response_model=dict)
async def collect_mistakes_from_practice(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    practice_id: str,
) -> Any:
    """
    从练习记录中自动收集错题

    系统会自动分析练习结果，将错误的题目添加到错题本。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        practice_id: 练习记录ID

    Returns:
        dict: 收集结果，包含收集到的错题数量和列表

    Raises:
        HTTPException 400: 练习未完成或其他错误
        HTTPException 403: 权限不足
    """
    # 权限检查：只有学生可以收集自己的错题
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以收集错题"
        )

    try:
        practice_uuid = uuid.UUID(practice_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的练习ID格式"
        )

    # 收集错题
    service = get_mistake_service(db)
    try:
        mistakes = await service.collect_mistakes_from_practice(practice_uuid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {
        "practice_id": practice_id,
        "collected_count": len(mistakes),
        "mistakes": [
            {
                "id": str(m.id),
                "question": m.question[:100] + "..." if len(m.question) > 100 else m.question,
                "mistake_type": m.mistake_type,
                "status": m.status,
            }
            for m in mistakes
        ],
        "message": f"成功收集 {len(mistakes)} 道错题"
    }


@router.get("/me", response_model=dict)
async def list_my_mistakes(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None, description="状态筛选"),
    mistake_type: Optional[str] = Query(None, description="错题类型筛选"),
    topic: Optional[str] = Query(None, description="主题筛选"),
    knowledge_point: Optional[str] = Query(None, description="知识点筛选"),
    needs_ai_analysis: Optional[bool] = Query(None, description="是否需要AI分析"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
) -> Any:
    """
    获取当前学生的错题列表

    支持按状态、类型、主题等条件筛选。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        status: 状态筛选 (pending, reviewing, mastered, ignored)
        mistake_type: 错题类型筛选
        topic: 主题筛选
        knowledge_point: 知识点筛选
        needs_ai_analysis: 是否需要AI分析筛选
        limit: 返回数量限制
        offset: 偏移量

    Returns:
        dict: 错题列表和总数
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以查看自己的错题"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id

    # 解析筛选参数
    status_enum = MistakeStatus(status) if status else None
    type_enum = MistakeType(mistake_type) if mistake_type else None

    # 获取错题列表
    service = get_mistake_service(db)
    mistakes, total = await service.list_student_mistakes(
        student_id=student_id,
        status=status_enum,
        mistake_type=type_enum,
        topic=topic,
        knowledge_point=knowledge_point,
        needs_ai_analysis=needs_ai_analysis,
        limit=limit,
        offset=offset,
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "mistakes": [
            {
                "id": str(m.id),
                "question": m.question,
                "wrong_answer": m.wrong_answer,
                "correct_answer": m.correct_answer,
                "mistake_type": m.mistake_type,
                "status": m.status,
                "explanation": m.explanation,
                "knowledge_points": m.knowledge_points,
                "difficulty_level": m.difficulty_level,
                "topic": m.topic,
                "mistake_count": m.mistake_count,
                "review_count": m.review_count,
                "last_mistaken_at": m.last_mistaken_at.isoformat() if m.last_mistaken_at else None,
                "mastery_level": round(m.mastery_level, 2),
                "ai_suggestion": m.ai_suggestion,
            }
            for m in mistakes
        ]
    }


@router.get("/me/statistics", response_model=dict)
async def get_my_mistake_statistics(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取当前学生的错题统计数据

    提供详细的错题统计，帮助了解学习薄弱环节。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）

    Returns:
        dict: 错题统计数据
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以查看自己的错题统计"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id

    # 获取统计数据
    service = get_mistake_service(db)
    statistics = await service.get_mistake_statistics(student_id)

    return statistics


@router.get("/me/review-plan", response_model=dict)
async def get_my_review_plan(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=5, le=50, description="返回的错题数量"),
) -> Any:
    """
    获取错题复习计划

    基于遗忘曲线和错题优先级，生成个性化复习计划。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        limit: 返回的错题数量

    Returns:
        dict: 复习计划，包含紧急、今日、本周需要复习的错题
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以查看自己的复习计划"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id

    # 获取复习计划
    service = get_mistake_service(db)
    review_plan = await service.get_review_plan(student_id, limit=limit)

    return review_plan


@router.get("/{mistake_id}", response_model=dict)
async def get_mistake(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mistake_id: str,
) -> Any:
    """
    获取错题详情

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        mistake_id: 错题ID

    Returns:
        dict: 错题详情

    Raises:
        HTTPException 404: 错题不存在
        HTTPException 403: 权限不足
    """
    try:
        mistake_uuid = uuid.UUID(mistake_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的错题ID格式"
        )

    # 获取错题
    service = get_mistake_service(db)
    try:
        mistake = await service.get_mistake(mistake_uuid)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="错题不存在"
        )

    # 权限检查：学生只能查看自己的错题
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生档案不存在，请先完善个人信息"
            )
        if mistake.student_id != current_user.student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此错题"
            )

    return {
        "id": str(mistake.id),
        "student_id": str(mistake.student_id),
        "practice_id": str(mistake.practice_id) if mistake.practice_id else None,
        "content_id": str(mistake.content_id) if mistake.content_id else None,
        "question": mistake.question,
        "wrong_answer": mistake.wrong_answer,
        "correct_answer": mistake.correct_answer,
        "mistake_type": mistake.mistake_type,
        "status": mistake.status,
        "explanation": mistake.explanation,
        "knowledge_points": mistake.knowledge_points,
        "difficulty_level": mistake.difficulty_level,
        "topic": mistake.topic,
        "mistake_count": mistake.mistake_count,
        "review_count": mistake.review_count,
        "last_reviewed_at": mistake.last_reviewed_at.isoformat() if mistake.last_reviewed_at else None,
        "first_mistaken_at": mistake.first_mistaken_at.isoformat() if mistake.first_mistaken_at else None,
        "last_mistaken_at": mistake.last_mistaken_at.isoformat() if mistake.last_mistaken_at else None,
        "ai_suggestion": mistake.ai_suggestion,
        "ai_analysis": mistake.ai_analysis,
        "extra_metadata": mistake.extra_metadata,
        "mastery_level": round(mistake.mastery_level, 2),
        "needs_review": mistake.needs_review,
        "is_mastered": mistake.is_mastered,
        "created_at": mistake.created_at.isoformat(),
        "updated_at": mistake.updated_at.isoformat(),
    }


@router.put("/{mistake_id}/status", response_model=dict)
async def update_mistake_status(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mistake_id: str,
    status_data: dict,
) -> Any:
    """
    更新错题状态

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        mistake_id: 错题ID
        status_data: 状态数据，包含：
            - status: 新状态 (pending, reviewing, mastered, ignored)

    Returns:
        dict: 更新后的错题记录

    Raises:
        HTTPException 400: 数据格式错误
        HTTPException 403: 权限不足
        HTTPException 404: 错题不存在
    """
    # 验证状态
    if "status" not in status_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少status字段"
        )

    try:
        status_enum = MistakeStatus(status_data["status"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的状态: {status_data.get('status')}"
        )

    try:
        mistake_uuid = uuid.UUID(mistake_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的错题ID格式"
        )

    # 权限检查：学生只能更新自己的错题状态
    service = get_mistake_service(db)
    mistake = await service.get_mistake(mistake_uuid)

    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生档案不存在，请先完善个人信息"
            )
        if mistake.student_id != current_user.student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权修改此错题"
            )

    # 更新状态
    updated_mistake = await service.update_mistake_status(mistake_uuid, status_enum)

    return {
        "id": str(updated_mistake.id),
        "status": updated_mistake.status,
        "message": "状态更新成功"
    }


@router.post("/{mistake_id}/retry", response_model=dict)
async def retry_mistake(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mistake_id: str,
    retry_data: dict,
) -> Any:
    """
    记录错题重做结果

    学生重新练习错题后，提交答案并记录结果。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        mistake_id: 错题ID
        retry_data: 重做数据，包含：
            - user_answer: 学生答案
            - is_correct: 是否正确

    Returns:
        dict: 重做结果，包含是否掌握、复习次数等

    Raises:
        HTTPException 400: 数据格式错误
        HTTPException 403: 权限不足
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以重做错题"
        )

    # 验证必填字段
    required_fields = ["user_answer", "is_correct"]
    for field in required_fields:
        if field not in retry_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {field}"
            )

    try:
        mistake_uuid = uuid.UUID(mistake_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的错题ID格式"
        )

    # 记录重做结果
    service = get_mistake_service(db)
    try:
        result = await service.record_mistake_retry(
            mistake_uuid,
            retry_data["user_answer"],
            retry_data["is_correct"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    return {
        "mistake_id": str(result["mistake"].id),
        "mastered": result["mastered"],
        "review_count": result["review_count"],
        "mistake_count": result["mistake_count"],
        "status": result["mistake"].status,
        "message": "掌握" if result["mastered"] else "继续加油"
    }


@router.delete("/{mistake_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mistake(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mistake_id: str,
) -> None:
    """
    删除错题记录

    注意：删除操作不可恢复，请谨慎使用。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        mistake_id: 错题ID

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 错题不存在
    """
    try:
        mistake_uuid = uuid.UUID(mistake_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的错题ID格式"
        )

    # 获取错题
    service = get_mistake_service(db)
    mistake = await service.get_mistake(mistake_uuid)

    # 权限检查：学生只能删除自己的错题，教师可以删除任何错题
    if current_user.role == UserRole.STUDENT:
        if not current_user.student_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="学生档案不存在，请先完善个人信息"
            )
        if mistake.student_id != current_user.student_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权删除此错题"
            )

    # 删除错题
    await db.delete(mistake)
    await db.commit()


@router.post("/{mistake_id}/analyze", response_model=dict)
async def analyze_mistake(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mistake_id: str,
) -> Any:
    """
    对单个错题进行AI分析

    使用AI生成详细的错误解析和学习建议。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        mistake_id: 错题ID

    Returns:
        dict: AI分析结果，包含：
            - explanation: 错误解释
            - knowledge_points: 知识点
            - recommendations: 学习建议
            - review_plan: 复习计划
            - encouragement: 鼓励语

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 错题不存在
        HTTPException 500: AI分析失败
    """
    # 权限检查：只有学生可以分析自己的错题
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以分析自己的错题"
        )

    try:
        mistake_uuid = uuid.UUID(mistake_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的错题ID格式"
        )

    # 获取错题
    mistake_service = get_mistake_service(db)
    try:
        mistake = await mistake_service.get_mistake(mistake_uuid)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="错题不存在"
        )

    # 权限检查：只能分析自己的错题
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )
    if mistake.student_id != current_user.student_profile.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权分析此错题"
        )

    # 执行AI分析
    analysis_service = get_mistake_analysis_service(db)
    try:
        analysis_result = await analysis_service.analyze_mistake(
            question=mistake.question,
            wrong_answer=mistake.wrong_answer,
            correct_answer=mistake.correct_answer,
            mistake_type=mistake.mistake_type,
            topic=mistake.topic,
            difficulty_level=mistake.difficulty_level,
            mistake_count=mistake.mistake_count,
            student_level=current_user.student_profile.current_cefr_level,
        )

        # 更新错题的AI分析结果
        updated_mistake = await analysis_service.update_ai_analysis(
            mistake_id=mistake_uuid,
            ai_suggestion=analysis_result.encouragement,
            ai_analysis={
                "mistake_category": analysis_result.mistake_category,
                "severity": analysis_result.severity,
                "explanation": analysis_result.explanation,
                "correct_approach": analysis_result.correct_approach,
                "knowledge_points": analysis_result.knowledge_points,
                "recommendations": [
                    {
                        "priority": rec.priority,
                        "category": rec.category,
                        "title": rec.title,
                        "description": rec.description,
                    }
                    for rec in analysis_result.recommendations
                ],
                "review_plan": {
                    "review_frequency": analysis_result.review_plan.review_frequency,
                    "next_review_days": analysis_result.review_plan.next_review_days,
                    "mastery_criteria": analysis_result.review_plan.mastery_criteria,
                },
            },
        )

        return {
            "mistake_id": str(mistake_uuid),
            "analysis": {
                "mistake_category": analysis_result.mistake_category,
                "severity": analysis_result.severity,
                "explanation": analysis_result.explanation,
                "correct_approach": analysis_result.correct_approach,
                "knowledge_points": analysis_result.knowledge_points,
                "recommendations": [
                    {
                        "priority": rec.priority,
                        "category": rec.category,
                        "title": rec.title,
                        "description": rec.description,
                        "resources": rec.resources,
                        "practice_exercises": rec.practice_exercises,
                        "estimated_time": rec.estimated_time,
                    }
                    for rec in analysis_result.recommendations
                ],
                "review_plan": {
                    "review_frequency": analysis_result.review_plan.review_frequency,
                    "next_review_days": analysis_result.review_plan.next_review_days,
                    "mastery_criteria": analysis_result.review_plan.mastery_criteria,
                    "review_method": analysis_result.review_plan.review_method,
                },
                "encouragement": analysis_result.encouragement,
            },
            "message": "AI分析完成"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI分析失败: {str(e)}"
        )


@router.post("/batch-analyze", response_model=dict)
async def batch_analyze_mistakes(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=20, description="批量分析的数量限制"),
) -> Any:
    """
    批量分析待AI分析的错题

    对所有标记为需要AI分析的错题进行批量分析，识别常见错误模式。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        limit: 批量分析的数量限制

    Returns:
        dict: 批量分析结果，包含：
            - analyzed_count: 分析的错题数量
            - summary: 整体分析总结
            - common_patterns: 常见错误模式
            - overall_recommendations: 总体学习建议
            - priority_topics: 需要重点关注的话题

    Raises:
        HTTPException 403: 权限不足
    """
    # 权限检查：只有学生可以分析自己的错题
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以分析自己的错题"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id

    # 获取需要AI分析的错题
    mistake_service = get_mistake_service(db)
    mistakes, total = await mistake_service.list_student_mistakes(
        student_id=student_id,
        needs_ai_analysis=True,
        limit=limit,
        offset=0,
    )

    if not mistakes:
        return {
            "analyzed_count": 0,
            "summary": "暂无需要AI分析的错题",
            "common_patterns": [],
            "overall_recommendations": [],
            "priority_topics": [],
            "message": "没有需要分析的错题"
        }

    # 准备批量分析数据
    mistakes_data = [
        {
            "question": m.question,
            "wrong_answer": m.wrong_answer,
            "correct_answer": m.correct_answer,
            "mistake_type": m.mistake_type,
            "topic": m.topic,
            "difficulty_level": m.difficulty_level,
            "mistake_count": m.mistake_count,
        }
        for m in mistakes
    ]

    # 执行批量分析
    analysis_service = get_mistake_analysis_service(db)
    try:
        batch_result = await analysis_service.analyze_mistakes_batch(
            mistakes_data=mistakes_data,
            student_level=current_user.student_profile.current_cefr_level,
        )

        # 更新所有错题的AI分析状态
        for i, mistake in enumerate(mistakes):
            if i < len(batch_result.results):
                result = batch_result.results[i]
                await analysis_service.update_ai_analysis(
                    mistake_id=mistake.id,
                    ai_suggestion=f"{result.encouragement}\n\n{result.explanation[:200]}...",
                    ai_analysis={
                        "mistake_category": result.mistake_category,
                        "severity": result.severity,
                        "explanation": result.explanation,
                        "correct_approach": result.correct_approach,
                        "knowledge_points": result.knowledge_points,
                        "batch_analyzed": True,
                    },
                )

        return {
            "analyzed_count": len(mistakes),
            "summary": batch_result.summary,
            "common_patterns": batch_result.common_patterns,
            "overall_recommendations": batch_result.overall_recommendations,
            "priority_topics": batch_result.priority_topics,
            "remaining_count": total - len(mistakes),
            "message": f"成功分析 {len(mistakes)} 道错题"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量AI分析失败: {str(e)}"
        )


@router.post("/export")
async def export_mistakes(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    format_type: str = Query("markdown", description="导出格式: markdown, pdf, word"),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    type_filter: Optional[str] = Query(None, description="类型筛选"),
    topic_filter: Optional[str] = Query(None, description="主题筛选"),
    knowledge_point_filter: Optional[str] = Query(None, description="知识点筛选"),
):
    """
    导出错题本

    学生可以导出自己的错题本，支持多种格式。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        format_type: 导出格式 (markdown, pdf, word)
        status_filter: 按状态筛选 (pending, reviewing, mastered, ignored)
        type_filter: 按类型筛选 (grammar, vocabulary, reading, etc.)
        topic_filter: 按主题筛选
        knowledge_point_filter: 按知识点筛选

    Returns:
        StreamingResponse: 文件流

    Raises:
        HTTPException 403: 权限不足
        HTTPException 400: 参数错误
    """
    # 权限检查：只有学生可以导出自己的错题本
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以导出错题本"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    # 验证导出格式
    valid_formats = ["markdown", "pdf", "word"]
    if format_type not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的导出格式: {format_type}。支持的格式: {', '.join(valid_formats)}"
        )

    # 构建筛选条件
    filters = {}
    if status_filter:
        try:
            MistakeStatus(status_filter)
            filters["status"] = status_filter
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的状态值: {status_filter}"
            )

    if type_filter:
        try:
            MistakeType(type_filter)
            filters["mistake_type"] = type_filter
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的类型值: {type_filter}"
            )

    if topic_filter:
        filters["topic"] = topic_filter

    if knowledge_point_filter:
        filters["knowledge_point"] = knowledge_point_filter

    try:
        # 获取导出服务
        export_service = get_mistake_export_service(db)
        student_id = str(current_user.student_profile.id)

        # 根据格式选择导出方法
        if format_type == "markdown":
            filename, content = await export_service.export_as_markdown(
                student_id=student_id,
                filters=filters if filters else None,
            )
            media_type = "text/markdown"
            file_extension = "md"

        elif format_type == "pdf":
            filename, content = await export_service.export_as_pdf(
                student_id=student_id,
                filters=filters if filters else None,
            )
            media_type = "application/pdf"
            file_extension = "pdf"

        else:  # word
            filename, content = await export_service.export_as_word(
                student_id=student_id,
                filters=filters if filters else None,
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            file_extension = "docx"

        # 创建文件流
        def iterfile():
            yield content

        # 编码文件名以支持中文
        from urllib.parse import quote
        encoded_filename = quote(filename)

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )


@router.post("/{mistake_id}/export")
async def export_single_mistake(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mistake_id: str,
    format_type: str = Query("markdown", description="导出格式: markdown, pdf, word"),
):
    """
    导出单个错题

    学生可以导出单个错题的详细分析报告。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是学生）
        mistake_id: 错题ID
        format_type: 导出格式 (markdown, pdf, word)

    Returns:
        StreamingResponse: 文件流

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 错题不存在
    """
    # 权限检查：只有学生可以导出自己的错题
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以导出错题"
        )

    # 检查学生档案是否存在
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    # 验证错题ID格式
    try:
        uuid.UUID(mistake_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的错题ID格式"
        )

    # 验证导出格式
    valid_formats = ["markdown", "pdf", "word"]
    if format_type not in valid_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的导出格式: {format_type}。支持的格式: {', '.join(valid_formats)}"
        )

    try:
        # 获取导出服务
        export_service = get_mistake_export_service(db)
        student_id = str(current_user.student_profile.id)

        # 根据格式选择导出方法
        if format_type == "markdown":
            filename, content = await export_service.export_as_markdown(
                student_id=student_id,
                single_mistake_id=mistake_id,
            )
            media_type = "text/markdown"

        elif format_type == "pdf":
            filename, content = await export_service.export_as_pdf(
                student_id=student_id,
                single_mistake_id=mistake_id,
            )
            media_type = "application/pdf"

        else:  # word
            filename, content = await export_service.export_as_word(
                student_id=student_id,
                single_mistake_id=mistake_id,
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        # 创建文件流
        def iterfile():
            yield content

        # 编码文件名以支持中文
        from urllib.parse import quote
        encoded_filename = quote(filename)

        return StreamingResponse(
            iterfile(),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
            }
        )

    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )


# ==================== 智能复习提醒 API ====================

@router.get("/review/today", response_model=dict)
async def get_today_review_list(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=50, description="返回数量限制"),
) -> Any:
    """
    获取今日复习清单

    基于艾宾浩斯遗忘曲线，返回今日需要复习的错题列表。

    Returns:
        dict: 今日复习清单，包含：
            - date: 日期
            - total_count: 待复习总数
            - today_count: 今日需复习数
            - overdue_count: 已过期数
            - urgent_count: 即将过期数
            - review_list: 复习列表
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以查看复习清单"
        )

    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id
    review_service = get_mistake_review_service(db)
    result = await review_service.get_today_review_list(student_id, limit=limit)

    return result


@router.get("/review/urgent", response_model=dict)
async def get_urgent_review(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=30, description="返回数量限制"),
) -> Any:
    """
    获取紧急复习项

    返回即将遗忘的错题（超过最佳复习时间或24小时内需要复习的）。

    Returns:
        dict: 紧急复习列表，包含即将遗忘的错题
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以查看紧急复习"
        )

    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id
    review_service = get_mistake_review_service(db)
    result = await review_service.get_urgent_review(student_id, limit=limit)

    return result


@router.get("/review/stats", response_model=dict)
async def get_review_statistics(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取复习统计

    返回学习统计数据，包括掌握率、复习次数、连续天数等。

    Returns:
        dict: 复习统计数据
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以查看复习统计"
        )

    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id
    review_service = get_mistake_review_service(db)
    result = await review_service.get_review_statistics(student_id)

    return result


@router.get("/review/recommend", response_model=dict)
async def recommend_review(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=30, description="返回数量限制"),
) -> Any:
    """
    推荐复习题目

    基于优先级分数智能推荐最需要复习的错题。

    Returns:
        dict: 推荐复习列表，按优先级排序
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以获取复习推荐"
        )

    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id
    review_service = get_mistake_review_service(db)
    result = await review_service.get_recommended_review(student_id, limit=limit)

    return result


@router.get("/review/calendar", response_model=dict)
async def get_review_calendar(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    days: int = Query(30, ge=7, le=90, description="天数"),
) -> Any:
    """
    获取复习日历

    返回未来N天的复习计划安排。

    Returns:
        dict: 复习日历，按日期分组
    """
    # 权限检查
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有学生可以查看复习日历"
        )

    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="学生档案不存在，请先完善个人信息"
        )

    student_id = current_user.student_profile.id
    review_service = get_mistake_review_service(db)
    result = await review_service.get_review_calendar(student_id, days=days)

    return result
