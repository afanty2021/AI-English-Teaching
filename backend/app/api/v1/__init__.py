"""
API v1模块
"""
from fastapi import APIRouter

from app.api.v1 import auth, contents, conversations, lesson_plans, students, practices, mistakes

api_router = APIRouter()

# 注册路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(contents.router, prefix="/contents", tags=["内容推荐"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["AI口语陪练"])
api_router.include_router(lesson_plans.router, prefix="/lesson-plans", tags=["AI辅助备课"])
api_router.include_router(students.router, prefix="/students", tags=["学生管理"])
api_router.include_router(practices.router, prefix="/practices", tags=["练习记录"])
api_router.include_router(mistakes.router, prefix="/mistakes", tags=["错题本"])
