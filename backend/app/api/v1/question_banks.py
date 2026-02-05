"""
题库API v1
提供题库的创建、查询、更新、删除等端点
"""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole
from app.models.question import QuestionBank, CEFRLevel
from app.services.question_bank_service import get_question_bank_service

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_question_bank(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_data: dict,
) -> Any:
    """
    创建题库

    教师可以创建题库来组织练习题目。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        bank_data: 题库数据，包含：
            - name: 题库名称（必填）
            - description: 题库描述（可选）
            - practice_type: 练习类型（必填）
            - difficulty_level: 难度等级（可选，CEFR: A1-C2）
            - tags: 标签列表（可选）
            - is_public: 是否公开（可选，默认false）

    Returns:
        dict: 创建的题库记录

    Raises:
        HTTPException 403: 权限不足
        HTTPException 400: 数据格式错误
    """
    # 权限检查：只有教师可以创建题库
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以创建题库"
        )

    # 验证必填字段
    required_fields = ["name", "practice_type"]
    for field in required_fields:
        if field not in bank_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {field}"
            )

    # 验证练习类型
    valid_types = ["reading", "listening", "grammar", "vocabulary", "writing", "speaking"]
    if bank_data["practice_type"] not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的练习类型，必须是: {', '.join(valid_types)}"
        )

    # 验证难度等级（如果提供）
    if "difficulty_level" in bank_data:
        try:
            level = CEFRLevel(bank_data["difficulty_level"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的难度等级，必须是CEFR标准（A1-C2）"
            )

    # 创建题库
    service = get_question_bank_service(db)
    bank = await service.create_question_bank(
        name=bank_data["name"],
        practice_type=bank_data["practice_type"],
        created_by=current_user.id,
        description=bank_data.get("description"),
        difficulty_level=bank_data.get("difficulty_level"),
        tags=bank_data.get("tags"),
        is_public=bank_data.get("is_public", False),
    )

    return {
        "id": str(bank.id),
        "name": bank.name,
        "description": bank.description,
        "practice_type": bank.practice_type,
        "difficulty_level": bank.difficulty_level,
        "tags": bank.tags,
        "is_public": bank.is_public,
        "question_count": bank.question_count,
        "created_by": str(bank.created_by),
        "created_at": bank.created_at.isoformat(),
        "message": "题库创建成功"
    }


@router.get("/{bank_id}", response_model=dict)
async def get_question_bank(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_id: uuid.UUID,
) -> Any:
    """
    获取题库详情

    返回指定题库的详细信息。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        bank_id: 题库记录ID

    Returns:
        dict: 题库记录详情

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 题库不存在
    """
    service = get_question_bank_service(db)

    try:
        bank = await service.get_question_bank(bank_id)

        # 权限检查：只能查看自己的题库或公开题库
        if bank.created_by != current_user.id and not bank.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此题库"
            )

        return {
            "id": str(bank.id),
            "name": bank.name,
            "description": bank.description,
            "practice_type": bank.practice_type,
            "difficulty_level": bank.difficulty_level,
            "tags": bank.tags,
            "is_public": bank.is_public,
            "question_count": bank.question_count,
            "created_by": str(bank.created_by),
            "created_at": bank.created_at.isoformat(),
            "updated_at": bank.updated_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{bank_id}", response_model=dict)
async def update_question_bank(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_id: uuid.UUID,
    update_data: dict,
) -> Any:
    """
    更新题库信息

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        bank_id: 题库记录ID
        update_data: 更新数据

    Returns:
        dict: 更新后的题库记录

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 题库不存在
    """
    # 权限检查：只有教师可以更新题库
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以更新题库"
        )

    service = get_question_bank_service(db)

    try:
        bank = await service.update_question_bank(
            bank_id=bank_id,
            user_id=current_user.id,
            name=update_data.get("name"),
            description=update_data.get("description"),
            difficulty_level=update_data.get("difficulty_level"),
            tags=update_data.get("tags"),
            is_public=update_data.get("is_public"),
        )

        return {
            "id": str(bank.id),
            "name": bank.name,
            "description": bank.description,
            "practice_type": bank.practice_type,
            "difficulty_level": bank.difficulty_level,
            "tags": bank.tags,
            "is_public": bank.is_public,
            "question_count": bank.question_count,
            "updated_at": bank.updated_at.isoformat(),
            "message": "题库更新成功"
        }

    except ValueError as e:
        if "不存在" in str(e) or "无权" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.delete("/{bank_id}", response_model=dict)
async def delete_question_bank(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_id: uuid.UUID,
) -> Any:
    """
    删除题库

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        bank_id: 题库记录ID

    Returns:
        dict: 删除结果

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 题库不存在
    """
    # 权限检查：只有教师可以删除题库
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以删除题库"
        )

    service = get_question_bank_service(db)

    try:
        await service.delete_question_bank(
            bank_id=bank_id,
            user_id=current_user.id,
        )

        return {"message": "题库删除成功"}

    except ValueError as e:
        if "不存在" in str(e) or "无权" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.get("/", response_model=dict)
async def list_question_banks(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    practice_type: Optional[str] = Query(None, description="练习类型筛选"),
    difficulty_level: Optional[str] = Query(None, description="难度等级筛选（CEFR: A1-C2）"),
    is_public: Optional[bool] = Query(None, description="是否公开筛选"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
) -> Any:
    """
    获取题库列表

    教师可以查看自己创建的题库和公开题库，学生只能查看公开题库。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        practice_type: 练习类型筛选
        difficulty_level: 难度等级筛选
        is_public: 是否公开筛选
        skip: 跳过的记录数
        limit: 返回的记录数

    Returns:
        dict: 题库列表和总数

    Raises:
        HTTPException 403: 权限不足
    """
    service = get_question_bank_service(db)

    # 确定用户ID参数
    user_id = current_user.id if current_user.role == UserRole.TEACHER else None
    include_public = current_user.role == UserRole.STUDENT

    banks, total = await service.list_question_banks(
        user_id=user_id,
        practice_type=practice_type,
        difficulty_level=difficulty_level,
        is_public=is_public,
        include_public=include_public,
        limit=limit,
        offset=skip,
    )

    return {
        "total": total,
        "items": [
            {
                "id": str(bank.id),
                "name": bank.name,
                "description": bank.description,
                "practice_type": bank.practice_type,
                "difficulty_level": bank.difficulty_level,
                "tags": bank.tags,
                "is_public": bank.is_public,
                "question_count": bank.question_count,
                "created_by": str(bank.created_by),
                "created_at": bank.created_at.isoformat(),
            }
            for b in banks
        ],
    }


@router.get("/{bank_id}/questions", response_model=dict)
async def get_bank_questions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
) -> Any:
    """
    获取题库中的题目列表

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        bank_id: 题库ID
        skip: 跳过的题目数
        limit: 返回的题目数

    Returns:
        dict: 题目列表和总数

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 题库不存在
    """
    service = get_question_bank_service(db)

    try:
        # 先验证题库访问权限
        bank = await service.get_question_bank(bank_id)

        # 权限检查：只能查看自己的题库或公开题库
        if bank.created_by != current_user.id and not bank.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此题库的题目"
            )

        questions = await service.get_bank_questions(
            bank_id=bank_id,
            limit=limit,
            offset=skip,
        )

        # 获取总数
        all_questions = await service.get_bank_questions(bank_id)
        total = len(all_questions)

        return {
            "total": total,
            "items": [
                {
                    "id": str(q.id),
                    "question_type": q.question_type,
                    "content_text": q.content_text,
                    "difficulty_level": q.difficulty_level,
                    "topic": q.topic,
                    "knowledge_points": q.knowledge_points,
                    "options": q.options,
                    "has_audio": q.has_audio,
                    "order_index": q.order_index,
                    "created_at": q.created_at.isoformat(),
                }
                for q in questions
            ],
        }

    except ValueError as e:
        if "不存在" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.post("/{bank_id}/questions", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_question_to_bank(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_id: uuid.UUID,
    question_data: dict,
) -> Any:
    """
    添加题目到题库

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        bank_id: 题库ID
        question_data: 题目数据

    Returns:
        dict: 添加的题目

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 题库不存在
    """
    # 权限检查：只有教师可以添加题目
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以添加题目"
        )

    # 验证必填字段
    required_fields = ["question_id"]
    for field in required_fields:
        if field not in question_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {field}"
            )

    try:
        question_id = uuid.UUID(question_data["question_id"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的question_id格式"
        )

    service = get_question_bank_service(db)

    try:
        question = await service.add_question_to_bank(
            bank_id=bank_id,
            question_id=question_id,
            user_id=current_user.id,
            order_index=question_data.get("order_index"),
        )

        return {
            "id": str(question.id),
            "question_bank_id": str(question.question_bank_id),
            "order_index": question.order_index,
            "message": "题目添加成功"
        }

    except ValueError as e:
        if "不存在" in str(e) or "无权" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.delete("/{bank_id}/questions/{question_id}", response_model=dict)
async def remove_question_from_bank(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    bank_id: uuid.UUID,
    question_id: uuid.UUID,
) -> Any:
    """
    从题库移除题目

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        bank_id: 题库ID
        question_id: 题目ID

    Returns:
        dict: 移除结果

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 题库或题目不存在
    """
    # 权限检查：只有教师可以移除题目
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以移除题目"
        )

    service = get_question_bank_service(db)

    try:
        await service.remove_question_from_bank(
            bank_id=bank_id,
            question_id=question_id,
            user_id=current_user.id,
        )

        return {"message": "题目移除成功"}

    except ValueError as e:
        if "不存在" in str(e) or "无权" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
