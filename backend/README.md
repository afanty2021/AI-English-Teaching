# AI English Teaching System - Backend

AI 赋能的个性化英语学习平台后端服务。

## 技术栈

- **FastAPI** - 异步 Web 框架
- **PostgreSQL** - 主数据库
- **Redis** - 缓存和消息队列
- **Qdrant** - 向量数据库
- **Alembic** - 数据库迁移

## 快速开始

### 使用 Docker Compose

```bash
docker-compose up -d
```

### 本地开发

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## API 文档

启动服务后访问：http://localhost:8000/docs
