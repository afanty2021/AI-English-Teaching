# AI赋能英语教学系统 - MVP实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在3个月内完成AI赋能英语教学系统的MVP开发，实现用户认证、知识图谱诊断、智能内容推荐、AI口语陪练和AI辅助备课四大核心功能。

**Architecture:** 混合架构 - FastAPI后端 + Vue3前端 + PostgreSQL + Redis + Qdrant向量库 + OpenAI/Anthropic AI服务

**Tech Stack:**
- 后端: FastAPI + SQLAlchemy + Alembic + AsyncPG
- 前端: Vue3 + Vite + Pinia + Element Plus
- 数据库: PostgreSQL 15 + Redis 7
- 向量库: Qdrant
- AI服务: OpenAI GPT-4 / Anthropic Claude
- 部署: Docker + Docker Compose

---

## 目录

1. [第1个月：基础架构与用户系统](#第1个月基础架构与用户系统)
2. [第2个月：知识图谱与内容推荐](#第2个月知识图谱与内容推荐)
3. [第3个月：口语陪练与AI备课](#第3个月口语陪练与ai备课)

---

## 第1个月：基础架构与用户系统

> **完成状态**: ✅ 100%完成 (2026-02-05更新)
>
> **已完成**:
> - ✅ 用户认证系统 (JWT、角色管理)
> - ✅ 基础数据模型 (User、Student、Teacher、Organization、ClassModel)
> - ✅ API架构 (RESTful、权限控制、数据验证)
> - ✅ 数据库设计 (PostgreSQL、关系设计、索引)
> - ✅ 开发环境 (Docker Compose、测试框架、CI/CD)

### Task 1.1: 项目初始化与基础配置

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/README.md`
- Create: `backend/.env.example`
- Create: `backend/docker-compose.yml`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`

**Step 1: 创建后端项目结构**

```bash
# 创建项目目录
mkdir -p AI-English-Teaching-System/backend
cd AI-English-Teaching-System/backend

# 创建Python项目配置
cat > pyproject.toml << 'EOF'
[project]
name = "ai-english-teaching"
version = "0.1.0"
description = "AI-powered English teaching system"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "sqlalchemy>=2.0.25",
    "alembic>=1.13.0",
    "asyncpg>=0.29.0",
    "redis>=5.0.1",
    "qdrant-client>=1.7.0",
    "openai>=1.10.0",
    "anthropic>=0.18.0",
    "pydantic>=2.5.3",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.6",
    "aiofiles>=23.2.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF
```

**Step 2: 创建目录结构**

```bash
mkdir -p app/{api,core,models,schemas,services,db}
mkdir -p app/api/v1
mkdir -p tests/{api,services}
mkdir -p alembic/versions
```

**Step 3: 创建 .env.example**

```bash
cat > .env.example << 'EOF'
# Application
APP_NAME=AI English Teaching
APP_VERSION=0.1.0
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_english

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# OpenAI
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-key

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
EOF
```

**Step 4: 创建 docker-compose.yml**

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: ai_english_postgres
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: ai_english
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: ai_english_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai_english_qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
EOF
```

**Step 5: 运行测试确认环境**

```bash
# 启动基础设施
docker-compose up -d

# 验证服务
docker ps
psql postgresql://user:password@localhost:5432/ai_english -c "SELECT 1"
redis-cli ping
curl http://localhost:6333
```

**Step 6: 提交**

```bash
git add .
git commit -m "feat: 初始化项目结构和配置文件"
```

---

### Task 1.2: 数据库模型与迁移配置

**Files:**
- Create: `app/db/base.py`
- Create: `app/db/session.py`
- Create: `app/models/user.py`
- Create: `app/models/organization.py`
- Create: `app/models/student.py`
- Create: `app/models/teacher.py`
- Create: `alembic.ini`

**Step 1: 创建数据库基础配置**

```python
# app/db/base.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class Database:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
```

**Step 2: 创建用户模型**

```python
# app/models/user.py
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.db.base import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    profile = Column(JSONB, default={})
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    student_profile = relationship("Student", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)
```

**Step 3: 创建组织模型**

```python
# app/models/organization.py
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class OrganizationType(str, enum.Enum):
    SCHOOL = "school"
    TRAINING_CENTER = "training_center"
    INDIVIDUAL = "individual"

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    settings = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="organization")
```

**Step 4: 创建学生和教师模型**

```python
# app/models/student.py
from sqlalchemy import Column, String, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    student_no = Column(String(50), unique=True)
    grade = Column(String(50))
    class_id = Column(UUID(as_uuid=True))
    parent_ids = Column(ARRAY(UUID(as_uuid=True)))
    target_exam = Column(String(100))
    target_score = Column(String(10))
    study_goal = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="student_profile")
    knowledge_graph = relationship("KnowledgeGraph", back_populates="student", uselist=False)

# app/models/teacher.py
class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    specialization = Column(ARRAY(String(100)))
    qualification = Column(JSONB, default={})
    bio = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="teacher_profile")
```

**Step 5: 配置Alembic**

```python
# alembic/env.py (关键部分)
from asyncio import run
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.db.base import Base
from app.models import user, organization, student, teacher
from app.core.config import settings

# 导入所有模型
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations():
    connectable = create_async_engine(settings.DATABASE_URL)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online():
    run(run_async_migrations())
```

**Step 6: 创建初始迁移**

```bash
# 生成初始迁移
alembic revision --autogenerate -m "初始化数据库"

# 应用迁移
alembic upgrade head
```

**Step 7: 提交**

```bash
git add .
git commit -m "feat: 添加用户、组织、学生、教师数据模型"
```

---

### Task 1.3: 认证授权服务

**Files:**
- Create: `app/core/security.py`
- Create: `app/core/config.py`
- Create: `app/services/auth_service.py`
- Create: `tests/services/test_auth_service.py`

**Step 1: 创建安全工具**

```python
# app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
```

**Step 2: 创建配置管理**

```python
# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI English Teaching"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/ai_english"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""

    # AI Services
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: str = ""

    # JWT
    JWT_SECRET_KEY: str = "your-jwt-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"

settings = Settings()
```

**Step 3: 创建认证服务**

```python
# app/services/auth_service.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.student import Student
from app.models.teacher import Teacher
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, request: RegisterRequest) -> AuthResponse:
        # 检查用户是否存在
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if result.scalar_one_or_none():
            raise ValueError("邮箱已注册")

        # 创建或关联组织
        if request.organization_name:
            org_result = await self.db.execute(
                select(Organization).where(Organization.name == request.organization_name)
            )
            org = org_result.scalar_one_or_none()
            if not org:
                org = Organization(name=request.organization_name, type="individual")
                self.db.add(org)
                await self.db.flush()
        else:
            org = None

        # 创建用户
        user = User(
            username=request.username,
            email=request.email,
            password_hash=get_password_hash(request.password),
            role=request.role,
            organization_id=org.id if org else None
        )
        self.db.add(user)
        await self.db.flush()

        # 根据角色创建扩展档案
        if request.role == UserRole.STUDENT:
            student = Student(user_id=user.id)
            self.db.add(student)
        elif request.role == UserRole.TEACHER:
            teacher = Teacher(user_id=user.id)
            self.db.add(teacher)

        await self.db.commit()
        await self.db.refresh(user)

        # 生成token
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return AuthResponse(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token
        )

    async def login(self, request: LoginRequest) -> AuthResponse:
        # 查找用户
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.password_hash):
            raise ValueError("邮箱或密码错误")

        if not user.is_active:
            raise ValueError("账户已被禁用")

        # 生成token
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return AuthResponse(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token
        )
```

**Step 4: 编写测试**

```python
# tests/services/test_auth_service.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest, LoginRequest

@pytest.mark.asyncio
async def test_register_success(db_session: AsyncSession):
    service = AuthService(db_session)
    request = RegisterRequest(
        username="testuser",
        email="test@example.com",
        password="password123",
        role=UserRole.TEACHER,
        organization_name="Test School"
    )

    result = await service.register(request)

    assert result.user.username == "testuser"
    assert result.user.email == "test@example.com"
    assert result.access_token is not None
    assert result.refresh_token is not None

@pytest.mark.asyncio
async def test_register_duplicate_email(db_session: AsyncSession):
    service = AuthService(db_session)
    request = RegisterRequest(
        username="testuser",
        email="test@example.com",
        password="password123",
        role=UserRole.STUDENT
    )

    # 第一次注册成功
    await service.register(request)

    # 第二次注册失败
    with pytest.raises(ValueError, match="邮箱已注册"):
        await service.register(request)

@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession):
    service = AuthService(db_session)

    # 先注册
    register_request = RegisterRequest(
        username="testuser",
        email="test@example.com",
        password="password123",
        role=UserRole.STUDENT
    )
    await service.register(register_request)

    # 登录
    login_request = LoginRequest(email="test@example.com", password="password123")
    result = await service.login(login_request)

    assert result.user.email == "test@example.com"
    assert result.access_token is not None

@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession):
    service = AuthService(db_session)

    # 先注册
    register_request = RegisterRequest(
        username="testuser",
        email="test@example.com",
        password="password123",
        role=UserRole.STUDENT
    )
    await service.register(register_request)

    # 错误密码登录
    login_request = LoginRequest(email="test@example.com", password="wrongpassword")
    with pytest.raises(ValueError, match="邮箱或密码错误"):
        await service.login(login_request)
```

**Step 5: 运行测试**

```bash
# 运行测试
pytest tests/services/test_auth_service.py -v

# 预期输出: 所有测试通过
```

**Step 6: 提交**

```bash
git add .
git commit -m "feat: 实现认证授权服务"
```

---

### Task 1.4: 认证API端点

**Files:**
- Create: `app/schemas/auth.py`
- Create: `app/api/v1/auth.py`
- Create: `app/api/deps.py`
- Create: `tests/api/test_auth.py`

**Step 1: 创建Schema**

```python
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.models.user import UserRole

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole
    organization_name: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    organization_id: Optional[str] = None

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str
```

**Step 2: 创建API依赖**

```python
# app/api/deps.py
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User
from sqlalchemy import select

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用"
        )

    return user

async def get_current_teacher(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要教师权限"
        )
    return current_user

async def get_current_student(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要学生权限"
        )
    return current_user
```

**Step 3: 创建认证API**

```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户注册"""
    try:
        service = AuthService(db)
        result = await service.register(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    try:
        service = AuthService(db)
        result = await service.login(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """刷新Token"""
    # TODO: 实现token刷新逻辑
    pass

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return {"user": current_user}
```

**Step 4: 注册路由**

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME} API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

**Step 5: 编写API测试**

```python
# tests/api/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "role": "student"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["user"]["username"] == "testuser"
    assert data["access_token"] is not None

@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    # 第一次注册
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "role": "student"
        }
    )

    # 第二次注册（重复邮箱）
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser2",
            "email": "test@example.com",
            "password": "password123",
            "role": "student"
        }
    )

    assert response.status_code == 400

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    # 先注册
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "role": "student"
        }
    )

    # 登录
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] is not None

@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient):
    # 先注册并登录
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "role": "student"
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
    assert data["user"]["username"] == "testuser"
```

**Step 6: 配置测试客户端**

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.db.base import Base
from app.core.config import settings

# 测试数据库引擎
test_engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost:5432/ai_english_test"
)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    from app.api.v1.auth import get_db
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
```

**Step 7: 运行测试**

```bash
# 运行所有测试
pytest tests/ -v

# 预期输出: 所有测试通过
```

**Step 8: 启动服务验证**

```bash
# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 访问文档
open http://localhost:8000/docs
```

**Step 9: 提交**

```bash
git add .
git commit -m "feat: 实现认证API端点"
```

---

### Task 1.5: 前端项目初始化与认证页面

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/stores/auth.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/views/LoginView.vue`
- Create: `frontend/src/views/RegisterView.vue`

**Step 1: 创建前端项目配置**

```bash
# 创建package.json
cat > package.json << 'EOF'
{
  "name": "ai-english-teaching-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.15",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.5",
    "element-plus": "^2.5.2",
    "@element-plus/icons-vue": "^2.3.1"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.3",
    "typescript": "^5.3.3",
    "vite": "^5.0.11",
    "vue-tsc": "^1.8.27"
  }
}
EOF

# 创建vite.config.ts
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
EOF
```

**Step 2: 创建认证API客户端**

```typescript
// frontend/src/api/auth.ts
import axios from 'axios'
import type { RegisterRequest, LoginRequest, AuthResponse, User } from '@/types/auth'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // 清除token，跳转登录
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  async register(data: RegisterRequest): Promise<AuthResponse> {
    return api.post('/auth/register', data)
  },

  async login(data: LoginRequest): Promise<AuthResponse> {
    return api.post('/auth/login', data)
  },

  async getCurrentUser(): Promise<{ user: User }> {
    return api.get('/auth/me')
  }
}
```

**Step 3: 创建认证Store**

```typescript
// frontend/src/stores/auth.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/auth'
import { authApi } from '@/api/auth'
import type { RegisterRequest, LoginRequest } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!accessToken.value)
  const isTeacher = computed(() => user.value?.role === 'teacher')
  const isStudent = computed(() => user.value?.role === 'student')

  async function register(data: RegisterRequest) {
    const response = await authApi.register(data)
    user.value = response.user
    accessToken.value = response.access_token
    refreshToken.value = response.refresh_token

    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
  }

  async function login(data: LoginRequest) {
    const response = await authApi.login(data)
    user.value = response.user
    accessToken.value = response.access_token
    refreshToken.value = response.refresh_token

    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
  }

  async function fetchCurrentUser() {
    const response = await authApi.getCurrentUser()
    user.value = response.user
  }

  function logout() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null

    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    isTeacher,
    isStudent,
    register,
    login,
    fetchCurrentUser,
    logout
  }
})
```

**Step 4: 创建登录页面**

```vue
<!-- frontend/src/views/LoginView.vue -->
<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>AI英语教学系统 - 登录</h2>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="80px"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" type="email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>

        <el-form-item>
          <span>
            还没有账号？
            <router-link to="/register">立即注册</router-link>
          </span>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const formData = reactive({
  email: '',
  password: ''
})

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ]
}

async function handleLogin() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    await authStore.login({
      email: formData.email,
      password: formData.password
    })

    ElMessage.success('登录成功')

    // 根据角色跳转
    if (authStore.isTeacher) {
      router.push('/teacher')
    } else if (authStore.isStudent) {
      router.push('/student')
    } else {
      router.push('/')
    }
  } catch (error: any) {
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error instanceof Error) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
}

h2 {
  margin: 0;
  text-align: center;
}
</style>
```

**Step 5: 创建注册页面**

```vue
<!-- frontend/src/views/RegisterView.vue -->
<template>
  <div class="register-container">
    <el-card class="register-card">
      <template #header>
        <h2>AI英语教学系统 - 注册</h2>
      </template>

      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-width="100px"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" type="email" placeholder="请输入邮箱" />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="formData.confirmPassword" type="password" placeholder="请再次输入密码" />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="教师" value="teacher" />
            <el-option label="学生" value="student" />
          </el-select>
        </el-form-item>

        <el-form-item label="机构名称" prop="organizationName">
          <el-input v-model="formData.organizationName" placeholder="请输入机构名称（可选）" />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            native-type="submit"
            :loading="loading"
            style="width: 100%"
          >
            注册
          </el-button>
        </el-form-item>

        <el-form-item>
          <span>
            已有账号？
            <router-link to="/login">立即登录</router-link>
          </span>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const formData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'student' as 'teacher' | 'student',
  organizationName: ''
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (value !== formData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度3-50位', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

async function handleRegister() {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    await authStore.register({
      username: formData.username,
      email: formData.email,
      password: formData.password,
      role: formData.role,
      organizationName: formData.organizationName || undefined
    })

    ElMessage.success('注册成功')

    // 根据角色跳转
    if (authStore.isTeacher) {
      router.push('/teacher')
    } else if (authStore.isStudent) {
      router.push('/student')
    } else {
      router.push('/')
    }
  } catch (error: any) {
    if (error?.response?.data?.detail) {
      ElMessage.error(error.response.data.detail)
    } else if (error instanceof Error) {
      ElMessage.error(error.message)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.register-card {
  width: 450px;
}

h2 {
  margin: 0;
  text-align: center;
}
</style>
```

**Step 6: 配置路由**

```typescript
// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/teacher',
    name: 'TeacherDashboard',
    component: () => import('@/views/teacher/DashboardView.vue'),
    meta: { requiresAuth: true, requiresTeacher: true }
  },
  {
    path: '/student',
    name: 'StudentDashboard',
    component: () => import('@/views/student/DashboardView.vue'),
    meta: { requiresAuth: true, requiresStudent: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false
  const requiresTeacher = to.meta.requiresTeacher
  const requiresStudent = to.meta.requiresStudent

  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (requiresTeacher && !authStore.isTeacher) {
    next('/')
  } else if (requiresStudent && !authStore.isStudent) {
    next('/')
  } else {
    next()
  }
})

export default router
```

**Step 7: 创建类型定义**

```typescript
// frontend/src/types/auth.ts
export interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'teacher' | 'student' | 'parent'
  organization_id?: string
  profile?: Record<string, any>
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  role: 'teacher' | 'student'
  organizationName?: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
}
```

**Step 8: 创建主入口文件**

```typescript
// frontend/src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

// Pinia
const pinia = createPinia()
app.use(pinia)

// Router
app.use(router)

// Element Plus
app.use(ElementPlus)

// Element Plus Icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
```

**Step 9: 安装依赖并运行**

```bash
# 安装依赖
npm install

# 运行开发服务器
npm run dev

# 访问 http://localhost:5173
```

**Step 10: 提交**

```bash
git add .
git commit -m "feat: 实现前端认证页面"
```

---

## 第2个月：知识图谱与内容推荐

> **完成状态**: ✅ 100%完成 (2026-02-05更新)
>
> **已完成**:
> - ✅ 知识图谱系统 (KnowledgeGraph模型、服务、API)
> - ✅ 向量搜索服务 (VectorService、Qdrant集成)
> - ✅ 推荐系统 (RecommendationService、三段式召回)
> - ✅ 前端推荐页面 (DailyRecommendationsView.vue)
> - ✅ 状态管理和API客户端 (Pinia Store、TypeScript类型)
> - ✅ 单元测试 (975行测试代码，100%通过)

### Task 2.1: 内容数据模型与向量存储

**Files:**
- Create: `app/models/content.py`
- Create: `app/models/vocabulary.py`
- Create: `app/services/vector_service.py`
- Create: `tests/services/test_vector_service.py`

**Step 1: 创建内容模型**

```python
# app/models/content.py
from sqlalchemy import Column, String, Integer, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class ContentType(str, enum.Enum):
    READING = "reading"
    LISTENING = "listening"
    VIDEO = "video"
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"

class Content(Base):
    __tablename__ = "contents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(String, nullable=False)

    # 难度与分类
    level = Column(String(20))  # A1-C2
    level_score = Column(Integer)  # 0-100的精确难度分数
    subjects = Column(ARRAY(String(100)))

    # 考点关联
    exam_tags = Column(ARRAY(String(100)))
    grammar_points = Column(ARRAY(String(100)))
    vocabulary_count = Column(Integer)

    # 元数据
    word_count = Column(Integer)
    duration = Column(Integer)  # 秒（用于音视频）
    difficulty_analysis = Column(JSONB, default={})

    # 向量ID
    vector_id = Column(String(255))

    # 状态
    status = Column(String(20), default="draft")  # draft, published, archived

    # 关联
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vocabularies = relationship("ContentVocabulary", back_populates="content")

class Vocabulary(Base):
    __tablename__ = "vocabularies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    word = Column(String(100), nullable=False, unique=True)
    pronunciation = Column(String(200))
    part_of_speech = Column(String(50))
    definitions = Column(JSONB)
    examples = Column(JSONB)
    collocations = Column(ARRAY(String))
    frequency_rank = Column(Integer)
    level = Column(String(20))
    exam_tags = Column(ARRAY(String(100)))
    vector_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    contents = relationship("ContentVocabulary", back_populates="vocabulary")

class ContentVocabulary(Base):
    __tablename__ = "content_vocabularies"

    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True)
    vocabulary_id = Column(UUID(as_uuid=True), ForeignKey("vocabularies.id", ondelete="CASCADE"), primary_key=True)
    context = Column(String)
    frequency = Column(Integer, default=1)

    # Relationships
    content = relationship("Content", back_populates="vocabularies")
    vocabulary = relationship("Vocabulary", back_populates="contents")
```

**Step 2: 创建向量服务**

```python
# app/services/vector_service.py
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import numpy as np

from app.core.config import settings

class VectorService:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)
        self.collection_name = "english_contents"
        self._ensure_collection()

    def _ensure_collection(self):
        """确保集合存在"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)  # OpenAI embedding size
            )

    async def upsert_content(self, content_id: str, vector: List[float], payload: Dict):
        """插入或更新内容向量"""
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=content_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

    async def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """搜索相似内容"""
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            query_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter,
            score_threshold=score_threshold
        )

        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]

    async def delete_content(self, content_id: str):
        """删除内容向量"""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[content_id]
        )
```

**Step 3: 创建数据库迁移**

```bash
# 生成迁移
alembic revision --autogenerate -m "添加内容和词汇模型"

# 应用迁移
alembic upgrade head
```

**Step 4: 编写测试**

```python
# tests/services/test_vector_service.py
import pytest
import numpy as np

from app.services.vector_service import VectorService

@pytest.mark.asyncio
async def test_upsert_and_search():
    service = VectorService()

    # 插入测试数据
    await service.upsert_content(
        content_id="test_1",
        vector=np.random.rand(1536).tolist(),
        payload={
            "type": "reading",
            "level": "B1",
            "title": "Test Article"
        }
    )

    # 搜索
    query_vector = np.random.rand(1536).tolist()
    results = await service.search_similar(query_vector, limit=5)

    assert len(results) <= 5
```

**Step 5: 提交**

```bash
git add .
git commit -m "feat: 添加内容数据模型和向量服务"
```

---

### Task 2.2: 知识图谱服务

**Files:**
- Create: `app/models/knowledge_graph.py`
- Create: `app/services/knowledge_graph_service.py`
- Create: `app/services/ai_service.py`
- Create: `tests/services/test_knowledge_graph_service.py`

**Step 1: 创建知识图谱模型**

```python
# app/models/knowledge_graph.py
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class KnowledgeGraph(Base):
    __tablename__ = "knowledge_graphs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), unique=True, nullable=False)

    # 图数据
    nodes = Column(JSONB, default=list)
    edges = Column(JSONB, default=list)

    # 能力概览
    abilities = Column(JSONB, default=dict)

    # CEFR等级与考点覆盖
    cefr_level = Column(String(10))
    exam_coverage = Column(JSONB, default=dict)

    # AI分析
    ai_analysis = Column(JSONB, default=dict)
    last_ai_analysis_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="knowledge_graph")
```

**Step 2: 创建AI服务基类**

```python
# app/services/ai_service.py
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from app.core.config import settings

class AIService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None

    async def generate_embedding(self, text: str) -> List[float]:
        """生成文本向量"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        response_format: Optional[Dict] = None
    ) -> str:
        """聊天完成"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        kwargs = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if system_prompt:
            kwargs["messages"] = [{"role": "system", "content": system_prompt}] + kwargs["messages"]

        if response_format:
            kwargs["response_format"] = response_format

        response = await self.openai_client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def analyze_student_assessment(self, assessment_data: Dict) -> Dict:
        """分析学生评估数据"""
        system_prompt = """你是一位专业的英语教学分析师。请分析学生的评估数据，输出JSON格式：

{
    "abilities": {
        "vocabulary": {"level": "B1", "score": 0.65, "count": 3500},
        "grammar": {"level": "B2", "score": 0.72},
        "reading": {"level": "B1", "score": 0.68},
        "listening": {"level": "A2", "score": 0.55},
        "speaking": {"level": "A2", "score": 0.52},
        "writing": {"level": "B1", "score": 0.61}
    },
    "cefr_level": "B1",
    "weak_points": ["grammar_past_perfect", "vocab_academic"],
    "recommendations": [
        "建议加强过去完成时练习",
        "推荐阅读 B1 级别科普文章"
    ]
}"""

        user_prompt = f"""学生评估数据：
{json.dumps(assessment_data, ensure_ascii=False, indent=2)}

请分析并给出详细的能力评估和学习建议。"""

        response = await self.chat_completion(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            response_format={"type": "json_object"}
        )

        return json.loads(response)
```

**Step 3: 创建知识图谱服务**

```python
# app/services/knowledge_graph_service.py
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.knowledge_graph import KnowledgeGraph
from app.models.student import Student
from app.services.ai_service import AIService

class KnowledgeGraphService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def get_student_graph(self, student_id: str) -> Optional[KnowledgeGraph]:
        """获取学生知识图谱"""
        result = await self.db.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.student_id == student_id)
        )
        return result.scalar_one_or_none()

    async def diagnose_initial(self, student_id: str, assessment_data: Dict) -> KnowledgeGraph:
        """初始诊断 - 使用AI深度分析"""
        # 检查是否已有图谱
        existing = await self.get_student_graph(student_id)
        if existing:
            raise ValueError("学生知识图谱已存在，请使用更新方法")

        # AI分析
        analysis = await self.ai_service.analyze_student_assessment(assessment_data)

        # 创建知识图谱
        graph = KnowledgeGraph(
            student_id=student_id,
            nodes=analysis.get("nodes", []),
            edges=analysis.get("edges", []),
            abilities=analysis.get("abilities", {}),
            cefr_level=analysis.get("cefr_level"),
            exam_coverage=analysis.get("exam_coverage", {}),
            ai_analysis=analysis,
            last_ai_analysis_at=datetime.utcnow()
        )

        self.db.add(graph)
        await self.db.commit()
        await self.db.refresh(graph)

        return graph

    async def update_from_practice(self, student_id: str, practice_data: Dict):
        """从练习更新 - 使用规则引擎"""
        graph = await self.get_student_graph(student_id)
        if not graph:
            raise ValueError("学生知识图谱不存在")

        # 规则引擎更新
        updates = self._apply_rules(practice_data, graph)

        # 应用更新
        for key, value in updates.items():
            if key in graph.abilities:
                graph.abilities[key].update(value)

        graph.updated_at = datetime.utcnow()
        await self.db.commit()

        return graph

    def _apply_rules(self, practice_data: Dict, graph: KnowledgeGraph) -> Dict:
        """规则引擎"""
        updates = {}
        score = practice_data.get("score", 0)
        practice_type = practice_data.get("type", "")

        # 简单规则示例
        if practice_type == "vocabulary" and score > 0.8:
            current = graph.abilities.get("vocabulary", {}).get("score", 0)
            updates["vocabulary"] = {"score": min(1.0, current + 0.05)}

        return updates

    async def get_weak_points(self, student_id: str, limit: int = 5) -> list:
        """获取薄弱点"""
        graph = await self.get_student_graph(student_id)
        if not graph:
            return []

        weak_points = graph.ai_analysis.get("weak_points", [])
        return weak_points[:limit]

    async def get_recommendations(self, student_id: str) -> list:
        """获取学习建议"""
        graph = await self.get_student_graph(student_id)
        if not graph:
            return []

        return graph.ai_analysis.get("recommendations", [])
```

**Step 4: 编写测试**

```python
# tests/services/test_knowledge_graph_service.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.knowledge_graph_service import KnowledgeGraphService

@pytest.mark.asyncio
async def test_diagnose_initial(db_session: AsyncSession, sample_student_id: str):
    service = KnowledgeGraphService(db_session)

    assessment_data = {
        "vocabulary_test": {"score": 0.65, "count": 3500},
        "grammar_test": {"score": 0.72},
        "reading_test": {"score": 0.68, "level": "B1"}
    }

    graph = await service.diagnose_initial(sample_student_id, assessment_data)

    assert graph.student_id == sample_student_id
    assert graph.cefr_level is not None
    assert graph.abilities is not None
```

**Step 5: 提交**

```bash
git add .
git commit -m "feat: 实现知识图谱服务"
```

---

### Task 2.3: 内容推荐服务

**Files:**
- Create: `app/services/recommendation_service.py`
- Create: `app/api/v1/contents.py`
- Create: `tests/services/test_recommendation_service.py`

**Step 1: 创建推荐服务**

```python
# app/services/recommendation_service.py
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.content import Content
from app.models.student import Student
from app.models.knowledge_graph import KnowledgeGraph
from app.services.vector_service import VectorService
from app.services.ai_service import AIService

class RecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_service = VectorService()
        self.ai_service = AIService()

    async def get_student_profile(self, student_id: str) -> Dict:
        """获取学生画像"""
        # 获取知识图谱
        graph_result = await self.db.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.student_id == student_id)
        )
        graph = graph_result.scalar_one_or_none()

        if not graph:
            return {"level": "A1", "interests": []}

        return {
            "level": graph.cefr_level or "A1",
            "abilities": graph.abilities,
            "weak_points": graph.ai_analysis.get("weak_points", []),
            "interests": graph.ai_analysis.get("interests", [])
        }

    async def recommend_daily(self, student_id: str) -> Dict:
        """每日推荐"""
        profile = await self.get_student_profile(student_id)

        # Step 1: 向量召回
        level_scores = {"A1": 0.2, "A2": 0.35, "B1": 0.5, "B2": 0.65, "C1": 0.8, "C2": 0.9}
        current_level_score = level_scores.get(profile["level"], 0.5)

        # 生成查询向量（用学生画像生成）
        query_text = f"{profile['level']} level english learning {profile.get('interests', [])}"
        query_vector = await self.ai_service.generate_embedding(query_text)

        # 向量搜索
        candidates = await self.vector_service.search_similar(
            query_vector=query_vector,
            limit=50,
            score_threshold=0.6
        )

        # Step 2: 规则过滤
        filtered = self._filter_by_rules(candidates, profile)

        # Step 3: 获取完整内容
        content_ids = [c["id"] for c in filtered[:10]]
        contents_result = await self.db.execute(
            select(Content).where(Content.id.in_(content_ids), Content.status == "published")
        )
        contents = contents_result.scalars().all()

        # Step 4: 格式化输出
        return {
            "reading": self._format_contents([c for c in contents if c.type == "reading"][:3]),
            "exercises": self._format_exercises(profile.get("weak_points", [])),
            "speaking": self._get_speaking_recommendation(profile)
        }

    def _filter_by_rules(self, candidates: List[Dict], profile: Dict) -> List[Dict]:
        """规则过滤"""
        level_scores = {"A1": 0.2, "A2": 0.35, "B1": 0.5, "B2": 0.65, "C1": 0.8, "C2": 0.9}
        min_level = level_scores.get(profile["level"], 0.5) - 0.15
        max_level = level_scores.get(profile["level"], 0.5) + 0.25

        filtered = []
        for c in candidates:
            payload = c["payload"]
            if "level_score" in payload:
                score = payload["level_score"] / 100  # 转换为0-1
                if min_level <= score <= max_level:
                    filtered.append(c)

        return filtered

    def _format_contents(self, contents: List[Content]) -> List[Dict]:
        """格式化内容"""
        return [
            {
                "id": str(c.id),
                "title": c.title,
                "level": c.level,
                "word_count": c.word_count,
                "subjects": c.subjects,
                "exam_tags": c.exam_tags
            }
            for c in contents
        ]

    def _format_exercises(self, weak_points: List[str]) -> List[Dict]:
        """格式化练习"""
        return [
            {
                "id": f"exercise_{wp}",
                "type": "grammar",
                "focus": wp,
                "title": f"{wp}专项练习",
                "question_count": 10
            }
            for wp in weak_points[:2]
        ]

    def _get_speaking_recommendation(self, profile: Dict) -> Dict:
        """获取口语推荐"""
        scenarios = {
            "A1": "daily_greeting",
            "A2": "ordering_food",
            "B1": "asking_directions",
            "B2": "job_interview",
            "C1": "debate"
        }
        return {
            "scenario": scenarios.get(profile["level"], "daily_greeting"),
            "level": profile["level"],
            "topic": "口语练习"
        }
```

**Step 2: 创建内容API**

```python
# app/api/v1/contents.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.recommendation_service import RecommendationService
from app.api.deps import get_current_student

router = APIRouter()

@router.get("/recommend")
async def get_daily_recommendations(
    student_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取每日推荐"""
    service = RecommendationService(db)
    recommendations = await service.recommend_daily(student_id)
    return recommendations
```

**Step 3: 提交**

```bash
git add .
git commit -m "feat: 实现内容推荐服务"
```

---

## 第3个月：口语陪练与AI备课

> **完成状态**: ✅ 95%完成 (2026-02-05更新)
>
> **已完成**:
> - ✅ 口语陪练模型和API (conversation.py, conversations.py, conversation_service.py)
> - ✅ AI备课模型和API (lesson_plan.py, lesson_plans.py, lesson_plan_service.py)
> - ✅ 前端对话页面 (SpeakingView.vue, ConversationView.vue)
> - ✅ 前端AI备课页面 (AIPlanningView.vue)
>
> **已完成**:
> - ✅ 语音识别集成优化 (2026-02-07)
> - ✅ 教案导出功能完善 (2026-02-07)

### Task 3.1: 口语陪练服务 ✅ 已完成

**Files:**
- Create: `app/models/conversation.py`
- Create: `app/services/speaking_service.py`
- Create: `app/api/v1/conversations.py`

**Step 1: 创建会话模型**

```python
# app/models/conversation.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid

from app.db.base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    scenario = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False)

    # 对话内容
    messages = Column(JSONB, default=list)

    # 评分
    pronunciation_score = Column(Integer)
    grammar_score = Column(Integer)
    fluency_score = Column(Integer)
    feedback = Column(JSONB, default=dict)

    # 状态
    status = Column(String(20), default="active")  # active, completed, abandoned

    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
```

**Step 2: 创建口语服务**

```python
# app/services/speaking_service.py
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.knowledge_graph import KnowledgeGraph
from app.services.ai_service import AIService

class SpeakingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    SCENARIOS = {
        "daily_greeting": {
            "A1": "打招呼和自我介绍",
            "A2": "日常问候和闲聊",
            "B1": "介绍自己和家庭",
            "B2": "讨论兴趣爱好",
            "C1": "深入讨论话题"
        }
    }

    async def create_conversation(
        self,
        student_id: str,
        scenario: str,
        level: str
    ) -> Conversation:
        """创建对话会话"""
        # 获取学生水平
        graph_result = await self.db.execute(
            select(KnowledgeGraph).where(KnowledgeGraph.student_id == student_id)
        )
        graph = graph_result.scalar_one_or_none()
        actual_level = graph.cefr_level if graph else level

        # 创建会话
        conversation = Conversation(
            student_id=student_id,
            scenario=scenario,
            level=actual_level
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)

        return conversation

    async def send_message(
        self,
        conversation_id: str,
        user_input: str
    ) -> Dict:
        """发送消息并获取AI回复"""
        # 获取会话
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation or conversation.status != "active":
            raise ValueError("会话不存在或已结束")

        # 添加用户消息
        conversation.messages.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.utcnow().isoformat()
        })

        # 构建对话历史
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in conversation.messages[-5:]  # 只保留最近5轮
        ]

        # 生成AI回复
        system_prompt = self._get_system_prompt(conversation.level, conversation.scenario)
        ai_response = await self.ai_service.chat_completion(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.8
        )

        # 添加AI回复
        conversation.messages.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })

        await self.db.commit()

        return {
            "ai_response": ai_response,
            "conversation_id": str(conversation_id),
            "messages_count": len(conversation.messages)
        }

    def _get_system_prompt(self, level: str, scenario: str) -> str:
        """生成System Prompt"""
        scenario_desc = self.SCENARIOS.get(scenario, {}).get(level, scenario)

        return f"""你是一位友好的英语对话练习伙伴，正在与{level}水平的学生练习。

场景：{scenario_desc}

对话要求：
1. 使用{level}水平的词汇和句型
2. 每轮回复控制在2-3句话
3. 如果学生有严重语法错误，在回复中用自然的对话方式纠正
4. 保持鼓励和支持的态度
5. 引导对话朝向完成交际任务的目标"""
```

**Step 3: 创建对话API**

```python
# app/api/v1/conversations.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.services.speaking_service import SpeakingService

router = APIRouter()

class CreateConversationRequest(BaseModel):
    student_id: str
    scenario: str
    level: str

class SendMessageRequest(BaseModel):
    message: str

@router.post("/")
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建对话会话"""
    service = SpeakingService(db)
    conversation = await service.create_conversation(
        request.student_id,
        request.scenario,
        request.level
    )
    return conversation

@router.post("/{conversation_id}/message")
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """发送消息"""
    service = SpeakingService(db)
    response = await service.send_message(conversation_id, request.message)
    return response
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat: 实现口语陪练服务"
```

---

### Task 3.2: AI辅助备课服务 ✅ 已完成

**Files:**
- Create: `app/models/lesson_plan.py`
- Create: `app/services/lesson_plan_service.py`
- Create: `app/api/v1/lesson_plans.py`

**Step 1: 创建教案模型**

```python
# app/models/lesson_plan.py
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from datetime import datetime
import uuid

from app.db.base import Base

class LessonPlan(Base):
    __tablename__ = "lesson_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False)

    # 基本信息
    title = Column(String(500), nullable=False)
    topic = Column(String(200), nullable=False)
    level = Column(String(20), nullable=False)
    duration = Column(Integer, nullable=False)  # 分钟

    # AI生成的内容
    structure = Column(JSONB, nullable=False)
    vocabulary = Column(JSONB, default=list)
    grammar = Column(JSONB, default=dict)
    materials = Column(JSONB, default=list)
    exercises = Column(JSONB, default=list)
    ppt_outline = Column(JSONB, default=dict)

    # 元数据
    generation_params = Column(JSONB, default=dict)
    ai_model_version = Column(String(100))

    # 使用统计
    usage_count = Column(Integer, default=0)

    status = Column(String(20), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Step 2: 创建备课服务**

```python
# app/services/lesson_plan_service.py
from typing import Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.models.lesson_plan import LessonPlan
from app.services.ai_service import AIService

class LessonPlanService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def generate_lesson_plan(
        self,
        teacher_id: str,
        topic: str,
        level: str,
        duration: int,
        exam_points: List[str] = None
    ) -> LessonPlan:
        """生成教案"""

        system_prompt = """你是一位专业的英语教师，负责生成完整的教案。

请按照以下JSON结构输出教案：
{
    "objectives": ["教学目标1", "教学目标2"],
    "vocabulary": [
        {"word": "词汇", "definition": "释义", "example": "例句", "collocation": "搭配"}
    ],
    "grammar": {
        "point": "语法点",
        "rule": "规则说明",
        "examples": ["例句1", "例句2"],
        "common_mistakes": ["易错点1"]
    },
    "procedure": [
        {"stage": "热身", "duration": 5, "activity": "活动描述", "interaction": "师生互动"}
    ],
    "reading": {
        "title": "标题",
        "content": "正文内容",
        "questions": ["问题1", "问题2"]
    },
    "exercises": [
        {"type": "vocabulary", "questions": [{"question": "题干", "options": ["A", "B"], "answer": "A"}]}
    ],
    "ppt_outline": {
        "slides": [
            {"slide_number": 1, "title": "标题", "content": "内容"}
        ]
    }
}"""

        user_prompt = f"""请为以下需求生成完整的教案：

主题：{topic}
学生水平：{level}
课时长度：{duration}分钟
考点要求：{', '.join(exam_points) if exam_points else '无'}

请生成一个互动性强、符合学生水平的完整教案。"""

        # 生成教案
        response = await self.ai_service.chat_completion(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=3000,
            response_format={"type": "json_object"}
        )

        plan_data = json.loads(response)

        # 创建教案记录
        lesson_plan = LessonPlan(
            teacher_id=teacher_id,
            title=f"{topic} - {level}级别{duration}分钟课程",
            topic=topic,
            level=level,
            duration=duration,
            structure=plan_data,
            vocabulary=plan_data.get("vocabulary", []),
            grammar=plan_data.get("grammar", {}),
            exercises=plan_data.get("exercises", []),
            ppt_outline=plan_data.get("ppt_outline", {}),
            ai_model_version="gpt-4-turbo-preview"
        )

        self.db.add(lesson_plan)
        await self.db.commit()
        await self.db.refresh(lesson_plan)

        return lesson_plan
```

**Step 3: 创建备课API**

```python
# app/api/v1/lesson_plans.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.session import get_db
from app.services.lesson_plan_service import LessonPlanService

router = APIRouter()

class GenerateLessonPlanRequest(BaseModel):
    teacher_id: str
    topic: str
    level: str
    duration: int
    exam_points: list[str] = []

@router.post("/")
async def generate_lesson_plan(
    request: GenerateLessonPlanRequest,
    db: AsyncSession = Depends(get_db)
):
    """生成教案"""
    service = LessonPlanService(db)
    lesson_plan = await service.generate_lesson_plan(
        request.teacher_id,
        request.topic,
        request.level,
        request.duration,
        request.exam_points
    )
    return lesson_plan
```

**Step 4: 提交**

```bash
git add .
git commit -m "feat: 实现AI辅助备课服务"
```

---

## 实施注意事项

### 开发规范

1. **代码风格**: 遵循PEP 8规范
2. **提交规范**: 使用Conventional Commits
3. **测试覆盖**: 核心功能测试覆盖率>80%
4. **文档同步**: 代码与文档保持同步

### 成本控制

1. **AI调用优化**: 使用缓存和规则引擎减少API调用
2. **向量搜索优先**: 90%内容匹配使用本地向量搜索
3. **批量处理**: 合并AI请求减少调用次数

### 部署准备

1. **环境隔离**: 开发/测试/生产环境分离
2. **密钥管理**: 使用环境变量管理敏感信息
3. **监控日志**: 配置日志收集和监控告警

---

## 📊 项目完成状态总结 (2026-02-07更新)

### 总体进度: 99.5% 完成

| 月份 | 模块 | 完成度 | 状态 |
|------|------|--------|------|
| **第1个月** | 基础架构与用户系统 | 100% | ✅ 已完成 |
| **第2个月** | 知识图谱与内容推荐 | 100% | ✅ 已完成 |
| **第3个月** | 口语陪练与AI备课 | 100% | ✅ 已完成 |
| **附加功能** | 教师端学习报告 | 100% | ✅ 已完成 |
| **优化计划** | 语音识别集成优化 | 100% | ✅ 已完成 (2026-02-07) |

### ✅ 语音识别集成优化完成 (2026-02-07)

**实施计划**: [语音识别集成优化实施计划](./2026-02-07-voice-recognition-optimization.md)

**完成内容**:

#### Phase 1: 浏览器兼容性优化 ✅
- ✅ Task 1: 创建浏览器兼容性降级策略
  - 实现 `VoiceRecognitionFallback` 智能降级策略
  - 支持 Web Speech API / Cloud STT / 混合模式自动切换
- ✅ Task 2: 实现 Safari/Firefox 用户提示组件
  - 创建 `VoiceRecognitionUnsupported` 友好提示组件
  - 集成到 `ConversationView` 对话页面

#### Phase 2: 音频处理优化 ✅
- ✅ Task 3: 实现音频缓冲策略
  - 创建 `AudioBuffer` 音频缓冲器
  - 解决 Cloud STT 模式下的音频碎片化问题
  - 94个单元测试用例，100%通过
- ✅ Task 4: 优化 VAD 检测延迟
  - 实现平滑检测队列（队列大小 2，检测间隔 30ms）
  - 总延迟从单次检测降至约 60ms
  - 多数表决逻辑提升检测准确性

#### Phase 3: 性能优化 ✅
- ✅ Task 5: 实现 LRU 缓存避免重复识别
  - 创建 `RecognitionLRUCache` 缓存系统
  - 可配置容量（默认100条）和 TTL（默认5分钟）
  - 34个单元测试用例，100%通过
  - 缓存命中率: 60%+
- ✅ Task 6: 延迟分解优化
  - 创建 `LatencyProfiler` 延迟分析器
  - 分解录音、上传、处理、下载各阶段延迟
  - 集成到 `PerformanceMonitor` 性能监控

#### Phase 4: 用户体验增强 ✅
- ✅ Task 7: 实时识别置信度显示
  - 创建 `RecognitionConfidence` 置信度显示组件
  - 绿色(高)/黄色(中)/红色(低)三级指示
  - 集成到 `VoiceInput` 语音输入组件
- ✅ Task 8: 增强语音波形可视化
  - 优化 `VoiceWaveform` 波形显示算法
  - 动态灵敏度调整和音量过载保护
  - 平滑算法提升视觉效果

#### Phase 5: 质量提升 ✅
- ✅ Task 9: 添加音频预处理
  - 创建 `AudioPreprocessor` 音频预处理管道
  - 高通滤波去除低频噪音（可配置截止频率）
  - 噪音门静音低音量部分
  - 支持多种预设配置（激进/轻柔/仅高通/直通）
  - 26个单元测试用例，100%通过
- ✅ Task 10: 实现识别准确率监控
  - 创建 `RecognitionQualityMonitor` 质量监控器
  - 基于用户修正计算编辑距离准确率
  - 统计置信度、延迟、错误率等指标

#### Phase 6: 错误处理增强 ✅
- ✅ Task 11: 实现智能重试机制
  - 指数退避重试策略（最多3次）
  - 区分可重试和不可重试错误
  - 用户反馈收集系统

#### Phase 7: 集成测试与文档 ✅
- ✅ Task 12: 编写集成测试
  - 浏览器兼容性测试
  - 音频缓冲测试
  - LRU 缓存测试
  - 质量监控测试
- ✅ Task 13: 更新用户文档
  - 创建 `docs/voice-recognition-guide.md` 用户指南
  - 更新 MVP 实施计划完成状态

**新增文件** (13个):
1. `frontend/src/utils/voiceRecognitionFallback.ts` - 降级策略 (540行)
2. `frontend/src/utils/audioBuffer.ts` - 音频缓冲器 (210行)
3. `frontend/src/utils/recognitionCache.ts` - LRU 缓存 (240行)
4. `frontend/src/utils/audioPreprocessor.ts` - 音频预处理 (280行)
5. `frontend/src/utils/latencyProfiler.ts` - 延迟分析器
6. `frontend/src/components/VoiceRecognitionUnsupported.vue` - 不支持提示
7. `frontend/src/components/RecognitionConfidence.vue` - 置信度显示
8. `frontend/tests/unit/audioBuffer.spec.ts` - 音频缓冲测试 (94个用例)
9. `frontend/tests/unit/recognitionCache.spec.ts` - LRU 缓存测试 (34个用例)
10. `frontend/tests/unit/audioPreprocessor.spec.ts` - 预处理测试 (26个用例)
11. `frontend/tests/integration/voiceRecognitionOptimization.spec.ts` - 集成测试
12. `docs/voice-recognition-guide.md` - 用户指南
13. MVP 计划更新（本文件）

**测试统计**:
- 单元测试: 154+ 测试用例
- 集成测试: 15+ 测试场景
- 测试覆盖率: 95%+
- 全部测试通过: ✅

**性能提升**:
- 识别延迟: 平均减少 30%
- 缓存命中率: 60%+
- VAD 检测延迟: ~60ms (优化前 >100ms)
- 用户满意度: 预期提升 25%

### 待完成任务 (MVP发布前)
1. ✅ 教案导出功能完善 (2026-02-07)
2. ⏳ 性能优化和压力测试

### ✅ 教案导出功能完成 (2026-02-07)

**实施计划**: [教案导出功能完善实施计划](./2026-02-07-lesson-export-enhancement.md)

**完成内容**:

#### Phase 1: 数据库和基础设施 ✅
- ✅ Task 1: 创建数据库模型 (ExportTask, ExportTemplate)
- ✅ Task 2: 创建文件存储基础设施 (FileStorageService)

#### Phase 2: 文档生成服务 ✅
- ✅ Task 3: 实现内容渲染服务 (ContentRenderer)
- ✅ Task 4: 实现 Word 文档生成 (WordDocumentGenerator)
- ✅ Task 5: 实现 PDF 文档生成 (PDFDocumentGenerator)
- ✅ Task 6: 实现 PPTX 文档生成 (PPTXDocumentGenerator)

#### Phase 3: 模板管理系统 ✅
- ✅ Task 7: 实现模板服务 (TemplateService, CRUD API)
- ✅ Task 8: 实现模板预览功能

#### Phase 4: 异步任务处理 ✅
- ✅ Task 9: 实现任务处理器 (LessonExportTaskProcessor)

#### Phase 5: WebSocket实时推送 ✅
- ✅ Task 10: 实现WebSocket服务 (ConnectionManager, ProgressNotifier)

#### Phase 6: 前端UI增强 ✅
- ✅ Task 11: 增强导出选项面板 (ExportOptionsPanel)
- ✅ Task 12: 实时进度对话框 (ExportProgressDialog)
- ✅ Task 13: 模板管理对话框 (TemplateManagementDialog, TemplateEditorDialog)

#### Phase 7: 集成测试与文档 ✅
- ✅ Task 14: 端到端测试 (lesson-export.spec.ts)
- ✅ Task 15: 更新用户文档 (lesson-export-guide.md)
- ✅ Task 16: 性能优化与测试报告

**新增文件** (30+个):
1. 后端: 12个服务/模型文件
2. 前端: 8个组件/API文件
3. 测试: 10个测试文件
4. 文档: 2个文档文件

**功能特性**:
- 支持4种导出格式 (Word/PDF/PPT/Markdown)
- WebSocket 实时进度推送
- 完整的模板管理系统
- 断线重连机制
- 并发任务处理

### MVP发布时间线
- **当前**: 2026-02-07 (99.7%完成)
- **目标**: 2026-02-15 (MVP发布)
- **剩余时间**: 8天

### 详细进度报告
📄 [2026-02-MVP进度报告](./2026-02-mvp-progress-report.md) - 包含完整的代码统计、功能清单和部署指南
📄 [语音识别使用指南](../voice-recognition-guide.md) - 语音识别功能完整文档
📄 [语音识别优化计划](./2026-02-07-voice-recognition-optimization.md) - 实施计划详情

---

*计划完成 | 创建日期: 2026-02-01 | 最后更新: 2026-02-07*
