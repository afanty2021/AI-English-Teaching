"""
测试配置和共享fixtures
"""
import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import User, Organization, Student, Teacher, KnowledgeGraph
from app.main import app

# 确保在导入应用模块之前加载 .env 文件
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path, override=True)

# 测试数据库URL - 使用 Docker PostgreSQL (从 .env 读取)
from app.core.config import get_settings
TEST_DATABASE_URL = get_settings().DATABASE_URL


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


@pytest.fixture
def sample_student(db, test_organization):
    """示例学生用户"""
    from app.models import Student, User
    user = User(
        id=uuid4(),
        username="sample_student",
        email="sample_student@test.com",
        hashed_password="hashed_password",
        role="student",
        is_active=True
    )
    student = Student(
        id=uuid4(),
        user_id=user.id,
        organization_id=test_organization.id,
        target_exam="CET4",
        current_cefr_level="B1"
    )
    db.add(user)
    db.add(student)
    return student


@pytest.fixture
def sample_teacher(db, test_organization):
    """示例教师用户"""
    from app.models import Teacher, User
    user = User(
        id=uuid4(),
        username="sample_teacher",
        email="sample_teacher@test.com",
        hashed_password="hashed_password",
        role="teacher",
        is_active=True
    )
    teacher = Teacher(
        id=uuid4(),
        user_id=user.id,
        organization_id=test_organization.id,
        specialization=["reading", "writing"]
    )
    db.add(user)
    db.add(teacher)
    return teacher


@pytest.fixture
def sample_content(db):
    """示例内容"""
    from app.models import Content
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
    return content


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

    使用 Docker PostgreSQL 进行测试
    """
    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy import text

    engine: AsyncEngine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # 清理：先删除有外键依赖的表
    async with engine.begin() as conn:
        # 按照正确的顺序删除表，避免循环依赖问题
        await conn.execute(text("DROP TABLE IF EXISTS learning_reports CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS mistakes CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS practices CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS conversation_messages CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS conversations CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS lesson_plan_contents CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS lesson_plans CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS contents CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS knowledge_graphs CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS students CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS teachers CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS class_info CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS organizations CASCADE"))

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


@pytest.fixture
def test_organization(db: AsyncSession) -> Organization:
    """测试组织"""
    org = Organization(
        id=uuid4(),
        name="测试学校"
    )
    db.add(org)
    return org


@pytest.fixture
def test_student(db: AsyncSession, test_organization: Organization) -> Student:
    """测试学生用户"""
    user = User(
        id=uuid4(),
        username="test_student",
        email="student@test.com",
        hashed_password="hashed_password",
        role="student",
        is_active=True
    )
    student = Student(
        id=uuid4(),
        user_id=user.id,
        organization_id=test_organization.id,
        target_exam="CET4",
        current_cefr_level="B1"
    )
    db.add(user)
    db.add(student)
    return student


@pytest.fixture
def test_teacher(db: AsyncSession, test_organization: Organization) -> Teacher:
    """测试教师用户"""
    user = User(
        id=uuid4(),
        username="test_teacher",
        email="teacher@test.com",
        hashed_password="hashed_password",
        role="teacher",
        is_active=True
    )
    teacher = Teacher(
        id=uuid4(),
        user_id=user.id,
        organization_id=test_organization.id,
        specialization=["reading", "writing"]
    )
    db.add(user)
    db.add(teacher)
    return teacher


@pytest.fixture
def test_user(db: AsyncSession) -> User:
    """测试用户（User对象）"""
    user = User(
        id=uuid4(),
        username="test_user",
        email="test_user@test.com",
        hashed_password="hashed_password",
        role="student",
        is_active=True
    )
    db.add(user)
    return user


@pytest.fixture
def inactive_user(db: AsyncSession) -> User:
    """被禁用的测试用户"""
    user = User(
        id=uuid4(),
        username="inactive_user",
        email="inactive@test.com",
        hashed_password="hashed_password",
        role="student",
        is_active=False  # 被禁用
    )
    db.add(user)
    return user


@pytest.fixture
def db_session(db: AsyncSession) -> AsyncSession:
    """数据库会话别名（用于测试）"""
    return db
