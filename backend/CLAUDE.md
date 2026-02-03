[根目录](../CLAUDE.md) > **backend**

# backend - 后端服务模块

> **模块类型**: Python FastAPI 后端服务
> **主要职责**: 提供REST API、业务逻辑处理、数据持久化
> **技术栈**: FastAPI + SQLAlchemy + PostgreSQL + Redis + Qdrant

---

## 模块职责

backend 模块是 AI 赋能英语教学系统的核心后端服务，提供：

1. **用户认证与授权**: JWT token管理、用户注册登录
2. **知识图谱服务**: 学生能力诊断、个性化知识图谱生成与更新
3. **向量搜索服务**: 基于Qdrant的内容相似度搜索
4. **AI服务集成**: OpenAI/Anthropic API调用
5. **内容管理**: 教学内容的CRUD操作
6. **学习记录**: 学生练习记录与进度追踪

---

## 入口与启动

### 应用入口

- **主应用**: `app/main.py` (待创建)
- **当前状态**: 模块正在开发中，核心服务已实现

### 启动方式

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Makefile
make dev
```

### 服务地址

- API服务: http://localhost:8000
- Swagger文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

---

## 对外接口

### API路由结构

```
/api/v1/
├── /auth/          # 认证授权 (已实现)
│   ├── POST /register
│   ├── POST /login
│   └── GET  /me
├── /students/      # 学生管理 (待实现)
├── /contents/      # 内容管理 (待实现)
├── /practices/     # 练习记录 (待实现)
├── /conversations/ # 口语对话 (待实现)
└── /lesson-plans/  # 教案管理 (待实现)
```

### 核心API端点

**认证接口** (`app/api/v1/auth.py`):
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息

---

## 关键依赖与配置

### 项目依赖

核心依赖定义在 `pyproject.toml`：

| 依赖类别 | 主要包 | 版本要求 |
|---------|-------|----------|
| Web框架 | FastAPI, Uvicorn | >=0.109.0 |
| 数据库 | SQLAlchemy, AsyncPG, Alembic | >=2.0.25 |
| 缓存 | Redis, Hiredis | >=5.0.1 |
| 向量库 | Qdrant Client | >=1.7.0 |
| AI服务 | OpenAI, Anthropic | >=1.10.0 |
| 认证 | python-jose, passlib | >=3.3.0 |

### 环境变量

必要的环境变量（见 `.env.example`）：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ai_english

# Redis
REDIS_URL=redis://localhost:6379/0

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_VECTOR_SIZE=1536

# AI服务
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-turbo-preview
ANTHROPIC_API_KEY=your_anthropic_api_key

# JWT认证
JWT_SECRET_KEY=your_jwt_secret_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 数据模型

### 核心模型

| 模型 | 文件路径 | 描述 |
|------|----------|------|
| User | `app/models/user.py` (待创建) | 用户基础信息 |
| Student | `app/models/student.py` (待创建) | 学生档案 |
| Teacher | `app/models/teacher.py` (待创建) | 教师档案 |
| KnowledgeGraph | `app/models/knowledge_graph.py` | 知识图谱 |
| Content | `app/models/content.py` (待创建) | 教学内容 |
| Practice | `app/models/practice.py` (待创建) | 练习记录 |

### 数据库迁移

```bash
# 生成新迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

---

## 业务服务

### 知识图谱服务

**文件**: `app/services/knowledge_graph_service.py`

核心方法：
- `diagnose_initial()` - 初始AI诊断
- `update_from_practice()` - 规则引擎更新（零成本）
- `get_weak_points()` - 获取薄弱点
- `get_recommendations()` - 获取学习建议

### 向量搜索服务

**文件**: `app/services/vector_service.py`

核心方法：
- `upsert_content()` - 插入/更新内容向量
- `search_similar()` - 向量相似度搜索
- `search_by_text()` - 文本查询相似内容
- `recommend_content()` - 基于内容推荐相似内容

### 规则引擎

**文件**: `app/services/graph_rules.py`

核心方法：
- `analyze_practice()` - 分析练习记录
- `calculate_ability_update()` - 计算能力值更新
- `identify_weak_points()` - 识别薄弱点
- `detect_anomalies()` - 检测异常情况

---

## 测试与质量

### 测试结构

```
tests/
├── conftest.py                 # pytest配置
├── api/                        # API测试
│   └── test_auth.py           # 认证API测试
└── services/                   # 服务测试
    ├── test_auth_service.py
    ├── test_ai_service.py
    ├── test_knowledge_graph_service.py
    ├── test_vector_service.py
    ├── test_graph_rules.py
    └── test_embedding_service.py
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/services/test_knowledge_graph_service.py -v

# 查看覆盖率报告
open htmlcov/index.html
```

### 代码质量工具

```bash
# 代码格式化
black app tests

# 代码检查
ruff check app tests

# 类型检查
mypy app
```

---

## 常见问题

### 数据库连接问题

确认 Docker 服务运行：
```bash
docker-compose ps
```

测试数据库连接：
```bash
psql postgresql://user:password@localhost:5432/ai_english
```

### AI API 调用失败

检查环境变量：
```bash
echo $OPENAI_API_KEY
```

测试 API 连接：
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## 相关文件清单

### 核心文件

| 文件 | 描述 |
|------|------|
| `pyproject.toml` | 项目配置与依赖 |
| `alembic.ini` | 数据库迁移配置 |
| `docker-compose.yml` | Docker服务编排 |
| `app/core/config.py` (待创建) | 配置管理 |
| `app/core/security.py` | 认证与安全 |
| `app/db/base.py` | 数据库基类 |
| `app/api/v1/auth.py` | 认证API |
| `app/api/deps.py` | API依赖 |

### 服务文件

| 文件 | 描述 |
|------|------|
| `app/services/knowledge_graph_service.py` | 知识图谱服务 |
| `app/services/vector_service.py` | 向量搜索服务 |
| `app/services/graph_rules.py` | 规则引擎 |

### 模型文件

| 文件 | 描述 |
|------|------|
| `app/models/knowledge_graph.py` | 知识图谱模型 |

### 测试文件

| 文件 | 描述 |
|------|------|
| `tests/conftest.py` | pytest配置 |
| `tests/api/test_auth.py` | 认证API测试 |
| `tests/services/test_knowledge_graph_service.py` | 知识图谱服务测试 |
| `tests/services/test_vector_service.py` | 向量服务测试 |
| `tests/services/test_graph_rules.py` | 规则引擎测试 |

---

## 变更记录

### 2026-02-03 09:49:22
- 创建后端模块文档
- 整理核心服务与API接口
- 记录数据模型与测试结构
