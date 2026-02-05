"""
题目模型测试 - AI英语教学系统
测试 Question 和 QuestionBank 模型
"""
import pytest
import uuid

from app.models.question import (
    Question,
    QuestionBank,
    QuestionType,
    CEFRLevel,
)


class TestQuestionType:
    """测试题目类型枚举"""

    def test_question_type_values(self):
        """测试题目类型枚举值"""
        assert QuestionType.CHOICE.value == "choice"
        assert QuestionType.FILL_BLANK.value == "fill_blank"
        assert QuestionType.READING_COMPREHENSION.value == "reading_comprehension"
        assert QuestionType.WRITING.value == "writing"
        assert QuestionType.SPEAKING.value == "speaking"
        assert QuestionType.LISTENING.value == "listening"
        assert QuestionType.TRANSLATION.value == "translation"


class TestCEFRLevel:
    """测试CEFR难度等级枚举"""

    def test_cefr_level_values(self):
        """测试CEFR难度等级枚举值"""
        assert CEFRLevel.A1.value == "A1"
        assert CEFRLevel.A2.value == "A2"
        assert CEFRLevel.B1.value == "B1"
        assert CEFRLevel.B2.value == "B2"
        assert CEFRLevel.C1.value == "C1"
        assert CEFRLevel.C2.value == "C2"


class TestQuestion:
    """测试Question模型"""

    @pytest.fixture
    def question_data(self):
        """题目数据"""
        return {
            "question_type": QuestionType.CHOICE.value,
            "content_text": "What is the capital of France?",
            "difficulty_level": CEFRLevel.A2.value,
            "topic": "geography",
            "knowledge_points": ["capital", "geography"],
            "options": [
                {"id": "A", "text": "London"},
                {"id": "B", "text": "Paris"},
                {"id": "C", "text": "Berlin"},
            ],
            "correct_answer": "B",
            "explanation": "Paris is the capital of France.",
            "created_by": uuid.uuid4(),
        }

    def test_create_choice_question(self, question_data):
        """测试创建选择题"""
        question = Question(**question_data)

        assert question.question_type == QuestionType.CHOICE.value
        assert question.content_text == "What is the capital of France?"
        assert question.difficulty_level == CEFRLevel.A2.value
        assert question.topic == "geography"
        assert len(question.options) == 3
        assert question.correct_answer == "B"

    def test_create_fill_blank_question(self):
        """测试创建填空题"""
        data = {
            "question_type": QuestionType.FILL_BLANK.value,
            "content_text": "The capital of France is ___.",
            "difficulty_level": CEFRLevel.A1.value,
            "topic": "geography",
            "correct_answer": "Paris",
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)

        assert question.question_type == QuestionType.FILL_BLANK.value
        assert question.correct_answer == "Paris"

    def test_create_reading_comprehension(self):
        """测试创建阅读理解题"""
        data = {
            "question_type": QuestionType.READING_COMPREHENSION.value,
            "content_text": "What is the main idea of the passage?",
            "passage_content": "Paris is the capital of France...",
            "difficulty_level": CEFRLevel.B1.value,
            "topic": "reading",
            "correct_answer": {"1": "A", "2": "B"},
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)

        assert question.question_type == QuestionType.READING_COMPREHENSION.value
        assert question.passage_content == "Paris is the capital of France..."

    def test_is_choice_question_property(self, question_data):
        """测试选择题属性"""
        question = Question(**question_data)
        assert question.is_choice_question is True
        assert question.is_fill_blank_question is False
        assert question.is_reading_comprehension is False

    def test_is_fill_blank_question_property(self):
        """测试填空题属性"""
        data = {
            "question_type": QuestionType.FILL_BLANK.value,
            "content_text": "Fill in the blank.",
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)
        assert question.is_fill_blank_question is True
        assert question.is_choice_question is False

    def test_is_reading_comprehension_property(self):
        """测试阅读理解属性"""
        data = {
            "question_type": QuestionType.READING_COMPREHENSION.value,
            "content_text": "What is the main idea?",
            "passage_content": "Passage text...",
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)
        assert question.is_reading_comprehension is True

    def test_has_audio_property(self):
        """测试是否有音频"""
        data = {
            "question_type": QuestionType.LISTENING.value,
            "content_text": "Listen to the audio.",
            "audio_url": "https://example.com/audio.mp3",
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)
        assert question.has_audio is True

        question.audio_url = None
        assert question.has_audio is False

    def test_answer_type_single_choice(self):
        """测试单选题答案类型"""
        data = {
            "question_type": QuestionType.CHOICE.value,
            "content_text": "Single choice",
            "correct_answer": "A",
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)
        assert question.answer_type == "single"

    def test_answer_type_multiple_choice(self):
        """测试多选题答案类型"""
        data = {
            "question_type": QuestionType.CHOICE.value,
            "content_text": "Select all correct answers.",
            "correct_answer": ["A", "B"],
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)
        assert question.answer_type == "multiple"

    def test_answer_type_text(self):
        """测试文本答案类型"""
        data = {
            "question_type": QuestionType.FILL_BLANK.value,
            "content_text": "Fill in the blank.",
            "correct_answer": "answer",
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)
        assert question.answer_type == "text"

    def test_answer_type_complex(self):
        """测试复杂答案类型"""
        data = {
            "question_type": QuestionType.READING_COMPREHENSION.value,
            "content_text": "Answer the questions.",
            "correct_answer": {"1": "A", "2": "B"},
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)
        assert question.answer_type == "complex"

    def test_question_repr(self):
        """测试题目字符串表示"""
        data = {
            "question_type": QuestionType.CHOICE.value,
            "content_text": "Test question",
            "difficulty_level": CEFRLevel.A2.value,
            "topic": "test",
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)
        repr_str = repr(question)
        assert "Question" in repr_str
        assert "choice" in repr_str
        assert "A2" in repr_str
        assert "test" in repr_str


class TestQuestionBank:
    """测试QuestionBank模型"""

    @pytest.fixture
    def question_bank_data(self):
        """题库数据"""
        return {
            "name": "A2 语法练习",
            "description": "A2级别的语法题目",
            "practice_type": "grammar",
            "difficulty_level": CEFRLevel.A2.value,
            "tags": ["grammar", "a2"],
            "created_by": uuid.uuid4(),
            "is_public": True,
            "question_count": 0,
        }

    def test_create_question_bank(self, question_bank_data):
        """测试创建题库"""
        bank = QuestionBank(**question_bank_data)

        assert bank.name == "A2 语法练习"
        assert bank.description == "A2级别的语法题目"
        assert bank.practice_type == "grammar"
        assert bank.difficulty_level == CEFRLevel.A2.value
        assert bank.is_public is True
        assert bank.question_count == 0

    def test_is_empty_property(self):
        """测试是否为空"""
        data = {
            "name": "测试题库",
            "practice_type": "reading",
            "created_by": uuid.uuid4(),
            "question_count": 0,
        }
        bank = QuestionBank(**data)
        assert bank.is_empty is True

        bank.question_count = 5
        assert bank.is_empty is False

    def test_question_bank_repr(self):
        """测试题库字符串表示"""
        data = {
            "name": "测试题库",
            "practice_type": "reading",
            "created_by": uuid.uuid4(),
            "question_count": 0,
        }
        bank = QuestionBank(**data)
        repr_str = repr(bank)
        assert "QuestionBank" in repr_str
        assert "测试题库" in repr_str
        assert "reading" in repr_str
        assert "0" in repr_str  # question_count


class TestQuestionIntegration:
    """测试题目和题库的集成"""

    def test_question_knowledge_points_storage(self):
        """测试知识点存储"""
        data = {
            "question_type": QuestionType.CHOICE.value,
            "content_text": "Test question",
            "knowledge_points": ["present tense", "vocabulary", "grammar"],
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)

        assert len(question.knowledge_points) == 3
        assert "present tense" in question.knowledge_points

    def test_metadata_storage(self):
        """测试元数据存储"""
        data = {
            "question_type": QuestionType.CHOICE.value,
            "content_text": "Test question",
            "extra_metadata": {
                "source": "textbook",
                "page": 25,
                "notes": "Important concept",
            },
            "created_by": uuid.uuid4(),
        }
        question = Question(**data)

        assert question.extra_metadata["source"] == "textbook"
        assert question.extra_metadata["page"] == 25
