"""
错题本服务 - AI英语教学系统
处理错题的收集、分析、复习等业务逻辑
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, and_, or_, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Mistake,
    MistakeStatus,
    MistakeType,
    Practice,
    Student,
    Content,
)


class MistakeService:
    """
    错题本服务类

    核心功能：
    1. 从练习记录中自动收集错题
    2. 管理错题状态（待复习、复习中、已掌握）
    3. 生成错题复习计划
    4. 追踪错题掌握程度
    5. 统计错题数据
    6. AI生成错题解析和建议

    与知识图谱集成：
    - 错题数据可触发知识图谱更新
    - 根据错题类型识别薄弱知识点
    """

    def __init__(self, db: AsyncSession):
        """
        初始化错题本服务

        Args:
            db: 数据库会话
        """
        self.db = db

    async def create_mistake(
        self,
        student_id: uuid.UUID,
        question: str,
        wrong_answer: str,
        correct_answer: str,
        mistake_type: MistakeType,
        practice_id: Optional[uuid.UUID] = None,
        content_id: Optional[uuid.UUID] = None,
        explanation: Optional[str] = None,
        knowledge_points: Optional[List[str]] = None,
        difficulty_level: Optional[str] = None,
        topic: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Mistake:
        """
        创建错题记录

        Args:
            student_id: 学生ID
            question: 题目内容
            wrong_answer: 学生错误答案
            correct_answer: 正确答案
            mistake_type: 错题类型
            practice_id: 关联的练习记录ID（可选）
            content_id: 关联的内容ID（可选）
            explanation: 错题解析
            knowledge_points: 知识点列表
            difficulty_level: 难度等级
            topic: 主题分类
            extra_metadata: 扩展元数据

        Returns:
            Mistake: 创建的错题记录
        """
        mistake = Mistake(
            student_id=student_id,
            practice_id=practice_id,
            content_id=content_id,
            mistake_type=mistake_type.value,
            question=question,
            wrong_answer=wrong_answer,
            correct_answer=correct_answer,
            explanation=explanation,
            knowledge_points=knowledge_points or [],
            difficulty_level=difficulty_level,
            topic=topic,
            extra_metadata=extra_metadata or {},
            status=MistakeStatus.PENDING.value,
            first_mistaken_at=datetime.utcnow(),
            last_mistaken_at=datetime.utcnow(),
        )

        self.db.add(mistake)
        await self.db.commit()
        await self.db.refresh(mistake)

        return mistake

    async def collect_mistakes_from_practice(
        self,
        practice_id: uuid.UUID,
    ) -> List[Mistake]:
        """
        从练习记录中自动收集错题

        分析练习记录中的错误答案，自动创建错题记录。

        Args:
            practice_id: 练习记录ID

        Returns:
            List[Mistake]: 收集到的错题列表
        """
        # 获取练习记录
        practice = await self.db.get(Practice, practice_id)
        if not practice:
            raise ValueError(f"练习记录不存在: {practice_id}")

        # 检查是否已完成
        if practice.status != "completed":
            raise ValueError("练习未完成，无法收集错题")

        # 检查是否已收集过
        existing_mistakes = await self.db.execute(
            select(Mistake).where(Mistake.practice_id == practice_id)
        )
        if existing_mistakes.scalar_one_or_none():
            raise ValueError("该练习已收集过错题")

        # 从练习结果中提取错题
        mistakes = []
        answers = practice.answers or {}
        result_details = practice.result_details or {}

        # 假设answers格式为: {question_index: {question, user_answer, correct_answer, is_correct}}
        for question_idx, answer_data in answers.items():
            if not answer_data.get("is_correct", True):
                # 这是一个错题
                mistake_type = self._infer_mistake_type(
                    practice.practice_type,
                    answer_data.get("question_type"),
                )

                mistake = await self.create_mistake(
                    student_id=practice.student_id,
                    question=answer_data.get("question", ""),
                    wrong_answer=answer_data.get("user_answer", ""),
                    correct_answer=answer_data.get("correct_answer", ""),
                    mistake_type=mistake_type,
                    practice_id=practice_id,
                    content_id=practice.content_id,
                    difficulty_level=practice.difficulty_level,
                    topic=practice.topic,
                    extra_metadata={
                        "question_index": question_idx,
                        "question_type": answer_data.get("question_type"),
                        "options": answer_data.get("options"),
                    },
                )
                mistakes.append(mistake)

        return mistakes

    async def get_mistake(
        self,
        mistake_id: uuid.UUID,
    ) -> Mistake:
        """
        获取错题详情

        Args:
            mistake_id: 错题ID

        Returns:
            Mistake: 错题记录

        Raises:
            ValueError: 错题不存在
        """
        mistake = await self.db.get(Mistake, mistake_id)
        if not mistake:
            raise ValueError(f"错题不存在: {mistake_id}")
        return mistake

    async def list_student_mistakes(
        self,
        student_id: uuid.UUID,
        status: Optional[MistakeStatus] = None,
        mistake_type: Optional[MistakeType] = None,
        topic: Optional[str] = None,
        knowledge_point: Optional[str] = None,
        needs_ai_analysis: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Mistake], int]:
        """
        获取学生的错题列表

        Args:
            student_id: 学生ID
            status: 状态筛选
            mistake_type: 错题类型筛选
            topic: 主题筛选
            knowledge_point: 知识点筛选
            needs_ai_analysis: 是否需要AI分析筛选
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            tuple[List[Mistake], int]: (错题列表, 总数)
        """
        query = select(Mistake).where(Mistake.student_id == student_id)

        if status:
            query = query.where(Mistake.status == status.value)
        if mistake_type:
            query = query.where(Mistake.mistake_type == mistake_type.value)
        if topic:
            query = query.where(Mistake.topic == topic)
        if knowledge_point:
            query = query.where(Mistake.knowledge_points.contains([knowledge_point]))
        if needs_ai_analysis is not None:
            query = query.where(Mistake.needs_ai_analysis == needs_ai_analysis)

        # 按最后错误时间倒序
        query = query.order_by(Mistake.last_mistaken_at.desc())

        # 获取总数
        count_query = select(sql_func.count(Mistake.id)).where(Mistake.student_id == student_id)
        if status:
            count_query = count_query.where(Mistake.status == status.value)
        if mistake_type:
            count_query = count_query.where(Mistake.mistake_type == mistake_type.value)
        if topic:
            count_query = count_query.where(Mistake.topic == topic)
        if knowledge_point:
            count_query = count_query.where(Mistake.knowledge_points.contains([knowledge_point]))
        if needs_ai_analysis is not None:
            count_query = count_query.where(Mistake.needs_ai_analysis == needs_ai_analysis)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0

        # 分页
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        mistakes = result.scalars().all()

        return list(mistakes), total

    async def update_mistake_status(
        self,
        mistake_id: uuid.UUID,
        status: MistakeStatus,
    ) -> Mistake:
        """
        更新错题状态

        Args:
            mistake_id: 错题ID
            status: 新状态

        Returns:
            Mistake: 更新后的错题记录
        """
        mistake = await self.get_mistake(mistake_id)

        mistake.status = status.value

        # 如果开始复习，更新复习时间
        if status == MistakeStatus.REVIEWING:
            mistake.last_reviewed_at = datetime.utcnow()
            mistake.review_count += 1

        await self.db.commit()
        await self.db.refresh(mistake)

        return mistake

    async def record_mistake_retry(
        self,
        mistake_id: uuid.UUID,
        user_answer: str,
        is_correct: bool,
    ) -> Dict[str, Any]:
        """
        记录错题重做结果

        Args:
            mistake_id: 错题ID
            user_answer: 学生答案
            is_correct: 是否正确

        Returns:
            Dict[str, Any]: 重做结果，包含：
                - mistake: 错题记录
                - mastered: 是否掌握
                - review_count: 复习次数
        """
        mistake = await self.get_mistake(mistake_id)

        # 更新复习次数
        mistake.review_count += 1
        mistake.last_reviewed_at = datetime.utcnow()

        mastered = False

        if is_correct:
            # 答对了，检查是否掌握
            # 连续答对2次或复习3次以上可标记为掌握
            if mistake.review_count >= 2:
                mistake.status = MistakeStatus.MASTERED.value
                mastered = True
            else:
                mistake.status = MistakeStatus.REVIEWING.value
        else:
            # 又错了，重置状态并增加错误次数
            mistake.status = MistakeStatus.PENDING.value
            mistake.mistake_count += 1
            mistake.last_mistaken_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(mistake)

        return {
            "mistake": mistake,
            "mastered": mastered,
            "review_count": mistake.review_count,
            "mistake_count": mistake.mistake_count,
        }

    async def get_mistake_statistics(
        self,
        student_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取学生错题统计数据

        Args:
            student_id: 学生ID

        Returns:
            Dict[str, Any]: 统计数据，包含：
                - total_mistakes: 总错题数
                - by_status: 按状态统计
                - by_type: 按类型统计
                - by_topic: 按主题统计
                - mastery_rate: 掌握率
                - need_review_count: 待复习数量
                - recent_mistakes: 近期错题
        """
        # 获取所有错题
        query = select(Mistake).where(Mistake.student_id == student_id)
        result = await self.db.execute(query)
        all_mistakes = result.scalars().all()

        total_mistakes = len(all_mistakes)

        # 按状态统计
        by_status = {
            "pending": 0,
            "reviewing": 0,
            "mastered": 0,
            "ignored": 0,
        }
        for mistake in all_mistakes:
            by_status[mistake.status] = by_status.get(mistake.status, 0) + 1

        # 按类型统计
        by_type: Dict[str, int] = {}
        for mistake in all_mistakes:
            mtype = mistake.mistake_type
            by_type[mtype] = by_type.get(mtype, 0) + 1

        # 按主题统计
        by_topic: Dict[str, int] = {}
        for mistake in all_mistakes:
            if mistake.topic:
                topic = mistake.topic
                by_topic[topic] = by_topic.get(topic, 0) + 1

        # 掌握率
        mastered_count = by_status.get("mastered", 0)
        mastery_rate = mastered_count / total_mistakes if total_mistakes > 0 else 0

        # 待复习数量
        need_review_count = by_status.get("pending", 0) + by_status.get("reviewing", 0)

        # 近期错题（最近7天）
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_mistakes = [
            m for m in all_mistakes
            if m.last_mistaken_at >= week_ago
        ]

        # 高频错题（错误次数>=3）
        frequent_mistakes = [
            m for m in all_mistakes
            if m.mistake_count >= 3 and m.status != MistakeStatus.MASTERED.value
        ]

        return {
            "student_id": str(student_id),
            "total_mistakes": total_mistakes,
            "by_status": by_status,
            "by_type": by_type,
            "by_topic": by_topic,
            "mastery_rate": round(mastery_rate, 2),
            "need_review_count": need_review_count,
            "recent_mistakes_count": len(recent_mistakes),
            "frequent_mistakes_count": len(frequent_mistakes),
        }

    async def get_review_plan(
        self,
        student_id: uuid.UUID,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """
        获取错题复习计划

        基于艾宾浩斯遗忘曲线和错题重要性，生成个性化的复习计划。

        Args:
            student_id: 学生ID
            limit: 返回的错题数量

        Returns:
            Dict[str, Any]: 复习计划，包含：
                - urgent: 紧急复习（新错题、高频错题）
                - today: 今日复习
                - week: 本周复习
                - knowledge_points: 需要重点复习的知识点
        """
        # 获取待复习的错题
        query = select(Mistake).where(
            and_(
                Mistake.student_id == student_id,
                Mistake.status.in_([
                    MistakeStatus.PENDING.value,
                    MistakeStatus.REVIEWING.value,
                ])
            )
        ).order_by(
            # 按优先级排序：错误次数高 -> 最近错误 -> 复习次数少
            Mistake.mistake_count.desc(),
            Mistake.last_mistaken_at.desc(),
            Mistake.review_count.asc(),
        )

        result = await self.db.execute(query)
        all_pending = result.scalars().all()

        # 分类
        urgent = []
        today = []
        week = []

        for mistake in all_pending[:limit]:
            # 紧急：错误次数>=3 或 从未复习
            if mistake.mistake_count >= 3 or mistake.review_count == 0:
                urgent.append(mistake)
            # 今日：1-3天内需要复习的
            elif mistake.last_reviewed_at is None or \
                 (datetime.utcnow() - mistake.last_reviewed_at) < timedelta(days=3):
                today.append(mistake)
            # 本周：其他待复习
            else:
                week.append(mistake)

        # 统计需要重点复习的知识点
        knowledge_point_counts: Dict[str, int] = {}
        for mistake in all_pending:
            if mistake.knowledge_points:
                for kp in mistake.knowledge_points:
                    knowledge_point_counts[kp] = knowledge_point_counts.get(kp, 0) + 1

        # 排序取前10
        top_knowledge_points = sorted(
            knowledge_point_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            "student_id": str(student_id),
            "urgent": [{"id": str(m.id), "question": m.question[:100], "type": m.mistake_type} for m in urgent[:5]],
            "today": [{"id": str(m.id), "question": m.question[:100], "type": m.mistake_type} for m in today[:10]],
            "week": [{"id": str(m.id), "question": m.question[:100], "type": m.mistake_type} for m in week[:20]],
            "knowledge_points": top_knowledge_points,
            "total_pending": len(all_pending),
        }

    async def update_ai_analysis(
        self,
        mistake_id: uuid.UUID,
        ai_suggestion: str,
        ai_analysis: Optional[Dict[str, Any]] = None,
    ) -> Mistake:
        """
        更新错题的AI分析结果

        Args:
            mistake_id: 错题ID
            ai_suggestion: AI生成的学习建议
            ai_analysis: AI分析详情

        Returns:
            Mistake: 更新后的错题记录
        """
        mistake = await self.get_mistake(mistake_id)

        mistake.ai_suggestion = ai_suggestion
        mistake.ai_analysis = ai_analysis or {}
        mistake.needs_ai_analysis = False

        await self.db.commit()
        await self.db.refresh(mistake)

        return mistake

    def _infer_mistake_type(
        self,
        practice_type: str,
        question_type: Optional[str] = None,
    ) -> MistakeType:
        """
        根据练习类型推断错题类型

        Args:
            practice_type: 练习类型
            question_type: 题目类型（可选）

        Returns:
            MistakeType: 推断的错题类型
        """
        type_mapping = {
            "reading": MistakeType.READING,
            "listening": MistakeType.LISTENING,
            "writing": MistakeType.WRITING,
            "speaking": MistakeType.SPEAKING,
            "grammar": MistakeType.GRAMMAR,
            "vocabulary": MistakeType.VOCABULARY,
        }

        # 如果有明确的问题类型，优先使用
        if question_type:
            question_type_lower = question_type.lower()
            if "grammar" in question_type_lower:
                return MistakeType.GRAMMAR
            elif "vocab" in question_type_lower:
                return MistakeType.VOCABULARY
            elif "pronunciation" in question_type_lower:
                return MistakeType.PRONUNCIATION

        # 否则根据练习类型推断
        return type_mapping.get(practice_type, MistakeType.COMPREHENSION)


# 创建服务工厂函数
def get_mistake_service(db: AsyncSession) -> MistakeService:
    """
    获取错题本服务实例

    Args:
        db: 数据库会话

    Returns:
        MistakeService: 错题本服务实例
    """
    return MistakeService(db)
