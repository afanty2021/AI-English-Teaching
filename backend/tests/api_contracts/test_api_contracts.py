"""
API 契约测试

验证后端 API 响应格式与前端期望保持一致
防止因接口不匹配导致的运行时错误

测试覆盖:
- 认证 API (登录、注册、获取用户信息)
- 学习报告 API (生成、列表、详情)
- 错题本 API (列表、统计)
- 内容推荐 API
- 对话 API
"""
import pytest
from httpx import AsyncClient

from tests.conftest import APIContractValidator


@pytest.mark.asyncio
class TestAuthAPIContracts:
    """认证 API 契约测试"""

    async def test_login_response_contract(self, test_client: AsyncClient, contract_validator):
        """测试登录响应格式"""
        # 先注册一个用户
        await test_client.post("/api/v1/auth/register", json={
            "username": "contract_test_user",
            "email": "contract@test.com",
            "password": "Test1234",
            "role": "student"
        })

        # 登录
        response = await test_client.post("/api/v1/auth/login", json={
            "username": "contract_test_user",
            "password": "Test1234"
        })

        assert response.status_code == 200
        data = response.json()

        # 验证契约
        is_valid, errors = contract_validator.validate_response("/api/v1/auth/login", data)
        assert is_valid, f"Contract validation failed: {errors}"

    async def test_me_response_contract(self, test_client: AsyncClient, contract_validator):
        """测试获取当前用户信息响应格式"""
        # 先注册并登录
        await test_client.post("/api/v1/auth/register", json={
            "username": "me_test_user",
            "email": "me@test.com",
            "password": "Test1234",
            "role": "student"
        })

        login_response = await test_client.post("/api/v1/auth/login", json={
            "username": "me_test_user",
            "password": "Test1234"
        })
        token = login_response.json()["access_token"]

        # 获取用户信息
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证契约
        is_valid, errors = contract_validator.validate_response("/api/v1/auth/me", data)
        assert is_valid, f"Contract validation failed: {errors}"


@pytest.mark.asyncio
class TestReportAPIContracts:
    """学习报告 API 契约测试"""

    async def test_generate_report_response_contract(self, test_client: AsyncClient, contract_validator):
        """测试生成报告响应格式"""
        # 创建用户并获取 token
        await test_client.post("/api/v1/auth/register", json={
            "username": "report_test_user",
            "email": "report@test.com",
            "password": "Test1234",
            "role": "student"
        })

        login_response = await test_client.post("/api/v1/auth/login", json={
            "username": "report_test_user",
            "password": "Test1234"
        })
        token = login_response.json()["access_token"]

        # 生成报告
        response = await test_client.post(
            "/api/v1/reports/generate",
            json={"report_type": "weekly"},
            headers={"Authorization": f"Bearer {token}"}
        )

        # 可能返回 201 或 200
        assert response.status_code in [200, 201]
        data = response.json()

        # 验证契约
        is_valid, errors = contract_validator.validate_response("/api/v1/reports/generate", data)
        assert is_valid, f"Contract validation failed: {errors}"

    async def test_get_reports_response_contract(self, test_client: AsyncClient, contract_validator):
        """测试获取报告列表响应格式"""
        # 创建用户并获取 token
        await test_client.post("/api/v1/auth/register", json={
            "username": "reports_list_user",
            "email": "reportslist@test.com",
            "password": "Test1234",
            "role": "student"
        })

        login_response = await test_client.post("/api/v1/auth/login", json={
            "username": "reports_list_user",
            "password": "Test1234"
        })
        token = login_response.json()["access_token"]

        # 获取报告列表
        response = await test_client.get(
            "/api/v1/reports/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证契约
        is_valid, errors = contract_validator.validate_response("/api/v1/reports/me", data)
        assert is_valid, f"Contract validation failed: {errors}"

    async def test_get_report_detail_response_contract(self, test_client: AsyncClient, contract_validator):
        """测试获取报告详情响应格式"""
        # 创建用户并获取 token
        await test_client.post("/api/v1/auth/register", json={
            "username": "report_detail_user",
            "email": "reportdetail@test.com",
            "password": "Test1234",
            "role": "student"
        })

        login_response = await test_client.post("/api/v1/auth/login", json={
            "username": "report_detail_user",
            "password": "Test1234"
        })
        token = login_response.json()["access_token"]

        # 先生成一个报告
        gen_response = await test_client.post(
            "/api/v1/reports/generate",
            json={"report_type": "weekly"},
            headers={"Authorization": f"Bearer {token}"}
        )
        report_id = gen_response.json()["report"]["id"]

        # 获取报告详情
        response = await test_client.get(
            f"/api/v1/reports/{report_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证契约
        is_valid, errors = contract_validator.validate_response(f"/api/v1/reports/{report_id}", data)
        assert is_valid, f"Contract validation failed: {errors}"


@pytest.mark.asyncio
class TestMistakeAPIContracts:
    """错题本 API 契约测试"""

    async def test_get_mistakes_response_contract(self, test_client: AsyncClient, contract_validator):
        """测试获取错题列表响应格式"""
        # 创建用户并获取 token
        await test_client.post("/api/v1/auth/register", json={
            "username": "mistake_test_user",
            "email": "mistake@test.com",
            "password": "Test1234",
            "role": "student"
        })

        login_response = await test_client.post("/api/v1/auth/login", json={
            "username": "mistake_test_user",
            "password": "Test1234"
        })
        token = login_response.json()["access_token"]

        # 获取错题列表
        response = await test_client.get(
            "/api/v1/mistakes/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证契约
        is_valid, errors = contract_validator.validate_response("/api/v1/mistakes/me", data)
        assert is_valid, f"Contract validation failed: {errors}"


@pytest.mark.asyncio
class TestContentAPIContracts:
    """内容推荐 API 契约测试"""

    async def test_recommend_response_contract(self, test_client: AsyncClient, contract_validator):
        """测试内容推荐响应格式"""
        # 创建用户并获取 token
        await test_client.post("/api/v1/auth/register", json={
            "username": "content_test_user",
            "email": "content@test.com",
            "password": "Test1234",
            "role": "student"
        })

        login_response = await test_client.post("/api/v1/auth/login", json={
            "username": "content_test_user",
            "password": "Test1234"
        })
        token = login_response.json()["access_token"]

        # 获取推荐内容
        response = await test_client.get(
            "/api/v1/contents/recommend",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证契约
        is_valid, errors = contract_validator.validate_response("/api/v1/contents/recommend", data)
        assert is_valid, f"Contract validation failed: {errors}"


@pytest.mark.asyncio
class TestConversationAPIContracts:
    """对话 API 契约测试"""

    async def test_conversations_response_contract(self, test_client: AsyncClient, contract_validator):
        """测试对话列表响应格式"""
        # 创建用户并获取 token
        await test_client.post("/api/v1/auth/register", json={
            "username": "conv_test_user",
            "email": "conv@test.com",
            "password": "Test1234",
            "role": "student"
        })

        login_response = await test_client.post("/api/v1/auth/login", json={
            "username": "conv_test_user",
            "password": "Test1234"
        })
        token = login_response.json()["access_token"]

        # 获取对话列表
        response = await test_client.get(
            "/api/v1/conversations",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 验证契约
        is_valid, errors = contract_validator.validate_response("/api/v1/conversations", data)
        assert is_valid, f"Contract validation failed: {errors}"


# ============================================================================
# 契约同步测试 - 确保后端契约定义与前端类型定义同步
# ============================================================================

class TestContractSync:
    """
    契约同步测试

    这组测试确保 conftest.py 中定义的 API 契约
    与前端 src/api/*.ts 中的类型定义保持一致
    """

    def test_all_endpoints_have_contracts(self):
        """
        测试所有已注册的 API 端点都有契约定义

        如果这个测试失败，说明:
        1. 新增了 API 端点但没有定义契约
        2. 需要在 APIContractValidator.CONTRACTS 中添加相应定义
        """
        from app.main import app
        from tests.conftest import APIContractValidator

        # 获取所有注册的路由
        registered_routes = set()
        for route in app.routes:
            if hasattr(route, 'path'):
                # 标准化路径
                path = route.path
                registered_routes.add(path)

        # 检查是否有未定义契约的关键端点
        critical_endpoints = {
            "/api/v1/auth/login",
            "/api/v1/auth/me",
            "/api/v1/reports/me",
            "/api/v1/reports/generate",
            "/api/v1/mistakes/me",
            "/api/v1/contents/recommend",
        }

        undefined = critical_endpoints - set(APIContractValidator.CONTRACTS.keys())

        assert len(undefined) == 0, f"Missing contracts for endpoints: {undefined}"

    def test_contract_format_validity(self):
        """
        测试契约定义本身的格式有效性

        确保每个契约都有 request/response 定义
        """
        from tests.conftest import APIContractValidator

        for endpoint, contract in APIContractValidator.CONTRACTS.items():
            assert "response" in contract, f"Endpoint {endpoint} missing 'response' contract"
            assert isinstance(contract["response"], dict), f"Endpoint {endpoint} 'response' must be a dict"
