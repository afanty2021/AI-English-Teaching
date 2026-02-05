"""
简化版API测试
测试运行中的后端服务API端点
"""
import pytest
import asyncio
import aiohttp


BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def auth_token():
    """获取测试认证令牌"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "test_teacher", "password": "Test1234"}
        ) as response:
            data = await response.json()
            return data.get("access_token")


class TestRecommendationAPI:
    """推荐API测试"""

    @pytest.mark.asyncio
    async def test_recommend_endpoint_exists(self, auth_token):
        """测试推荐端点存在"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with session.get(
                f"{BASE_URL}/api/v1/contents/recommend",
                headers=headers
            ) as response:
                assert response.status in [200, 404]  # 200有内容，404无内容

    @pytest.mark.asyncio
    async def test_content_list_endpoint(self, auth_token):
        """测试内容列表端点"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with session.get(
                f"{BASE_URL}/api/v1/contents",
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "total" in data
                assert "items" in data

    @pytest.mark.asyncio
    async def test_content_search_endpoint(self, auth_token):
        """测试内容搜索端点"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with session.get(
                f"{BASE_URL}/api/v1/contents/search",
                params={"query": "test"},
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "results" in data
                assert "total" in data


class TestLessonTemplatesAPI:
    """教案模板API测试"""

    @pytest.mark.asyncio
    async def test_templates_list_endpoint(self, auth_token):
        """测试模板列表端点"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with session.get(
                f"{BASE_URL}/api/v1/lesson-templates",
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "items" in data
                assert "total" in data

    @pytest.mark.asyncio
    async def test_templates_categories_endpoint(self, auth_token):
        """测试模板分类端点"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with session.get(
                f"{BASE_URL}/api/v1/lesson-templates/categories",
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert isinstance(data, list)


class TestLessonExportAPI:
    """教案导出API测试"""

    @pytest.mark.asyncio
    async def test_export_templates_endpoint(self, auth_token):
        """测试导出模板端点"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with session.get(
                f"{BASE_URL}/api/v1/lesson-export/templates",
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "templates" in data
                assert isinstance(data["templates"], list)

    @pytest.mark.asyncio
    async def test_create_export_task(self, auth_token):
        """测试创建导出任务"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with session.post(
                f"{BASE_URL}/api/v1/lesson-export/tasks",
                params={"lesson_id": "00000000-0000-0000-0000-000000000000", "format": "word"},
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "task" in data

    @pytest.mark.asyncio
    async def test_export_tasks_list(self, auth_token):
        """测试导出任务列表"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {auth_token}"}
            async with session.get(
                f"{BASE_URL}/api/v1/lesson-export/tasks",
                headers=headers
            ) as response:
                assert response.status == 200
                data = await response.json()
                assert "tasks" in data
                assert "total" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
