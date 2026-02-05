"""
推荐系统API测试
测试内容推荐、反馈、历史、统计等端点
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime

from app.models import User, Student, Organization, Content
from app.core.security import create_access_token


class TestContentRecommendationAPI:
    """内容推荐API测试"""

    @pytest.mark.asyncio
    async def test_get_recommendations(
        self, test_client, test_student, db
    ):
        """测试获取每日推荐"""
        # 确保测试内容存在
        content = Content(
            id=uuid4(),
            title="Test Reading Article",
            description="A test reading article",
            content_type="reading",
            difficulty_level="intermediate",
            topic="technology",
            content_text="This is a test article.",
            is_published=True,
            view_count=10
        )
        db.add(content)
        await db.commit()

        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "reading" in data or "reading_recommendations" in data

    @pytest.mark.asyncio
    async def test_get_content_detail(
        self, test_client, test_student, db
    ):
        """测试获取内容详情"""
        content = Content(
            id=uuid4(),
            title="Test Reading Article",
            description="A test reading article",
            content_type="reading",
            difficulty_level="intermediate",
            topic="technology",
            content_text="This is a test article.",
            is_published=True,
            view_count=10
        )
        db.add(content)
        await db.commit()

        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            f"/api/v1/contents/{content.id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Reading Article"
        assert data["content_type"] == "reading"

    @pytest.mark.asyncio
    async def test_get_content_detail_not_found(self, test_client, test_student):
        """测试获取不存在的内容"""
        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        fake_id = str(uuid4())
        response = await test_client.get(
            f"/api/v1/contents/{fake_id}",
            headers=headers
        )
        assert response.status_code == 404


class TestContentCompletionAPI:
    """内容完成API测试"""

    @pytest.mark.asyncio
    async def test_mark_content_complete(
        self, test_client, test_student, db
    ):
        """测试标记内容完成"""
        content = Content(
            id=uuid4(),
            title="Test Reading Article",
            description="A test reading article",
            content_type="reading",
            difficulty_level="intermediate",
            topic="technology",
            content_text="This is a test article.",
            is_published=True
        )
        db.add(content)
        await db.commit()

        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/contents/complete",
            json={
                "content_id": str(content.id),
                "content_type": "reading",
                "completed_at": datetime.utcnow().isoformat(),
                "time_spent": 300
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "earned_points" in data


class TestFeedbackAPI:
    """推荐反馈API测试"""

    @pytest.mark.asyncio
    async def test_submit_feedback(
        self, test_client, test_student, db
    ):
        """测试提交反馈"""
        content = Content(
            id=uuid4(),
            title="Test Reading Article",
            description="A test reading article",
            content_type="reading",
            difficulty_level="intermediate",
            topic="technology",
            content_text="This is a test article.",
            is_published=True
        )
        db.add(content)
        await db.commit()

        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/contents/feedback",
            json={
                "content_id": str(content.id),
                "satisfaction": 4,
                "reason": "内容很有帮助",
                "feedback_type": "recommendation"
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True

    @pytest.mark.asyncio
    async def test_submit_feedback_invalid_rating(
        self, test_client, test_student, db
    ):
        """测试提交无效评分"""
        content = Content(
            id=uuid4(),
            title="Test Reading Article",
            content_type="reading",
            difficulty_level="intermediate",
            content_text="This is a test article.",
            is_published=True
        )
        db.add(content)
        await db.commit()

        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.post(
            "/api/v1/contents/feedback",
            json={
                "content_id": str(content.id),
                "satisfaction": 10,  # 无效评分
                "reason": "test"
            },
            headers=headers
        )
        assert response.status_code == 422  # 验证错误


class TestRecommendationHistoryAPI:
    """推荐历史API测试"""

    @pytest.mark.asyncio
    async def test_get_history(
        self, test_client, test_student, db
    ):
        """测试获取推荐历史"""
        from app.models.recommendation import RecommendationHistory

        content = Content(
            id=uuid4(),
            title="Test Reading Article",
            content_type="reading",
            difficulty_level="intermediate",
            content_text="This is a test article.",
            is_published=True
        )
        db.add(content)
        await db.commit()

        # 创建历史记录
        history = RecommendationHistory(
            user_id=test_student.id,
            content_id=content.id,
            content_type="reading"
        )
        db.add(history)
        await db.commit()

        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/contents/recommend/history",
            params={"page": 1, "limit": 20},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert "has_more" in data


class TestRecommendationStatsAPI:
    """推荐统计API测试"""

    @pytest.mark.asyncio
    async def test_get_stats(
        self, test_client, test_student
    ):
        """测试获取推荐统计"""
        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/contents/recommend/stats",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_recommendations" in data
        assert "completion_rate" in data
        assert "average_satisfaction" in data
        assert "most_popular_topics" in data
        assert "improvement_areas" in data


class TestRecommendationPreferencesAPI:
    """推荐偏好API测试"""

    @pytest.mark.asyncio
    async def test_update_preferences(
        self, test_client, test_student
    ):
        """测试更新推荐偏好"""
        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.put(
            "/api/v1/contents/recommend/preferences",
            json={
                "preferred_topics": ["technology", "science"],
                "preferred_content_types": ["reading", "listening"],
                "difficulty_preference": "same",
                "study_time_preference": 60
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "preferred_topics" in data


class TestContentSearchAPI:
    """内容搜索API测试"""

    @pytest.mark.asyncio
    async def test_search_contents(
        self, test_client, test_student, db
    ):
        """测试搜索内容"""
        content = Content(
            id=uuid4(),
            title="Technology Article",
            description="An article about technology",
            content_type="reading",
            difficulty_level="intermediate",
            topic="technology",
            content_text="This is a tech article.",
            is_published=True
        )
        db.add(content)
        await db.commit()

        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/contents/search",
            params={
                "query": "technology",
                "content_type": "reading"
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert "query" in data


class TestContentListAPI:
    """内容列表API测试"""

    @pytest.mark.asyncio
    async def test_list_contents(
        self, test_client, test_student, db
    ):
        """测试获取内容列表"""
        content = Content(
            id=uuid4(),
            title="Test Reading Article",
            description="A test reading article",
            content_type="reading",
            difficulty_level="intermediate",
            topic="technology",
            content_text="This is a test article.",
            is_published=True,
            view_count=10
        )
        db.add(content)
        await db.commit()

        token = create_access_token(data={"sub": str(test_student.user_id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await test_client.get(
            "/api/v1/contents",
            params={
                "content_type": "reading",
                "skip": 0,
                "limit": 20
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert "skip" in data
        assert "limit" in data
