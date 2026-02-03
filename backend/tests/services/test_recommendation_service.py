"""
测试内容推荐服务
"""
import asyncio
import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Content, Student, User, ContentType, DifficultyLevel, ExamType
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import StudentProfile, RecommendationFilter


@pytest.mark.asyncio
async def test_get_student_profile(db: AsyncSession):
    """测试获取学生画像"""
    # 创建测试用户和学生
    user_id = uuid4()

    user = User(
        id=user_id,
        username="test_profile_user",
        email="test_profile@example.com",
        password_hash="hash",
        role="student",
        is_active=True
    )
    db.add(user)

    student = Student(
        id=uuid4(),
        user_id=user_id,
        target_exam="cet4",
        target_score=500,
        current_cefr_level="B1"
    )
    db.add(student)
    await db.commit()

    # 测试获取学生画像
    profile = await RecommendationService.get_student_profile(
        db=db_session,
        student_id=student.id
    )

    assert profile.student_id == student.id
    assert profile.target_exam == "cet4"
    assert profile.current_cefr_level == "B1"


@pytest.mark.asyncio
async def test_recommend_daily_basic(db: AsyncSession):
    """测试基础每日推荐功能"""
    # 创建测试学生
    user_id = uuid4()

    user = User(
        id=user_id,
        username="test_recommend_user",
        email="test_recommend@example.com",
        password_hash="hash",
        role="student",
        is_active=True
    )
    db.add(user)

    student = Student(
        id=uuid4(),
        user_id=user_id,
        target_exam="cet4",
        current_cefr_level="B1"
    )
    db.add(student)
    await db.commit()

    # 创建测试内容
    contents = [
        Content(
            title="Test Reading Content",
            content_type=ContentType.READING.value,
            difficulty_level=DifficultyLevel.INTERMEDIATE.value,
            exam_type="cet4",
            topic="test",
            is_published=True,
            word_count=500
        ),
        Content(
            title="Test Grammar Content",
            content_type=ContentType.GRAMMAR.value,
            difficulty_level=DifficultyLevel.INTERMEDIATE.value,
            exam_type="cet4",
            topic="grammar",
            is_published=True,
            word_count=300
        )
    ]

    for content in contents:
        db.add(content)
    await db.commit()

    # 测试推荐
    recommendations = await RecommendationService.recommend_daily(
        db=db_session,
        student_id=student.id
    )

    assert recommendations is not None
    assert hasattr(recommendations, 'reading_recommendations')
    assert hasattr(recommendations, 'exercise_recommendations')
    assert hasattr(recommendations, 'daily_goals')
    assert recommendations.total_recommendations >= 0


@pytest.mark.asyncio
async def test_recommend_with_filter(db: AsyncSession):
    """测试带过滤条件的推荐"""
    # 创建测试学生
    user_id = uuid4()

    user = User(
        id=user_id,
        username="test_filter_user",
        email="test_filter@example.com",
        password_hash="hash",
        role="student",
        is_active=True
    )
    db.add(user)

    student = Student(
        id=uuid4(),
        user_id=user_id,
        target_exam="cet4",
        current_cefr_level="B1"
    )
    db.add(student)

    # 创建不同类型和难度的测试内容
    contents = [
        Content(
            title=f"Content {i}",
            content_type=ContentType.READING.value if i % 2 == 0 else ContentType.GRAMMAR.value,
            difficulty_level=DifficultyLevel.INTERMEDIATE.value if i % 3 == 0 else DifficultyLevel.ELEMENTARY.value,
            exam_type="cet4",
            topic="test",
            is_published=True,
            word_count=200 + i * 50
        )
        for i in range(10)
    ]

    for content in contents:
        db.add(content)
    await db.commit()

    # 测试带类型过滤的推荐
    filter_params = RecommendationFilter(
        content_types=[ContentType.READING.value],
        max_recommendations=5
    )

    recommendations = await RecommendationService.recommend_daily(
        db=db_session,
        student_id=student.id,
        filter_params=filter_params
    )

    # 验证只返回阅读类型的内容
    for rec in recommendations.reading_recommendations:
        assert rec is not None


@pytest.mark.asyncio
async def test_i_plus_one_difficulty(db: AsyncSession):
    """测试 i+1 理论的难度控制"""
    # 测试不同 CEFR 级别的难度范围计算
    test_cases = [
        ("A1", [DifficultyLevel.BEGINNER.value, DifficultyLevel.ELEMENTARY.value]),
        ("A2", [DifficultyLevel.ELEMENTARY.value, DifficultyLevel.INTERMEDIATE.value]),
        ("B1", [DifficultyLevel.INTERMEDIATE.value, DifficultyLevel.UPPER_INTERMEDIATE.value]),
        ("B2", [DifficultyLevel.UPPER_INTERMEDIATE.value, DifficultyLevel.ADVANCED.value]),
        ("C1", [DifficultyLevel.ADVANCED.value, DifficultyLevel.PROFICIENT.value]),
    ]

    for cefr_level, expected_levels in test_cases:
        profile = StudentProfile(
            student_id=uuid4(),
            current_cefr_level=cefr_level,
            target_exam="cet4",
            weak_points=[],
            mastered_points=[],
            learning_points=[]
        )

        target_difficulty = RecommendationService._get_target_difficulty(profile)
        difficulty_range = RecommendationService._get_i_plus_one_range(target_difficulty)

        assert all(level in difficulty_range for level in expected_levels)


@pytest.mark.asyncio
async def test_recommendation_score_calculation(db: AsyncSession):
    """测试推荐分数计算"""
    content = Content(
        title="Test Content",
        content_type=ContentType.READING.value,
        difficulty_level=DifficultyLevel.INTERMEDIATE.value,
        exam_type="cet4",
        topic="environment",
        knowledge_points=["environment", "pollution"],
        is_published=True,
        is_featured=True,
        word_count=500
    )

    profile = StudentProfile(
        student_id=uuid4(),
        current_cefr_level="B1",
        target_exam="cet4",
        weak_points=["pollution"],
        mastered_points=[],
        learning_points=["environment"]
    )

    score = await RecommendationService._calculate_recommendation_score(
        content=content,
        profile=profile
    )

    assert 0 <= score <= 100
    assert score > 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
