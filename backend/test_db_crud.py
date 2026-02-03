"""
测试数据库CRUD操作
验证User、Organization、Student、Teacher模型的基本功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import AsyncSessionLocal, engine
from app.models.organization import Organization
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User


async def test_crud_operations():
    """测试基本的CRUD操作"""

    async with AsyncSessionLocal() as session:
        # 1. 先创建管理员用户
        print("=== 1. 创建管理员用户 ===")
        admin = User(
            username="admin",
            email="admin@test.com",
            password_hash="hashed_password_here",  # 实际使用set_password方法
            role="organization_admin",
            is_active=True,
            is_superuser=False,
            full_name="管理员",
            phone="13800138000"
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        print(f"创建管理员用户成功: {admin.username} (ID: {admin.id})")

        # 2. 创建组织（关联管理员）
        print("\n=== 2. 创建组织 ===")
        org = Organization(
            name="测试教育机构",
            code="TEST001",
            admin_user_id=admin.id,  # 关联管理员用户
            address="测试地址123号",
            phone="010-12345678",
            email="test@example.com",
            description="这是一个测试组织",
            is_active=True,
            license_info={"license_no": "LIC123456"}
        )
        session.add(org)
        await session.commit()
        await session.refresh(org)
        print(f"创建组织成功: {org.name} (ID: {org.id})")

        # 3. 创建教师用户和教师信息
        print("\n=== 3. 创建教师 ===")
        teacher_user = User(
            username="teacher1",
            email="teacher1@test.com",
            password_hash="hashed_password_here",
            role="teacher",
            is_active=True,
            full_name="张老师",
            phone="13800138001"
        )
        session.add(teacher_user)
        await session.commit()
        await session.refresh(teacher_user)

        teacher = Teacher(
            user_id=teacher_user.id,
            organization_id=org.id,
            teacher_no="T001",
            real_name="张老师",
            gender="男",
            status="active",
            teacher_type="full_time",
            education="本科",
            graduate_school="北京师范大学",
            major="数学",
            certificates={"name": "教师资格证", "no": "20210001"},
            bank_info={"bank": "工商银行", "account": "6222021234567890"}
        )
        session.add(teacher)
        await session.commit()
        await session.refresh(teacher)
        print(f"创建教师成功: {teacher.real_name} (工号: {teacher.teacher_no})")

        # 4. 创建学生用户和学生信息
        print("\n=== 4. 创建学生 ===")
        student_user = User(
            username="student1",
            email="student1@test.com",
            password_hash="hashed_password_here",
            role="student",
            is_active=True,
            full_name="李明",
            phone="13800138002"
        )
        session.add(student_user)
        await session.commit()
        await session.refresh(student_user)

        student = Student(
            user_id=student_user.id,
            organization_id=org.id,
            student_no="S001",
            real_name="李明",
            gender="男",
            parent_name="李父",
            parent_phone="13900139000",
            school="北京第一中学",
            grade="高一",
            is_enrolled=True,
            extra_data={"hobbies": ["篮球", "编程"]}
        )
        session.add(student)
        await session.commit()
        await session.refresh(student)
        print(f"创建学生成功: {student.real_name} (学号: {student.student_no})")

        # 5. 查询测试
        print("\n=== 5. 查询测试 ===")

        # 查询所有用户
        result = await session.execute(select(User).limit(10))
        users = result.scalars().all()
        print(f"用户总数查询: 找到 {len(users)} 个用户")
        for user in users:
            print(f"  - {user.username} ({user.role})")

        # 查询该组织的所有学生
        result = await session.execute(
            select(Student).where(Student.organization_id == org.id)
        )
        students = result.scalars().all()
        print(f"\n组织 {org.name} 的学生: {len(students)} 人")

        # 查询该组织的所有教师
        result = await session.execute(
            select(Teacher).where(Teacher.organization_id == org.id)
        )
        teachers = result.scalars().all()
        print(f"组织 {org.name} 的教师: {len(teachers)} 人")

        # 6. 更新测试
        print("\n=== 6. 更新测试 ===")
        student.grade = "高二"
        await session.commit()
        await session.refresh(student)
        print(f"学生 {student.real_name} 年级已更新为: {student.grade}")

        # 7. 删除测试（实际使用中可能不删除，仅用于测试）
        print("\n=== 7. 清理测试数据 ===")
        await session.delete(student)
        await session.delete(teacher)
        await session.delete(student_user)
        await session.delete(teacher_user)
        await session.delete(org)
        await session.delete(admin)
        await session.commit()
        print("测试数据已清理")

        print("\n=== 所有测试通过 ===")


async def main():
    """主函数"""
    print("开始测试数据库CRUD操作...\n")

    try:
        await test_crud_operations()
        print("\n测试完成!")
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
