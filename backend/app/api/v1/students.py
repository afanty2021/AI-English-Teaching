"""
学生管理API v1
提供学生查询、知识图谱获取、初始诊断等端点
优化：使用 joinedload 避免 N+1 查询，使用 Redis 缓存加速访问
"""
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, Student, UserRole, ClassStudent
from app.schemas.recommendation import StudentProfile
from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.student_cache_service import get_student_cache, StudentCacheService

router = APIRouter()


async def _get_teacher_class_ids(db: AsyncSession, teacher_id: uuid.UUID) -> list[uuid.UUID]:
    """
    获取教师负责的班级ID列表

    Args:
        db: 数据库会话
        teacher_id: 教师ID

    Returns:
        list[uuid.UUID]: 班级ID列表
    """
    from sqlalchemy import select, text
    from app.models.class_model import ClassInfo

    # 使用原生SQL查询教师作为主教师或辅导教师的班级
    # 使用 PostgreSQL 的 ANY 操作符来检查 ARRAY 是否包含特定值
    sql_query = text("""
        SELECT id FROM classes
        WHERE head_teacher_id = :teacher_id
           OR :teacher_id = ANY(assistant_teacher_ids)
    """)

    result = await db.execute(sql_query, {"teacher_id": str(teacher_id)})
    return [row[0] for row in result.fetchall()]


async def _get_class_student_ids(db: AsyncSession, class_ids: list[uuid.UUID]) -> set[uuid.UUID]:
    """
    获取班级中的学生ID集合

    Args:
        db: 数据库会话
        class_ids: 班级ID列表

    Returns:
        set[uuid.UUID]: 学生ID集合
    """
    if not class_ids:
        return set()

    from sqlalchemy import select

    query = select(ClassStudent.student_id).where(
        ClassStudent.class_id.in_(class_ids),
        ClassStudent.enrollment_status == "active"
    )
    result = await db.execute(query)
    return {row[0] for row in result.all()}


@router.get("/", response_model=list[StudentProfile])
async def list_students(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
    class_id: uuid.UUID | None = Query(None, description="按班级筛选"),
) -> Any:
    """
    获取学生列表

    教师可以查看自己班级的学生，管理员可以查看所有学生。
    支持分页和按班级筛选。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        skip: 跳过的记录数
        limit: 返回的记录数
        class_id: 班级ID筛选条件

    Returns:
        list[StudentProfile]: 学生档案列表

    Raises:
        HTTPException 403: 权限不足
    """
    # 权限检查：只有教师和管理员可以查看学生列表
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以查看学生列表"
        )

    from sqlalchemy import select
    from app.models.student import Student as StudentModel

    query = select(StudentModel)

    # 获取教师的班级权限
    allowed_student_ids = None
    if current_user.role == UserRole.TEACHER:
        teacher_id = current_user.teacher_profile.id

        # 如果指定了班级，检查是否有权限
        if class_id:
            teacher_class_ids = await _get_teacher_class_ids(db, teacher_id)
            if class_id not in teacher_class_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查看该班级的学生"
                )
        else:
            # 自动限制为教师班级的学生
            teacher_class_ids = await _get_teacher_class_ids(db, teacher_id)
            allowed_student_ids = await _get_class_student_ids(db, teacher_class_ids)

            if allowed_student_ids:
                query = query.where(StudentModel.id.in_(allowed_student_ids))
            else:
                # 教师没有班级，返回空列表
                return []

    # 按班级筛选
    if class_id:
        # 通过班级学生关联表查询
        from app.models.class_model import ClassStudent
        class_query = select(ClassStudent.student_id).where(
            ClassStudent.class_id == class_id,
            ClassStudent.enrollment_status == "active"
        )
        class_result = await db.execute(class_query)
        student_ids = [row[0] for row in class_result.all()]

        if student_ids:
            query = query.where(StudentModel.id.in_(student_ids))
        else:
            return []

    # 分页
    query = query.offset(skip).limit(limit)

    # 使用 joinedload 预加载关联的 User，避免 N+1 查询
    from sqlalchemy.orm import selectinload
    query = query.options(selectinload(StudentModel.user))

    result = await db.execute(query)
    students = result.scalars().all()

    # 转换为响应格式 - 现在 User 已预加载，无额外查询
    profiles = []
    for student in students:
        profiles.append(StudentProfile(
            id=str(student.id),
            user_id=str(student.user_id),
            username=student.user.username if student.user else "",
            email=student.user.email if student.user else "",
            target_exam=student.target_exam,
            target_score=student.target_score,
            study_goal=student.study_goal,
            current_cefr_level=student.current_cefr_level,
            grade=student.grade,
            created_at=student.created_at,
        ))

    return profiles


@router.get("/{student_id}", response_model=StudentProfile)
async def get_student(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: uuid.UUID,
) -> Any:
    """
    获取学生详情

    教师可以查看自己班级的学生详情，学生只能查看自己的信息。
    优化：使用 Redis 缓存 + joinedload 预加载

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        student_id: 学生ID

    Returns:
        StudentProfile: 学生档案详情

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 学生不存在
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.student import Student as StudentModel

    # 1. 尝试从缓存获取
    cache = await get_student_cache()
    cache_key = str(student_id)
    cached_profile = await cache.get_student_profile(cache_key)

    if cached_profile:
        # 缓存命中，直接返回
        return cached_profile

    # 2. 缓存未命中，从数据库查询
    # 使用 joinedload 预加载 User 关联
    query = select(StudentModel).options(
        selectinload(StudentModel.user)
    ).where(StudentModel.id == student_id)

    result = await db.execute(query)
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )

    # 权限检查
    if current_user.role == UserRole.STUDENT:
        # 学生只能查看自己的信息
        if current_user.student_profile.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他学生的信息"
            )
    elif current_user.role == UserRole.TEACHER:
        # 教师只能查看自己班级的学生
        teacher_id = current_user.teacher_profile.id
        teacher_class_ids = await _get_teacher_class_ids(db, teacher_id)
        allowed_student_ids = await _get_class_student_ids(db, teacher_class_ids)

        if student_id not in allowed_student_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看该学生的信息"
            )

    # 3. 构建响应并缓存
    profile = StudentProfile(
        id=str(student.id),
        user_id=str(student.user_id),
        username=student.user.username if student.user else "",
        email=student.user.email if student.user else "",
        target_exam=student.target_exam,
        target_score=student.target_score,
        study_goal=student.study_goal,
        current_cefr_level=student.current_cefr_level,
        grade=student.grade,
        created_at=student.created_at,
    )

    # 异步缓存（不阻塞响应）
    await cache.set_student_profile(cache_key, profile.model_dump())

    return profile


@router.get("/{student_id}/knowledge-graph")
async def get_student_knowledge_graph(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: uuid.UUID,
) -> Any:
    """
    获取学生知识图谱

    返回学生的知识图谱JSON数据，包含各知识点的能力值。
    优化：使用 Redis 缓存加速访问

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        student_id: 学生ID

    Returns:
        dict: 知识图谱数据

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 学生或知识图谱不存在
    """
    from sqlalchemy import select
    from app.models.knowledge_graph import KnowledgeGraph

    # 1. 尝试从缓存获取
    cache = await get_student_cache()
    cache_key = str(student_id)
    cached_kg = await cache.get_student_knowledge_graph(cache_key)

    if cached_kg:
        # 缓存命中，标记来源
        cached_kg["from_cache"] = True
        return cached_kg

    # 2. 缓存未命中，从数据库查询
    # 权限检查
    if current_user.role == UserRole.STUDENT:
        if current_user.student_profile.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他学生的知识图谱"
            )
    elif current_user.role == UserRole.TEACHER:
        # 教师只能查看自己班级学生的知识图谱
        teacher_id = current_user.teacher_profile.id
        teacher_class_ids = await _get_teacher_class_ids(db, teacher_id)
        allowed_student_ids = await _get_class_student_ids(db, teacher_class_ids)

        if student_id not in allowed_student_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看该学生的知识图谱"
            )

    # 查询知识图谱
    query = select(KnowledgeGraph).where(KnowledgeGraph.student_id == student_id)
    result = await db.execute(query)
    kg = result.scalar_one_or_none()

    if not kg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识图谱不存在，请先进行初始诊断"
        )

    # 3. 构建响应并缓存
    kg_data = {
        "student_id": str(kg.student_id),
        "nodes": kg.nodes,
        "edges": kg.edges,
        "abilities": kg.abilities,
        "cefr_level": kg.cefr_level,
        "exam_coverage": kg.exam_coverage,
        "ai_analysis": kg.ai_analysis,
        "last_ai_analysis_at": kg.last_ai_analysis_at.isoformat() if kg.last_ai_analysis_at else None,
        "version": kg.version,
        "created_at": kg.created_at.isoformat(),
        "updated_at": kg.updated_at.isoformat(),
        "from_cache": False,
    }

    # 异步缓存
    await cache.set_student_knowledge_graph(cache_key, kg_data)

    return kg_data


@router.post("/{student_id}/diagnose", status_code=status.HTTP_202_ACCEPTED)
async def diagnose_student(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: uuid.UUID,
) -> Any:
    """
    执行学生初始AI诊断

    使用AI分析学生的英语水平，生成个性化知识图谱。
    这是一个异步操作，可能需要较长时间。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        student_id: 学生ID

    Returns:
        dict: 包含诊断任务ID的消息

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 学生不存在
    """
    from sqlalchemy import select
    from app.models.student import Student as StudentModel

    # 权限检查：只有教师和管理员可以触发诊断
    if current_user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师和管理员可以触发诊断"
        )

    # 教师只能诊断自己班级的学生
    if current_user.role == UserRole.TEACHER:
        teacher_id = current_user.teacher_profile.id
        teacher_class_ids = await _get_teacher_class_ids(db, teacher_id)
        allowed_student_ids = await _get_class_student_ids(db, teacher_class_ids)

        if student_id not in allowed_student_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只能诊断自己班级的学生"
            )

    # 检查学生是否存在
    query = select(StudentModel).where(StudentModel.id == student_id)
    result = await db.execute(query)
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )

    # 执行诊断（传入空的练习数据，实际应用中应该从测试或问卷获取）
    try:
        kg_service = KnowledgeGraphService(db)
        result = await kg_service.diagnose_initial(
            db=db,
            student_id=student_id,
            practice_data=[],  # 实际应用中应该传入真实的练习数据
        )

        # 诊断完成后使相关缓存失效，确保下次获取时拿到最新数据
        cache = await get_student_cache()
        await cache.invalidate_student_all(str(student_id))

        return {
            "message": "诊断完成",
            "student_id": str(student_id),
            "status": "completed",
            "cefr_level": result.get("cefr_level"),
            "abilities": result.get("abilities"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"诊断失败: {str(e)}"
        )


@router.get("/{student_id}/progress")
async def get_student_progress(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: uuid.UUID,
) -> Any:
    """
    获取学生学习进度

    返回学生的学习进度统计，包括完成的内容、练习记录等。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        student_id: 学生ID

    Returns:
        dict: 学习进度数据

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 学生不存在
    """
    from sqlalchemy import select, func
    from app.models.student import Student as StudentModel
    from app.models.conversation import Conversation
    from app.models.practice import Practice

    # 权限检查
    if current_user.role == UserRole.STUDENT:
        if current_user.student_profile.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看其他学生的进度"
            )
    elif current_user.role == UserRole.TEACHER:
        # 教师只能查看自己班级学生的进度
        teacher_id = current_user.teacher_profile.id
        teacher_class_ids = await _get_teacher_class_ids(db, teacher_id)
        allowed_student_ids = await _get_class_student_ids(db, teacher_class_ids)

        if student_id not in allowed_student_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看该学生的进度"
            )

    # 检查学生是否存在
    query = select(StudentModel).where(StudentModel.id == student_id)
    result = await db.execute(query)
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学生不存在"
        )

    # 优化：使用单个查询获取所有统计数据，避免多次 COUNT
    from sqlalchemy import case, func

    # 统计对话次数
    conv_count_subquery = select(func.count(Conversation.id)).where(
        Conversation.student_id == student_id
    ).scalar_correlated_subquery()

    # 统计练习次数
    practice_count_subquery = select(func.count(Practice.id)).where(
        Practice.student_id == student_id
    ).scalar_correlated_subquery()

    # 计算平均分（已完成状态）
    avg_score_subquery = select(func.avg(Practice.score)).where(
        Practice.student_id == student_id,
        Practice.status == "completed"
    ).scalar_correlated_subquery()

    # 组合查询
    stats_query = select(
        conv_count_subquery.label("conversation_count"),
        practice_count_subquery.label("practice_count"),
        avg_score_subquery.label("average_score")
    )

    stats_result = await db.execute(stats_query)
    stats = stats_result.one_or_none()

    return {
        "student_id": str(student_id),
        "target_exam": student.target_exam,
        "target_score": student.target_score,
        "current_cefr_level": student.current_cefr_level,
        "conversation_count": stats.conversation_count if stats else 0,
        "practice_count": stats.practice_count if stats else 0,
        "average_score": round(stats.average_score, 2) if stats and stats.average_score else 0,
    }
