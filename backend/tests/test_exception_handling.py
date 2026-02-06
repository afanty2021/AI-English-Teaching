"""
异常处理测试 - AI英语教学系统

测试内容：
- 业务异常类定义
- 异常转换为字典格式
- 全局异常处理器
- HTTP 状态码映射
"""
import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.core.exceptions import (
    BaseException,
    AuthenticationError,
    BusinessError,
    ValidationError,
    ResourceNotFoundError,
    PermissionError,
    RateLimitError,
    UserNotFoundError,
    StudentNotFoundError,
    TokenExpiredError,
    ForbiddenError,
)
from app.core.exception_handler import setup_exception_handlers


# 创建测试应用
@pytest.fixture
def test_app():
    """创建测试 FastAPI 应用"""
    app = FastAPI()

    @app.get("/test/auth-error")
    async def auth_error():
        raise AuthenticationError("认证失败")

    @app.get("/test/resource-not-found")
    async def resource_not_found():
        raise ResourceNotFoundError("资源不存在")

    @app.get("/test/validation-error")
    async def validation_error():
        raise ValidationError("数据验证失败")

    @app.get("/test/permission-error")
    async def permission_error():
        raise ForbiddenError("禁止访问")

    @app.get("/test/rate-limit")
    async def rate_limit():
        raise RateLimitError("请求过于频繁", retry_after=60)

    @app.get("/test/custom-error")
    async def custom_error():
        raise BusinessError("自定义业务错误", error_code="CUSTOM_ERROR")

    @app.get("/test/user-not-found")
    async def user_not_found():
        raise UserNotFoundError()

    @app.get("/test/token-expired")
    async def token_expired():
        raise TokenExpiredError()

    setup_exception_handlers(app)
    return app


class TestExceptionClasses:
    """异常类单元测试"""

    def test_base_exception_to_dict(self):
        """测试 BaseException 转换为字典"""
        exc = BaseException(detail="测试错误", error_code="TEST_ERROR")
        result = exc.to_dict()

        assert result["success"] is False
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "测试错误"

    def test_authentication_error_defaults(self):
        """测试认证异常默认值"""
        exc = AuthenticationError()

        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.error_code == "AUTHENTICATION_ERROR"
        assert exc.detail == "认证失败"

    def test_resource_not_found_error_defaults(self):
        """测试资源不存在异常默认值"""
        exc = ResourceNotFoundError()

        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "RESOURCE_NOT_FOUND"
        assert exc.detail == "请求的资源不存在"

    def test_user_not_found_error_defaults(self):
        """测试用户不存在异常默认值"""
        exc = UserNotFoundError()

        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.error_code == "USER_NOT_FOUND"
        assert exc.detail == "用户不存在"

    def test_validation_error_defaults(self):
        """测试验证异常默认值"""
        exc = ValidationError("字段验证失败")

        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.detail == "字段验证失败"

    def test_permission_error_defaults(self):
        """测试权限异常默认值"""
        exc = PermissionError()

        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.error_code == "PERMISSION_ERROR"
        assert exc.detail == "权限不足"

    def test_rate_limit_error_retry_after(self):
        """测试速率限制异常的 Retry-After 头"""
        exc = RateLimitError(retry_after=120)

        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.retry_after == 120
        assert exc.headers["Retry-After"] == "120"

    def test_custom_business_error(self):
        """测试自定义业务异常"""
        exc = BusinessError(
            detail="库存不足",
            error_code="INSUFFICIENT_STOCK"
        )

        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.error_code == "INSUFFICIENT_STOCK"
        assert exc.detail == "库存不足"

    def test_exception_repr(self):
        """测试异常字符串表示"""
        exc = BusinessError("测试消息", error_code="TEST")
        repr_str = repr(exc)

        assert "BusinessError" in repr_str
        assert "TEST" in repr_str
        assert "测试消息" in repr_str


class TestExceptionHandlers:
    """异常处理器集成测试"""

    @pytest.mark.asyncio
    async def test_authentication_error_handler(self, test_app: FastAPI):
        """测试认证异常处理器"""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/auth-error")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_resource_not_found_handler(self, test_app: FastAPI):
        """测试资源不存在异常处理器"""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/resource-not-found")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validation_error_handler(self, test_app: FastAPI):
        """测试验证异常处理器"""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/validation-error")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_permission_error_handler(self, test_app: FastAPI):
        """测试权限异常处理器"""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/permission-error")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_rate_limit_handler(self, test_app: FastAPI):
        """测试速率限制异常处理器"""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/rate-limit")

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "RATE_LIMIT_ERROR"
        assert response.headers.get("Retry-After") == "60"

    @pytest.mark.asyncio
    async def test_custom_error_handler(self, test_app: FastAPI):
        """测试自定义业务异常处理器"""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/custom-error")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "CUSTOM_ERROR"
        assert data["error"]["message"] == "自定义业务错误"

    @pytest.mark.asyncio
    async def test_user_not_found_handler(self, test_app: FastAPI):
        """测试用户不存在异常处理器"""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/user-not-found")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"]["code"] == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_token_expired_handler(self, test_app: FastAPI):
        """测试 Token 过期异常处理器"""
        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/test/token-expired")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"]["code"] == "TOKEN_EXPIRED"


class TestExceptionHierarchy:
    """异常继承关系测试"""

    def test_user_not_found_inherits_from_resource_not_found(self):
        """测试 UserNotFoundError 继承自 ResourceNotFoundError"""
        exc = UserNotFoundError()
        # 应该能够被 ResourceNotFoundError 处理器捕获
        assert isinstance(exc, ResourceNotFoundError)

    def test_authentication_errors_inherit_from_base(self):
        """测试认证错误继承链"""
        exc = TokenExpiredError()

        assert isinstance(exc, TokenExpiredError)
        assert isinstance(exc, AuthenticationError)
        assert isinstance(exc, BaseException)

    def test_permission_errors_inherit_from_base(self):
        """测试权限错误继承链"""
        exc = ForbiddenError()

        assert isinstance(exc, ForbiddenError)
        assert isinstance(exc, PermissionError)
        assert isinstance(exc, BaseException)

    def test_business_errors_inherit_from_base(self):
        """测试业务错误继承链"""
        exc = ValidationError()

        assert isinstance(exc, ValidationError)
        assert isinstance(exc, BusinessError)
        assert isinstance(exc, BaseException)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
