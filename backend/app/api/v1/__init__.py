"""
API v1模块
"""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    contents,
    conversations,
    users,
    lesson_plans,
    lesson_templates,
    lesson_export,
    lesson_shares,
    students,
    practices,
    mistakes,
    learning_reports,
    question_banks,
    questions,
    practice_sessions,
    reports_enhanced,
    notifications,
    export_templates,
    export_websocket,
)

api_router = APIRouter()

# 注册路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(contents.router, prefix="/contents", tags=["内容推荐"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["AI口语陪练"])
api_router.include_router(lesson_plans.router, prefix="/lesson-plans", tags=["AI辅助备课"])
api_router.include_router(lesson_templates.router, prefix="/lesson-templates", tags=["教案模板"])
api_router.include_router(lesson_export.router, prefix="/lesson-export", tags=["教案导出"])
api_router.include_router(lesson_shares.router, prefix="/lesson-plans", tags=["教案分享"])
api_router.include_router(students.router, prefix="/students", tags=["学生管理"])
api_router.include_router(practices.router, prefix="/practices", tags=["练习记录"])
api_router.include_router(mistakes.router, prefix="/mistakes", tags=["错题本"])
api_router.include_router(learning_reports.router, prefix="/reports", tags=["学习报告"])
api_router.include_router(reports_enhanced.router, prefix="", tags=["增强报告"])
api_router.include_router(question_banks.router, prefix="/question-banks", tags=["题库管理"])
api_router.include_router(questions.router, prefix="/questions", tags=["题目管理"])
api_router.include_router(practice_sessions.router, prefix="/practice-sessions", tags=["练习会话"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["通知设置"])
api_router.include_router(export_templates.router, prefix="/export-templates", tags=["导出模板"])
api_router.include_router(export_websocket.router, tags=["导出WebSocket"])
