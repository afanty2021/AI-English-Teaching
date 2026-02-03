"""
创建测试数据 - AI英语教学系统
填充数据库中的示例内容、词汇表、教案等
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.session_manager import get_db as get_db_session
from app.models import (
    Content,
    ContentType,
    DifficultyLevel,
    ContentVocabulary,
    KnowledgeGraph,
    LessonPlan,
    LessonPlanTemplate,
    Student,
    Teacher,
    User,
    UserRole,
    Vocabulary,
)


async def create_test_users(db: AsyncSession) -> dict:
    """创建测试用户"""
    print("\n" + "="*60)
    print("创建测试用户...")
    print("="*60)

    users = {}

    # 测试密码
    test_password = "Test1234"
    password_hash = get_password_hash(test_password)

    # 检查是否已有测试用户
    existing = await db.execute(select(User).where(User.username == "test_student"))
    if existing.scalar_one_or_none():
        print("⚠️  测试用户已存在，跳过创建")
        return users

    # 创建测试学生
    student_user = User(
        username="test_student",
        email="student@test.com",
        password_hash=password_hash,
        full_name="测试学生",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(student_user)
    await db.flush()

    student = Student(
        user_id=student_user.id,
        student_no="S2024001",
        grade="大一",
        target_exam="CET4",
        target_score=500,
        current_cefr_level="B1",
    )
    db.add(student)
    users["student"] = (student_user, student)

    # 创建测试教师
    teacher_user = User(
        username="test_teacher",
        email="teacher@test.com",
        password_hash=password_hash,
        full_name="测试教师",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add(teacher_user)
    await db.flush()

    teacher = Teacher(
        user_id=teacher_user.id,
        specialization=["英语口语", "写作教学", "语法"],
        bio="专注于AI辅助英语教学，拥有10年教学经验",
    )
    db.add(teacher)
    users["teacher"] = (teacher_user, teacher)

    await db.commit()
    print(f"✅ 创建了 {len(users)} 组测试用户")
    return users


async def create_vocabulary_list(db: AsyncSession) -> list:
    """创建词汇表"""
    print("\n" + "="*60)
    print("创建词汇表...")
    print("="*60)

    vocabularies = []

    # CET4 核心词汇 - 使用正确的 JSON 格式
    cet4_words = [
        {
            "word": "achieve",
            "part_of_speech": ["v."],
            "definitions": [{"pos": "v.", "meaning": "实现，达成"}],
            "english_definition": "to successfully complete something or get a good result",
            "examples": ["He worked hard to achieve his goal.", "She achieved great success in her career."],
            "difficulty_level": "B1",
            "frequency_level": 7,
            "phonetic": "/əˈtʃiːv/",
        },
        {
            "word": "analyze",
            "part_of_speech": ["v."],
            "definitions": [{"pos": "v.", "meaning": "分析"}],
            "english_definition": "to examine or think about something carefully",
            "examples": ["We need to analyze the data carefully.", "The scientist analyzed the samples."],
            "difficulty_level": "B2",
            "frequency_level": 6,
            "phonetic": "/ˈænəlaɪz/",
        },
        {
            "word": "appreciate",
            "part_of_speech": ["v."],
            "definitions": [{"pos": "v.", "meaning": "感激，欣赏"}],
            "english_definition": "to be grateful for something",
            "examples": ["I appreciate your help.", "She appreciates fine art."],
            "difficulty_level": "B1",
            "frequency_level": 6,
            "phonetic": "/əˈpriːʃieɪt/",
        },
        {
            "word": "approach",
            "part_of_speech": ["v.", "n."],
            "definitions": [
                {"pos": "v.", "meaning": "接近，着手处理"},
                {"pos": "n.", "meaning": "方法，途径"}
            ],
            "english_definition": "to come near in distance or time; a way of doing something",
            "examples": ["We need a new approach to this problem.", "Winter is approaching."],
            "difficulty_level": "B1",
            "frequency_level": 8,
            "phonetic": "/əˈprəʊtʃ/",
        },
        {
            "word": "available",
            "part_of_speech": ["adj."],
            "definitions": [{"pos": "adj.", "meaning": "可获得的，有空的"}],
            "english_definition": "free and able to do something",
            "examples": ["Are you available tomorrow?", "This product is available in all stores."],
            "difficulty_level": "A2",
            "frequency_level": 9,
            "phonetic": "/əˈveɪləbl/",
        },
        {
            "word": "basic",
            "part_of_speech": ["adj."],
            "definitions": [{"pos": "adj.", "meaning": "基本的，基础的"}],
            "english_definition": "forming the main or most important part of something",
            "examples": ["This is a basic concept.", "We need to learn the basic skills first."],
            "difficulty_level": "A2",
            "frequency_level": 8,
            "phonetic": "/ˈbeɪsɪk/",
        },
        {
            "word": "beneficial",
            "part_of_speech": ["adj."],
            "definitions": [{"pos": "adj.", "meaning": "有益的，有利的"}],
            "english_definition": "helpful or useful",
            "examples": ["Exercise is beneficial for health.", "This policy is beneficial to everyone."],
            "difficulty_level": "B2",
            "frequency_level": 5,
            "phonetic": "/ˌbenɪˈfɪʃl/",
        },
        {
            "word": "challenge",
            "part_of_speech": ["n.", "v."],
            "definitions": [
                {"pos": "n.", "meaning": "挑战，难题"},
                {"pos": "v.", "meaning": "向...挑战"}
            ],
            "english_definition": "something that is difficult to deal with; to question if something is true or right",
            "examples": ["This is a big challenge.", "She challenged his decision."],
            "difficulty_level": "B1",
            "frequency_level": 7,
            "phonetic": "/ˈtʃælɪndʒ/",
        },
        {
            "word": "develop",
            "part_of_speech": ["v."],
            "definitions": [{"pos": "v.", "meaning": "发展，开发"}],
            "english_definition": "to grow or change into something more advanced",
            "examples": ["The city is developing rapidly.", "Children develop quickly."],
            "difficulty_level": "A2",
            "frequency_level": 9,
            "phonetic": "/dɪˈveləp/",
        },
        {
            "word": "effective",
            "part_of_speech": ["adj."],
            "definitions": [{"pos": "adj.", "meaning": "有效的，起作用的"}],
            "english_definition": "producing the result that is wanted",
            "examples": ["This is an effective solution.", "We need effective communication."],
            "difficulty_level": "B1",
            "frequency_level": 7,
            "phonetic": "/ɪˈfektɪv/",
        },
    ]

    # 创建词汇
    for word_data in cet4_words:
        vocab = Vocabulary(**word_data)
        db.add(vocab)
        vocabularies.append(vocab)

    await db.commit()
    print(f"✅ 创建了 {len(vocabularies)} 个词汇条目")
    return vocabularies


async def create_sample_content(db: AsyncSession, vocabularies: list) -> list:
    """创建示例内容"""
    print("\n" + "="*60)
    print("创建示例内容...")
    print("="*60)

    contents = []

    # 示例阅读材料
    reading_materials = [
        {
            "title": "The Benefits of Reading English Daily",
            "type": ContentType.READING,
            "difficulty": DifficultyLevel.INTERMEDIATE,
            "text": """Reading English every day is one of the most effective ways to improve your language skills. When you read regularly, you encounter new vocabulary in context, which helps you remember words better than simply memorizing lists.

Additionally, reading exposes you to different sentence structures and grammatical patterns. This exposure helps you develop an intuitive understanding of how English works, making it easier to produce your own sentences later.

Start with materials that match your current level. If a text is too difficult, you may feel frustrated. If it's too easy, you won't learn much. The key is to find material that challenges you slightly - often called "i+1" in language learning, where you understand most of the content but encounter some new words or structures.

Try to read for at least 15-30 minutes every day. This consistency is more important than reading for hours once a week. Your brain needs regular exposure to consolidate what you learn.

Remember to vary your reading materials. Newspapers, novels, academic articles, and even blogs each offer different types of language exposure. This variety helps you develop well-rounded skills.""",
            "topic": "Language Learning",
            "exam_type": "CET4",
        },
        {
            "title": "Understanding Present Perfect Tense",
            "type": ContentType.GRAMMAR,
            "difficulty": DifficultyLevel.ELEMENTARY,
            "text": """The Present Perfect tense is a crucial aspect of English grammar that connects the past to the present. It is formed using "have" or "has" plus the past participle of the verb.

We use the Present Perfect for several purposes:

1. Actions that happened at an unspecified time in the past
   - Example: "I have visited Paris." (We don't know when)

2. Actions that started in the past and continue to the present
   - Example: "She has lived here for ten years." (Still living here)

3. Actions that happened recently and have present relevance
   - Example: "I have just finished my homework." (The homework is done now)

Common time expressions used with Present Perfect include: "just," "already," "yet," "ever," "never," "since," and "for."

Remember: We cannot use specific time expressions like "yesterday" or "last week" with Present Perfect. For those, we use Simple Past tense.

Practice makes perfect! Try using this tense in your daily conversations to become more comfortable with it.""",
            "topic": "Grammar",
            "exam_type": "CET4",
        },
        {
            "title": "Tips for CET4 Listening Preparation",
            "type": ContentType.VOCABULARY,
            "difficulty": DifficultyLevel.UPPER_INTERMEDIATE,
            "text": """Preparing for CET4 listening requires consistent practice and the right strategies. Here are some effective tips:

1. Listen to English materials daily - news, podcasts, or movies help you get used to natural speech patterns.

2. Practice note-taking - during the test, you'll hear each passage only once. Good notes help you remember key information.

3. Learn to identify key words - questions often focus on specific details like numbers, names, places, and reasons.

4. Familiarize yourself with different accents - CET4 listening may include British and American accents.

5. Practice with past exam papers - this helps you understand the test format and time constraints.

Common question types include:
- Multiple choice about main ideas
- Detail questions asking for specific information
- Inference questions requiring you to understand implications
- Questions about speakers' attitudes or purposes

Remember, improving listening skills takes time. Don't get discouraged if progress seems slow at first. Consistent practice is the key to success.""",
            "topic": "Exam Preparation",
            "exam_type": "CET4",
        },
    ]

    # 创建内容
    for material in reading_materials:
        content = Content(
            title=material["title"],
            content_type=material["type"].value,
            difficulty_level=material["difficulty"].value,
            content_text=material["text"],
            topic=material["topic"],
            exam_type=material["exam_type"],
            word_count=len(material["text"].split()),
        )
        db.add(content)
        await db.flush()

        # 关联词汇（检查词汇是否出现在内容中）
        content_lower = material["text"].lower()
        for vocab in vocabularies:
            if vocab.word.lower() in content_lower:
                cv = ContentVocabulary(
                    content_id=content.id,
                    vocabulary_id=vocab.id,
                )
                db.add(cv)

        contents.append(content)

    await db.commit()
    print(f"✅ 创建了 {len(contents)} 个内容条目")
    return contents


async def create_knowledge_graph(db: AsyncSession, users: dict):
    """创建知识图谱"""
    print("\n" + "="*60)
    print("创建知识图谱...")
    print("="*60)

    if not users.get("student"):
        print("⚠️  没有学生用户，跳过知识图谱创建")
        return None

    _, student = users["student"]

    # 检查是否已有知识图谱
    existing = await db.execute(
        select(KnowledgeGraph).where(KnowledgeGraph.student_id == student.id)
    )
    if existing.scalar_one_or_none():
        print("⚠️  知识图谱已存在")
        return None

    graph = KnowledgeGraph(
        student_id=student.id,
        nodes={
            "abilities": {
                "listening": {"level": 60, "confidence": 0.7},
                "reading": {"level": 75, "confidence": 0.8},
                "speaking": {"level": 55, "confidence": 0.6},
                "writing": {"level": 65, "confidence": 0.7},
                "grammar": {"level": 50, "confidence": 0.6},
                "vocabulary": {"level": 70, "confidence": 0.75},
            },
            "knowledge_points": {
                "present_perfect": {"mastered": True, "last_reviewed": "2024-01-15"},
                "past_continuous": {"mastered": False, "last_reviewed": "2024-01-10"},
                "articles": {"mastered": True, "last_reviewed": "2024-01-12"},
            },
        },
        edges={
            "prerequisites": {
                "present_perfect": ["past_simple", "present_simple"],
                "past_continuous": ["past_simple"],
            },
            "related": {
                "present_perfect": ["past_simple", "present_perfect_continuous"],
            },
        },
        metadata={
            "last_updated": datetime.now().isoformat(),
            "total_practice_hours": 25,
            "strongest_area": "reading",
            "weakest_area": "grammar",
        },
    )

    db.add(graph)
    await db.commit()
    print("✅ 创建了知识图谱")
    return graph


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("📝 创建测试数据")
    print("="*60)
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    async for db in get_db_session():
        try:
            # 创建测试用户
            users = await create_test_users(db)

            # 创建词汇表
            vocabularies = await create_vocabulary_list(db)

            # 创建示例内容
            contents = await create_sample_content(db, vocabularies)

            # 创建知识图谱
            graph = await create_knowledge_graph(db, users)

            print("\n" + "="*60)
            print("✅ 测试数据创建完成")
            print("="*60)
            print(f"📊 数据统计:")
            print(f"  - 用户: {len(users)} 组")
            print(f"  - 词汇: {len(vocabularies)} 条")
            print(f"  - 内容: {len(contents)} 条")
            print(f"  - 知识图谱: {'1 个' if graph else '已存在'}")

            # 显示测试账号信息
            if users.get("student"):
                print(f"\n🔑 测试账号:")
                print(f"  学生: test_student / Test1234")
            if users.get("teacher"):
                print(f"  教师: test_teacher / Test1234")

            print(f"\n📅 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"\n❌ 创建测试数据失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
