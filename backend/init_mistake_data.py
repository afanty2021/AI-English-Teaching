"""
创建测试错题数据 - AI英语教学系统
为学生用户添加各种类型的错题记录，用于测试错题本功能

用法:
    python init_mistake_data.py       # 交互式运行
    python init_mistake_data.py --force  # 强制覆盖现有数据
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_manager import get_db as get_db_session
from app.models import User, Student, MistakeStatus, MistakeType
from app.models.mistake import Mistake


async def get_test_student(db: AsyncSession):
    """获取测试学生用户"""
    result = await db.execute(
        select(User).where(User.username == "test_student")
    )
    user = result.scalar_one_or_none()

    if not user:
        print("❌ 测试学生用户不存在，请先运行 init_test_data.py")
        return None

    # 预加载 student_profile
    result = await db.execute(
        select(User)
        .where(User.username == "test_student")
    )
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(User)
        .options(selectinload(User.student_profile))
        .where(User.username == "test_student")
    )
    user = result.scalar_one_or_none()

    return user


async def create_grammar_mistakes(db: AsyncSession, student_id, student_user):
    """创建语法类错题"""
    print("\n创建语法错题...")

    from app.models.mistake import Mistake
    from app.services.mistake_service import get_mistake_service

    service = get_mistake_service(db)

    grammar_mistakes = [
        {
            "question": "I _____ to the store yesterday when I saw him.",
            "wrong_answer": "was going",
            "correct_answer": "was going",
            "mistake_type": MistakeType.GRAMMAR,
            "explanation": "过去进行时表示过去某个时间正在进行的动作。这里虽然答案对了，但让我们用另一个例子：I _____ my homework when the phone rang.",
            "knowledge_points": ["past_continuous", "tense"],
            "difficulty_level": "B1",
            "topic": "Grammar - Tenses",
        },
        {
            "question": "She has been working here _____ five years.",
            "wrong_answer": "since",
            "correct_answer": "for",
            "mistake_type": MistakeType.GRAMMAR,
            "explanation": "'for' + 时间段表示动作持续了多久；'since' + 时间点表示动作从什么时候开始。五年是时间段，应该用 for。",
            "knowledge_points": ["present_perfect", "for_vs_since"],
            "difficulty_level": "A2",
            "topic": "Grammar - Present Perfect",
        },
        {
            "question": "If I _____ rich, I would travel around the world.",
            "wrong_answer": "am",
            "correct_answer": "were",
            "mistake_type": MistakeType.GRAMMAR,
            "explanation": "虚拟语气中，be动词在if从句中统一用were，不管主语是什么人称。",
            "knowledge_points": ["subjunctive", "conditional"],
            "difficulty_level": "B2",
            "topic": "Grammar - Conditionals",
        },
        {
            "question": "Neither the teacher nor the students _____ happy with the result.",
            "wrong_answer": "is",
            "correct_answer": "are",
            "mistake_type": MistakeType.GRAMMAR,
            "explanation": "neither...nor...连接主语时，谓语动词遵循就近原则，与最近的主语一致。students是复数，所以用are。",
            "knowledge_points": ["subject_verb_agreement", "correlative_conjunctions"],
            "difficulty_level": "B2",
            "topic": "Grammar - Agreement",
        },
        {
            "question": "I look forward to _____ from you soon.",
            "wrong_answer": "hear",
            "correct_answer": "hearing",
            "mistake_type": MistakeType.GRAMMAR,
            "explanation": "'look forward to' 中的 to 是介词，后面接名词或动名词，不定式符号to后面才接动词原形。",
            "knowledge_points": ["prepositions", "gerunds"],
            "difficulty_level": "B1",
            "topic": "Grammar - Prepositions",
        },
    ]

    created = []
    for i, data in enumerate(grammar_mistakes, 1):
        mistake = await service.create_mistake(
            student_id=student_id,
            question=data["question"],
            wrong_answer=data["wrong_answer"],
            correct_answer=data["correct_answer"],
            mistake_type=data["mistake_type"],
            explanation=data.get("explanation"),
            knowledge_points=data.get("knowledge_points"),
            difficulty_level=data.get("difficulty_level"),
            topic=data.get("topic"),
        )
        created.append(mistake)
        print(f"  ✓ {i}. {data['topic']}: {data['question'][:40]}...")

    return created


async def create_vocabulary_mistakes(db: AsyncSession, student_id):
    """创建词汇类错题"""
    print("\n创建词汇错题...")

    from app.services.mistake_service import get_mistake_service

    service = get_mistake_service(db)

    vocab_mistakes = [
        {
            "question": "The teacher gave us some _____ on how to improve our writing.",
            "wrong_answer": "advices",
            "correct_answer": "advice",
            "mistake_type": MistakeType.VOCABULARY,
            "explanation": "advice 是不可数名词，不能加 's'。表示多条建议时可以用 pieces of advice。",
            "knowledge_points": ["uncountable_nouns", "advice"],
            "difficulty_level": "A2",
            "topic": "Vocabulary - Uncountable Nouns",
        },
        {
            "question": "I made a big _____ in my presentation.",
            "wrong_answer": "fault",
            "correct_answer": "mistake",
            "mistake_type": MistakeType.VOCABULARY,
            "explanation": "mistake 指日常生活中犯的错误；fault 指性格上的缺点或过失。这里指犯错误应用 mistake。",
            "knowledge_points": ["confusing_words", "mistake_vs_fault"],
            "difficulty_level": "B1",
            "topic": "Vocabulary - Confusing Words",
        },
        {
            "question": "The movie was very _____. I enjoyed it a lot.",
            "wrong_answer": "amused",
            "correct_answer": "amusing",
            "mistake_type": MistakeType.VOCABULARY,
            "explanation": "-ing 形容词修饰物，表示令人...的；-ed 形容词修饰人，表示感到...的。电影令人愉快，用 amusing。",
            "knowledge_points": ["adjective_endings", "-ing_vs_-ed"],
            "difficulty_level": "B1",
            "topic": "Vocabulary - Adjectives",
        },
        {
            "question": "She _____ to music every evening.",
            "wrong_answer": "hears",
            "correct_answer": "listens to",
            "mistake_type": MistakeType.VOCABULARY,
            "explanation": "'listen to' 表示注意听、倾听；'hear' 表示听到的结果。听音乐应用 listen to music。",
            "knowledge_points": ["confusing_verbs", "listen_vs_hear"],
            "difficulty_level": "A2",
            "topic": "Vocabulary - Verbs",
        },
        {
            "question": "There are _____ benefits to regular exercise.",
            "wrong_answer": "much",
            "correct_answer": "many",
            "mistake_type": MistakeType.VOCABULARY,
            "explanation": "benefits 是可数名词复数，应该用 many 修饰。much 修饰不可数名词。",
            "knowledge_points": ["quantifiers", "many_vs_much"],
            "difficulty_level": "A2",
            "topic": "Vocabulary - Quantifiers",
        },
    ]

    created = []
    for i, data in enumerate(vocab_mistakes, 1):
        mistake = await service.create_mistake(
            student_id=student_id,
            question=data["question"],
            wrong_answer=data["wrong_answer"],
            correct_answer=data["correct_answer"],
            mistake_type=data["mistake_type"],
            explanation=data.get("explanation"),
            knowledge_points=data.get("knowledge_points"),
            difficulty_level=data.get("difficulty_level"),
            topic=data.get("topic"),
        )
        created.append(mistake)
        print(f"  ✓ {i}. {data['topic']}: {data['question'][:40]}...")

    return created


async def create_reading_mistakes(db: AsyncSession, student_id):
    """创建阅读理解类错题"""
    print("\n创建阅读理解错题...")

    from app.services.mistake_service import get_mistake_service

    service = get_mistake_service(db)

    reading_mistakes = [
        {
            "question": "According to the passage, what is the main idea of the text?",
            "passage": "Reading English every day is one of the most effective ways to improve your language skills. When you read regularly, you encounter new vocabulary in context...",
            "wrong_answer": "How to use a dictionary",
            "correct_answer": "Benefits of daily reading practice",
            "mistake_type": MistakeType.READING,
            "explanation": "文章主旨是每天阅读英语的好处，而不是如何使用字典。需要通读全文，抓住中心思想。",
            "knowledge_points": ["main_idea", "reading_comprehension"],
            "difficulty_level": "B1",
            "topic": "Reading - Main Idea",
        },
        {
            "question": "What does the word 'consistency' mean in this context?",
            "passage": "The key is to find material that challenges you slightly. Try to read for at least 15-30 minutes every day. This consistency is more important than reading for hours once a week.",
            "wrong_answer": "Reading speed",
            "correct_answer": "Regular and continuous practice",
            "mistake_type": MistakeType.READING,
            "explanation": "consistency 在这里指的是保持规律的、持续的练习，而不是阅读速度。上下文提到每天15-30分钟比一周一次读几小时更重要。",
            "knowledge_points": ["vocabulary_in_context", "inference"],
            "difficulty_level": "B2",
            "topic": "Reading - Vocabulary in Context",
        },
        {
            "question": "What can be inferred about the author's attitude towards difficult texts?",
            "passage": "If a text is too difficult, you may feel frustrated. If it's too easy, you won't learn much. The key is to find material that challenges you slightly.",
            "wrong_answer": "Difficult texts are always better",
            "correct_answer": "Find appropriately challenging materials",
            "mistake_type": MistakeType.READING,
            "explanation": "作者认为太难的文本会让人沮丧，太简单的学不到东西，关键是要找到稍微有挑战性的材料（i+1理论）。",
            "knowledge_points": ["inference", "author_attitude"],
            "difficulty_level": "B2",
            "topic": "Reading - Inference",
        },
    ]

    created = []
    for i, data in enumerate(reading_mistakes, 1):
        question = f"{data['question']}\n\nPassage: {data['passage'][:100]}..."
        mistake = await service.create_mistake(
            student_id=student_id,
            question=question,
            wrong_answer=data["wrong_answer"],
            correct_answer=data["correct_answer"],
            mistake_type=data["mistake_type"],
            explanation=data.get("explanation"),
            knowledge_points=data.get("knowledge_points"),
            difficulty_level=data.get("difficulty_level"),
            topic=data.get("topic"),
        )
        created.append(mistake)
        print(f"  ✓ {i}. {data['topic']}: {data['question'][:40]}...")

    return created


async def create_writing_mistakes(db: AsyncSession, student_id):
    """创建写作类错题"""
    print("\n创建写作错题...")

    from app.services.mistake_service import get_mistake_service

    service = get_mistake_service(db)

    writing_mistakes = [
        {
            "question": "Correct the sentence: 'I have went to the park yesterday.'",
            "wrong_answer": "I have went to the park yesterday.",
            "correct_answer": "I went to the park yesterday.",
            "mistake_type": MistakeType.WRITING,
            "explanation": "句子中有明确的时间状语 yesterday，应该用一般过去时 went，不能用现在完成时 have went（而且have gone才是正确的现在完成时形式）。",
            "knowledge_points": ["past_simple", "present_perfect", "time_expressions"],
            "difficulty_level": "A2",
            "topic": "Writing - Tense Consistency",
        },
        {
            "question": "Correct the sentence: 'There is many people in the room.'",
            "wrong_answer": "There is many people in the room.",
            "correct_answer": "There are many people in the room.",
            "mistake_type": MistakeType.WRITING,
            "explanation": "There be 句型中，be动词的单复数取决于后面的主语。people是复数，应该用are。",
            "knowledge_points": ["there_be", "subject_verb_agreement"],
            "difficulty_level": "A2",
            "topic": "Writing - There Be Structure",
        },
        {
            "question": "Correct the sentence: 'Although it was raining, but he went out.'",
            "wrong_answer": "Although it was raining, but he went out.",
            "correct_answer": "Although it was raining, he went out.",
            "mistake_type": MistakeType.WRITING,
            "explanation": "英语中 although 和 but 不能同时使用，只能选一个。这是中式英语的典型错误。",
            "knowledge_points": ["conjunctions", "although_vs_but"],
            "difficulty_level": "B1",
            "topic": "Writing - Conjunctions",
        },
    ]

    created = []
    for i, data in enumerate(writing_mistakes, 1):
        mistake = await service.create_mistake(
            student_id=student_id,
            question=data["question"],
            wrong_answer=data["wrong_answer"],
            correct_answer=data["correct_answer"],
            mistake_type=data["mistake_type"],
            explanation=data.get("explanation"),
            knowledge_points=data.get("knowledge_points"),
            difficulty_level=data.get("difficulty_level"),
            topic=data.get("topic"),
        )
        created.append(mistake)
        print(f"  ✓ {i}. {data['topic']}: {data['question'][:40]}...")

    return created


async def update_mistake_metadata(db: AsyncSession, mistakes):
    """更新错题的额外元数据，模拟真实的复习情况"""
    print("\n更新错题元数据...")

    from datetime import datetime, timedelta
    import random

    for i, mistake in enumerate(mistakes):
        # 随机设置一些错题的状态
        rand = random.random()

        if rand < 0.3:
            # 30% 已掌握
            mistake.status = MistakeStatus.MASTERED
            mistake.review_count = random.randint(3, 6)
            mistake.last_reviewed_at = datetime.utcnow() - timedelta(days=random.randint(1, 7))

        elif rand < 0.6:
            # 30% 复习中
            mistake.status = MistakeStatus.REVIEWING
            mistake.review_count = random.randint(1, 3)
            mistake.last_reviewed_at = datetime.utcnow() - timedelta(days=random.randint(0, 3))

        else:
            # 40% 待复习
            mistake.status = MistakeStatus.PENDING
            mistake.review_count = random.randint(0, 1)

        # 随机设置错误次数
        mistake.mistake_count = random.randint(1, 5)

        # 设置时间
        base_time = datetime.utcnow() - timedelta(days=random.randint(1, 30))
        mistake.first_mistaken_at = base_time
        mistake.last_mistaken_at = base_time + timedelta(days=random.randint(0, 10))

        await db.flush()

        if (i + 1) % 5 == 0:
            print(f"  ✓ 已更新 {i + 1} 条错题的元数据")

    await db.commit()
    print("  ✅ 错题元数据更新完成")


async def main():
    """主函数"""
    # 检查命令行参数
    force_mode = "--force" in sys.argv

    print("\n" + "="*60)
    print("📝 创建测试错题数据")
    print("="*60)
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async for db in get_db_session():
        try:
            # 获取测试学生
            student_user = await get_test_student(db)
            if not student_user or not student_user.student_profile:
                print("❌ 测试学生用户不存在或没有学生档案")
                return

            student_id = student_user.student_profile.id

            # 检查是否已有错题数据
            existing_result = await db.execute(
                select(Mistake).where(Mistake.student_id == student_id)
            )
            existing_mistakes = existing_result.scalars().all()
            existing_count = len(existing_mistakes)

            if existing_count > 0:
                print(f"\n⚠️  已存在 {existing_count} 条错题数据")

                if force_mode:
                    print("🔄 强制模式：删除现有数据并重新创建...")
                    await db.execute(
                        sql_delete(Mistake).where(Mistake.student_id == student_id)
                    )
                    await db.commit()
                    print("✅ 已删除现有错题数据")
                else:
                    # 非交互模式直接保留现有数据
                    print("ℹ️  保留现有错题数据，跳过创建")
                    print(f"💡 提示: 使用 --force 参数可强制重新创建")

                    # 显示现有数据统计
                    status_count = {}
                    type_count = {}
                    for m in existing_mistakes:
                        status_count[m.status] = status_count.get(m.status, 0) + 1
                        type_count[m.mistake_type] = type_count.get(m.mistake_type, 0) + 1

                    print(f"\n📊 现有数据统计:")
                    for status, count in sorted(status_count.items()):
                        print(f"  - {status}: {count} 条")
                    return

            # 创建各类错题
            all_mistakes = []

            grammar_mistakes = await create_grammar_mistakes(db, student_id, student_user)
            all_mistakes.extend(grammar_mistakes)

            vocab_mistakes = await create_vocabulary_mistakes(db, student_id)
            all_mistakes.extend(vocab_mistakes)

            reading_mistakes = await create_reading_mistakes(db, student_id)
            all_mistakes.extend(reading_mistakes)

            writing_mistakes = await create_writing_mistakes(db, student_id)
            all_mistakes.extend(writing_mistakes)

            # 更新元数据
            await update_mistake_metadata(db, all_mistakes)

            print("\n" + "="*60)
            print("✅ 测试错题数据创建完成")
            print("="*60)
            print(f"📊 数据统计:")
            print(f"  - 语法错题: {len(grammar_mistakes)} 条")
            print(f"  - 词汇错题: {len(vocab_mistakes)} 条")
            print(f"  - 阅读错题: {len(reading_mistakes)} 条")
            print(f"  - 写作错题: {len(writing_mistakes)} 条")
            print(f"  - 总计: {len(all_mistakes)} 条")

            print(f"\n🔑 测试账号: test_student / Test1234")
            print(f"📅 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"\n❌ 创建错题数据失败: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(main())
