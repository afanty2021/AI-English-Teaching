"""
练习会话服务 - AI英语教学系统
处理学生练习会话的业务逻辑，支持断点续答
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Student, User, Question, QuestionBank, Practice, PracticeType
from app.models.question import QuestionType
from app.models.practice_session import PracticeSession, SessionStatus
from app.services.practice_service import get_practice_service
from app.services.question_service import get_question_service


class PracticeSessionService:
    """
    练习会话服务类

    核心功能：
    1. 开始练习会话
    2. 获取会话详情
    3. 提交单题答案（保存进度）
    4. 获取当前题目
    5. 下一题/上一题
    6. 暂停/恢复会话
    7. 完成会话
    8. 计算练习结果
    9. 获取会话统计

    关键特性：
    - 实时保存答案，支持断点续答
    - 完成后自动生成Practice记录
    - 自动触发知识图谱更新（零成本）
    """

    def __init__(self, db: AsyncSession):
        """
        初始化练习会话服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.practice_service = get_practice_service(db)
        self.question_service = get_question_service(db)

    async def start_practice_session(
        self,
        student_id: uuid.UUID,
        practice_type: str,
        question_bank_id: Optional[uuid.UUID] = None,
        question_ids: Optional[List[uuid.UUID]] = None,
        random_count: Optional[int] = None,
        difficulty_level: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> PracticeSession:
        """
        开始练习会话

        Args:
            student_id: 学生ID
            practice_type: 练习类型
            question_bank_id: 题库ID（可选）
            question_ids: 指定题目ID列表（可选）
            random_count: 随机抽取题目数量（可选）
            difficulty_level: 难度等级筛选（可选）
            topic: 主题筛选（可选）

        Returns:
            PracticeSession: 创建的练习会话

        Raises:
            ValueError: 学生不存在或无题目可用
        """
        # 验证学生存在
        student = await self.db.get(Student, student_id)
        if not student:
            raise ValueError("学生不存在")

        # 获取题目列表
        if question_ids:
            # 使用指定的题目ID列表
            questions = await self._get_questions_by_ids(question_ids)
        elif question_bank_id:
            # 从题库获取题目
            questions = await self._get_questions_from_bank(
                question_bank_id, random_count, difficulty_level, topic
            )
        elif random_count:
            # 随机抽取题目
            questions = await self._get_random_questions(
                practice_type, random_count, difficulty_level, topic
            )
        else:
            raise ValueError("必须指定题目来源（题库、题目列表或随机抽取）")

        if not questions:
            raise ValueError("没有可用的题目")

        # 提取题目ID列表
        final_question_ids = [str(q.id) for q in questions]

        # 创建会话
        session = PracticeSession(
            student_id=student_id,
            question_bank_id=question_bank_id,
            practice_type=practice_type,
            status=SessionStatus.IN_PROGRESS.value,
            current_question_index=0,
            total_questions=len(final_question_ids),
            answered_questions=0,
            correct_questions=0,
            answers={},
            question_ids=final_question_ids,
            started_at=datetime.utcnow(),
        )

        # 设置当前题目
        if final_question_ids:
            session.current_question_id = uuid.UUID(final_question_ids[0])

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def get_session(
        self,
        session_id: uuid.UUID,
    ) -> PracticeSession:
        """
        获取会话详情

        Args:
            session_id: 会话ID

        Returns:
            PracticeSession: 会话详情

        Raises:
            ValueError: 会话不存在
        """
        return await self._get_session(session_id)

    async def submit_answer(
        self,
        session_id: uuid.UUID,
        question_id: uuid.UUID,
        answer: Any,
        user_id: uuid.UUID,
    ) -> PracticeSession:
        """
        提交单题答案（保存进度）

        Args:
            session_id: 会话ID
            question_id: 题目ID
            answer: 学生答案
            user_id: 学生ID

        Returns:
            PracticeSession: 更新后的会话

        Raises:
            ValueError: 会话不存在或权限不足
        """
        # 获取会话
        session = await self._get_session(session_id)

        # 权限检查
        if session.student_id != user_id:
            raise ValueError("无权操作此会话")

        # 检查会话状态
        if session.status == SessionStatus.COMPLETED.value:
            raise ValueError("会话已完成，无法提交答案")

        # 恢复暂停的会话
        if session.status == SessionStatus.PAUSED.value:
            session.status = SessionStatus.IN_PROGRESS.value

        # 获取题目以验证答案
        question = await self.question_service.get_question(question_id)

        # 判断答案是否正确
        is_correct = self._check_answer(question, answer)

        # 保存答案
        question_id_str = str(question_id)
        session.answers[question_id_str] = {
            "answer": answer,
            "is_correct": is_correct,
            "answered_at": datetime.utcnow().isoformat(),
        }

        # 更新统计
        if question_id_str not in session.answers or \
           "is_correct" not in session.answers[question_id_str]:
            # 新答题或之前没有正确性标记，更新计数
            pass

        # 重新计算已答题数和正确数
        answered_count = len(session.answers)
        correct_count = sum(
            1 for a in session.answers.values()
            if a.get("is_correct", False)
        )

        session.answered_questions = answered_count
        session.correct_questions = correct_count
        session.last_active_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def get_current_question(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取当前题目

        Args:
            session_id: 会话ID
            user_id: 学生ID

        Returns:
            Dict[str, Any]: 当前题目信息

        Raises:
            ValueError: 会话不存在或权限不足
        """
        # 获取会话
        session = await self._get_session(session_id)

        # 权限检查
        if session.student_id != user_id:
            raise ValueError("无权访问此会话")

        # 获取当前题目ID
        if not session.question_ids or session.current_question_index >= len(session.question_ids):
            raise ValueError("没有更多题目")

        current_question_id = uuid.UUID(session.question_ids[session.current_question_index])

        # 获取题目
        question = await self.question_service.get_question(current_question_id)

        # 获取之前的答案（如果有）
        previous_answer = session.answers.get(str(current_question_id))

        return {
            "question": question,
            "question_number": session.current_question_number,
            "total_questions": session.total_questions,
            "previous_answer": previous_answer,
            "is_last_question": session.is_last_question,
            "is_first_question": session.is_first_question,
        }

    async def next_question(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        下一题

        Args:
            session_id: 会话ID
            user_id: 学生ID

        Returns:
            Dict[str, Any]: 下一题信息

        Raises:
            ValueError: 会话不存在、权限不足或没有下一题
        """
        # 获取会话
        session = await self._get_session(session_id)

        # 权限检查
        if session.student_id != user_id:
            raise ValueError("无权操作此会话")

        # 检查是否有下一题
        if not session.has_next_question:
            raise ValueError("没有下一题")

        # 移动到下一题
        session.current_question_index += 1
        next_question_id = uuid.UUID(session.question_ids[session.current_question_index])
        session.current_question_id = next_question_id
        session.last_active_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        # 获取题目
        question = await self.question_service.get_question(next_question_id)
        previous_answer = session.answers.get(str(next_question_id))

        return {
            "question": question,
            "question_number": session.current_question_number,
            "total_questions": session.total_questions,
            "previous_answer": previous_answer,
            "is_last_question": session.is_last_question,
            "is_first_question": session.is_first_question,
        }

    async def previous_question(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        上一题

        Args:
            session_id: 会话ID
            user_id: 学生ID

        Returns:
            Dict[str, Any]: 上一题信息

        Raises:
            ValueError: 会话不存在、权限不足或没有上一题
        """
        # 获取会话
        session = await self._get_session(session_id)

        # 权限检查
        if session.student_id != user_id:
            raise ValueError("无权操作此会话")

        # 检查是否有上一题
        if not session.has_previous_question:
            raise ValueError("没有上一题")

        # 移动到上一题
        session.current_question_index -= 1
        prev_question_id = uuid.UUID(session.question_ids[session.current_question_index])
        session.current_question_id = prev_question_id
        session.last_active_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        # 获取题目
        question = await self.question_service.get_question(prev_question_id)
        previous_answer = session.answers.get(str(prev_question_id))

        return {
            "question": question,
            "question_number": session.current_question_number,
            "total_questions": session.total_questions,
            "previous_answer": previous_answer,
            "is_last_question": session.is_last_question,
            "is_first_question": session.is_first_question,
        }

    async def pause_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> PracticeSession:
        """
        暂停会话

        Args:
            session_id: 会话ID
            user_id: 学生ID

        Returns:
            PracticeSession: 更新后的会话

        Raises:
            ValueError: 会话不存在或权限不足
        """
        # 获取会话
        session = await self._get_session(session_id)

        # 权限检查
        if session.student_id != user_id:
            raise ValueError("无权操作此会话")

        # 检查状态
        if session.status != SessionStatus.IN_PROGRESS.value:
            raise ValueError(f"无法暂停状态为 {session.status} 的会话")

        # 暂停会话
        session.status = SessionStatus.PAUSED.value
        session.paused_at = datetime.utcnow()
        session.last_active_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def resume_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> PracticeSession:
        """
        恢复暂停的会话

        Args:
            session_id: 会话ID
            user_id: 学生ID

        Returns:
            PracticeSession: 更新后的会话

        Raises:
            ValueError: 会话不存在或权限不足
        """
        # 获取会话
        session = await self._get_session(session_id)

        # 权限检查
        if session.student_id != user_id:
            raise ValueError("无权操作此会话")

        # 检查状态
        if session.status != SessionStatus.PAUSED.value:
            raise ValueError(f"无法恢复状态为 {session.status} 的会话")

        # 恢复会话
        session.status = SessionStatus.IN_PROGRESS.value
        session.last_active_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def complete_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        完成练习会话

        Args:
            session_id: 会话ID
            user_id: 学生ID

        Returns:
            Dict[str, Any]: 完成结果，包含：
                - session: 会话
                - practice_record: 创建的Practice记录
                - result: 练习结果统计

        Raises:
            ValueError: 会话不存在或权限不足
        """
        # 获取会话
        session = await self._get_session(session_id)

        # 权限检查
        if session.student_id != user_id:
            raise ValueError("无权操作此会话")

        # 检查状态
        if session.status == SessionStatus.COMPLETED.value:
            raise ValueError("会话已完成")

        # 计算最终得分和正确率
        score, correct_rate = await self._calculate_final_score(session)

        # 更新会话状态
        session.status = SessionStatus.COMPLETED.value
        session.completed_at = datetime.utcnow()
        session.score = score
        session.correct_rate = correct_rate

        await self.db.commit()
        await self.db.refresh(session)

        # 创建Practice记录
        practice_record = await self._create_practice_record(session)

        # 更新会话的practice_record引用
        session.practice_record_id = practice_record.id
        session.practice_record_created = True

        await self.db.commit()
        await self.db.refresh(session)

        # 生成结果统计
        result = await self._calculate_session_result(session)

        return {
            "session": session,
            "practice_record": practice_record,
            "result": result,
        }

    async def get_session_result(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        获取会话结果

        Args:
            session_id: 会话ID
            user_id: 学生ID

        Returns:
            Dict[str, Any]: 会话结果统计

        Raises:
            ValueError: 会话不存在或权限不足
        """
        # 获取会话
        session = await self._get_session(session_id)

        # 权限检查
        if session.student_id != user_id:
            raise ValueError("无权访问此会话")

        return await self._calculate_session_result(session)

    async def list_student_sessions(
        self,
        student_id: uuid.UUID,
        status: Optional[SessionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[PracticeSession], int]:
        """
        获取学生的会话列表

        Args:
            student_id: 学生ID
            status: 状态筛选
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            tuple[List[PracticeSession], int]: (会话列表, 总数)
        """
        query = select(PracticeSession).where(PracticeSession.student_id == student_id)

        if status:
            query = query.where(PracticeSession.status == status.value)

        # 按创建时间倒序
        query = query.order_by(PracticeSession.created_at.desc())

        # 获取总数
        count_query = select(func.count(PracticeSession.id)).where(
            PracticeSession.student_id == student_id
        )
        if status:
            count_query = count_query.where(PracticeSession.status == status.value)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        # 分页
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return list(sessions), total

    async def _get_session(self, session_id: uuid.UUID) -> PracticeSession:
        """获取会话（内部方法）"""
        query = select(PracticeSession).where(PracticeSession.id == session_id)
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"会话不存在: {session_id}")

        return session

    async def _get_questions_by_ids(self, question_ids: List[uuid.UUID]) -> List[Question]:
        """根据ID列表获取题目"""
        query = select(Question).where(
            Question.id.in_(question_ids),
            Question.is_active == True
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_questions_from_bank(
        self,
        question_bank_id: uuid.UUID,
        count: Optional[int] = None,
        difficulty_level: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[Question]:
        """从题库获取题目"""
        query = select(Question).where(
            Question.question_bank_id == question_bank_id,
            Question.is_active == True
        )

        if difficulty_level:
            query = query.where(Question.difficulty_level == difficulty_level)

        if topic:
            query = query.where(Question.topic == topic)

        query = query.order_by(Question.order_index)

        if count:
            query = query.limit(count)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _get_random_questions(
        self,
        practice_type: str,
        count: int,
        difficulty_level: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[Question]:
        """随机抽取题目"""
        # 构建查询
        query = select(Question).where(
            Question.is_active == True
        )

        # 根据练习类型推断题目类型
        type_mapping = {
            "reading": [QuestionType.READING_COMPREHENSION.value, QuestionType.CHOICE.value],
            "listening": [QuestionType.LISTENING.value],
            "grammar": [QuestionType.CHOICE.value, QuestionType.FILL_BLANK.value],
            "vocabulary": [QuestionType.CHOICE.value, QuestionType.FILL_BLANK.value],
            "writing": [QuestionType.WRITING.value],
            "speaking": [QuestionType.SPEAKING.value],
        }

        valid_types = type_mapping.get(practice_type, [])
        if valid_types:
            query = query.where(Question.question_type.in_(valid_types))

        if difficulty_level:
            query = query.where(Question.difficulty_level == difficulty_level)

        if topic:
            query = query.where(Question.topic == topic)

        # 随机排序并限制数量
        query = query.order_by(func.random()).limit(count)

        result = await self.db.execute(query)
        questions = list(result.scalars().all())

        # 如果题目不足，返回所有找到的题目
        return questions

    def _check_answer(self, question: Question, answer: Any) -> bool:
        """
        检查答案是否正确

        Args:
            question: 题目
            answer: 学生答案

        Returns:
            bool: 是否正确
        """
        if not question.correct_answer:
            return False

        if question.is_choice_question:
            # 选择题
            if isinstance(question.correct_answer, list):
                # 多选
                return sorted(answer) == sorted(question.correct_answer)
            else:
                # 单选
                return answer == question.correct_answer

        elif question.is_fill_blank_question:
            # 填空题
            correct = question.correct_answer
            if isinstance(correct, list):
                # 多个空
                return isinstance(answer, list) and len(answer) == len(correct) and \
                       all(a.strip().lower() == c.strip().lower() for a, c in zip(answer, correct))
            else:
                # 单个空
                return str(answer).strip().lower() == str(correct).strip().lower()

        elif question.is_reading_comprehension:
            # 阅读理解（可能有多个小题）
            if isinstance(question.correct_answer, dict):
                if isinstance(answer, dict):
                    return all(
                        str(answer.get(k, "")).strip().lower() == str(v).strip().lower()
                        for k, v in question.correct_answer.items()
                    )

        # 默认情况
        return str(answer).strip().lower() == str(question.correct_answer).strip().lower()

    async def _calculate_final_score(self, session: PracticeSession) -> tuple[float, float]:
        """
        计算最终得分和正确率

        Returns:
            tuple[float, float]: (得分, 正确率)
        """
        total = session.total_questions
        if total == 0:
            return 0.0, 0.0

        correct = session.correct_questions
        correct_rate = correct / total
        score = correct_rate * 100

        return score, correct_rate

    async def _create_practice_record(self, session: PracticeSession) -> Practice:
        """
        创建Practice记录

        Args:
            session: 练习会话

        Returns:
            Practice: 创建的练习记录
        """
        # 获取会话中的所有题目
        questions = await self._get_questions_by_ids(
            [uuid.UUID(qid) for qid in session.question_ids]
        )

        # 计算得分和正确率
        score, correct_rate = await self._calculate_final_score(session)

        # 使用practice_service创建记录
        practice = await self.practice_service.create_practice(
            student_id=session.student_id,
            practice_type=PracticeType(session.practice_type),
            content_id=None,  # 会话练习不关联单一内容
            total_questions=session.total_questions,
            difficulty_level=None,  # 会话可能包含多种难度
            topic=session.practice_type,
        )

        # 更新为完成状态
        practice.status = "completed"  # 使用字符串而不是枚举值
        practice.completed_at = session.completed_at or datetime.utcnow()
        practice.score = score
        practice.correct_rate = correct_rate
        practice.correct_questions = session.correct_questions
        practice.time_spent = session.time_spent
        practice.answers = session.answers

        # 尝试更新知识图谱（会话练习使用整体主题）
        try:
            practice_data = {
                "content_id": None,
                "topic": session.practice_type,
                "difficulty": "intermediate",  # 会话练习默认中等难度
                "score": score,
                "correct_rate": correct_rate,
                "time_spent": session.time_spent,
                "practice_type": session.practice_type,
            }

            # 这将自动更新知识图谱（零成本）
            result = await self.practice_service.complete_practice(
                practice_id=practice.id,
                score=score,
                answers=session.answers,
                result_details={"session_id": str(session.id)},
                time_spent=session.time_spent,
            )

            # 更新会话的知识图谱更新记录
            session.graph_update = result.get("graph_update_result", {})

        except Exception as e:
            # 知识图谱更新失败，记录但不影响
            session.graph_update = {"error": str(e)}

        await self.db.commit()
        await self.db.refresh(practice)

        return practice

    async def _calculate_session_result(self, session: PracticeSession) -> Dict[str, Any]:
        """
        计算会话结果统计

        Args:
            session: 练习会话

        Returns:
            Dict[str, Any]: 结果统计
        """
        # 获取所有题目
        questions = await self._get_questions_by_ids(
            [uuid.UUID(qid) for qid in session.question_ids]
        )

        # 按题目分类统计
        by_type = {}
        by_difficulty = {}
        by_topic = {}

        for question in questions:
            qid_str = str(question.id)
            answer_info = session.answers.get(qid_str, {})
            is_correct = answer_info.get("is_correct", False)

            # 按类型统计
            qtype = question.question_type
            if qtype not in by_type:
                by_type[qtype] = {"total": 0, "correct": 0}
            by_type[qtype]["total"] += 1
            if is_correct:
                by_type[qtype]["correct"] += 1

            # 按难度统计
            if question.difficulty_level:
                diff = question.difficulty_level
                if diff not in by_difficulty:
                    by_difficulty[diff] = {"total": 0, "correct": 0}
                by_difficulty[diff]["total"] += 1
                if is_correct:
                    by_difficulty[diff]["correct"] += 1

            # 按主题统计
            if question.topic:
                top = question.topic
                if top not in by_topic:
                    by_topic[top] = {"total": 0, "correct": 0}
                by_topic[top]["total"] += 1
                if is_correct:
                    by_topic[top]["correct"] += 1

        # 错题列表
        wrong_questions = []
        for question in questions:
            qid_str = str(question.id)
            answer_info = session.answers.get(qid_str, {})
            if not answer_info.get("is_correct", False):
                wrong_questions.append({
                    "question_id": qid_str,
                    "question": question,
                    "user_answer": answer_info.get("answer"),
                    "correct_answer": question.correct_answer,
                    "explanation": question.explanation,
                })

        return {
            "session_id": str(session.id),
            "total_questions": session.total_questions,
            "answered_questions": session.answered_questions,
            "correct_questions": session.correct_questions,
            "incorrect_questions": session.total_questions - session.correct_questions,
            "score": session.score or 0,
            "correct_rate": session.correct_rate or 0,
            "time_spent": session.time_spent,
            "duration_seconds": session.duration_seconds,
            "by_type": by_type,
            "by_difficulty": by_difficulty,
            "by_topic": by_topic,
            "wrong_questions": wrong_questions,
            "wrong_question_count": len(wrong_questions),
        }


# 创建服务工厂函数
def get_practice_session_service(db: AsyncSession) -> PracticeSessionService:
    """
    获取练习会话服务实例

    Args:
        db: 数据库会话

    Returns:
        PracticeSessionService: 练习会话服务实例
    """
    return PracticeSessionService(db)
