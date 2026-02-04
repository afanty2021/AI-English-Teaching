"""
数据模型模块 - AI英语教学系统
"""
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.knowledge_graph import KnowledgeGraph
from app.models.content import (
    Content,
    Vocabulary,
    ContentVocabulary,
    ContentType,
    DifficultyLevel,
    ExamType,
)
from app.models.lesson_plan import LessonPlan, LessonPlanTemplate
from app.models.conversation import (
    Conversation,
    ConversationScenario,
    ConversationStatus,
)
from app.models.practice import (
    Practice,
    PracticeStatus,
    PracticeType,
)
from app.models.mistake import (
    Mistake,
    MistakeStatus,
    MistakeType,
)
from app.models.class_model import ClassInfo, ClassStudent
from app.models.learning_report import LearningReport

__all__ = [
    "User",
    "UserRole",
    "Organization",
    "Student",
    "Teacher",
    "KnowledgeGraph",
    "Content",
    "Vocabulary",
    "ContentVocabulary",
    "ContentType",
    "DifficultyLevel",
    "ExamType",
    "LessonPlan",
    "LessonPlanTemplate",
    "Conversation",
    "ConversationScenario",
    "ConversationStatus",
    "Practice",
    "PracticeStatus",
    "PracticeType",
    "Mistake",
    "MistakeStatus",
    "MistakeType",
    "ClassInfo",
    "ClassStudent",
    "LearningReport",
]
