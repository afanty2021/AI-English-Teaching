"""
练习会话模型测试 - AI英语教学系统
测试 PracticeSession 模型
"""
import pytest
from datetime import datetime, timedelta
import uuid

from app.models.practice_session import (
    PracticeSession,
    SessionStatus,
)


class TestSessionStatus:
    """测试会话状态枚举"""

    def test_session_status_values(self):
        """测试会话状态枚举值"""
        assert SessionStatus.IN_PROGRESS.value == "in_progress"
        assert SessionStatus.PAUSED.value == "paused"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.ABANDONED.value == "abandoned"


class TestPracticeSession:
    """测试PracticeSession模型"""

    @pytest.fixture
    def session_data(self):
        """会话数据"""
        return {
            "student_id": uuid.uuid4(),
            "practice_type": "reading",
            "status": SessionStatus.IN_PROGRESS.value,
            "current_question_index": 0,
            "total_questions": 10,
            "answered_questions": 0,
            "correct_questions": 0,
            "answers": {},
            "question_ids": [str(uuid.uuid4()) for _ in range(10)],
        }

    def test_create_session(self, session_data):
        """测试创建会话"""
        session = PracticeSession(**session_data)

        assert session.status == SessionStatus.IN_PROGRESS.value
        assert session.current_question_index == 0
        assert session.total_questions == 10
        assert session.answered_questions == 0
        assert session.correct_questions == 0

    def test_is_active_property(self, session_data):
        """测试是否活跃"""
        session = PracticeSession(**session_data)

        # 进行中
        assert session.is_active is True

        # 暂停
        session.status = SessionStatus.PAUSED.value
        assert session.is_active is True

        # 完成
        session.status = SessionStatus.COMPLETED.value
        assert session.is_active is False

    def test_is_completed_property(self, session_data):
        """测试是否已完成"""
        session = PracticeSession(**session_data)

        assert session.is_completed is False

        session.status = SessionStatus.COMPLETED.value
        assert session.is_completed is True

    def test_is_paused_property(self, session_data):
        """测试是否已暂停"""
        session = PracticeSession(**session_data)

        assert session.is_paused is False

        session.status = SessionStatus.PAUSED.value
        session.paused_at = datetime.utcnow()
        assert session.is_paused is True

    def test_progress_percentage(self, session_data):
        """测试进度百分比"""
        session = PracticeSession(**session_data)

        # 初始进度
        assert session.progress_percentage == 0.0

        # 回答5题
        session.answered_questions = 5
        assert session.progress_percentage == 50.0

        # 全部回答
        session.answered_questions = 10
        assert session.progress_percentage == 100.0

    def test_current_correct_rate(self, session_data):
        """测试当前正确率"""
        session = PracticeSession(**session_data)

        # 初始正确率
        assert session.current_correct_rate == 0.0

        # 回答5题，4题正确
        session.answered_questions = 5
        session.correct_questions = 4
        assert session.current_correct_rate == 0.8

    def test_remaining_questions(self, session_data):
        """测试剩余题目数"""
        session = PracticeSession(**session_data)

        assert session.remaining_questions == 10

        session.answered_questions = 3
        assert session.remaining_questions == 7

    def test_can_resume(self, session_data):
        """测试是否可以恢复"""
        session = PracticeSession(**session_data)

        # 初始状态不能恢复
        assert session.can_resume is False

        # 暂停后可以恢复
        session.status = SessionStatus.PAUSED.value
        session.paused_at = datetime.utcnow()
        assert session.can_resume is True

    def test_duration_seconds(self, session_data):
        """测试练习时长"""
        session = PracticeSession(**session_data)

        # 未完成，返回None
        assert session.duration_seconds is None

        # 完成后返回实际时长
        session.started_at = datetime.utcnow() - timedelta(minutes=5)
        session.completed_at = datetime.utcnow()
        duration = session.duration_seconds
        assert duration is not None
        assert 295 <= duration <= 305  # 约5分钟

    def test_is_first_question(self, session_data):
        """测试是否第一题"""
        session = PracticeSession(**session_data)

        assert session.is_first_question is True

        session.current_question_index = 1
        assert session.is_first_question is False

    def test_is_last_question(self, session_data):
        """测试是否最后一题"""
        session = PracticeSession(**session_data)

        session.current_question_index = 0
        assert session.is_last_question is False

        session.current_question_index = 9  # 最后一题
        assert session.is_last_question is True

    def test_current_question_number(self, session_data):
        """测试当前题号"""
        session = PracticeSession(**session_data)

        session.current_question_index = 0
        assert session.current_question_number == 1

        session.current_question_index = 5
        assert session.current_question_number == 6

    def test_has_next_question(self, session_data):
        """测试是否有下一题"""
        session = PracticeSession(**session_data)

        session.current_question_index = 0
        assert session.has_next_question is True

        session.current_question_index = 9
        assert session.has_next_question is False

    def test_has_previous_question(self, session_data):
        """测试是否有上一题"""
        session = PracticeSession(**session_data)

        session.current_question_index = 0
        assert session.has_previous_question is False

        session.current_question_index = 1
        assert session.has_previous_question is True

    def test_get_answer(self, session_data):
        """测试获取答题记录"""
        session = PracticeSession(**session_data)

        question_id = uuid.UUID(session.question_ids[0])
        session.answers[str(question_id)] = {
            "answer": "A",
            "is_correct": True,
            "answered_at": datetime.utcnow().isoformat(),
        }

        answer = session.get_answer(question_id)
        assert answer is not None
        assert answer["answer"] == "A"
        assert answer["is_correct"] is True

    def test_is_question_answered(self, session_data):
        """测试题目是否已作答"""
        session = PracticeSession(**session_data)

        question_id = uuid.UUID(session.question_ids[0])

        # 未作答
        assert session.is_question_answered(question_id) is False

        # 作答后
        session.answers[str(question_id)] = {"answer": "A"}
        assert session.is_question_answered(question_id) is True

    def test_get_question_id_at(self, session_data):
        """测试获取指定索引的题目ID"""
        session = PracticeSession(**session_data)

        # 有效索引
        qid = session.get_question_id_at(0)
        assert qid == uuid.UUID(session.question_ids[0])

        # 无效索引
        qid = session.get_question_id_at(100)
        assert qid is None

    def test_get_unanswered_question_ids(self, session_data):
        """测试获取未作答题目ID"""
        session = PracticeSession(**session_data)

        # 回答前3题
        for i in range(3):
            question_id = uuid.UUID(session.question_ids[i])
            session.answers[str(question_id)] = {"answer": "A"}

        unanswered = session.get_unanswered_question_ids()
        assert len(unanswered) == 7

    def test_get_answered_question_ids(self, session_data):
        """测试获取已作答题目ID"""
        session = PracticeSession(**session_data)

        # 回答前3题
        for i in range(3):
            question_id = uuid.UUID(session.question_ids[i])
            session.answers[str(question_id)] = {"answer": "A"}

        answered = session.get_answered_question_ids()
        assert len(answered) == 3

    def test_calculate_current_score(self, session_data):
        """测试计算当前得分"""
        session = PracticeSession(**session_data)

        # 5题4正确
        session.answered_questions = 5
        session.correct_questions = 4
        score = session.calculate_current_score()
        assert score == 80.0

    def test_session_repr(self):
        """测试会话字符串表示"""
        data = {
            "student_id": uuid.uuid4(),
            "practice_type": "reading",
            "status": SessionStatus.IN_PROGRESS.value,
            "current_question_index": 0,
            "total_questions": 10,
            "answered_questions": 0,
            "correct_questions": 0,
            "answers": {},
            "question_ids": [str(uuid.uuid4()) for _ in range(10)],
        }
        session = PracticeSession(**data)
        repr_str = repr(session)
        assert "PracticeSession" in repr_str
        assert "reading" in repr_str
        assert "in_progress" in repr_str
        assert "0/10" in repr_str


class TestPracticeSessionLifecycle:
    """测试练习会话生命周期"""

    def test_complete_lifecycle(self):
        """测试完整的会话生命周期"""
        question_ids = [str(uuid.uuid4()) for _ in range(3)]

        # 创建会话
        session = PracticeSession(
            student_id=uuid.uuid4(),
            practice_type="reading",
            status=SessionStatus.IN_PROGRESS.value,
            current_question_index=0,
            total_questions=3,
            answered_questions=0,
            correct_questions=0,
            answers={},
            question_ids=question_ids,
        )

        # 初始状态
        assert session.status == SessionStatus.IN_PROGRESS.value
        assert session.progress_percentage == 0.0

        # 回答第1题
        session.answers[question_ids[0]] = {"answer": "A", "is_correct": True}
        session.answered_questions = 1
        session.correct_questions = 1
        session.current_question_index = 1

        assert session.progress_percentage == pytest.approx(33.33, rel=0.1)

        # 暂停会话
        session.status = SessionStatus.PAUSED.value
        session.paused_at = datetime.utcnow()
        assert session.is_paused is True

        # 恢复会话
        session.status = SessionStatus.IN_PROGRESS.value
        assert session.is_active is True

        # 完成会话
        for i in range(1, 3):
            session.answers[question_ids[i]] = {"answer": "A"}
        session.answered_questions = 3
        session.correct_questions = 2
        session.current_question_index = 3
        session.status = SessionStatus.COMPLETED.value
        session.completed_at = datetime.utcnow()

        assert session.is_completed is True
        assert session.progress_percentage == 100.0
        assert session.current_correct_rate == pytest.approx(0.667, rel=0.1)

    def test_abandoned_session(self):
        """测试放弃会话"""
        session = PracticeSession(
            student_id=uuid.uuid4(),
            practice_type="reading",
            status=SessionStatus.IN_PROGRESS.value,
            current_question_index=0,
            total_questions=5,
            answered_questions=0,
            correct_questions=0,
            answers={},
            question_ids=[str(uuid.uuid4()) for _ in range(5)],
        )

        # 放弃会话
        session.status = SessionStatus.ABANDONED.value
        assert session.is_active is False
        assert session.is_completed is False
