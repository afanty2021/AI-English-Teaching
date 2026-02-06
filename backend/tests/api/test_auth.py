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
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
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
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
            }
        )

        # 第二次注册相同用户名
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "duplicate",
                "email": "user2@example.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
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
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
            }
        )

        # 第二次注册相同邮箱
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
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
                "confirm_password": "weak",
                "role": "student",
            }
        )

        assert response.status_code == 422

    async def test_register_password_mismatch(self, async_client: AsyncClient):
        """
        测试密码不匹配注册

        验证：
        - 返回422验证错误
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123!",
                "confirm_password": "DifferentPass123",
                "role": "student",
            }
        )

        assert response.status_code == 422

    async def test_register_invalid_role(self, async_client: AsyncClient):
        """
        测试无效角色注册

        验证：
        - 返回422验证错误
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "invalid_role",
            }
        )

        assert response.status_code == 422

    async def test_login_with_username(self, async_client: AsyncClient):
        """
        测试使用用户名登录

        验证：
        - 登录成功返回200状态码
        - 返回token信息
        """
        # 先注册用户
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
            }
        )

        # 使用用户名登录
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "loginuser",
                "password": "TestPass123!",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"

    async def test_login_with_email(self, async_client: AsyncClient):
        """
        测试使用邮箱登录

        验证：
        - 登录成功返回200状态码
        - 返回token信息
        """
        # 先注册用户
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "emailuser",
                "email": "email@test.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
            }
        )

        # 使用邮箱登录
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "email@test.com",
                "password": "TestPass123!",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_invalid_credentials(self, async_client: AsyncClient):
        """
        测试无效凭据登录

        验证：
        - 返回401错误
        - 错误信息正确
        """
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "WrongPassword123",
            }
        )

        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    async def test_get_current_user(self, async_client: AsyncClient):
        """
        测试获取当前用户信息

        验证：
        - 需要认证
        - 返回当前用户信息
        """
        # 先注册并登录
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "currentuser",
                "email": "current@test.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
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
        assert data["email"] == "current@test.com"
        assert data["role"] == "student"

    async def test_get_current_user_unauthorized(self, async_client: AsyncClient):
        """
        测试未授权访问当前用户信息

        验证：
        - 返回401错误
        """
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_refresh_token(self, async_client: AsyncClient):
        """
        测试刷新token

        验证：
        - 使用有效的refresh_token获取新的access_token
        """
        # 先注册
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "refreshtoken",
                "email": "refresh@test.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
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
        assert "token_type" in data

    async def test_refresh_invalid_token(self, async_client: AsyncClient):
        """
        测试刷新无效token

        验证：
        - 返回401错误
        """
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )

        assert response.status_code == 401

    async def test_logout(self, async_client: AsyncClient):
        """
        测试登出

        验证：
        - 登出成功返回204状态码
        """
        # 先注册并登录
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "logoutuser",
                "email": "logout@test.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
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
        - 使用正确的旧密码可以修改密码
        """
        # 先注册并登录
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "pwduser",
                "email": "pwd@test.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
            }
        )
        token = register_response.json()["access_token"]

        # 修改密码
        response = await async_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "TestPass123!",
                "new_password": "NewPass456!",
            }
        )

        assert response.status_code == 204

        # 使用新密码登录验证
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "pwduser",
                "password": "NewPass456!",
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
        await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "wrongpwd",
                "email": "wrongpwd@test.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "student",
            }
        )

        # 登录获取token
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "username": "wrongpwd",
                "password": "TestPass123!",
            }
        )
        token = login_response.json()["access_token"]

        # 使用错误的旧密码修改密码
        response = await async_client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "old_password": "WrongPassword",
                "new_password": "NewPass456!",
            }
        )

        assert response.status_code == 400
        assert "旧密码错误" in response.json()["detail"]

    async def test_register_teacher(self, async_client: AsyncClient):
        """
        测试教师注册

        验证：
        - 教师注册成功返回201状态码
        - 返回用户角色为teacher
        """
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "username": "teacheruser",
                "email": "teacher@test.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
                "role": "teacher",
                "full_name": "Test Teacher",
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user"]["role"] == "teacher"
        assert data["user"]["username"] == "teacheruser"
