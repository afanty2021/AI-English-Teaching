"""
业务服务层模块
包含所有业务逻辑服务
"""
from app.services import auth_service, recommendation_service
from app.services import question_service, question_bank_service, practice_session_service
from app.services import template_service
from app.services.document_generators import WordDocumentGenerator

__all__ = [
    "auth_service",
    "recommendation_service",
    "question_service",
    "question_bank_service",
    "practice_session_service",
    "template_service",
    "WordDocumentGenerator",
]
