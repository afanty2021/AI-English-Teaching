"""
测试配置和共享fixtures
"""
import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import User, Organization, Student, Teacher, KnowledgeGraph
from app.main import app

# 测试数据库URL - 使用 PostgreSQL 以获得完整功能支持
# 如果 Docker PostgreSQL 不可用，将自动使用 SQLite
import os
POSTGRES_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/english_teaching_test"
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", POSTGRES_URL)


# ============================================================================
# API 契约测试支持
# ============================================================================

class APIContractValidator:
    """
    API 契约验证器

    用于验证 API 响应是否符合前端期望的格式
    防止前后端接口不匹配导致的运行时错误
    """

    # 定义各 API 端点的期望响应格式
    # 这些契约应该与前端 src/api/*.ts 中的类型定义保持一致
    CONTRACTS = {
        "/api/v1/auth/login": {
            "response": {
                "access_token": "string",
                "refresh_token": "string",
                "token_type": "string",
                "expires_in": "int",
                "user": {
                    "id": "uuid",
                    "username": "string",
                    "email": "string",
                    "role": "string",
                    "is_active": "boolean",
                    "created_at": "string"
                }
            }
        },
        "/api/v1/auth/me": {
            "response": {
                "user": {
                    "id": "uuid",
                    "username": "string",
                    "email": "string",
                    "role": "string"
                }
            }
        },
        "/api/v1/reports/me": {
            "response": {
                "total": "int",
                "limit": "int",
                "offset": "int",
                "reports": "array"
            }
        },
        "/api/v1/reports/generate": {
            "request": {
                "report_type": "string",
                "period_start": "string",
                "period_end": "string"
            },
            "response": {
                "report": "object",
                "message": "string"
            }
        },
        "/api/v1/reports/{id}": {
            "response": {
                "id": "uuid",
                "student_id": "uuid",
                "report_type": "string",
                "period_start": "string",
                "period_end": "string",
                "status": "string",
                "statistics": "object",
                "ability_analysis": "object",
                "weak_points": "object",
                "recommendations": "object",
                "created_at": "string"
            }
        },
        "/api/v1/mistakes/me": {
            "response": {
                "total": "int",
                "limit": "int",
                "offset": "int",
                "mistakes": "array"
            }
        },
        "/api/v1/contents/recommend": {
            "response": {
                "reading": "array",
                "exercises": "array"
            }
        },
        "/api/v1/conversations": {
            "response": {
                "total": "int",
                "conversations": "array"
            }
        }
    }

    @classmethod
    def validate_response(cls, endpoint: str, response_data: dict) -> tuple[bool, list[str]]:
        """
        验证 API 响应是否符合契约

        Args:
            endpoint: API 端点路径（支持 {id} 占位符）
            response_data: 实际响应数据

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # 标准化端点路径（处理 {id} 等占位符）
        normalized_endpoint = cls._normalize_endpoint(endpoint)

        if normalized_endpoint not in cls.CONTRACTS:
            # 未定义契约的端点发出警告但不失败
            return True, [f"Warning: No contract defined for {normalized_endpoint}"]

        contract = cls.CONTRACTS[normalized_endpoint]["response"]

        # 验证必填字段
        for field, expected_type in contract.items():
            if field not in response_data:
                errors.append(f"Missing required field: '{field}'")
                continue

            # 如果是嵌套对象，递归验证
            if isinstance(expected_type, dict):
                if not isinstance(response_data[field], dict):
                    errors.append(f"Field '{field}' should be object, got {type(response_data[field]).__name__}")
                else:
                    # 递归验证嵌套对象
                    nested_valid, nested_errors = cls._validate_object(
                        response_data[field], expected_type, field
                    )
                    if not nested_valid:
                        errors.extend(nested_errors)
            else:
                type_valid, type_error = cls._validate_field_type(
                    response_data[field], expected_type, field
                )
                if not type_valid:
                    errors.append(type_error)

        return len(errors) == 0, errors

    @classmethod
    def _normalize_endpoint(cls, endpoint: str) -> str:
        """标准化端点路径，将 {id} 等替换为实际值"""
        import re
        # 将路径参数（如 UUID）替换为 {id}
        return re.sub(r'/[0-9a-f-]{36}(?=/|$)', '/{id}', endpoint)

    @classmethod
    def _validate_object(cls, data: dict, schema: dict, prefix: str = "") -> tuple[bool, list[str]]:
        """验证嵌套对象"""
        errors = []
        for field, expected_type in schema.items():
            full_field = f"{prefix}.{field}" if prefix else field
            if field not in data:
                errors.append(f"Missing field: '{full_field}'")
                continue

            type_valid, type_error = cls._validate_field_type(
                data[field], expected_type, full_field
            )
            if not type_valid:
                errors.append(type_error)

        return len(errors) == 0, errors

    @classmethod
    def _validate_field_type(cls, value, expected_type: str, field_name: str) -> tuple[bool, str]:
        """验证字段类型"""
        actual_type = cls._get_type_name(value)

        if expected_type == "array":
            if not isinstance(value, list):
                return False, f"Field '{field_name}' should be array, got {actual_type}"
        elif expected_type == "int":
            if not isinstance(value, int) or isinstance(value, bool):
                return False, f"Field '{field_name}' should be int, got {actual_type}"
        elif expected_type == "float":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, f"Field '{field_name}' should be float, got {actual_type}"
        elif expected_type == "string":
            if not isinstance(value, str):
                return False, f"Field '{field_name}' should be string, got {actual_type}"
        elif expected_type == "boolean":
            if not isinstance(value, bool):
                return False, f"Field '{field_name}' should be boolean, got {actual_type}"
        elif expected_type == "object":
            if not isinstance(value, dict):
                return False, f"Field '{field_name}' should be object, got {actual_type}"
        elif expected_type == "uuid":
            if not isinstance(value, str) or not cls._is_valid_uuid(value):
                return False, f"Field '{field_name}' should be valid UUID, got {value}"

        return True, ""

    @staticmethod
    def _get_type_name(value) -> str:
        """获取值的类型名称"""
        if isinstance(value, list):
            return "array"
        if isinstance(value, dict):
            return "object"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, int):
            return "int"
        if isinstance(value, str):
            return "string"
        if isinstance(value, float):
            return "float"
        if value is None:
            return "null"
        return "unknown"

    @staticmethod
    def _is_valid_uuid(uuid_string: str) -> bool:
        """验证 UUID 格式"""
        try:
            uuid4(uuid_string.replace("-", ""))
            return True
        except ValueError:
            return False


@pytest.fixture
def contract_validator() -> type[APIContractValidator]:
    """提供契约验证器 fixture"""
    return APIContractValidator


@pytest_asyncio.fixture
async def test_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    创建测试 HTTP 客户端

    使用 FastAPI 的 ASGI 应用进行测试，无需启动服务器
    """
    # 依赖注入覆盖：使用测试会话
    async def override_get_db():
        yield db

    from app.api.deps import get_db
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test1234",
        "full_name": "Test User",
        "role": "student"
    }


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """
    创建测试数据库引擎

    使用 PostgreSQL 以获得完整功能支持
    确保测试数据库已创建: createdb english_teaching_test
    """
    from sqlalchemy.ext.asyncio import AsyncEngine

    engine: AsyncEngine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
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
