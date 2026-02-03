"""
认证API测试
测试注册、登录、获取用户信息等认证相关端点
"""
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.main import app
from app.api.deps import get_db


@pytest.fixture
async def async_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建异步HTTP客户端用于测试

    使用dependency override注入测试数据库会话
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestAuthAPI:
    """认证API测试类"""

    async def test_register_user(self, async_client: AsyncClient):
        """
        测试用户注册API

        验证：
        - 注册成功返回201状态码
        - 返回用户信息和token
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123",
                "full_name": "Test User",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["role"] == "student"

    async def test_register_duplicate_username(self, async_client: AsyncClient):
        """
        测试重复用户名注册

        验证：
        - 返回400错误
        - 错误信息正确
        """
        # 第一次注册
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "user1@example.com",
                "password": "TestPass123",
            }
        )

        # 第二次注册相同用户名
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "user2@example.com",
                "password": "TestPass123",
            }
        )

        assert response.status_code == 400
        assert "用户名已被使用" in response.json()["detail"]

    async def test_register_duplicate_email(self, async_client: AsyncClient):
        """
        测试重复邮箱注册

        验证：
        - 返回400错误
        - 错误信息正确
        """
        # 第一次注册
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "password": "TestPass123",
            }
        )

        # 第二次注册相同邮箱
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "TestPass123",
            }
        )

        assert response.status_code == 400
        assert "邮箱已被注册" in response.json()["detail"]

    async def test_register_invalid_password(self, async_client: AsyncClient):
        """
        测试无效密码注册

        验证：
        - 返回422验证错误
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "weak",  # 不符合密码强度要求
            }
        )

        assert response.status_code == 422

    async def test_login_with_username(self, async_client: AsyncClient):
        """
        测试使用用户名登录

        验证：
        - 登录成功返回200
        - 返回token和用户信息
        """
        # 先注册用户
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "TestPass123",
            }
        )

        # 使用用户名登录
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "loginuser",
                "password": "TestPass123",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data

    async def test_login_with_email(self, async_client: AsyncClient):
        """
        测试使用邮箱登录

        验证：
        - 登录成功返回200
        - 返回token和用户信息
        """
        # 先注册用户
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "emailuser",
                "email": "emaillogin@example.com",
                "password": "TestPass123",
            }
        )

        # 使用邮箱登录
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "emaillogin@example.com",
                "password": "TestPass123",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """
        测试无效凭据登录

        验证：
        - 返回401错误
        """
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "WrongPass123",
            }
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    async def test_get_current_user(self, async_client: AsyncClient):
        """
        测试获取当前用户信息

        验证：
        - 返回200状态码
        - 返回正确的用户信息
        """
        # 先注册并登录
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "currentuser",
                "email": "current@example.com",
                "password": "TestPass123",
            }
        )
        token = register_response.json()["access_token"]

        # 获取当前用户信息
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"
        assert data["email"] == "current@example.com"

    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """
        测试未授权访问用户信息

        验证：
        - 返回401错误
        """
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "未提供认证凭据" in response.json()["detail"]

    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """
        测试使用无效token访问

        验证：
        - 返回401错误
        """
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    async def test_refresh_token(self, async_client: AsyncClient):
        """
        测试刷新token

        验证：
        - 返回新的token
        """
        # 先注册
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "refreshuser",
                "email": "refresh@example.com",
                "password": "TestPass123",
            }
        )
        refresh_token = register_response.json()["refresh_token"]

        # 刷新token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token_invalid(self, async_client: AsyncClient):
        """
        测试使用无效refresh token

        验证：
        - 返回401错误
        """
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"}
        )

        assert response.status_code == 401

    async def test_logout(self, async_client: AsyncClient):
        """
        测试登出

        验证：
        - 返回204状态码
        """
        # 先注册
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "logoutuser",
                "email": "logout@example.com",
                "password": "TestPass123",
            }
        )
        token = register_response.json()["access_token"]

        # 登出
        response = await async_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 204

    async def test_change_password(self, async_client: AsyncClient):
        """
        测试修改密码

        验证：
        - 返回204状态码
        - 可以用新密码登录
        """
        # 先注册
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "passworduser",
                "email": "password@example.com",
                "password": "OldPass123",
            }
        )
        token = register_response.json()["access_token"]

        # 修改密码
        response = await async_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "OldPass123",
                "new_password": "NewPass456",
            }
        )

        assert response.status_code == 204

        # 验证可以用新密码登录
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "passworduser",
                "password": "NewPass456",
            }
        )
        assert login_response.status_code == 200

    async def test_change_password_wrong_old_password(self, async_client: AsyncClient):
        """
        测试使用错误的旧密码修改密码

        验证：
        - 返回400错误
        """
        # 先注册
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "wrongpassuser",
                "email": "wrongpass@example.com",
                "password": "CorrectPass123",
            }
        )
        token = register_response.json()["access_token"]

        # 使用错误的旧密码
        response = await async_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "WrongPass123",
                "new_password": "NewPass456",
            }
        )

        assert response.status_code == 400
        assert "旧密码错误" in response.json()["detail"]


@pytest.mark.asyncio
class TestHealthCheck:
    """健康检查测试"""

    async def test_root_endpoint(self, async_client: AsyncClient):
        """测试根路径"""
        response = await async_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    async def test_health_check(self, async_client: AsyncClient):
        """测试健康检查端点"""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
