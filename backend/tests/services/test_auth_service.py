"""
认证服务测试
测试用户注册、登录、token生成等功能
"""
import uuid
from datetime import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


@pytest.mark.asyncio
class TestAuthServiceRegister:
    """测试用户注册功能"""

    async def test_register_success(self, db: AsyncSession):
        """测试注册成功"""
        register_data = RegisterRequest(
            username="testuser",
            email="test@example.com",
            password="TestPass123",
            full_name="Test User",
            phone="13800138000"
        )

        result = await AuthService.register(db, register_data)

        assert result.user.username == "testuser"
        assert result.user.email == "test@example.com"
        assert result.user.role == UserRole.STUDENT
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "bearer"
        assert result.expires_in > 0

    async def test_register_with_organization(self, db: AsyncSession):
        """测试注册并创建组织"""
        register_data = RegisterRequest(
            username="orgadmin",
            email="orgadmin@example.com",
            password="TestPass123",
            full_name="Organization Admin",
            organization_name="Test Organization"
        )

        result = await AuthService.register(db, register_data)

        assert result.user.role == UserRole.ORGANIZATION_ADMIN
        assert result.user.organization_id is not None

    async def test_register_duplicate_username(self, db: AsyncSession):
        """测试重复用户名注册失败"""
        # 第一次注册
        register_data1 = RegisterRequest(
            username="duplicate",
            email="user1@example.com",
            password="TestPass123"
        )
        await AuthService.register(db, register_data1)

        # 第二次注册相同用户名
        register_data2 = RegisterRequest(
            username="duplicate",
            email="user2@example.com",
            password="TestPass123"
        )

        with pytest.raises(ValueError, match="用户名已被使用"):
            await AuthService.register(db, register_data2)

    async def test_register_duplicate_email(self, db: AsyncSession):
        """测试重复邮箱注册失败"""
        # 第一次注册
        register_data1 = RegisterRequest(
            username="user1",
            email="duplicate@example.com",
            password="TestPass123"
        )
        await AuthService.register(db, register_data1)

        # 第二次注册相同邮箱
        register_data2 = RegisterRequest(
            username="user2",
            email="duplicate@example.com",
            password="TestPass123"
        )

        with pytest.raises(ValueError, match="邮箱已被注册"):
            await AuthService.register(db, register_data2)

    async def test_register_duplicate_organization_name(self, db: AsyncSession):
        """测试重复组织名称注册失败"""
        # 第一次注册
        register_data1 = RegisterRequest(
            username="admin1",
            email="admin1@example.com",
            password="TestPass123",
            organization_name="Same Organization"
        )
        await AuthService.register(db, register_data1)

        # 第二次注册相同组织名称
        register_data2 = RegisterRequest(
            username="admin2",
            email="admin2@example.com",
            password="TestPass123",
            organization_name="Same Organization"
        )

        with pytest.raises(ValueError, match="组织名称已被使用"):
            await AuthService.register(db, register_data2)


@pytest.mark.asyncio
class TestAuthServiceLogin:
    """测试用户登录功能"""

    async def test_login_with_username_success(self, db: AsyncSession):
        """测试使用用户名登录成功"""
        # 先注册
        register_data = RegisterRequest(
            username="loginuser",
            email="login@example.com",
            password="TestPass123"
        )
        await AuthService.register(db, register_data)

        # 使用用户名登录
        login_data = LoginRequest(
            username="loginuser",
            password="TestPass123"
        )
        result = await AuthService.login(db, login_data)

        assert result.user.username == "loginuser"
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.user.last_login_at is not None

    async def test_login_with_email_success(self, db: AsyncSession):
        """测试使用邮箱登录成功"""
        # 先注册
        register_data = RegisterRequest(
            username="emaillogin",
            email="emaillogin@example.com",
            password="TestPass123"
        )
        await AuthService.register(db, register_data)

        # 使用邮箱登录
        login_data = LoginRequest(
            username="emaillogin@example.com",
            password="TestPass123"
        )
        result = await AuthService.login(db, login_data)

        assert result.user.email == "emaillogin@example.com"
        assert result.access_token is not None

    async def test_login_wrong_password(self, db: AsyncSession):
        """测试错误密码登录失败"""
        # 先注册
        register_data = RegisterRequest(
            username="wrongpass",
            email="wrongpass@example.com",
            password="TestPass123"
        )
        await AuthService.register(db, register_data)

        # 使用错误密码登录
        login_data = LoginRequest(
            username="wrongpass",
            password="WrongPass123"
        )

        with pytest.raises(ValueError, match="用户名或密码错误"):
            await AuthService.login(db, login_data)

    async def test_login_nonexistent_user(self, db: AsyncSession):
        """测试不存在的用户登录失败"""
        login_data = LoginRequest(
            username="nonexistent",
            password="TestPass123"
        )

        with pytest.raises(ValueError, match="用户名或密码错误"):
            await AuthService.login(db, login_data)

    async def test_login_inactive_user(self, db: AsyncSession):
        """测试禁用用户登录失败"""
        # 先注册
        register_data = RegisterRequest(
            username="inactive",
            email="inactive@example.com",
            password="TestPass123"
        )
        await AuthService.register(db, register_data)

        # 禁用用户
        user = await db.execute(
            select(User).where(User.username == "inactive")
        )
        user = user.scalar_one_or_none()
        user.is_active = False
        await db.commit()

        # 尝试登录
        login_data = LoginRequest(
            username="inactive",
            password="TestPass123"
        )

        with pytest.raises(ValueError, match="账户已被禁用"):
            await AuthService.login(db, login_data)


@pytest.mark.asyncio
class TestAuthServiceRefreshToken:
    """测试刷新令牌功能"""

    async def test_refresh_token_success(self, db: AsyncSession):
        """测试刷新令牌成功"""
        # 先登录
        register_data = RegisterRequest(
            username="refreshuser",
            email="refresh@example.com",
            password="TestPass123"
        )
        auth_response = await AuthService.register(db, register_data)

        # 刷新令牌
        result = await AuthService.refresh_token(db, auth_response.refresh_token)

        assert result["access_token"] is not None
        assert result["refresh_token"] is not None
        assert result["token_type"] == "bearer"
        assert result["expires_in"] > 0
        # 新token应该与旧token不同
        assert result["access_token"] != auth_response.access_token

    async def test_refresh_token_invalid(self, db: AsyncSession):
        """测试无效刷新令牌"""
        invalid_token = "invalid.refresh.token"

        with pytest.raises(ValueError, match="无效的刷新令牌"):
            await AuthService.refresh_token(db, invalid_token)

    async def test_refresh_token_nonexistent_user(self, db: AsyncSession):
        """测试不存在用户的刷新令牌"""
        from app.core.security import create_refresh_token

        # 创建一个不存在的用户ID的token
        fake_user_id = uuid.uuid4()
        refresh_token = create_refresh_token(subject=str(fake_user_id))

        with pytest.raises(ValueError, match="用户不存在"):
            await AuthService.refresh_token(db, refresh_token)


@pytest.mark.asyncio
class TestAuthServiceGetCurrentUser:
    """测试获取当前用户功能"""

    async def test_get_current_user_success(self, db: AsyncSession):
        """测试获取当前用户成功"""
        # 先注册
        register_data = RegisterRequest(
            username="getuser",
            email="getuser@example.com",
            password="TestPass123",
            full_name="Get User"
        )
        auth_response = await AuthService.register(db, register_data)

        # 获取用户信息
        user_response = await AuthService.get_current_user(db, auth_response.user.id)

        assert user_response.username == "getuser"
        assert user_response.email == "getuser@example.com"
        assert user_response.full_name == "Get User"
        assert user_response.id == auth_response.user.id

    async def test_get_current_user_not_found(self, db: AsyncSession):
        """测试获取不存在的用户"""
        fake_user_id = uuid.uuid4()

        with pytest.raises(ValueError, match="用户不存在"):
            await AuthService.get_current_user(db, fake_user_id)


@pytest.mark.asyncio
class TestAuthServiceChangePassword:
    """测试修改密码功能"""

    async def test_change_password_success(self, db: AsyncSession):
        """测试修改密码成功"""
        # 先注册
        register_data = RegisterRequest(
            username="changepass",
            email="changepass@example.com",
            password="OldPass123"
        )
        auth_response = await AuthService.register(db, register_data)

        # 修改密码
        await AuthService.change_password(
            db,
            auth_response.user.id,
            old_password="OldPass123",
            new_password="NewPass123"
        )

        # 使用新密码登录
        login_data = LoginRequest(
            username="changepass",
            password="NewPass123"
        )
        result = await AuthService.login(db, login_data)

        assert result.user.username == "changepass"

    async def test_change_password_wrong_old_password(self, db: AsyncSession):
        """测试使用错误的旧密码修改密码失败"""
        # 先注册
        register_data = RegisterRequest(
            username="wrongold",
            email="wrongold@example.com",
            password="CorrectPass123"
        )
        auth_response = await AuthService.register(db, register_data)

        # 使用错误的旧密码
        with pytest.raises(ValueError, match="旧密码错误"):
            await AuthService.change_password(
                db,
                auth_response.user.id,
                old_password="WrongPass123",
                new_password="NewPass123"
            )

    async def test_change_password_nonexistent_user(self, db: AsyncSession):
        """测试为不存在的用户修改密码"""
        fake_user_id = uuid.uuid4()

        with pytest.raises(ValueError, match="用户不存在"):
            await AuthService.change_password(
                db,
                fake_user_id,
                old_password="OldPass123",
                new_password="NewPass123"
            )
