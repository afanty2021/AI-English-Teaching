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
from app.models.lesson_plan_share import (
    LessonPlanShare,
    SharePermission,
    ShareStatus
)
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
from app.models.question import (
    Question,
    QuestionBank,
    QuestionType,
    CEFRLevel,
)
from app.models.practice_session import (
    PracticeSession,
    SessionStatus,
)
from app.models.recommendation import (
    RecommendationFeedback,
    RecommendationHistory,
    RecommendationPreference,
)
from app.models.share_statistics_history import ShareStatisticsHistory
from app.models.notification_preference import NotificationPreference
from app.models.export_task import (
    ExportTask,
    TaskStatus,
    ExportFormat,
)
from app.models.export_template import (
    ExportTemplate,
    TemplateFormat,
)

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
    "LessonPlanShare",
    "SharePermission",
    "ShareStatus",
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
    "Question",
    "QuestionBank",
    "QuestionType",
    "CEFRLevel",
    "PracticeSession",
    "SessionStatus",
    "RecommendationFeedback",
    "RecommendationHistory",
    "RecommendationPreference",
    "ShareStatisticsHistory",
    "NotificationPreference",
    "ExportTask",
    "TaskStatus",
    "ExportFormat",
    "ExportTemplate",
    "TemplateFormat",
]
