# AI English Teaching System - Backend

基于 FastAPI 的 AI 驱动英语教学系统后端服务，提供用户管理、课程内容、AI 对话、语音识别等功能。

## 功能特性

- 用户认证与授权
- AI 智能对话（OpenAI GPT-4 / Anthropic Claude）
- 语音识别与合成
- 语法检查与纠错
- 词汇学习与追踪
- 学习进度分析
- 向量数据库搜索

## 技术栈

- **Web 框架**: FastAPI 0.109+
- **数据库**: PostgreSQL 15 + SQLAlchemy 2.0
- **缓存**: Redis 7
- **向量数据库**: Qdrant
- **AI 模型**: OpenAI GPT-4, Anthropic Claude 3
- **异步运行时**: asyncio + uvicorn

## 快速开始

### 前置要求

- Python 3.11+
- Docker & Docker Compose
- Git

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/ai-english-teaching-system.git
cd ai-english-teaching-system/backend
```

### 2. 启动基础服务

使用 Docker Compose 启动 PostgreSQL、Redis 和 Qdrant：

```bash
docker-compose up -d
```

验证服务状态：

```bash
docker-compose ps
```

应该看到所有服务都是 `Up` 状态。

### 3. 安装 Python 依赖

创建虚拟环境：

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

安装依赖：

```bash
pip install -e ".[dev]"
```

### 4. 配置环境变量

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下必要参数：

```env
# 数据库连接
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/english_teaching

# Redis 连接
REDIS_URL=redis://localhost:6379/0

# OpenAI API（必需）
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic API（可选）
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# JWT 密钥（生产环境必须修改）
SECRET_KEY=your_secret_key_change_this_in_production
```

### 5. 初始化数据库

运行数据库迁移：

```bash
alembic upgrade head
```

### 6. 启动开发服务器

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或者使用 Makefile：

```bash
make dev
```

服务将在 http://localhost:8000 启动。

### 7. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发指南

### 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由
│   │   └── v1/          # API v1 版本
│   ├── core/            # 核心配置与工具
│   ├── models/          # SQLAlchemy 数据模型
│   ├── schemas/         # Pydantic 数据模式
│   ├── services/        # 业务逻辑服务
│   ├── db/              # 数据库会话管理
│   └── main.py          # FastAPI 应用入口
├── tests/               # 测试代码
├── alembic/             # 数据库迁移
├── pyproject.toml       # 项目配置
├── docker-compose.yml   # Docker 服务编排
└── README.md            # 本文件
```

### 运行测试

```bash
pytest
```

运行测试并生成覆盖率报告：

```bash
pytest --cov=app --cov-report=html
```

### 代码格式化

使用 Black 格式化代码：

```bash
black app tests
```

使用 Ruff 进行代码检查：

```bash
ruff check app tests
```

### 类型检查

```bash
mypy app
```

## Docker 命令

启动所有服务：

```bash
docker-compose up -d
```

查看服务日志：

```bash
docker-compose logs -f
```

查看特定服务日志：

```bash
docker-compose logs -f postgres
```

停止所有服务：

```bash
docker-compose down
```

停止并删除所有数据：

```bash
docker-compose down -v
```

启动管理工具：

```bash
docker-compose --profile tools up -d
```

这将启动 PgAdmin (http://localhost:5050) 和 Redis Commander (http://localhost:8081)。

## 环境变量说明

### 数据库配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql+asyncpg://postgres:postgres@localhost:5432/english_teaching` |
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379/0` |
| `QDRANT_HOST` | Qdrant 主机 | `localhost` |
| `QDRANT_PORT` | Qdrant HTTP 端口 | `6333` |

### AI 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | 必需 |
| `OPENAI_MODEL` | GPT 模型名称 | `gpt-4-turbo-preview` |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 可选 |
| `ANTHROPIC_MODEL` | Claude 模型名称 | `claude-3-opus-20240229` |

### 认证配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `SECRET_KEY` | JWT 签名密钥 | 必需（生产环境必须修改） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 访问令牌过期时间（分钟） | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 刷新令牌过期时间（天） | `7` |

## 生产部署

### 使用 Docker 构建镜像

```bash
docker build -t ai-english-backend .
```

### 使用 Docker Compose 部署

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 环境检查清单

- [ ] 修改 `SECRET_KEY` 为强随机密钥
- [ ] 设置 `ENVIRONMENT=production`
- [ ] 配置真实的数据库连接
- [ ] 配置 AI API 密钥
- [ ] 启用 HTTPS
- [ ] 配置 CORS 允许的域名
- [ ] 设置适当的日志级别
- [ ] 配置监控和告警

## 常见问题

### Docker 服务启动失败

检查端口是否被占用：

```bash
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :6333  # Qdrant
```

### 数据库连接失败

确认 Docker 服务正在运行：

```bash
docker-compose ps
```

测试数据库连接：

```bash
psql postgresql://postgres:postgres@localhost:5432/english_teaching
```

### AI API 调用失败

确认 API 密钥已正确配置：

```bash
echo $OPENAI_API_KEY
```

测试 API 连接：

```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## 许可证

MIT License

## 联系方式

- 项目主页: https://github.com/yourusername/ai-english-teaching-system
- 问题反馈: https://github.com/yourusername/ai-english-teaching-system/issues
