"""
练习记录服务 - AI英语教学系统
处理练习记录的业务逻辑，包括自动更新知识图谱
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Practice, PracticeStatus, PracticeType, Content, Student
from app.services.knowledge_graph_service import get_knowledge_graph_service


class PracticeService:
    """
    练习记录服务类

    核心功能：
    1. 创建练习记录
    2. 更新练习进度
    3. 完成练习并自动更新知识图谱
    4. 查询练习记录
    5. 统计练习数据

    关键特性：
    - 练习完成后自动触发规则引擎更新知识图谱
    - 零成本更新：使用规则引擎而非AI调用
    - 智能判断何时需要AI复盘
    """

    def __init__(self, db: AsyncSession):
        """
        初始化练习服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.kg_service = get_knowledge_graph_service()

    async def create_practice(
        self,
        student_id: uuid.UUID,
        practice_type: PracticeType,
        content_id: Optional[uuid.UUID] = None,
        total_questions: Optional[int] = None,
        difficulty_level: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> Practice:
        """
        创建新的练习记录

        Args:
            student_id: 学生ID
            practice_type: 练习类型
            content_id: 内容ID（可选）
            total_questions: 题目总数
            difficulty_level: 难度等级
            topic: 主题分类

        Returns:
            Practice: 创建的练习记录
        """
        practice = Practice(
            student_id=student_id,
            content_id=content_id,
            practice_type=practice_type.value,
            status=PracticeStatus.IN_PROGRESS.value,
            total_questions=total_questions,
            difficulty_level=difficulty_level,
            topic=topic,
            started_at=datetime.utcnow(),
        )

        self.db.add(practice)
        await self.db.commit()
        await self.db.refresh(practice)

        return practice

    async def update_practice_progress(
        self,
        practice_id: uuid.UUID,
        completed_questions: int,
        correct_questions: int,
        answers: Optional[Dict[str, Any]] = None,
        time_spent: Optional[int] = None,
    ) -> Practice:
        """
        更新练习进度

        Args:
            practice_id: 练习记录ID
            completed_questions: 已完成题目数
            correct_questions: 正确题目数
            answers: 答案详情
            time_spent: 累计耗时（秒）

        Returns:
            Practice: 更新后的练习记录

        Raises:
            ValueError: 练习记录不存在或已完成
        """
        # 获取练习记录
        practice = await self._get_practice(practice_id)

        if practice.status == PracticeStatus.COMPLETED.value:
            raise ValueError("练习已完成，无法更新进度")

        # 计算正确率
        correct_rate = (
            correct_questions / completed_questions
            if completed_questions > 0
            else 0
        )

        # 更新进度
        practice.completed_questions = completed_questions
        practice.correct_questions = correct_questions
        practice.correct_rate = correct_rate
        practice.time_spent = time_spent or practice.time_spent

        if answers:
            practice.answers = answers

        # 检查是否完成所有题目
        if practice.total_questions and completed_questions >= practice.total_questions:
            practice.status = PracticeStatus.COMPLETED.value
            practice.completed_at = datetime.utcnow()

            # 计算得分
            practice.score = correct_rate * 100

        await self.db.commit()
        await self.db.refresh(practice)

        return practice

    async def complete_practice(
        self,
        practice_id: uuid.UUID,
        score: Optional[float] = None,
        answers: Optional[Dict[str, Any]] = None,
        result_details: Optional[Dict[str, Any]] = None,
        time_spent: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        完成练习并自动更新知识图谱

        这是核心方法，完成练习后自动触发规则引擎更新知识图谱。

        Args:
            practice_id: 练习记录ID
            score: 最终得分（0-100）
            answers: 完整答案
            result_details: 结果详情
            time_spent: 总耗时（秒）

        Returns:
            Dict[str, Any]: 完成结果，包含：
                - practice: 练习记录
                - graph_updated: 知识图谱是否更新
                - graph_update_result: 更新结果（如果已更新）
        """
        # 获取练习记录
        practice = await self._get_practice(practice_id)

        if practice.status == PracticeStatus.COMPLETED.value:
            raise ValueError("练习已完成")

        # 更新练习状态
        practice.status = PracticeStatus.COMPLETED.value
        practice.completed_at = datetime.utcnow()

        if score is not None:
            practice.score = score

        if answers:
            practice.answers = answers

        if result_details:
            practice.result_details = result_details

        if time_spent is not None:
            practice.time_spent = time_spent

        # 计算正确率（如果没有）
        if practice.correct_rate is None and practice.completed_questions > 0:
            practice.correct_rate = (
                practice.correct_questions / practice.completed_questions
            )
            if practice.score is None:
                practice.score = practice.correct_rate * 100

        # 准备练习数据用于知识图谱更新
        practice_data = {
            "content_id": str(practice.content_id) if practice.content_id else None,
            "topic": practice.topic or practice.practice_type,
            "difficulty": practice.difficulty_level or "intermediate",
            "score": practice.score or 0,
            "correct_rate": practice.correct_rate or 0,
            "time_spent": practice.time_spent,
            "practice_type": practice.practice_type,
        }

        # 尝试更新知识图谱
        graph_updated = False
        graph_update_result = None

        try:
            # 使用规则引擎更新知识图谱
            graph_update_result = await self.kg_service.update_from_practice(
                db=self.db,
                student_id=practice.student_id,
                practice_record=practice_data,
            )

            # 标记知识图谱已更新
            practice.graph_updated = True
            practice.graph_update = {
                "updated_at": datetime.utcnow().isoformat(),
                "abilities": graph_update_result.get("updated_abilities", {}),
                "changes": graph_update_result.get("changes", {}),
                "need_ai_review": graph_update_result.get("need_ai_review", False),
            }

            graph_updated = True

        except Exception as e:
            # 知识图谱更新失败，记录但不影响练习完成
            practice.graph_update = {
                "updated_at": datetime.utcnow().isoformat(),
                "error": str(e),
            }

        await self.db.commit()
        await self.db.refresh(practice)

        return {
            "practice": practice,
            "graph_updated": graph_updated,
            "graph_update_result": graph_update_result,
        }

    async def get_practice(
        self,
        practice_id: uuid.UUID,
    ) -> Practice:
        """
        获取练习记录详情

        Args:
            practice_id: 练习记录ID

        Returns:
            Practice: 练习记录

        Raises:
            ValueError: 练习记录不存在
        """
        return await self._get_practice(practice_id)

    async def list_student_practices(
        self,
        student_id: uuid.UUID,
        practice_type: Optional[PracticeType] = None,
        status: Optional[PracticeStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[Practice], int]:
        """
        获取学生的练习记录列表

        Args:
            student_id: 学生ID
            practice_type: 练习类型筛选
            status: 状态筛选
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            tuple[List[Practice], int]: (练习记录列表, 总数)
        """
        query = select(Practice).where(Practice.student_id == student_id)

        if practice_type:
            query = query.where(Practice.practice_type == practice_type.value)

        if status:
            query = query.where(Practice.status == status.value)

        # 按创建时间倒序
        query = query.order_by(Practice.created_at.desc())

        # 获取总数
        count_query = select(Practice.id).where(Practice.student_id == student_id)
        if practice_type:
            count_query = count_query.where(Practice.practice_type == practice_type.value)
        if status:
            count_query = count_query.where(Practice.status == status.value)

        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # 分页
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        practices = result.scalars().all()

        return list(practices), total

    async def get_student_practice_stats(
        self,
        student_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取学生练习统计数据

        Args:
            student_id: 学生ID

        Returns:
            Dict[str, Any]: 统计数据，包含：
                - total_practices: 总练习数
                - completed_practices: 完成的练习数
                - average_score: 平均得分
                - total_time_spent: 总耗时
                - by_type: 按类型统计
                - by_difficulty: 按难度统计
                - recent_activity: 近期活动
        """
        # 获取所有练习
        query = select(Practice).where(Practice.student_id == student_id)
        result = await self.db.execute(query)
        all_practices = result.scalars().all()

        # 基础统计
        total_practices = len(all_practices)
        completed_practices = [
            p for p in all_practices
            if p.status == PracticeStatus.COMPLETED.value
        ]

        # 平均得分
        scores = [
            p.score for p in completed_practices
            if p.score is not None
        ]
        average_score = sum(scores) / len(scores) if scores else 0

        # 总耗时
        total_time_spent = sum(p.time_spent for p in all_practices)

        # 按类型统计
        by_type: Dict[str, Dict[str, Any]] = {}
        for practice in all_practices:
            ptype = practice.practice_type
            if ptype not in by_type:
                by_type[ptype] = {
                    "total": 0,
                    "completed": 0,
                    "average_score": 0,
                }
            by_type[ptype]["total"] += 1
            if practice.status == PracticeStatus.COMPLETED.value:
                by_type[ptype]["completed"] += 1

        # 计算各类型平均分
        for ptype, stats in by_type.items():
            type_scores = [
                p.score for p in all_practices
                if p.practice_type == ptype and p.score is not None
            ]
            if type_scores:
                stats["average_score"] = sum(type_scores) / len(type_scores)

        # 按难度统计
        by_difficulty: Dict[str, int] = {}
        for practice in all_practices:
            if practice.difficulty_level:
                difficulty = practice.difficulty_level
                by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1

        # 近期活动（最近7天）
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = [
            p for p in all_practices
            if p.created_at >= week_ago
        ]

        return {
            "student_id": str(student_id),
            "total_practices": total_practices,
            "completed_practices": len(completed_practices),
            "average_score": round(average_score, 2),
            "total_time_spent": total_time_spent,
            "by_type": by_type,
            "by_difficulty": by_difficulty,
            "recent_activity_count": len(recent_activity),
        }

    async def _get_practice(self, practice_id: uuid.UUID) -> Practice:
        """获取练习记录（内部方法）"""
        query = select(Practice).where(Practice.id == practice_id)
        result = await self.db.execute(query)
        practice = result.scalar_one_or_none()

        if not practice:
            raise ValueError(f"练习记录不存在: {practice_id}")

        return practice


# 创建服务工厂函数
def get_practice_service(db: AsyncSession) -> PracticeService:
    """
    获取练习服务实例

    Args:
        db: 数据库会话

    Returns:
        PracticeService: 练习服务实例
    """
    return PracticeService(db)
