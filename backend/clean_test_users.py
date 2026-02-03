"""
清理旧测试用户 - AI英语教学系统
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_manager import get_db as get_db_session
from app.models import User, Student, Teacher, KnowledgeGraph


async def clean_test_users():
    """删除测试用户及相关数据"""
    print("清理旧测试用户...")

    async for db in get_db_session():
        try:
            # 先获取用户ID
            users_result = await db.execute(
                select(User.id, User.username).where(User.username.in_(["test_student", "test_teacher"]))
            )
            users = users_result.all()

            if not users:
                print("⚠️  没有找到旧测试用户")
                return

            user_ids = [u[0] for u in users]

            # 删除知识图谱
            await db.execute(
                delete(KnowledgeGraph).where(KnowledgeGraph.student_id.in_(user_ids))
            )

            # 删除学生档案
            await db.execute(
                delete(Student).where(Student.user_id.in_(user_ids))
            )

            # 删除教师档案
            await db.execute(
                delete(Teacher).where(Teacher.user_id.in_(user_ids))
            )

            # 删除用户
            await db.execute(
                delete(User).where(User.id.in_(user_ids))
            )

            await db.commit()
            print(f"✅ 已删除 {len(users)} 个旧测试用户")
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(clean_test_users())
