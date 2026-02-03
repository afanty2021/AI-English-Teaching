"""
内容推荐API v1
提供每日推荐、内容详情、内容完成标记等端点
"""
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, Student
from app.schemas.recommendation import (
    DailyContentResponse,
    ContentDetailResponse,
    CompleteContentRequest,
    CompleteContentResponse,
    RecommendationFilter,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter()


@router.get("/recommend", response_model=DailyContentResponse)
async def get_daily_recommendations(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    content_types: Optional[list[str]] = Query(None, description="内容类型过滤"),
    difficulty_levels: Optional[list[str]] = Query(None, description="难度等级过滤"),
    topics: Optional[list[str]] = Query(None, description="主题过滤"),
    exam_types: Optional[list[str]] = Query(None, description="考试类型过滤"),
    max_recommendations: int = Query(10, ge=1, le=50, description="最大推荐数量"),
) -> Any:
    """
    获取每日内容推荐

    基于i+1理论和三段式召回策略（向量召回 → 规则过滤 → AI精排）
    为学生提供个性化的学习内容推荐。

    召回策略说明：
    1. **向量召回**（90%）：使用Qdrant向量相似度进行语义检索
    2. **规则过滤**：应用i+1难度控制、主题匹配等规则
    3. **AI精排**（10%）：使用LLM对Top候选进行精细化排序

    成本优化：90%本地召回 + 10% AI精排

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        content_types: 内容类型过滤（可选）
        difficulty_levels: 难度等级过滤（可选）
        topics: 主题过滤（可选）
        exam_types: 考试类型过滤（可选）
        max_recommendations: 最大推荐数量（1-50）

    Returns:
        DailyContentResponse: 包含阅读、练习、口语等推荐内容

    Raises:
        HTTPException 404: 学生不存在
        HTTPException 500: 推荐服务异常
    """
    try:
        # 获取学生ID
        from app.models import Student

        student = await db.execute(
            select(Student).where(Student.user_id == current_user.id)
        )
        student = student.scalar_one_or_none()

        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="学生信息不存在"
            )

        # 构建过滤条件
        filter_params = None
        if any([content_types, difficulty_levels, topics, exam_types]):
            filter_params = RecommendationFilter(
                content_types=content_types,
                difficulty_levels=difficulty_levels,
                topics=topics,
                exam_types=exam_types,
                max_recommendations=max_recommendations,
            )

        # 获取推荐
        recommendations = await RecommendationService.recommend_daily(
            db=db,
            student_id=student.id,
            filter_params=filter_params,
        )

        return recommendations

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"推荐服务异常: {str(e)}"
        )


@router.get("/{content_id}", response_model=ContentDetailResponse)
async def get_content_detail(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    content_id: uuid.UUID,
) -> Any:
    """
    获取内容详情

    获取指定内容的详细信息，包括正文、相关词汇、知识点等。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        content_id: 内容ID

    Returns:
        ContentDetailResponse: 内容详情

    Raises:
        HTTPException 404: 内容不存在
    """
    from sqlalchemy import select
    from app.models import Content

    content = await db.execute(
        select(Content)
        .where(Content.id == content_id)
    )
    content = content.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在"
        )

    # 增加阅读次数
    content.view_count += 1
    await db.commit()

    # TODO: 加载相关词汇信息
    vocabularies = []

    return ContentDetailResponse(
        id=content.id,
        title=content.title,
        description=content.description,
        content_type=content.content_type,
        difficulty_level=content.difficulty_level,
        exam_type=content.exam_type,
        topic=content.topic,
        tags=content.tags or [],
        content_text=content.content_text,
        media_url=content.media_url,
        duration=content.duration,
        word_count=content.word_count,
        knowledge_points=content.knowledge_points or [],
        vocabularies=vocabularies,
        view_count=content.view_count,
        favorite_count=content.favorite_count,
        created_at=content.created_at,
        updated_at=content.updated_at,
    )


@router.post("/{content_id}/complete", response_model=CompleteContentResponse)
async def mark_content_complete(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    content_id: uuid.UUID,
    complete_data: CompleteContentRequest,
) -> Any:
    """
    标记内容完成

    记录用户完成内容的情况，更新学习进度和知识点掌握度。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        content_id: 内容ID
        complete_data: 完成数据（用时、得分、反馈）

    Returns:
        CompleteContentResponse: 完成响应（积分、掌握度更新等）

    Raises:
        HTTPException 404: 内容或学生不存在
    """
    from sqlalchemy import select
    from app.models import Content, Student, StudentProgress

    # 获取学生信息
    student = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = student.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生信息不存在"
        )

    # 获取内容信息
    content = await db.execute(
        select(Content).where(Content.id == content_id)
    )
    content = content.scalar_one_or_none()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="内容不存在"
        )

    # TODO: 创建学习记录
    # TODO: 更新知识点掌握度
    # TODO: 计算获得积分

    return CompleteContentResponse(
        success=True,
        message="内容完成记录成功",
        earned_points=10,  # 示例：完成获得10积分
        updated_mastery={
            "knowledge_points": content.knowledge_points or [],
            "mastery_increase": 0.1,  # 示例：掌握度提升10%
        }
    )


@router.get("/student/profile", response_model=dict)
async def get_student_profile(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    获取学生画像

    返回当前学生的学习画像，包括能力评估、知识点掌握情况等。

    Args:
        db: 数据库会话
        current_user: 当前认证用户

    Returns:
        dict: 学生画像信息

    Raises:
        HTTPException 404: 学生不存在
    """
    from sqlalchemy import select
    from app.models import Student

    student = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = student.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生信息不存在"
        )

    profile = await RecommendationService.get_student_profile(
        db=db,
        student_id=student.id
    )

    return profile.model_dump()


@router.get("/", response_model=dict)
async def list_contents(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    content_type: Optional[str] = Query(None, description="内容类型"),
    difficulty_level: Optional[str] = Query(None, description="难度等级"),
    topic: Optional[str] = Query(None, description="主题"),
    exam_type: Optional[str] = Query(None, description="考试类型"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
) -> Any:
    """
    获取内容列表

    支持按类型、难度、主题等条件筛选内容。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        content_type: 内容类型（可选）
        difficulty_level: 难度等级（可选）
        topic: 主题（可选）
        exam_type: 考试类型（可选）
        skip: 跳过数量（分页用）
        limit: 返回数量

    Returns:
        dict: 内容列表和总数
    """
    from sqlalchemy import select, func, and_
    from app.models import Content

    # 构建查询条件
    conditions = [Content.is_published == True]

    if content_type:
        conditions.append(Content.content_type == content_type)
    if difficulty_level:
        conditions.append(Content.difficulty_level == difficulty_level)
    if topic:
        conditions.append(Content.topic == topic)
    if exam_type:
        conditions.append(Content.exam_type == exam_type)

    # 查询总数
    count_query = select(func.count(Content.id)).where(and_(*conditions))
    total = await db.execute(count_query)
    total = total.scalar()

    # 查询内容
    query = (
        select(Content)
        .where(and_(*conditions))
        .order_by(Content.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    contents = result.scalars().all()

    return {
        "total": total,
        "items": [
            {
                "id": str(c.id),
                "title": c.title,
                "description": c.description,
                "content_type": c.content_type,
                "difficulty_level": c.difficulty_level,
                "topic": c.topic,
                "word_count": c.word_count,
                "duration": c.duration,
            }
            for c in contents
        ],
        "skip": skip,
        "limit": limit,
    }
