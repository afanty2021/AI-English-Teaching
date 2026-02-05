"""
练习会话API v1
提供练习会话的创建、答题、导航、完成等端点
"""
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User, UserRole
from app.models.question import QuestionType
from app.services.practice_session_service import get_practice_session_service

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def start_practice_session(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_data: dict,
) -> Any:
    """
    开始练习会话

    创建一个新的练习会话，支持多种题目来源。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_data: 会话数据，包含：
            - question_source: 题目来源类型（必填）："bank", "questions", "random"
            - question_bank_id: 题库ID（question_source=bank时必填）
            - question_ids: 题目ID列表（question_source=questions时必填）
            - practice_type: 练习类型（question_source=random时必填）
            - difficulty_level: 难度等级（random时可选）
            - count: 随机题目数量（random时可选，默认10）
            - title: 会话标题（可选）

    Returns:
        dict: 创建的练习会话

    Raises:
        HTTPException 400: 数据格式错误
        HTTPException 404: 题库或题目不存在
    """
    # 验证必填字段
    if "question_source" not in session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必填字段: question_source"
        )

    question_source = session_data["question_source"]

    # 验证题目来源
    if question_source not in ["bank", "questions", "random"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的题目来源，必须是: bank, questions, random"
        )

    # 根据来源验证相应字段
    if question_source == "bank" and "question_bank_id" not in session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question_source=bank时，必须提供question_bank_id"
        )

    if question_source == "questions" and "question_ids" not in session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question_source=questions时，必须提供question_ids数组"
        )

    if question_source == "random" and "practice_type" not in session_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="question_source=random时，必须提供practice_type"
        )

    service = get_practice_session_service(db)

    try:
        session = await service.start_practice_session(
            student_id=current_user.id,
            question_source=question_source,
            question_bank_id=session_data.get("question_bank_id"),
            question_ids=session_data.get("question_ids"),
            practice_type=session_data.get("practice_type"),
            difficulty_level=session_data.get("difficulty_level"),
            count=session_data.get("count", 10),
            title=session_data.get("title"),
        )

        return {
            "id": str(session.id),
            "title": session.title,
            "status": session.status,
            "total_questions": session.total_questions,
            "current_question_index": session.current_question_index,
            "question_count": session.question_count,
            "correct_count": session.correct_count,
            "created_at": session.created_at.isoformat(),
            "message": "练习会话创建成功"
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


@router.get("/{session_id}", response_model=dict)
async def get_practice_session(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: uuid.UUID,
) -> Any:
    """
    获取练习会话详情

    返回指定练习会话的详细信息。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_id: 练习会话ID

    Returns:
        dict: 练习会话详情

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 会话不存在
    """
    service = get_practice_session_service(db)

    try:
        session = await service.get_practice_session(session_id)

        # 权限检查：只能查看自己的会话
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权查看此练习会话"
            )

        return {
            "id": str(session.id),
            "title": session.title,
            "status": session.status,
            "total_questions": session.total_questions,
            "current_question_index": session.current_question_index,
            "question_count": session.question_count,
            "correct_count": session.correct_count,
            "progress_percentage": session.progress_percentage,
            "current_correct_rate": session.current_correct_rate,
            "question_bank_id": str(session.question_bank_id) if session.question_bank_id else None,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/{session_id}/current", response_model=dict)
async def get_current_question(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: uuid.UUID,
) -> Any:
    """
    获取当前题目

    返回当前需要回答的题目，如果已答过则包含之前的答案。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_id: 练习会话ID

    Returns:
        dict: 当前题目详情

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 会话不存在或已完成
    """
    service = get_practice_session_service(db)

    try:
        # 验证会话权限
        session = await service.get_practice_session(session_id)
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此练习会话"
            )

        question_data = await service.get_current_question(session_id)

        return {
            "session_id": str(session_id),
            "question_index": question_data["index"],
            "total_questions": question_data["total"],
            "is_answered": question_data["is_answered"],
            "previous_answer": question_data.get("previous_answer"),
            "question": {
                "id": str(question_data["question"].id),
                "question_type": question_data["question"].question_type,
                "content_text": question_data["question"].content_text,
                "difficulty_level": question_data["question"].difficulty_level,
                "topic": question_data["question"].topic,
                "knowledge_points": question_data["question"].knowledge_points,
                "options": question_data["question"].options,
                "order_index": question_data["question"].order_index,
                "passage_content": question_data["question"].passage_content,
                "audio_url": question_data["question"].audio_url,
            }
        }

    except ValueError as e:
        if "不存在" in str(e) or "已完成" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.post("/{session_id}/submit", response_model=dict)
async def submit_answer(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: uuid.UUID,
    answer_data: dict,
) -> Any:
    """
    提交答案

    提交当前题目的答案，支持断点续答。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_id: 练习会话ID
        answer_data: 答案数据，包含：
            - answer: 用户答案（必填）
            - question_index: 题目索引（可选，默认当前题目）

    Returns:
        dict: 答题结果

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 会话不存在
    """
    # 验证必填字段
    if "answer" not in answer_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必填字段: answer"
        )

    service = get_practice_session_service(db)

    try:
        # 验证会话权限
        session = await service.get_practice_session(session_id)
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此练习会话"
            )

        result = await service.submit_answer(
            session_id=session_id,
            answer=answer_data["answer"],
            question_index=answer_data.get("question_index"),
        )

        return {
            "is_correct": result["is_correct"],
            "correct_answer": result["correct_answer"],
            "explanation": result.get("explanation"),
            "current_question_index": result["current_question_index"],
            "correct_count": result["correct_count"],
            "question_count": result["question_count"],
            "is_completed": result["is_completed"],
            "message": "答案提交成功" if result["is_correct"] else "答案错误"
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


@router.post("/{session_id}/navigate", response_model=dict)
async def navigate_question(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: uuid.UUID,
    navigation_data: dict,
) -> Any:
    """
    导航题目

    在题目之间前后切换（翻页）。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_id: 练习会话ID
        navigation_data: 导航数据，包含：
            - direction: 方向（必填）："next" 或 "previous"

    Returns:
        dict: 新的当前题目

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 会话不存在或无更多题目
    """
    # 验证必填字段
    if "direction" not in navigation_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少必填字段: direction"
        )

    if navigation_data["direction"] not in ["next", "previous"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的direction，必须是: next 或 previous"
        )

    service = get_practice_session_service(db)

    try:
        # 验证会话权限
        session = await service.get_practice_session(session_id)
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此练习会话"
            )

        if navigation_data["direction"] == "next":
            question_data = await service.next_question(session_id)
        else:
            question_data = await service.previous_question(session_id)

        return {
            "session_id": str(session_id),
            "question_index": question_data["index"],
            "total_questions": question_data["total"],
            "is_answered": question_data["is_answered"],
            "previous_answer": question_data.get("previous_answer"),
            "question": {
                "id": str(question_data["question"].id),
                "question_type": question_data["question"].question_type,
                "content_text": question_data["question"].content_text,
                "difficulty_level": question_data["question"].difficulty_level,
                "topic": question_data["question"].topic,
                "knowledge_points": question_data["question"].knowledge_points,
                "options": question_data["question"].options,
                "order_index": question_data["question"].order_index,
                "passage_content": question_data["question"].passage_content,
                "audio_url": question_data["question"].audio_url,
            }
        }

    except ValueError as e:
        if "不存在" in str(e) or "无更多" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )


@router.post("/{session_id}/pause", response_model=dict)
async def pause_session(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: uuid.UUID,
) -> Any:
    """
    暂停练习会话

    暂停当前练习，稍后可以继续。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_id: 练习会话ID

    Returns:
        dict: 暂停结果

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 会话不存在
    """
    service = get_practice_session_service(db)

    try:
        # 验证会话权限
        session = await service.get_practice_session(session_id)
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此练习会话"
            )

        await service.pause_session(session_id)

        return {"message": "练习会话已暂停"}

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{session_id}/resume", response_model=dict)
async def resume_session(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: uuid.UUID,
) -> Any:
    """
    继续练习会话

    从暂停状态继续练习。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_id: 练习会话ID

    Returns:
        dict: 当前题目

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 会话不存在
    """
    service = get_practice_session_service(db)

    try:
        # 验证会话权限
        session = await service.get_practice_session(session_id)
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此练习会话"
            )

        question_data = await service.resume_session(session_id)

        return {
            "session_id": str(session_id),
            "question_index": question_data["index"],
            "total_questions": question_data["total"],
            "is_answered": question_data["is_answered"],
            "previous_answer": question_data.get("previous_answer"),
            "question": {
                "id": str(question_data["question"].id),
                "question_type": question_data["question"].question_type,
                "content_text": question_data["question"].content_text,
                "difficulty_level": question_data["question"].difficulty_level,
                "topic": question_data["question"].topic,
                "knowledge_points": question_data["question"].knowledge_points,
                "options": question_data["question"].options,
                "order_index": question_data["question"].order_index,
                "passage_content": question_data["question"].passage_content,
                "audio_url": question_data["question"].audio_url,
            },
            "message": "练习会话已继续"
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{session_id}/complete", response_model=dict)
async def complete_session(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: uuid.UUID,
) -> Any:
    """
    完成练习会话

    完成当前练习并生成结果报告。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_id: 练习会话ID

    Returns:
        dict: 练习结果

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 会话不存在
    """
    service = get_practice_session_service(db)

    try:
        # 验证会话权限
        session = await service.get_practice_session(session_id)
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此练习会话"
            )

        result = await service.complete_session(session_id)

        return {
            "session_id": str(session_id),
            "practice_id": str(result["practice_id"]) if result.get("practice_id") else None,
            "total_questions": result["total_questions"],
            "answered_questions": result["answered_questions"],
            "correct_count": result["correct_count"],
            "correct_rate": result["correct_rate"],
            "statistics": result["statistics"],
            "wrong_questions": result["wrong_questions"],
            "completed_at": result["completed_at"],
            "message": "练习完成"
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


@router.get("/", response_model=dict)
async def list_practice_sessions(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = Query(None, description="状态筛选"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回的记录数"),
) -> Any:
    """
    获取练习会话列表

    返回当前用户的练习会话列表。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        status_filter: 状态筛选（in_progress, paused, completed）
        skip: 跳过的记录数
        limit: 返回的记录数

    Returns:
        dict: 练习会话列表和总数
    """
    service = get_practice_session_service(db)

    sessions, total = await service.list_practice_sessions(
        student_id=current_user.id,
        status_filter=status_filter,
        limit=limit,
        offset=skip,
    )

    return {
        "total": total,
        "items": [
            {
                "id": str(s.id),
                "title": s.title,
                "status": s.status,
                "total_questions": s.total_questions,
                "current_question_index": s.current_question_index,
                "question_count": s.question_count,
                "correct_count": s.correct_count,
                "progress_percentage": s.progress_percentage,
                "question_bank_id": str(s.question_bank_id) if s.question_bank_id else None,
                "created_at": s.created_at.isoformat(),
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in sessions
        ],
    }


@router.get("/{session_id}/result", response_model=dict)
async def get_session_result(
    *,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    session_id: uuid.UUID,
) -> Any:
    """
    获取练习结果详情

    返回已完成练习会话的详细结果。

    Args:
        db: 数据库会话
        current_user: 当前认证用户
        session_id: 练习会话ID

    Returns:
        dict: 练习结果详情

    Raises:
        HTTPException 403: 权限不足
        HTTPException 404: 会话不存在或未完成
    """
    service = get_practice_session_service(db)

    try:
        # 验证会话权限
        session = await service.get_practice_session(session_id)
        if session.student_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权访问此练习会话"
            )

        if session.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="练习会话尚未完成"
            )

        result = await service.get_session_result(session_id)

        return {
            "session_id": str(session_id),
            "practice_id": str(result["practice_id"]) if result.get("practice_id") else None,
            "total_questions": result["total_questions"],
            "answered_questions": result["answered_questions"],
            "correct_count": result["correct_count"],
            "correct_rate": result["correct_rate"],
            "statistics": result["statistics"],
            "wrong_questions": result["wrong_questions"],
            "completed_at": result["completed_at"],
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
