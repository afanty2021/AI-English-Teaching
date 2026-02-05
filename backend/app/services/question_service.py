"""
题目服务 - AI英语教学系统
处理题目的CRUD操作
"""
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserRole
from app.models.question import Question, QuestionBank, QuestionType
from app.services.question_bank_service import get_question_bank_service


class QuestionService:
    """
    题目服务类

    核心功能：
    1. 创建题目
    2. 更新题目
    3. 删除题目
    4. 获取题目详情
    5. 列出题目（支持筛选）
    6. 批量创建题目
    """

    def __init__(self, db: AsyncSession):
        """
        初始化题目服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def create_question(
        self,
        question_type: str,
        content_text: str,
        created_by: uuid.UUID,
        question_bank_id: Optional[uuid.UUID] = None,
        difficulty_level: Optional[str] = None,
        topic: Optional[str] = None,
        knowledge_points: Optional[List[str]] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        correct_answer: Optional[Any] = None,
        explanation: Optional[str] = None,
        order_index: Optional[int] = None,
        passage_content: Optional[str] = None,
        audio_url: Optional[str] = None,
        sample_answer: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Question:
        """
        创建新题目

        Args:
            question_type: 题目类型
            content_text: 题目内容
            created_by: 创建者ID
            question_bank_id: 所属题库ID
            difficulty_level: 难度等级（CEFR: A1-C2）
            topic: 主题分类
            knowledge_points: 知识点列表
            options: 选项列表（选择题）
            correct_answer: 正确答案
            explanation: 题目解析
            order_index: 排序序号
            passage_content: 文章内容（阅读理解）
            audio_url: 音频URL（听力题）
            sample_answer: 参考答案（写作/口语）
            extra_metadata: 扩展元数据

        Returns:
            Question: 创建的题目

        Raises:
            ValueError: 用户不存在或权限不足
        """
        # 验证用户存在且是教师
        user = await self.db.get(User, created_by)
        if not user:
            raise ValueError("用户不存在")
        if user.role != UserRole.TEACHER:
            raise ValueError("只有教师可以创建题目")

        # 如果指定了题库，验证题库存在且用户有权限
        if question_bank_id:
            bank_service = get_question_bank_service(self.db)
            bank = await bank_service.get_question_bank(question_bank_id)
            if bank.created_by != created_by:
                raise ValueError("无权向此题库添加题目")

        question = Question(
            question_type=question_type,
            content_text=content_text,
            question_bank_id=question_bank_id,
            difficulty_level=difficulty_level,
            topic=topic,
            knowledge_points=knowledge_points or [],
            options=options or [],
            correct_answer=correct_answer or {},
            explanation=explanation,
            created_by=created_by,
            order_index=order_index,
            passage_content=passage_content,
            audio_url=audio_url,
            sample_answer=sample_answer,
            extra_metadata=extra_metadata or {},
        )

        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)

        # 更新题库题目数量
        if question_bank_id:
            bank_service = get_question_bank_service(self.db)
            await bank_service.update_question_count(question_bank_id)

        return question

    async def update_question(
        self,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
        content_text: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        topic: Optional[str] = None,
        knowledge_points: Optional[List[str]] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        correct_answer: Optional[Any] = None,
        explanation: Optional[str] = None,
        is_active: Optional[bool] = None,
        passage_content: Optional[str] = None,
        audio_url: Optional[str] = None,
        sample_answer: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Question:
        """
        更新题目信息

        Args:
            question_id: 题目ID
            user_id: 操作用户ID
            content_text: 新题目内容
            difficulty_level: 新难度等级
            topic: 新主题
            knowledge_points: 新知识点列表
            options: 新选项
            correct_answer: 新正确答案
            explanation: 新解析
            is_active: 是否启用
            passage_content: 新文章内容
            audio_url: 新音频URL
            sample_answer: 新参考答案
            extra_metadata: 新扩展元数据

        Returns:
            Question: 更新后的题目

        Raises:
            ValueError: 题目不存在或权限不足
        """
        # 获取题目
        question = await self._get_question(question_id)

        # 权限检查：只有创建者可以修改
        if question.created_by != user_id:
            raise ValueError("无权修改此题目")

        # 更新字段
        update_data = {}
        if content_text is not None:
            update_data["content_text"] = content_text
        if difficulty_level is not None:
            update_data["difficulty_level"] = difficulty_level
        if topic is not None:
            update_data["topic"] = topic
        if knowledge_points is not None:
            update_data["knowledge_points"] = knowledge_points
        if options is not None:
            update_data["options"] = options
        if correct_answer is not None:
            update_data["correct_answer"] = correct_answer
        if explanation is not None:
            update_data["explanation"] = explanation
        if is_active is not None:
            update_data["is_active"] = is_active
        if passage_content is not None:
            update_data["passage_content"] = passage_content
        if audio_url is not None:
            update_data["audio_url"] = audio_url
        if sample_answer is not None:
            update_data["sample_answer"] = sample_answer
        if extra_metadata is not None:
            update_data["extra_metadata"] = extra_metadata

        if update_data:
            await self.db.execute(
                update(Question)
                .where(Question.id == question_id)
                .values(**update_data)
            )
            await self.db.commit()
            await self.db.refresh(question)

        return question

    async def delete_question(
        self,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """
        删除题目

        Args:
            question_id: 题目ID
            user_id: 操作用户ID

        Raises:
            ValueError: 题目不存在或权限不足
        """
        # 获取题目
        question = await self._get_question(question_id)

        # 权限检查：只有创建者可以删除
        if question.created_by != user_id:
            raise ValueError("无权删除此题目")

        # 记录题库ID（用于更新计数）
        bank_id = question.question_bank_id

        # 删除题目
        await self.db.delete(question)
        await self.db.commit()

        # 更新题库题目数量
        if bank_id:
            bank_service = get_question_bank_service(self.db)
            await bank_service.update_question_count(bank_id)

    async def get_question(
        self,
        question_id: uuid.UUID,
    ) -> Question:
        """
        获取题目详情

        Args:
            question_id: 题目ID

        Returns:
            Question: 题目详情

        Raises:
            ValueError: 题目不存在
        """
        return await self._get_question(question_id)

    async def list_questions(
        self,
        user_id: Optional[uuid.UUID] = None,
        question_type: Optional[QuestionType] = None,
        difficulty_level: Optional[str] = None,
        topic: Optional[str] = None,
        question_bank_id: Optional[uuid.UUID] = None,
        is_active: Optional[bool] = True,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Question], int]:
        """
        列出题目

        Args:
            user_id: 用户ID（用于权限过滤）
            question_type: 题目类型筛选
            difficulty_level: 难度等级筛选
            topic: 主题筛选
            question_bank_id: 题库ID筛选
            is_active: 是否只显示启用的题目
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            tuple[List[Question], int]: (题目列表, 总数)
        """
        query = select(Question)

        # 筛选条件
        if question_type:
            query = query.where(Question.question_type == question_type.value)

        if difficulty_level:
            query = query.where(Question.difficulty_level == difficulty_level)

        if topic:
            query = query.where(Question.topic == topic)

        if question_bank_id:
            query = query.where(Question.question_bank_id == question_bank_id)

        if is_active is not None:
            query = query.where(Question.is_active == is_active)

        # 权限过滤：只显示用户创建的题目或公开题库的题目
        if user_id:
            # 获取用户创建的题库ID列表
            user_bank_ids = await self._get_user_bank_ids(user_id)
            query = query.where(
                (Question.created_by == user_id) |
                (Question.question_bank_id.in_(user_bank_ids))
            )
        else:
            # 未指定用户，只返回公开题库的题目
            public_bank_ids = await self._get_public_bank_ids()
            query = query.where(Question.question_bank_id.in_(public_bank_ids))

        # 按创建时间倒序
        query = query.order_by(Question.created_at.desc())

        # 获取总数
        count_query = select(func.count(Question.id))
        if question_type:
            count_query = count_query.where(Question.question_type == question_type.value)
        if difficulty_level:
            count_query = count_query.where(Question.difficulty_level == difficulty_level)
        if topic:
            count_query = count_query.where(Question.topic == topic)
        if question_bank_id:
            count_query = count_query.where(Question.question_bank_id == question_bank_id)
        if is_active is not None:
            count_query = count_query.where(Question.is_active == is_active)
        if user_id:
            user_bank_ids = await self._get_user_bank_ids(user_id)
            count_query = count_query.where(
                (Question.created_by == user_id) |
                (Question.question_bank_id.in_(user_bank_ids))
            )
        else:
            public_bank_ids = await self._get_public_bank_ids()
            count_query = count_query.where(Question.question_bank_id.in_(public_bank_ids))

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        questions = result.scalars().all()

        return list(questions), total

    async def batch_create_questions(
        self,
        questions_data: List[Dict[str, Any]],
        created_by: uuid.UUID,
        question_bank_id: Optional[uuid.UUID] = None,
    ) -> List[Question]:
        """
        批量创建题目

        Args:
            questions_data: 题目数据列表
            created_by: 创建者ID
            question_bank_id: 所属题库ID

        Returns:
            List[Question]: 创建的题目列表
        """
        created_questions = []

        for i, data in enumerate(questions_data):
            # 设置排序序号
            if "order_index" not in data:
                data["order_index"] = i

            question = await self.create_question(
                created_by=created_by,
                question_bank_id=question_bank_id,
                **data
            )
            created_questions.append(question)

        return created_questions

    async def _get_question(self, question_id: uuid.UUID) -> Question:
        """获取题目（内部方法）"""
        query = select(Question).where(Question.id == question_id)
        result = await self.db.execute(query)
        question = result.scalar_one_or_none()

        if not question:
            raise ValueError(f"题目不存在: {question_id}")

        return question

    async def _get_user_bank_ids(self, user_id: uuid.UUID) -> List[uuid.UUID]:
        """获取用户创建的题库ID列表"""
        query = select(QuestionBank.id).where(QuestionBank.created_by == user_id)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_public_bank_ids(self) -> List[uuid.UUID]:
        """获取公开题库ID列表"""
        query = select(QuestionBank.id).where(QuestionBank.is_public == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())


# 创建服务工厂函数
def get_question_service(db: AsyncSession) -> QuestionService:
    """
    获取题目服务实例

    Args:
        db: 数据库会话

    Returns:
        QuestionService: 题目服务实例
    """
    return QuestionService(db)
