"""
测试数据种子脚本

为 AI English Teaching System 生成更多测试数据，包括：
- 学生数据
- 教师数据
- 内容数据（阅读、练习、视频等）
- 词汇数据
- 知识图谱数据
"""
import asyncio
import sys
import os
import random

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models import (
    User, UserRole, Student, ContentType, DifficultyLevel,
    ExamType, Content, Vocabulary, KnowledgeGraph,
    ContentVocabulary, LessonPlan
)
from app.services.conversation_service import ConversationService
from app.models.conversation import ConversationScenario


# 测试数据配置
STUDENT_COUNT = 20
TEACHER_COUNT = 5
CONTENT_COUNT = 50
VOCABULARY_COUNT = 100


# ==================== 学生数据 ====================

STUDENT_TEMPLATES = [
    {"username": "student_a1", "cefr": "A1", "exam": "cet4"},
    {"username": "student_a2", "cefr": "A2", "exam": "cet4"},
    {"username": "student_b1", "cefr": "B1", "exam": "cet4"},
    {"username": "student_b2", "cefr": "B2", "exam": "cet6"},
    {"username": "student_c1", "cefr": "C1", "exam": "ielts"},
    {"username": "student_c2", "cefr": "C2", "exam": "toefl"},
]

# ==================== 教师数据 ====================

TEACHER_TEMPLATES = [
    {"username": "teacher_wang", "name": "王老师"},
    {"username": "teacher_li", "name": "李老师"},
    {"username": "teacher_zhang", "name": "张老师"},
    {"username": "teacher_liu", "name": "刘老师"},
    {"username": "teacher_chen", "name": "陈老师"},
]

# ==================== 内容数据 ====================

CONTENT_TEMPLATES = [
    {
        "title": "Environmental Protection",
        "topic": "environment",
        "content_type": ContentType.READING,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "exam": ExamType.CET4,
        "knowledge_points": ["environment_vocabulary", "present_continuous", "modal_verbs"],
    },
    {
        "title": "Business Email Writing",
        "topic": "business",
        "content_type": ContentType.READING,
        "difficulty": DifficultyLevel.UPPER_INTERMEDIATE,
        "exam": ExamType.CET6,
        "knowledge_points": ["formal_writing", "business_terms", "email_etiquette"],
    },
    {
        "title": "Travel Vocabulary",
        "topic": "travel",
        "content_type": ContentType.VOCABULARY,
        "difficulty": DifficultyLevel.ELEMENTARY,
        "exam": ExamType.GENERAL,
        "knowledge_points": ["travel_terms", "directions", "transportation"],
    },
    {
        "title": "IELTS Speaking Practice",
        "topic": "speaking",
        "content_type": ContentType.VIDEO,
        "difficulty": DifficultyLevel.ADVANCED,
        "exam": ExamType.IELTS,
        "knowledge_points": ["speaking_fluency", "pronunciation", "idioms"],
    },
    {
        "title": "TOEFL Listening Tips",
        "topic": "listening",
        "content_type": ContentType.LISTENING,
        "difficulty": DifficultyLevel.ADVANCED,
        "exam": ExamType.TOEFL,
        "knowledge_points": ["listening_comprehension", "note_taking", "main_ideas"],
    },
    {
        "title": "Grammar: Present Perfect",
        "topic": "grammar",
        "content_type": ContentType.GRAMMAR,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "exam": ExamType.GENERAL,
        "knowledge_points": ["present_perfect", "past_participle", "time_expressions"],
    },
    {
        "title": "Daily Conversations",
        "topic": "daily_life",
        "content_type": ContentType.READING,
        "difficulty": DifficultyLevel.BEGINNER,
        "exam": ExamType.GENERAL,
        "knowledge_points": ["greetings", "introductions", "common_phrases"],
    },
    {
        "title": "Academic Writing Skills",
        "topic": "writing",
        "content_type": ContentType.READING,
        "difficulty": DifficultyLevel.UPPER_INTERMEDIATE,
        "exam": ExamType.IELTS,
        "knowledge_points": ["essay_structure", "academic_language", "cohesion"],
    },
    {
        "title": "News Article Analysis",
        "topic": "current_events",
        "content_type": ContentType.READING,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "exam": ExamType.CET6,
        "knowledge_points": ["news_vocabulary", "skimming", "scanning"],
    },
    {
        "title": "Cultural Differences",
        "topic": "culture",
        "content_type": ContentType.READING,
        "difficulty": DifficultyLevel.INTERMEDIATE,
        "exam": ExamType.GENERAL,
        "knowledge_points": ["cultural_awareness", "comparison", "traditions"],
    },
]

# ==================== 词汇数据 ====================

VOCABULARY_TEMPLATES = [
    {"word": "environment", "phonetic": "/ɪnˈvaɪrənmənt/", "pos": "noun", "cn": "环境", "level": "B1"},
    {"word": "pollution", "phonetic": "/pəˈluːʃn/", "pos": "noun", "cn": "污染", "level": "B1"},
    {"word": "sustainable", "phonetic": "/səˈsteɪnəbl/", "pos": "adj", "cn": "可持续的", "level": "B2"},
    {"word": "renewable", "phonetic": "/rɪˈnjuːəbl/", "pos": "adj", "cn": "可再生的", "level": "B2"},
    {"word": "carbon", "phonetic": "/ˈkɑːrbən/", "pos": "noun", "cn": "碳", "level": "B1"},
    {"word": "emissions", "phonetic": "/iˈmɪʃnz/", "pos": "noun", "cn": "排放", "level": "B2"},
    {"word": "global", "phonetic": "/ˈɡloʊbl/", "pos": "adj", "cn": "全球的", "level": "A2"},
    {"word": "warming", "phonetic": "/ˈwɔːrmɪŋ/", "pos": "noun", "cn": "变暖", "level": "A2"},
    {"word": "business", "phonetic": "/ˈbɪznəs/", "pos": "noun", "cn": "商业", "level": "A2"},
    {"word": "meeting", "phonetic": "/ˈmiːtɪŋ/", "pos": "noun", "cn": "会议", "level": "A1"},
    {"word": "presentation", "phonetic": "/ˌpriːzenˈteɪʃn/", "pos": "noun", "cn": "演示", "level": "B1"},
    {"word": "negotiation", "phonetic": "/nɪˌɡoʊʃiˈeɪʃn/", "pos": "noun", "cn": "谈判", "level": "B2"},
    {"word": "contract", "phonetic": "/ˈkɒntrækt/", "pos": "noun", "cn": "合同", "level": "B2"},
    {"word": "agreement", "phonetic": "/əˈɡriːmənt/", "pos": "noun", "cn": "协议", "level": "B1"},
    {"word": "strategy", "phonetic": "/ˈstrætədʒi/", "pos": "noun", "cn": "策略", "level": "B2"},
    {"word": "analyze", "phonetic": "/ˈænəlaɪz/", "pos": "verb", "cn": "分析", "level": "B2"},
    {"word": "evaluate", "phonetic": "/ɪˈvæljueɪt/", "pos": "verb", "cn": "评估", "level": "C1"},
    {"word": "implement", "phonetic": "/ˈɪmplɪment/", "pos": "verb", "cn": "实施", "level": "B2"},
    {"word": "innovative", "phonetic": "/ˈɪnəveɪtɪv/", "pos": "adj", "cn": "创新的", "level": "C1"},
    {"word": "efficient", "phonetic": "/ɪˈfɪʃnt/", "pos": "adj", "cn": "高效的", "level": "B2"},
    {"word": "collaborate", "phonetic": "/kəˈlæbəreɪt/", "pos": "verb", "cn": "合作", "level": "B2"},
]

# ==================== 知识点图谱数据 ====================

KNOWLEDGE_GRAPH_TEMPLATES = {
    "grammar": {
        "present_perfect": {"name": "现在完成时", "category": "时态", "prerequisites": ["present_simple", "past_simple"]},
        "past_continuous": {"name": "过去进行时", "category": "时态", "prerequisites": ["past_simple"]},
        "conditionals": {"name": "条件句", "category": "语法结构", "prerequisites": ["present_simple", "future_simple"]},
        "passive_voice": {"name": "被动语态", "category": "语态", "prerequisites": ["past_participle"]},
        "reported_speech": {"name": "间接引语", "category": "语法结构", "prerequisites": ["tenses"]},
    },
    "vocabulary": {
        "academic_vocabulary": {"name": "学术词汇", "category": "词汇", "prerequisites": []},
        "business_terms": {"name": "商务术语", "category": "词汇", "prerequisites": []},
        "idioms": {"name": "习语", "category": "词汇", "prerequisites": []},
        "phrasal_verbs": {"name": "短语动词", "category": "词汇", "prerequisites": []},
        "collocations": {"name": "词组搭配", "category": "词汇", "prerequisites": []},
    },
    "skills": {
        "reading_comprehension": {"name": "阅读理解", "category": "技能", "prerequisites": []},
        "listening_comprehension": {"name": "听力理解", "category": "技能", "prerequisites": []},
        "speaking_fluency": {"name": "口语流利度", "category": "技能", "prerequisites": []},
        "writing_coherence": {"name": "写作连贯性", "category": "技能", "prerequisites": []},
        "pronunciation": {"name": "发音", "category": "技能", "prerequisites": []},
    },
}


# ==================== 数据生成函数 ====================

async def hash_password(password: str) -> str:
    """哈希密码"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


async def create_students(db: AsyncSession, count: int = STUDENT_COUNT):
    """创建学生数据"""
    print(f"创建 {count} 个学生...")

    students = []
    for i in range(count):
        template = STUDENT_TEMPLATES[i % len(STUDENT_TEMPLATES)]
        username = f"{template['username']}_{i+1}"

        # 创建用户
        user = User(
            username=username,
            email=f"{username}@example.com",
            password_hash=await hash_password("password123"),
            role=UserRole.STUDENT,
            is_active=True,
        )
        db.add(user)
        await db.flush()

        # 创建学生档案
        student = Student(
            user_id=user.id,
            student_no=f"STU{20240000 + i}",
            grade=f"{(i % 4) + 1}",
            current_cefr_level=template['cefr'],
            target_exam=template['exam'],
            target_score=80 + (i % 20),
            study_goal="提高英语水平",
        )

        # 创建知识图谱
        knowledge_graph = KnowledgeGraph(
            student_id=student.id,
            nodes={},
            edges=[],
            abilities={},
        )

        # 添加随机知识点
        all_kps = list(KNOWLEDGE_GRAPH_TEMPLATES['grammar'].keys()) + \
                  list(KNOWLEDGE_GRAPH_TEMPLATES['vocabulary'].keys()) + \
                  list(KNOWLEDGE_GRAPH_TEMPLATES['skills'].keys())

        nodes = {}
        for kp_id in random.sample(all_kps, min(5, len(all_kp))):
            nodes[kp_id] = {
                "mastery": random.uniform(0.3, 0.9),
                "last_practiced": datetime.utcnow().isoformat(),
            }

        knowledge_graph.nodes = nodes

        db.add(student)
        db.add(knowledge_graph)
        students.append(student)

    await db.commit()
    print(f"  完成！创建了 {len(students)} 个学生")
    return students


async def create_teachers(db: AsyncSession, count: int = TEACHER_COUNT):
    """创建教师数据"""
    print(f"创建 {count} 个教师...")

    teachers = []
    for i in range(count):
        template = TEACHER_TEMPLATES[i % len(TEACHER_TEMPLATES)]
        username = f"{template['username']}_{i+1}"

        user = User(
            username=username,
            email=f"{username}@example.com",
            password_hash=await hash_password("password123"),
            role=UserRole.TEACHER,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        teachers.append(user)

    await db.commit()
    print(f"  完成！创建了 {len(teachers)} 个教师")
    return teachers


async def create_content(db: AsyncSession, count: int = CONTENT_COUNT):
    """创建内容数据"""
    print(f"创建 {count} 个内容...")

    contents = []
    for i in range(count):
        template = CONTENT_TEMPLATES[i % len(CONTENT_TEMPLATES)]

        content = Content(
            title=f"{template['title']} #{i+1}",
            description=f"关于{template['topic']}的学习内容",
            content_type=template['content_type'],
            difficulty_level=template['difficulty'],
            exam_type=template['exam'],
            topic=template['topic'],
            knowledge_points=template['knowledge_points'],
            content_text=f"这是关于{template['topic']}的详细学习内容。包含词汇、语法和练习。" * 10,
            word_count=200 + (i * 10),
            is_published=True,
            view_count=i * 15,
            favorite_count=i // 3,
            tags=[template['topic'], template['exam'].value if template['exam'] else 'general'],
            is_featured=(i % 5 == 0),
            sort_order=count - i,
        )
        db.add(content)
        contents.append(content)

    await db.commit()
    print(f"  完成！创建了 {len(contents)} 个内容")
    return contents


async def create_vocabulary(db: AsyncSession, count: int = VOCABULARY_COUNT):
    """创建词汇数据"""
    print(f"创建 {count} 个词汇...")

    vocabularies = []
    for i in range(count):
        template = VOCABULARY_TEMPLATES[i % len(VOCABULARY_TEMPLATES)]

        vocab = Vocabulary(
            word=template['word'],
            phonetic=template['phonetic'],
            part_of_speech=template['pos'],
            meaning_cn=template['cn'],
            meaning_en=f"English definition for {template['word']}",
            difficulty_level=template['level'],
            frequency=(count - i) * 10,
            example_sentence=f"Here is an example sentence using {template['word']}.",
            example_translation=f"使用{template['cn']}的例句。",
            collocations=[],
            synonyms=[],
            antonyms=[],
            level=template['level'],
        )
        db.add(vocab)
        vocabularies.append(vocab)

    await db.commit()
    print(f"  完成！创建了 {len(vocabularies)} 个词汇")
    return vocabularies


async def create_conversations(db: AsyncSession, student_ids: list):
    """创建对话练习数据"""
    print(f"为 {len(student_ids)} 个学生创建对话练习...")

    conv_service = ConversationService()
    scenarios = list(ConversationScenario)

    import random
    conversations = []

    for student_id in student_ids[:10]:  # 为前10个学生创建对话
        for scenario in random.sample(scenarios, min(3, len(scenarios))):  # 每个学生3个对话
            try:
                conversation = await conv_service.create_conversation(
                    db=db,
                    student_id=str(student_id),
                    scenario=scenario,
                    level=random.choice(["A1", "A2", "B1", "B2", "C1"])
                )

                # 添加一些消息
                await conv_service.send_message(
                    db=db,
                    conversation_id=str(conversation.id),
                    user_message="Hello, I want to practice English."
                )

                conversations.append(conversation)
            except Exception as e:
                print(f"  创建对话失败: {e}")

    await db.commit()
    print(f"  完成！创建了 {len(conversations)} 个对话")
    return conversations


async def main():
    """主函数"""
    print("=" * 50)
    print("AI English Teaching System - 测试数据种子")
    print("=" * 50)

    async with AsyncSessionLocal() as db:
        # 1. 创建学生
        students = await create_students(db, STUDENT_COUNT)

        # 2. 创建教师
        teachers = await create_teachers(db, TEACHER_COUNT)

        # 3. 创建内容
        contents = await create_content(db, CONTENT_COUNT)

        # 4. 创建词汇
        vocabularies = await create_vocabulary(db, VOCABULARY_COUNT)

        # 5. 创建对话
        student_ids = [s.id for s in students]
        await create_conversations(db, student_ids)

    print("\n" + "=" * 50)
    print("测试数据创建完成！")
    print(f"  学生: {STUDENT_COUNT} 个")
    print(f"  教师: {TEACHER_COUNT} 个")
    print(f"  内容: {CONTENT_COUNT} 个")
    print(f"  词汇: {VOCABULARY_COUNT} 个")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
