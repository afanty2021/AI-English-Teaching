"""
测试 Conversation 模型集成
验证 Student 和 Conversation 之间的关系是否正确工作
"""
import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session_manager import get_db as get_db_session
from app.models import (
    Student,
    Conversation,
    ConversationScenario,
    ConversationStatus,
)


async def test_conversation_creation():
    """测试创建会话"""
    print("\n" + "="*60)
    print("测试 1: 创建会话")
    print("="*60)

    async for db in get_db_session():
        try:
            # 获取测试学生
            result = await db.execute(
                select(Student).limit(1)
            )
            student = result.scalar_one_or_none()

            if not student:
                print("⚠️  没有找到学生，请先运行 init_test_data.py")
                return False

            # 创建新会话
            conversation = Conversation(
                student_id=student.id,
                scenario=ConversationScenario.DAILY_GREETING,
                level="B1",
                status=ConversationStatus.ACTIVE,
                messages="[]",
            )
            db.add(conversation)
            await db.commit()

            print(f"✅ 会话创建成功: ID={conversation.id}")
            print(f"   学生ID: {conversation.student_id}")
            print(f"   场景: {conversation.scenario.value}")
            print(f"   状态: {conversation.status.value}")

            return True

        except Exception as e:
            print(f"❌ 创建会话失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_student_conversations_relation():
    """测试 Student -> Conversations 关系"""
    print("\n" + "="*60)
    print("测试 2: Student -> Conversations 关系")
    print("="*60)

    async for db in get_db_session():
        try:
            # 获取学生并预加载 conversations 关系
            result = await db.execute(
                select(Student)
                .options(selectinload(Student.conversations))
                .limit(1)
            )
            student = result.scalar_one_or_none()

            if not student:
                print("⚠️  没有找到学生")
                return False

            # 通过关系访问会话
            conversations = student.conversations
            print(f"✅ 学生 {student.id} 的会话数量: {len(conversations)}")

            for conv in conversations:
                print(f"   - 会话 {conv.id}: {conv.scenario.value} ({conv.status.value})")

            return True

        except Exception as e:
            print(f"❌ 关系测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_conversation_student_relation():
    """测试 Conversation -> Student 关系"""
    print("\n" + "="*60)
    print("测试 3: Conversation -> Student 关系")
    print("="*60)

    async for db in get_db_session():
        try:
            # 获取会话并预加载 student 关系
            result = await db.execute(
                select(Conversation)
                .options(selectinload(Conversation.student))
                .limit(1)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                print("⚠️  没有找到会话")
                return False

            # 通过关系访问学生
            student = conversation.student
            print(f"✅ 会话 {conversation.id} 所属学生:")
            print(f"   学生ID: {student.id}")
            print(f"   目标考试: {student.target_exam}")
            print(f"   CEFR等级: {student.current_cefr_level}")

            return True

        except Exception as e:
            print(f"❌ 关系测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_add_message_to_conversation():
    """测试添加消息到会话"""
    print("\n" + "="*60)
    print("测试 4: 添加消息到会话")
    print("="*60)

    async for db in get_db_session():
        try:
            # 获取会话
            result = await db.execute(
                select(Conversation).limit(1)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                print("⚠️  没有找到会话")
                return False

            # 添加消息
            conversation.add_message(
                role="assistant",
                content="Hello! How are you today?",
                metadata={"corrections": []}
            )
            conversation.add_message(
                role="user",
                content="I'm fine, thank you!",
            )

            await db.commit()

            # 获取消息
            messages = conversation.get_messages()
            print(f"✅ 消息添加成功，当前消息数量: {len(messages)}")
            for msg in messages:
                print(f"   - {msg['role']}: {msg['content'][:50]}...")

            return True

        except Exception as e:
            print(f"❌ 添加消息失败: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 Conversation 模型集成测试")
    print("="*60)

    tests = [
        ("创建会话", test_conversation_creation),
        ("Student->Conversations关系", test_student_conversations_relation),
        ("Conversation->Student关系", test_conversation_student_relation),
        ("添加消息", test_add_message_to_conversation),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 打印总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
