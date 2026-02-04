"""
测试 PDF 导出功能
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session_manager import get_db as get_db_session
from app.models import User, UserRole
from app.services.mistake_export_service import get_mistake_export_service


async def main():
    """测试 PDF 导出"""
    print("\n" + "="*60)
    print("📄 测试 PDF 导出功能")
    print("="*60)

    async for db in get_db_session():
        try:
            # 获取测试学生
            result = await db.execute(
                select(User)
                .options(selectinload(User.student_profile))
                .where(User.username == "test_student")
            )
            user = result.scalar_one_or_none()

            if not user or not user.student_profile:
                print("❌ 测试学生用户不存在")
                return

            student_id = str(user.student_profile.id)

            # 检查错题数量
            from app.models.mistake import Mistake
            count_result = await db.execute(
                select(func.count(Mistake.id)).where(Mistake.student_id == user.student_profile.id)
            )
            mistake_count = count_result.scalar()
            print(f"\n📊 学生 {user.username} 有 {mistake_count} 条错题")

            if mistake_count == 0:
                print("⚠️  没有错题数据，请先运行 init_mistake_data.py")
                return

            # 获取导出服务
            export_service = get_mistake_export_service(db)

            # 测试 Markdown 导出
            print("\n🔧 测试 Markdown 导出...")
            try:
                filename, content = await export_service.export_as_markdown(
                    student_id=student_id,
                    filters=None,
                )
                print(f"  ✅ Markdown 导出成功")
                print(f"     文件名: {filename}")
                print(f"     内容长度: {len(content)} 字符")

                # 保存到文件
                output_path = f"/tmp/{filename}"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"     已保存到: {output_path}")
            except Exception as e:
                print(f"  ❌ Markdown 导出失败: {e}")
                import traceback
                traceback.print_exc()

            # 测试 PDF 导出
            print("\n🔧 测试 PDF 导出...")
            try:
                filename, content = await export_service.export_as_pdf(
                    student_id=student_id,
                    filters=None,
                )
                print(f"  ✅ PDF 导出成功")
                print(f"     文件名: {filename}")
                print(f"     内容大小: {len(content)} 字节")

                # 保存到文件
                output_path = f"/tmp/{filename}"
                with open(output_path, 'wb') as f:
                    f.write(content)
                print(f"     已保存到: {output_path}")

                # 显示文件信息
                import os
                file_size = os.path.getsize(output_path)
                print(f"     文件大小: {file_size / 1024:.2f} KB")

            except Exception as e:
                print(f"  ❌ PDF 导出失败: {e}")
                import traceback
                traceback.print_exc()

            print("\n" + "="*60)
            print("✅ 测试完成")
            print("="*60)

        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
