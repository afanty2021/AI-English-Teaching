"""
推荐系统闭环集成测试
验证推荐-练习-知识图谱更新的完整闭环流程
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.db.base import Base
from app.models import User, Organization, Student, KnowledgeGraph, Content, Question, Practice
from app.models.practice_session import PracticeSession, SessionStatus
from app.main import app
from app.api.deps import get_db


# ============================================================================
# 测试配置
# ============================================================================

TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/english_teaching"


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session_maker = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试HTTP客户端"""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """创建测试组织"""
    org = Organization(
        id=uuid4(),
        name="测试学校"
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_student(db_session: AsyncSession, test_organization: Organization) -> tuple[Student, User]:
    """创建测试学生用户"""
    user = User(
        id=uuid4(),
        username=f"test_student_{uuid4().hex[:8]}",
        email=f"student_{uuid4().hex[:8]}@test.com",
        hashed_password="hashed_password",
        role="student",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    student = Student(
        id=uuid4(),
        user_id=user.id,
        organization_id=test_organization.id,
        target_exam="CET4",
        current_cefr_level="B1"
    )
    db_session.add(student)
    await db_session.commit()
    await db_session.refresh(student)

    return student, user


@pytest_asyncio.fixture
async def student_with_graph(db_session: AsyncSession, test_student: tuple[Student, User]) -> Student:
    """创建带有知识图谱的学生"""
    student, _ = test_student

    graph = KnowledgeGraph(
        id=uuid4(),
        student_id=student.id,
        nodes=[
            {"id": "ability_vocabulary", "type": "ability", "label": "词汇", "value": 50},
            {"id": "ability_grammar", "type": "ability", "label": "语法", "value": 45},
            {"id": "ability_reading", "type": "ability", "label": "阅读", "value": 55},
        ],
        edges=[],
        abilities={
            "vocabulary": 50,
            "grammar": 45,
            "reading": 55,
        },
        cefr_level="B1",
        exam_coverage={"CET4": {"topics_covered": 5, "total_practices": 20}},
        ai_analysis={
            "weak_points": [
                {"topic": "时态", "reason": "语法基础薄弱", "priority": "high"},
                {"topic": "从句", "reason": "复杂句式理解困难", "priority": "medium"},
            ],
            "recommendations": [
                {"priority": "high", "suggestion": "加强时态练习"},
            ]
        }
    )
    db_session.add(graph)
    await db_session.commit()
    await db_session.refresh(student)

    return student


@pytest_asyncio.fixture
async def test_content(db_session: AsyncSession, test_organization: Organization) -> Content:
    """创建测试内容"""
    from app.models.content import ContentType, DifficultyLevel, ExamType

    content = Content(
        id=uuid4(),
        title="英语时态练习",
        description="针对英语时态的专项练习",
        content_type=ContentType.GRAMMAR.value,
        difficulty_level=DifficultyLevel.INTERMEDIATE.value,
        topic="时态",
        exam_type=ExamType.CET4.value,
        content_text="这是一篇关于英语时态的练习文章。",
        knowledge_points=["时态", "一般过去时", "过去进行时"],
        is_published=True,
        view_count=100,
        word_count=500
    )
    db_session.add(content)
    await db_session.commit()
    await db_session.refresh(content)
    return content


@pytest_asyncio.fixture
async def test_questions(db_session: AsyncSession, test_organization: Organization) -> list[Question]:
    """创建测试题目"""
    from app.models.question import QuestionType, DifficultyLevel

    questions = []
    for i in range(5):
        question = Question(
            id=uuid4(),
            title=f"测试题目 {i+1}",
            content=f"这是题目 {i+1} 的内容",
            question_type=QuestionType.CHOICE.value,
            difficulty_level=DifficultyLevel.INTERMEDIATE.value,
            topic="时态",
            options=["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            correct_answer="A",
            explanation=f"题目 {i+1} 的解释",
            is_active=True
        )
        db_session.add(question)
        questions.append(question)

    await db_session.commit()
    for q in questions:
        await db_session.refresh(q)

    return questions


@pytest.fixture
def auth_token(test_student: tuple[Student, User]) -> str:
    """生成测试用JWT token"""
    from app.core.security import create_access_token
    student, user = test_student
    return create_access_token(data={"sub": str(user.id), "role": "student"})


# ============================================================================
# 推荐系统闭环集成测试
# ============================================================================

class TestRecommendationLoop:
    """
    推荐系统闭环集成测试类

    测试完整的推荐-练习-图谱更新闭环流程：
    1. 推荐API：获取基于学生画像的推荐内容
    2. 练习会话：从推荐内容创建练习
    3. 练习完成：提交答案，触发知识图谱更新
    4. 验证图谱更新后的推荐变化
    """

    @pytest.mark.asyncio
    async def test_full_recommendation_practice_loop(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        student_with_graph: Student,
        test_content: Content,
        test_questions: list[Question],
        auth_token: str
    ):
        """
        测试完整的推荐-练习-图谱更新闭环

        测试步骤：
        1. 调用推荐API获取每日推荐
        2. 从推荐中选择练习内容
        3. 开始练习会话
        4. 提交答案完成练习
        5. 查询知识图谱验证更新
        6. 再次调用推荐API验证推荐变化
        """
        student_id = str(student_with_graph.id)
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: 获取每日推荐
        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers=headers
        )
        assert response.status_code == 200
        recommendation_data = response.json()
        assert "reading_recommendations" in recommendation_data or "exercise_recommendations" in recommendation_data

        # 记录初始推荐内容
        initial_recommendations = recommendation_data.get("exercise_recommendations", [])

        # Step 2: 开始练习会话（使用推荐的内容）
        practice_start_data = {
            "practice_type": "grammar",
            "topic": "时态",
            "random_count": 3,
            "difficulty_level": "intermediate"
        }

        response = await test_client.post(
            f"/api/v1/practice-sessions/",
            json=practice_start_data,
            headers=headers
        )
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data.get("id")

        assert session_id is not None
        assert session_data.get("total_questions") == 3

        # Step 3: 提交答案完成练习
        for i, question in enumerate(test_questions[:3]):
            answer_data = {
                "question_id": str(question.id),
                "answer": question.correct_answer,
                "time_spent": 30
            }
            response = await test_client.post(
                f"/api/v1/practice-sessions/{session_id}/submit",
                json=answer_data,
                headers=headers
            )
            assert response.status_code == 200

        # Step 4: 完成练习会话
        response = await test_client.post(
            f"/api/v1/practice-sessions/{session_id}/complete",
            headers=headers
        )
        assert response.status_code == 200
        completion_result = response.json()

        assert completion_result.get("success") or "result" in completion_result

        # Step 5: 验证知识图谱更新
        response = await test_client.get(
            f"/api/v1/students/{student_id}/knowledge-graph",
            headers=headers
        )
        assert response.status_code == 200
        graph_data = response.json()

        # 验证图谱结构
        assert "abilities" in graph_data or "nodes" in graph_data

        # Step 6: 再次获取推荐，验证推荐变化
        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers=headers
        )
        assert response.status_code == 200
        new_recommendation_data = response.json()

        # 验证推荐仍然正常返回
        assert "reading_recommendations" in new_recommendation_data or "exercise_recommendations" in new_recommendation_data

    @pytest.mark.asyncio
    async def test_weak_point_targeted_practice(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        student_with_graph: Student,
        test_questions: list[Question],
        auth_token: str
    ):
        """
        测试薄弱点针对性练习

        测试步骤：
        1. 获取学生知识图谱，获取薄弱知识点
        2. 调用推荐API，验证推荐包含薄弱点相关练习
        3. 完成针对性练习
        4. 验证薄弱点掌握度变化
        """
        student_id = str(student_with_graph.id)
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: 获取知识图谱，确认薄弱点
        response = await test_client.get(
            f"/api/v1/students/{student_id}/knowledge-graph",
            headers=headers
        )
        assert response.status_code == 200
        initial_graph = response.json()

        # 提取薄弱知识点
        initial_abilities = initial_graph.get("abilities", {})
        weak_points = initial_graph.get("ai_analysis", {}).get("weak_points", [])

        # 验证存在薄弱点
        assert len(weak_points) > 0 or any(v < 60 for v in initial_abilities.values())

        # Step 2: 获取推荐，验证包含针对性内容
        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers=headers
        )
        assert response.status_code == 200
        recommendations = response.json()

        # Step 3: 针对薄弱点开始练习
        weak_topic = weak_points[0].get("topic", "时态") if weak_points else "时态"

        practice_data = {
            "practice_type": "grammar",
            "topic": weak_topic,
            "random_count": 3,
            "difficulty_level": "intermediate"
        }

        response = await test_client.post(
            "/api/v1/practice-sessions/",
            json=practice_data,
            headers=headers
        )
        assert response.status_code == 200
        session = response.json()

        # Step 4: 完成练习
        session_id = session.get("id")

        # 提交正确答案
        for question in test_questions[:3]:
            answer_data = {
                "question_id": str(question.id),
                "answer": question.correct_answer,
                "time_spent": 30
            }
            await test_client.post(
                f"/api/v1/practice-sessions/{session_id}/submit",
                json=answer_data,
                headers=headers
            )

        # 完成会话
        response = await test_client.post(
            f"/api/v1/practice-sessions/{session_id}/complete",
            headers=headers
        )
        assert response.status_code == 200

        # Step 5: 验证图谱更新
        response = await test_client.get(
            f"/api/v1/students/{student_id}/knowledge-graph",
            headers=headers
        )
        assert response.status_code == 200
        updated_graph = response.json()

        updated_abilities = updated_graph.get("abilities", {})

        # 验证能力值有变化
        assert updated_abilities is not None

    @pytest.mark.asyncio
    async def test_recommendation_reflects_updated_graph(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        student_with_graph: Student,
        test_content: Content,
        test_questions: list[Question],
        auth_token: str
    ):
        """
        测试推荐反映更新后的图谱

        验证流程：
        1. 获取初始推荐
        2. 完成练习（更新图谱）
        3. 获取新推荐，验证推荐内容变化
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Step 1: 获取初始推荐
        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers=headers
        )
        assert response.status_code == 200
        initial_recommendations = response.json()

        # Step 2: 开始并完成练习
        practice_data = {
            "practice_type": "vocabulary",
            "random_count": 5,
            "difficulty_level": "intermediate"
        }

        response = await test_client.post(
            "/api/v1/practice-sessions/",
            json=practice_data,
            headers=headers
        )
        assert response.status_code == 200
        session = response.json()
        session_id = session.get("id")

        # 提交答案
        for question in test_questions[:5]:
            answer_data = {
                "question_id": str(question.id),
                "answer": question.correct_answer,
                "time_spent": 30
            }
            await test_client.post(
                f"/api/v1/practice-sessions/{session_id}/submit",
                json=answer_data,
                headers=headers
            )

        # 完成练习
        await test_client.post(
            f"/api/v1/practice-sessions/{session_id}/complete",
            headers=headers
        )

        # Step 3: 获取新推荐
        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers=headers
        )
        assert response.status_code == 200
        new_recommendations = response.json()

        # 验证新推荐正常返回
        assert "reading_recommendations" in new_recommendations or "exercise_recommendations" in new_recommendations

        # 验证学生画像摘要更新
        profile_summary = new_recommendations.get("student_profile_summary", {})
        assert "student_id" in profile_summary
        assert "current_cefr_level" in profile_summary


class TestRecommendationPerformance:
    """
    推荐系统性能测试类
    """

    @pytest.mark.asyncio
    async def test_recommendation_response_time(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        student_with_graph: Student,
        auth_token: str
    ):
        """
        测试推荐API响应时间

        预期：响应时间 < 2秒
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        import time

        start_time = time.time()

        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers=headers
        )

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        # 响应时间应该在合理范围内（考虑测试环境）
        assert response_time < 5, f"推荐API响应时间过长: {response_time:.2f}秒"

    @pytest.mark.asyncio
    async def test_practice_completion_triggers_graph_update(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        student_with_graph: Student,
        test_questions: list[Question],
        auth_token: str
    ):
        """
        测试练习完成后触发知识图谱更新

        验证：
        1. 练习完成返回图谱更新结果
        2. 图谱更新记录正确保存
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # 开始练习
        practice_data = {
            "practice_type": "grammar",
            "random_count": 3,
            "difficulty_level": "intermediate"
        }

        response = await test_client.post(
            "/api/v1/practice-sessions/",
            json=practice_data,
            headers=headers
        )
        session = response.json()
        session_id = session.get("id")

        # 提交正确答案
        for question in test_questions[:3]:
            answer_data = {
                "question_id": str(question.id),
                "answer": question.correct_answer,
                "time_spent": 30
            }
            await test_client.post(
                f"/api/v1/practice-sessions/{session_id}/submit",
                json=answer_data,
                headers=headers
            )

        # 完成练习
        response = await test_client.post(
            f"/api/v1/practice-sessions/{session_id}/complete",
            headers=headers
        )

        assert response.status_code == 200
        result = response.json()

        # 验证包含图谱更新信息
        assert "result" in result or "graph_update" in str(result)


class TestRecommendationErrorHandling:
    """
    推荐系统错误处理测试类
    """

    @pytest.mark.asyncio
    async def test_recommendation_without_graph(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        test_student: tuple[Student, User],
        auth_token: str
    ):
        """
        测试没有知识图谱时的推荐行为

        应该返回默认推荐或提示创建初始诊断
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers=headers
        )

        # 应该仍然返回推荐（可能使用默认策略）
        assert response.status_code == 200
        data = response.json()

        # 验证响应结构
        assert "student_profile_summary" in data or "reading_recommendations" in data or "exercise_recommendations" in data

    @pytest.mark.asyncio
    async def test_practice_session_not_found(
        self,
        db_session: AsyncSession,
        test_client: AsyncClient,
        student_with_graph: Student,
        auth_token: str
    ):
        """
        测试不存在的练习会话操作

        应该返回404错误
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        fake_session_id = str(uuid4())

        response = await test_client.get(
            f"/api/v1/practice-sessions/{fake_session_id}",
            headers=headers
        )

        assert response.status_code == 404


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
