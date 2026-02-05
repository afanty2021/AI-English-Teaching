"""
题库服务 - AI英语教学系统
处理题库的CRUD操作和题目管理
"""
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import User, UserRole
from app.models.question import QuestionBank, Question


class QuestionBankService:
    """
    题库服务类

    核心功能：
    1. 创建题库
    2. 更新题库
    3. 删除题库
    4. 获取题库详情
    5. 列出题库（支持筛选）
    6. 添加题目到题库
    7. 从题库移除题目
    8. 获取题库中的题目
    9. 更新题库题目数量统计
    """

    def __init__(self, db: AsyncSession):
        """
        初始化题库服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def create_question_bank(
        self,
        name: str,
        practice_type: str,
        created_by: uuid.UUID,
        description: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: bool = False,
    ) -> QuestionBank:
        """
        创建新题库

        Args:
            name: 题库名称
            practice_type: 练习类型（reading, listening, grammar, vocabulary, writing, speaking）
            created_by: 创建者ID
            description: 题库描述
            difficulty_level: 难度等级
            tags: 标签列表
            is_public: 是否公开

        Returns:
            QuestionBank: 创建的题库

        Raises:
            ValueError: 用户不存在或权限不足
        """
        # 验证用户存在且是教师
        user = await self.db.get(User, created_by)
        if not user:
            raise ValueError("用户不存在")
        if user.role != UserRole.TEACHER:
            raise ValueError("只有教师可以创建题库")

        question_bank = QuestionBank(
            name=name,
            description=description,
            practice_type=practice_type,
            difficulty_level=difficulty_level,
            tags=tags or [],
            created_by=created_by,
            is_public=is_public,
            question_count=0,
        )

        self.db.add(question_bank)
        await self.db.commit()
        await self.db.refresh(question_bank)

        return question_bank

    async def update_question_bank(
        self,
        bank_id: uuid.UUID,
        user_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
    ) -> QuestionBank:
        """
        更新题库信息

        Args:
            bank_id: 题库ID
            user_id: 操作用户ID
            name: 新名称
            description: 新描述
            difficulty_level: 新难度等级
            tags: 新标签
            is_public: 是否公开

        Returns:
            QuestionBank: 更新后的题库

        Raises:
            ValueError: 题库不存在或权限不足
        """
        # 获取题库
        bank = await self._get_question_bank(bank_id)

        # 权限检查：只有创建者可以修改
        if bank.created_by != user_id:
            raise ValueError("无权修改此题库")

        # 更新字段
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if difficulty_level is not None:
            update_data["difficulty_level"] = difficulty_level
        if tags is not None:
            update_data["tags"] = tags
        if is_public is not None:
            update_data["is_public"] = is_public

        if update_data:
            await self.db.execute(
                update(QuestionBank)
                .where(QuestionBank.id == bank_id)
                .values(**update_data)
            )
            await self.db.commit()
            await self.db.refresh(bank)

        return bank

    async def delete_question_bank(
        self,
        bank_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """
        删除题库

        Args:
            bank_id: 题库ID
            user_id: 操作用户ID

        Raises:
            ValueError: 题库不存在或权限不足
        """
        # 获取题库
        bank = await self._get_question_bank(bank_id)

        # 权限检查：只有创建者可以删除
        if bank.created_by != user_id:
            raise ValueError("无权删除此题库")

        # 删除题库（级联删除题目）
        await self.db.delete(bank)
        await self.db.commit()

    async def get_question_bank(
        self,
        bank_id: uuid.UUID,
    ) -> QuestionBank:
        """
        获取题库详情

        Args:
            bank_id: 题库ID

        Returns:
            QuestionBank: 题库详情

        Raises:
            ValueError: 题库不存在
        """
        return await self._get_question_bank(bank_id)

    async def list_question_banks(
        self,
        user_id: Optional[uuid.UUID] = None,
        practice_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        is_public: Optional[bool] = None,
        include_public: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[QuestionBank], int]:
        """
        列出题库

        Args:
            user_id: 用户ID（用于过滤私有题库）
            practice_type: 练习类型筛选
            difficulty_level: 难度等级筛选
            is_public: 是否公开筛选
            include_public: 是否包含公开题库
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            tuple[List[QuestionBank], int]: (题库列表, 总数)
        """
        query = select(QuestionBank)

        # 筛选条件
        if practice_type:
            query = query.where(QuestionBank.practice_type == practice_type)

        if difficulty_level:
            query = query.where(QuestionBank.difficulty_level == difficulty_level)

        if is_public is not None:
            query = query.where(QuestionBank.is_public == is_public)
        elif user_id:
            # 如果指定了用户，返回该用户的题库和公开题库
            if include_public:
                query = query.where(
                    (QuestionBank.created_by == user_id) | (QuestionBank.is_public == True)
                )
            else:
                query = query.where(QuestionBank.created_by == user_id)
        elif not include_public:
            # 如果没有指定用户且不包含公开题库，返回空
            return [], 0

        # 按创建时间倒序
        query = query.order_by(QuestionBank.created_at.desc())

        # 获取总数
        count_query = select(func.count(QuestionBank.id))
        if practice_type:
            count_query = count_query.where(QuestionBank.practice_type == practice_type)
        if difficulty_level:
            count_query = count_query.where(QuestionBank.difficulty_level == difficulty_level)
        if is_public is not None:
            count_query = count_query.where(QuestionBank.is_public == is_public)
        elif user_id:
            if include_public:
                count_query = count_query.where(
                    (QuestionBank.created_by == user_id) | (QuestionBank.is_public == True)
                )
            else:
                count_query = count_query.where(QuestionBank.created_by == user_id)
        elif not include_public:
            count_query = count_query.where(False)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        banks = result.scalars().all()

        return list(banks), total

    async def add_question_to_bank(
        self,
        bank_id: uuid.UUID,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
        order_index: Optional[int] = None,
    ) -> Question:
        """
        添加题目到题库

        Args:
            bank_id: 题库ID
            question_id: 题目ID
            user_id: 操作用户ID
            order_index: 排序序号

        Returns:
            Question: 更新后的题目

        Raises:
            ValueError: 题库或题目不存在，或权限不足
        """
        # 获取题库
        bank = await self._get_question_bank(bank_id)

        # 权限检查：只有创建者可以添加题目
        if bank.created_by != user_id:
            raise ValueError("无权修改此题库")

        # 获取题目
        question = await self.db.get(Question, question_id)
        if not question:
            raise ValueError("题目不存在")

        # 检查题目是否已属于其他题库
        if question.question_bank_id and question.question_bank_id != bank_id:
            raise ValueError("题目已属于其他题库")

        # 设置题库和排序
        question.question_bank_id = bank_id
        if order_index is not None:
            question.order_index = order_index

        # 更新题库题目数量
        await self._increment_question_count(bank_id)

        await self.db.commit()
        await self.db.refresh(question)

        return question

    async def remove_question_from_bank(
        self,
        bank_id: uuid.UUID,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """
        从题库移除题目

        Args:
            bank_id: 题库ID
            question_id: 题目ID
            user_id: 操作用户ID

        Raises:
            ValueError: 题库不存在，或权限不足
        """
        # 获取题库
        bank = await self._get_question_bank(bank_id)

        # 权限检查：只有创建者可以移除题目
        if bank.created_by != user_id:
            raise ValueError("无权修改此题库")

        # 获取题目
        question = await self.db.execute(
            select(Question).where(
                Question.id == question_id,
                Question.question_bank_id == bank_id
            )
        )
        question = question.scalar_one_or_none()

        if not question:
            raise ValueError("题目不在此题库中")

        # 移除题目
        question.question_bank_id = None
        question.order_index = None

        # 更新题库题目数量
        await self._decrement_question_count(bank_id)

        await self.db.commit()

    async def get_bank_questions(
        self,
        bank_id: uuid.UUID,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Question]:
        """
        获取题库中的题目列表

        Args:
            bank_id: 题库ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            List[Question]: 题目列表

        Raises:
            ValueError: 题库不存在
        """
        # 确保题库存在
        await self._get_question_bank(bank_id)

        query = select(Question).where(
            Question.question_bank_id == bank_id,
            Question.is_active == True
        ).order_by(Question.order_index)

        if limit:
            query = query.limit(limit)
        query = query.offset(offset)

        result = await self.db.execute(query)
        questions = result.scalars().all()

        return list(questions)

    async def update_question_count(
        self,
        bank_id: uuid.UUID,
    ) -> None:
        """
        更新题库的题目数量统计

        Args:
            bank_id: 题库ID
        """
        # 统计题目数量
        count_query = select(func.count(Question.id)).where(
            Question.question_bank_id == bank_id
        )
        result = await self.db.execute(count_query)
        count = result.scalar() or 0

        # 更新题库
        await self.db.execute(
            update(QuestionBank)
            .where(QuestionBank.id == bank_id)
            .values(question_count=count)
        )
        await self.db.commit()

    async def _get_question_bank(self, bank_id: uuid.UUID) -> QuestionBank:
        """获取题库（内部方法）"""
        query = select(QuestionBank).where(QuestionBank.id == bank_id)
        result = await self.db.execute(query)
        bank = result.scalar_one_or_none()

        if not bank:
            raise ValueError(f"题库不存在: {bank_id}")

        return bank

    async def _increment_question_count(self, bank_id: uuid.UUID) -> None:
        """增加题库题目计数"""
        await self.db.execute(
            update(QuestionBank)
            .where(QuestionBank.id == bank_id)
            .values(question_count=QuestionBank.question_count + 1)
        )

    async def _decrement_question_count(self, bank_id: uuid.UUID) -> None:
        """减少题库题目计数"""
        await self.db.execute(
            update(QuestionBank)
            .where(QuestionBank.id == bank_id)
            .values(question_count=QuestionBank.question_count - 1)
        )


# 创建服务工厂函数
def get_question_bank_service(db: AsyncSession) -> QuestionBankService:
    """
    获取题库服务实例

    Args:
        db: 数据库会话

    Returns:
        QuestionBankService: 题库服务实例
    """
    return QuestionBankService(db)
