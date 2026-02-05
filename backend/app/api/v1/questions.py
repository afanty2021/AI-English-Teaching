"""
题目API v1
提供题目的创建、查询、更新、删除等端点
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole
from app.models.question import Question, QuestionType
from app.services.question_service import get_question_service

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_question(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    question_data: dict,
) -> Any:
    """
    创建题目

    教师可以创建各类题目。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        question_data: 题目数据，包含：
            - question_type: 题目类型（必填）
            - content_text: 题目内容（必填）
            - question_bank_id: 所属题库ID（可选）
            - difficulty_level: 难度等级（CEFR: A1-C2）
            - topic: 主题分类
            - knowledge_points: 知识点列表
            - options: 选项列表（选择题）
            - correct_answer: 正确答案
            - explanation: 题目解析
            - order_index: 排序序号
            - passage_content: 文章内容（阅读理解）
            - audio_url: 音频URL（听力题）
            - sample_answer: 参考答案（写作/口语）
            - extra_metadata: 扩展元数据

    Returns:
        dict: 创建的题目记录

    Raises:
        HTTPException 403: 权限不足
        HTTPException 400: 数据格式错误
    """
    # 权限检查：只有教师可以创建题目
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以创建题目"
        )

    # 验证必填字段
    required_fields = ["question_type", "content_text"]
    for field in required_fields:
        if field not in question_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"缺少必填字段: {field}"
            )

    # 验证题目类型
    try:
        question_type = QuestionType(question_data["question_type"])
    except ValueError:
        valid_types = [t.value for t in QuestionType]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的题目类型，必须是: {', '.join(valid_types)}"
        )

    # 验证难度等级（如果提供）
    if question_data.get("difficulty_level"):
        from app.models.question import CEFRLevel
        try:
            CEFRLevel(question_data["difficulty_level"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的难度等级，必须是CEFR标准（A1-C2）"
            )

    service = get_question_service(db)

    try:
        question = await service.create_question(
            question_type=question_type,
            content_text=question_data["content_text"],
            created_by=current_user.id,
            question_bank_id=question_data.get("question_bank_id"),
            difficulty_level=question_data.get("difficulty_level"),
            topic=question_data.get("topic"),
            knowledge_points=question_data.get("knowledge_points"),
            options=question_data.get("options"),
            correct_answer=question_data.get("correct_answer"),
            explanation=question_data.get("explanation"),
            order_index=question_data.get("order_index"),
            passage_content=question_data.get("passage_content"),
            audio_url=question_data.get("audio_url"),
            sample_answer=question_data.get("sample_answer"),
            extra_metadata=question_data.get("extra_metadata"),
        )

        return {
            "id": str(question.id),
            "question_type": question.question_type,
            "content_text": question.content_text,
            "question_bank_id": str(question.question_bank_id) if question.question_bank_id else None,
            "difficulty_level": question.difficulty_level,
            "topic": question.topic,
            "knowledge_points": question.knowledge_points,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "order_index": question.order_index,
            "passage_content": question.passage_content,
            "audio_url": question.audio_url,
            "sample_answer": question.sample_answer,
            "created_by": str(question.created_by),
            "created_at": question.created_at.isoformat(),
            "message": "题目创建成功"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{question_id}", response_model=dict)
async def get_question(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    question_id: uuid.UUID,
) -> Any:
    """
    获取题目详情

    返回指定题目的详细信息。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        question_id: 题目记录ID

    Returns:
        dict: 题目记录详情

    Raises:
        HTTPException 404: 题目不存在
    """
    service = get_question_service(db)

    try:
        question = await service.get_question(question_id)

        # 权限检查：只能查看自己创建的题目或公开题库的题目
        if question.created_by != current_user.id:
            # 检查是否属于公开题库
            if question.question_bank_id:
                from app.services.question_bank_service import get_question_bank_service
                bank_service = get_question_bank_service(db)
                try:
                    bank = await bank_service.get_question_bank(question.question_bank_id)
                    if not bank.is_public:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="无权查看此题目"
                        )
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="无权查看此题目"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权查看此题目"
                )

        return {
            "id": str(question.id),
            "question_type": question.question_type,
            "content_text": question.content_text,
            "question_bank_id": str(question.question_bank_id) if question.question_bank_id else None,
            "difficulty_level": question.difficulty_level,
            "topic": question.topic,
            "knowledge_points": question.knowledge_points,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "order_index": question.order_index,
            "passage_content": question.passage_content,
            "audio_url": question.audio_url,
            "sample_answer": question.sample_answer,
            "extra_metadata": question.extra_metadata,
            "is_active": question.is_active,
            "created_by": str(question.created_by),
            "created_at": question.created_at.isoformat(),
            "updated_at": question.updated_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/{question_id}", response_model=dict)
async def update_question(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    question_id: uuid.UUID,
    update_data: dict,
) -> Any:
    """
    更新题目信息

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        question_id: 题目记录ID
        update_data: 更新数据

    Returns:
        dict: 更新后的题目记录

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 题目不存在
    """
    # 权限检查：只有教师可以更新题目
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以更新题目"
        )

    service = get_question_service(db)

    try:
        question = await service.update_question(
            question_id=question_id,
            user_id=current_user.id,
            content_text=update_data.get("content_text"),
            difficulty_level=update_data.get("difficulty_level"),
            topic=update_data.get("topic"),
            knowledge_points=update_data.get("knowledge_points"),
            options=update_data.get("options"),
            correct_answer=update_data.get("correct_answer"),
            explanation=update_data.get("explanation"),
            is_active=update_data.get("is_active"),
            passage_content=update_data.get("passage_content"),
            audio_url=update_data.get("audio_url"),
            sample_answer=update_data.get("sample_answer"),
            extra_metadata=update_data.get("extra_metadata"),
        )

        return {
            "id": str(question.id),
            "question_type": question.question_type,
            "content_text": question.content_text,
            "question_bank_id": str(question.question_bank_id) if question.question_bank_id else None,
            "difficulty_level": question.difficulty_level,
            "topic": question.topic,
            "knowledge_points": question.knowledge_points,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "is_active": question.is_active,
            "updated_at": question.updated_at.isoformat(),
            "message": "题目更新成功"
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


@router.delete("/{question_id}", response_model=dict)
async def delete_question(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    question_id: uuid.UUID,
) -> Any:
    """
    删除题目

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        question_id: 题目记录ID

    Returns:
        dict: 删除结果

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 题目不存在
    """
    # 权限检查：只有教师可以删除题目
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以删除题目"
        )

    service = get_question_service(db)

    try:
        await service.delete_question(
            question_id=question_id,
            user_id=current_user.id,
        )

        return {"message": "题目删除成功"}

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
async def list_questions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    question_type: Optional[str] = Query(None, description="题目类型筛选"),
    difficulty_level: Optional[str] = Query(None, description="难度等级筛选（CEFR: A1-C2）"),
    topic: Optional[str] = Query(None, description="主题筛选"),
    question_bank_id: Optional[uuid.UUID] = Query(None, description="题库ID筛选"),
    is_active: Optional[bool] = Query(True, description="是否只显示启用的题目"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
) -> Any:
    """
    获取题目列表

    教师可以查看自己创建的题目，学生可以查看公开题库的题目。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        question_type: 题目类型筛选
        difficulty_level: 难度等级筛选
        topic: 主题筛选
        question_bank_id: 题库ID筛选
        is_active: 是否只显示启用的题目
        skip: 跳过的记录数
        limit: 返回的记录数

    Returns:
        dict: 题目列表和总数
    """
    service = get_question_service(db)

    # 确定用户ID参数
    user_id = current_user.id if current_user.role == UserRole.TEACHER else None

    # 转换题目类型
    q_type = None
    if question_type:
        try:
            q_type = QuestionType(question_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的题目类型: {question_type}"
            )

    questions, total = await service.list_questions(
        user_id=user_id,
        question_type=q_type,
        difficulty_level=difficulty_level,
        topic=topic,
        question_bank_id=question_bank_id,
        is_active=is_active,
        limit=limit,
        offset=skip,
    )

    return {
        "total": total,
        "items": [
            {
                "id": str(q.id),
                "question_type": q.question_type,
                "content_text": q.content_text,
                "question_bank_id": str(q.question_bank_id) if q.question_bank_id else None,
                "difficulty_level": q.difficulty_level,
                "topic": q.topic,
                "knowledge_points": q.knowledge_points,
                "options": q.options,
                "has_audio": q.has_audio,
                "is_active": q.is_active,
                "order_index": q.order_index,
                "created_by": str(q.created_by),
                "created_at": q.created_at.isoformat(),
            }
            for q in questions
        ],
    }


@router.post("/batch", response_model=dict, status_code=status.HTTP_201_CREATED)
async def batch_create_questions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    batch_data: dict,
) -> Any:
    """
    批量创建题目

    教师可以批量创建题目到指定题库。

    Args:
        db: 数据库会话
        current_user: 当前认证用户（必须是教师）
        batch_data: 批量数据，包含：
            - questions: 题目数据列表（必填）
            - question_bank_id: 所属题库ID（可选）

    Returns:
        dict: 创建的题目列表

    Raises:
        HTTPException 403: 权限不足
        HTTPException 400: 数据格式错误
    """
    # 权限检查：只有教师可以批量创建题目
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有教师可以批量创建题目"
        )

    # 验证必填字段
    if "questions" not in batch_data or not isinstance(batch_data["questions"], list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必填字段: questions（必须是数组）"
        )

    if not batch_data["questions"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="questions数组不能为空"
        )

    service = get_question_service(db)

    try:
        questions = await service.batch_create_questions(
            questions_data=batch_data["questions"],
            created_by=current_user.id,
            question_bank_id=batch_data.get("question_bank_id"),
        )

        return {
            "total": len(questions),
            "items": [
                {
                    "id": str(q.id),
                    "question_type": q.question_type,
                    "content_text": q.content_text,
                    "question_bank_id": str(q.question_bank_id) if q.question_bank_id else None,
                    "order_index": q.order_index,
                }
                for q in questions
            ],
            "message": f"成功创建 {len(questions)} 道题目"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
