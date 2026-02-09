# 部署运维手册

> **文档版本**: v1.0
> **适用版本**: AI 赋能英语教学系统 v1.0+
> **最后更新**: 2026-02-09

---

## 目录

1. [系统概述](#1-系统概述)
2. [环境要求](#2-环境要求)
3. [快速部署](#3-快速部署)
4. [详细配置](#4-详细配置)
5. [服务管理](#5-服务管理)
6. [监控运维](#6-监控运维)
7. [备份恢复](#7-备份恢复)
8. [故障排查](#8-故障排查)
9. [安全加固](#9-安全加固)
10. [性能调优](#10-性能调优)

---

## 1. 系统概述

### 1.1 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户访问层                                   │
├─────────────────────────────────────────────────────────────────────┤
│    教师端 Web    │    学生端 Web    │    移动端 (预留)             │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Nginx / 反向代理                               │
│                   (SSL终结、负载均衡、静态资源)                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌───────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│     前端 (Vue3)       │ │   后端 (FastAPI) │ │    AI 服务         │
│    静态资源服务       │ │   REST API       │ │  (OpenAI/Claude)   │
└───────────────────────┘ └─────────────────┘ └─────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌───────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   PostgreSQL 15       │ │   Redis 7      │ │    Qdrant          │
│   主数据库            │ │   缓存/会话    │ │    向量数据库       │
└───────────────────────┘ └─────────────────┘ └─────────────────────┘
```

### 1.2 组件清单

| 组件 | 版本 | 端口 | 说明 |
|------|------|------|------|
| **Frontend** | Vue3 | 5173 | 开发服务器 |
| **Backend** | FastAPI | 8000 | API 服务 |
| **PostgreSQL** | 15 | 5432 | 主数据库 |
| **Redis** | 7 | 6379 | 缓存/会话 |
| **Qdrant** | 1.7+ | 6333 | 向量检索 |
| **Nginx** | 1.24 | 80/443 | 反向代理 |

### 1.3 技术栈

| 层级 | 技术选型 |
|------|----------|
| 前端 | Vue3 + Vite + Pinia + Element Plus + ECharts |
| 后端 | FastAPI + SQLAlchemy + Alembic |
| 数据库 | PostgreSQL 15 + Redis 7 + Qdrant |
| AI服务 | OpenAI GPT-4 / Anthropic Claude |
| PDF导出 | markdown2 + weasyprint 61.2 |
| 部署 | Docker + Docker Compose |

---

## 2. 环境要求

### 2.1 硬件要求

| 部署规模 | CPU | 内存 | 磁盘 | 网络 |
|---------|------|------|------|------|
| **开发环境** | 4核 | 8GB | 50GB SSD | 百兆 |
| **测试环境** | 8核 | 16GB | 100GB SSD | 千兆 |
| **生产环境** | 16核 | 32GB+ | 200GB+ SSD | 千兆 |

### 2.2 软件要求

#### 必需软件

| 软件 | 最低版本 | 推荐版本 | 用途 |
|------|----------|----------|------|
| Docker | 20.10 | 24.0+ | 容器化部署 |
| Docker Compose | 2.0 | 2.20+ | 多容器编排 |
| Git | 2.0 | 2.40+ | 版本控制 |

#### 可选软件

| 软件 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 本地开发 |
| Node.js | 18+ | 前端开发 |
| pgAdmin | Latest | 数据库管理 |

### 2.3 网络要求

**出站端口**：
- 443 (HTTPS) - AI API 调用
- 5432 - PostgreSQL 连接
- 6379 - Redis 连接
- 6333 - Qdrant 连接

**入站端口**：
- 80/443 - Web 访问
- 22 - SSH (可选)

---

## 3. 快速部署

### 3.1 克隆项目

```bash
# 克隆项目
git clone https://github.com/your-org/AI-English-Teaching-System.git
cd AI-English-Teaching-System
```

### 3.2 环境准备

#### 使用 Docker Compose 启动基础服务

```bash
# 进入后端目录
cd backend

# 启动基础服务 (PostgreSQL, Redis, Qdrant)
docker-compose up -d

# 检查服务状态
docker-compose ps

# 预期输出：
# NAME                  STATUS    PORTS
# -----------------------------------------------------------------------
# backend-postgres-1    Up        0.0.0.0:5432->5432/tcp
# backend-redis-1       Up        0.0.0.0:6379->6379/tcp
# backend-qdrant-1     Up        0.0.0.0:6333->6333/tcp
```

### 3.3 后端部署

#### 1. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[dev]"
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

**`.env` 文件配置示例**：

```env
# ============ 数据库配置 ============
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_english

# ============ Redis配置 ============
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# ============ Qdrant配置 ============
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_VECTOR_SIZE=1536

# ============ JWT认证配置 ============
JWT_SECRET_KEY=your-secure-jwt-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============ OpenAI配置 ============
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small

# ============ Anthropic配置 ============
ANTHROPIC_API_KEY=your-anthropic-api-key

# ============ 文件存储 ============
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=10485760  # 10MB

# ============ 日志配置 ============
LOG_LEVEL=INFO
LOG_FORMAT=json
```

#### 3. 数据库迁移

```bash
# 执行数据库迁移
alembic upgrade head

# 验证迁移成功
alembic current
```

#### 4. 创建测试数据（可选）

```bash
# 创建测试用户
python scripts/create_test_data.py
```

#### 5. 启动后端服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用后台运行
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > logs/uvicorn.log 2>&1 &
```

### 3.4 前端部署

#### 1. 安装依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install
```

#### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（API 地址）
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

#### 3. 启动开发服务器

```bash
npm run dev
```

#### 4. 生产构建

```bash
# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

### 3.5 验证部署

#### 1. 检查后端服务

```bash
# 检查 API 健康
curl http://localhost:8000/health

# 预期响应：
# {"status": "healthy", "version": "1.0.0"}
```

#### 2. 检查前端服务

```
浏览器访问: http://localhost:5173
```

#### 3. 登录测试

使用测试账号登录：

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 教师 | test_teacher | Test1234 |
| 学生 | test_student | Test1234 |

---

## 4. 详细配置

### 4.1 Docker Compose 配置

#### 开发环境 `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: ai-english-postgres
    environment:
      POSTGRES_DB: ai_english
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: ai-english-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: ai-english-qdrant
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
    environment:
      QDRANT__LOG__LEVEL: INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  qdrant_data:

networks:
  default:
    name: ai-english-network
```

### 4.2 Nginx 配置（生产环境）

```nginx
# /etc/nginx/sites-available/ai-english.conf

upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream frontend {
    server 127.0.0.1:5173;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # 前端静态资源
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 文件上传大小
        client_max_body_size 50M;
    }

    # 静态资源
    location /static/ {
        alias /path/to/frontend/dist/assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 文件上传
    location /uploads/ {
        alias /path/to/backend/uploads/;
        expires 7d;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy";
        add_header Content-Type text/plain;
    }
}
```

### 4.3 环境变量详解

#### 数据库配置

```env
# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database

# 连接池配置
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
```

#### Redis 配置

```env
# Redis 连接
REDIS_URL=redis://:password@host:6379/0

# 会话配置
REDIS_SESSION_PREFIX=sess:
SESSION_EXPIRE_HOURS=24

# 缓存配置
REDIS_CACHE_PREFIX=cache:
STUDENT_PROFILE_TTL=300      # 5分钟
STUDENT_KG_TTL=600           # 10分钟
USER_PROFILE_TTL=300         # 5分钟
CLASS_STUDENTS_TTL=120       # 2分钟
```

#### AI 服务配置

```env
# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4096
OPENAI_TEMPERATURE=0.7
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIM=1536

# Anthropic
ANTHROPIC_API_KEY=ant-xxx
ANTHROPIC_MODEL=claude-3-opus-20240229
ANTHROPIC_MAX_TOKENS=4096
```

### 4.4 日志配置

```env
# 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# 日志格式: json, plain
LOG_FORMAT=json

# 日志文件
LOG_DIR=logs
LOG_FILE=app.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# 结构化日志
STRUCTURED_LOGGING=true
```

---

## 5. 服务管理

### 5.1 服务启停

#### Docker Compose 管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启所有服务
docker-compose restart

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend

# 查看服务状态
docker-compose ps
```

#### 服务单独管理

```bash
# 启动特定服务
docker-compose start postgres
docker-compose start redis
docker-compose start qdrant

# 停止特定服务
docker-compose stop postgres

# 重启特定服务
docker-compose restart backend
```

### 5.2 后端服务管理

#### 使用 Systemd（生产环境）

创建服务文件 `/etc/systemd/system/ai-english-backend.service`：

```ini
[Unit]
Description=AI English Teaching Backend Service
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/ai-english/backend
Environment="PATH=/opt/ai-english/backend/venv/bin"
ExecStart=/opt/ai-english/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=append:/var/log/ai-english/backend.log
StandardError=append:/var/log/ai-english/backend-error.log

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
# 重新加载 systemd
systemctl daemon-reload

# 启用服务
systemctl enable ai-english-backend

# 启动服务
systemctl start ai-english-backend

# 查看状态
systemctl status ai-english-backend

# 查看日志
journalctl -u ai-english-backend -f
```

### 5.3 健康检查

#### API 健康端点

```bash
# 检查后端健康
curl http://localhost:8000/health

# 响应示例：
# {
#   "status": "healthy",
#   "version": "1.0.0",
#   "components": {
#     "database": "healthy",
#     "redis": "healthy",
#     "qdrant": "healthy"
#   }
# }
```

#### Docker 健康检查

```bash
# 检查容器健康状态
docker inspect --format='{{.State.Health.Status}}' backend-postgres-1
docker inspect --format='{{.State.Health.Status}}' backend-redis-1
docker inspect --format='{{.State.Health.Status}}' backend-qdrant-1
```

---

## 6. 监控运维

### 6.1 日志管理

#### 日志查看

```bash
# 后端日志
tail -f logs/app.log

# 聚合日志
tail -f logs/*.log

# 搜索错误
grep "ERROR" logs/app.log

# 查看最近100行
tail -n 100 logs/app.log
```

#### 日志轮转

使用 `logrotate` 配置日志轮转：

```
# /etc/logrotate.d/ai-english

/opt/ai-english/backend/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload ai-english-backend > /dev/null 2>&1 || true
    endscript
}
```

### 6.2 性能监控

#### Prometheus 指标端点

```bash
# 获取指标
curl http://localhost:8000/metrics

# 关键指标：
# - http_requests_total 请求总数
# - http_request_duration_seconds 请求延迟
# - db_query_duration_seconds 数据库查询延迟
# - cache_hit_total 缓存命中
# - cache_miss_total 缓存未命中
```

#### 导出任务监控

```bash
# 检查导出任务状态
curl http://localhost:8000/api/v1/exports/tasks

# 响应示例：
# {
#   "active_tasks": 2,
#   "queued_tasks": 1,
#   "completed_today": 15,
#   "failed_today": 0
# }
```

### 6.3 资源监控

#### Docker Stats

```bash
# 查看容器资源使用
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# 输出示例：
# NAME                 CPU %   MEM USAGE / LIMIT
# backend-postgres-1   0.5%   256MB / 8GB
# backend-redis-1      0.2%   32MB / 2GB
# backend-qdrant-1     1.2%   512MB / 4GB
# backend-app-1         2.5%   512MB / 4GB
```

#### cAdvisor（可选）

```bash
# 启动 cAdvisor
docker run \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker:/var/lib/docker:ro \
  --publish=8080:8080 \
  --detach=true \
  --name=cadvisor \
  google/cadvisor:latest
```

访问 `http://localhost:8080` 查看资源监控面板。

### 6.4 告警配置

#### 告警规则示例（Prometheus Alertmanager）

```yaml
# alerts.yml

groups:
  - name: ai-english-alerts
    rules:
      # 服务宕机
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "服务 {{ $labels.job }} 已宕机"

      # CPU 使用率过高
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率超过 80%"

      # 内存不足
      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率超过 85%"

      # 磁盘空间不足
      - alert: LowDiskSpace
        expr: (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) * 100 > 90
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "磁盘空间不足 90%"

      # 数据库连接池耗尽
      - alert: DBConnectionPoolExhausted
        expr: pg_stat_activity_count > pg_settings_max_connections * 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "数据库连接池接近耗尽"
```

---

## 7. 备份恢复

### 7.1 数据库备份

#### PostgreSQL 备份

```bash
#!/bin/bash
# backup_db.sh

# 配置
BACKUP_DIR="/opt/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="ai_english"
DB_USER="postgres"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份（压缩）
pg_dump -U $DB_USER -d $DB_NAME | gzip > $BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz

# 保留最近30天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# 输出日志
echo "[$(date)] Backup completed: ${DB_NAME}_${DATE}.sql.gz"
```

#### 添加 cron 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加每日凌晨2点备份
0 2 * * * /opt/scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

### 7.2 Redis 备份

```bash
#!/bin/bash
# backup_redis.sh

BACKUP_DIR="/opt/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# BGSAVE 触发后台保存
redis-cli BGSAVE

# 等待保存完成
while [ $(redis-cli LASTSAVE) == $(redis-cli LASTSAVE) ]; do
    sleep 1
done

# 复制 RDB 文件
cp /data/dump.rdb $BACKUP_DIR/dump_${DATE}.rdb
gzip $BACKUP_DIR/dump_${DATE}.rdb

# 保留最近7天备份
find $BACKUP_DIR -name "*.rdb.gz" -mtime +7 -delete
```

### 7.3 Qdrant 备份

```bash
#!/bin/bash
# backup_qdrant.sh

BACKUP_DIR="/opt/backups/qdrant"
DATE=$(date +%Y%m%d_%H%M%S)
COLLECTION_NAME="contents"

mkdir -p $BACKUP_DIR

# 导出集合数据
curl -X POST "http://localhost:6333/collections/${COLLECTION_NAME}/points/export" \
  -H "Content-Type: application/json" \
  -d '{"export_params": {"file":"points.jsonl"}}' \
  > $BACKUP_DIR/qdrant_${DATE}.jsonl.gz

# 保留最近30天备份
find $BACKUP_DIR -name "*.jsonl.gz" -mtime +30 -delete
```

### 7.4 完整备份脚本

```bash
#!/bin/bash
# full_backup.sh

BACKUP_BASE="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_BASE}/full_${DATE}"

mkdir -p $BACKUP_DIR

echo "[$(date)] Starting full backup..."

# 备份数据库
echo "Backing up PostgreSQL..."
pg_dump -U postgres ai_english | gzip > $BACKUP_DIR/database.sql.gz

# 备份 Redis
echo "Backing up Redis..."
redis-cli BGSAVE
cp /data/dump.rdb $BACKUP_DIR/dump.rdb
gzip $BACKUP_DIR/dump.rdb

# 备份 Qdrant
echo "Backing up Qdrant..."
curl -X POST "http://localhost:6333/collections/contents/points/export" \
  -H "Content-Type: application/json" \
  -d '{"export_params": {"file":"points.jsonl"}}' \
  > $BACKUP_DIR/qdrant.jsonl
gzip $BACKUP_DIR/qdrant.jsonl

# 备份上传文件
echo "Backing up uploads..."
tar -czf $BACKUP_DIR/uploads.tar.gz /opt/ai-english/backend/uploads

# 备份配置文件
echo "Backing up config..."
tar -czf $BACKUP_DIR/config.tar.gz /opt/ai-english/backend/.env

# 创建备份清单
cat > $BACKUP_DIR/manifest.txt << EOF
Backup Date: $DATE
PostgreSQL: database.sql.gz
Redis: dump.rdb.gz
Qdrant: qdrant.jsonl.gz
Uploads: uploads.tar.gz
Config: config.tar.gz
EOF

echo "[$(date)] Backup completed: $BACKUP_DIR"
```

### 7.5 恢复操作

#### 恢复 PostgreSQL

```bash
# 停止应用
systemctl stop ai-english-backend

# 删除并重建数据库
docker-compose stop postgres
rm -rf postgres_data/*
docker-compose start postgres

# 等待数据库启动
sleep 5

# 恢复数据
gunzip -c /opt/backups/postgres/ai_english_20260208_020000.sql.gz | \
  psql -U postgres -d ai_english

# 启动应用
systemctl start ai-english-backend
```

#### 恢复 Redis

```bash
# 停止 Redis
docker-compose stop redis

# 备份当前数据
mv redis_data/dump.rdb redis_data/dump.rdb.bak

# 解压备份
gunzip /opt/backups/redis/dump_20260208_020000.rdb.gz -c > redis_data/dump.rdb

# 启动 Redis
docker-compose start redis
```

---

## 8. 故障排查

### 8.1 常见问题

#### 问题 1：数据库连接失败

**症状**：
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**排查步骤**：

```bash
# 1. 检查 PostgreSQL 容器状态
docker ps | grep postgres

# 2. 检查容器日志
docker-compose logs postgres

# 3. 检查端口监听
netstat -tlnp | grep 5432

# 4. 测试连接
psql -h localhost -U postgres -d ai_english
```

**解决方案**：

```bash
# 如果容器未运行
docker-compose start postgres

# 如果数据损坏，重建数据库
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

#### 问题 2：Redis 连接失败

**症状**：
```
redis.exceptions.ConnectionError: Error while reading from socket
```

**排查步骤**：

```bash
# 1. 检查 Redis 容器状态
docker ps | grep redis

# 2. 测试 Redis 连接
redis-cli ping

# 3. 检查内存使用
redis-cli info memory
```

**解决方案**：

```bash
# 重启 Redis
docker-compose restart redis

# 如果内存不足，清理数据
redis-cli FLUSHDB
```

#### 问题 3：Qdrant 向量服务异常

**症状**：
```
qdrant_client.common.PayloadValidationError: Field with payload
```

**排查步骤**：

```bash
# 1. 检查 Qdrant 健康
curl http://localhost:6333/health

# 2. 检查集合状态
curl http://localhost:6333/collections/contents

# 3. 查看 Qdrant 日志
docker-compose logs qdrant
```

#### 问题 4：AI API 调用失败

**症状**：
```
openai.error.RateLimitError: Rate limit reached
```

**排查步骤**：

```bash
# 1. 检查 API 密钥配置
cat .env | grep OPENAI

# 2. 测试 API 连接
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 3. 检查 API 配额
# 访问 OpenAI Dashboard 查看使用量
```

**解决方案**：

```bash
# 1. 添加重试逻辑
# 在代码中配置 max_retries

# 2. 使用备用 API
# 配置 Anthropic 作为备用

# 3. 降级使用
# 使用更小的模型
OPENAI_MODEL=gpt-3.5-turbo
```

#### 问题 5：PDF 导出失败

**症状**：
```
weasyprint.exceptions.WeasyPrintError: Failed to find font
```

**排查步骤**：

```bash
# 1. 检查字体安装
fc-list | grep "Noto Sans"

# 2. 检查字体缓存
fc-cache -fv

# 3. 查看 PDF 渲染日志
docker-compose logs backend | grep PDF
```

**解决方案**：

```bash
# 安装中文字体
# Ubuntu/Debian
apt-get install fonts-noto-cjk

# macOS
brew install font-noto-cjk

# 重建字体缓存
fc-cache -fv
```

### 8.2 诊断命令

```bash
#!/bin/bash
# diagnose.sh

echo "=== AI English Teaching System Diagnostic Report ==="
echo "Date: $(date)"
echo

echo "=== Docker Services Status ==="
docker-compose ps
echo

echo "=== Service Health Checks ==="
echo "Backend: $(curl -s http://localhost:8000/health || echo 'FAILED')"
echo "PostgreSQL: $(pg_isready -U postgres && echo 'OK' || echo 'FAILED')"
echo "Redis: $(redis-cli ping && echo 'OK' || echo 'FAILED')"
echo "Qdrant: $(curl -s http://localhost:6333/health || echo 'FAILED')"
echo

echo "=== Resource Usage ==="
docker stats --no-stream
echo

echo "=== Recent Errors (Last 100 lines) ==="
tail -n 100 logs/app.log | grep -i error || echo "No recent errors found"
echo

echo "=== Disk Usage ==="
df -h
echo

echo "=== Memory Usage ==="
free -h
echo

echo "=== End of Diagnostic Report ==="
```

### 8.3 日志分析

```bash
# 分析错误频率
grep "ERROR" logs/app.log | awk -F'{' '{print $NF}' | sort | uniq -c | sort -rn | head -20

# 分析慢请求
grep "slow" logs/app.log

# 分析 API 响应时间
grep "duration" logs/app.log | awk '{print $NF}' | sort -rn | head -20
```

---

## 9. 安全加固

### 9.1 服务器安全

#### SSH 加固

```bash
# /etc/ssh/sshd_config

# 禁用 root 登录
PermitRootLogin no

# 禁用密码登录，使用密钥
PasswordAuthentication no
PubkeyAuthentication yes

# 限制登录尝试次数
MaxAuthTries 3

# 限制登录 IP
AllowUsers admin@192.168.1.0/24 teacher@192.168.1.0/24
```

#### 防火墙配置

```bash
# 使用 UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
ufw enable
```

### 9.2 应用安全

#### JWT 安全配置

```python
# app/core/security.py

# 关键配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 较短的过期时间
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 生产环境使用强密钥
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # 至少32位
```

#### API 速率限制

```python
# app/core/rate_limiter.py

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# 登录限制：5次/分钟
@router.post("/login")
@limiter.limit("5/minute")
async def login():
    ...

# API 请求限制：100次/分钟
@router.get("/students")
@limiter.limit("100/minute")
async def list_students():
    ...
```

### 9.3 数据库安全

#### PostgreSQL 安全配置

```sql
-- 创建应用专用用户
CREATE USER ai_english_app WITH PASSWORD 'strong_password_here';
GRANT ALL PRIVILEGES ON DATABASE ai_english TO ai_english_app;

-- 限制数据库访问
REVOKE CONNECT ON DATABASE ai_english FROM PUBLIC;
GRANT CONNECT ON DATABASE ai_english TO ai_english_app;

-- 限制 schema 访问
GRANT USAGE ON SCHEMA public TO ai_english_app;
GRANT ALL ON SCHEMA public TO ai_english_app;
```

### 9.4 加密配置

#### SSL/TLS 证书

使用 Let's Encrypt 免费证书：

```bash
# 安装 certbot
apt-get install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
echo "0 0 * * * certbot renew --quiet" | crontab -
```

### 9.5 敏感数据保护

```bash
# 设置文件权限
chmod 600 .env          # 环境变量文件
chmod 600 uploads/*     # 上传文件
chmod 700 logs/         # 日志目录
```

---

## 10. 性能调优

### 10.1 数据库优化

#### PostgreSQL 配置优化

```sql
-- /var/lib/postgresql/data/postgresql.conf

# 内存配置
shared_buffers = 256MB                    # 总内存的25%
effective_cache_size = 1GB               # 总内存的50%
work_mem = 64MB                          # 复杂查询工作内存
maintenance_work_mem = 256MB             # 维护操作内存

# 连接配置
max_connections = 100

# WAL 配置
wal_buffers = 64MB
checkpoint_completion_target = 0.9

# 查询优化
random_page_cost = 1.1                   # SSD 优化
effective_io_concurrency = 200          # SSD 优化
default_statistics_target = 100

# 自动清理
autovacuum = on
autovacuum_naptime = 30s
autovacuum_vacuum_cost_delay = 5ms
```

#### 索引优化

```sql
-- 创建常用查询索引
CREATE INDEX idx_student_user_id ON students(user_id);
CREATE INDEX idx_practice_student_id ON practices(student_id);
CREATE INDEX idx_conversation_student_id ON conversations(student_id);
CREATE INDEX idx_mistake_student_id ON mistakes(student_id);
CREATE INDEX idx_learning_report_student_id ON learning_reports(student_id);

-- 部分索引（只索引活跃数据）
CREATE INDEX idx_class_student_active ON class_students(class_id)
  WHERE enrollment_status = 'active';

-- 向量索引（Qdrant）
-- Qdrant 自动创建 HNSW 索引
```

### 10.2 Redis 优化

```bash
# /etc/redis/redis.conf

# 内存配置
maxmemory 1gb
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec

# 连接配置
timeout 300
tcp-keepalive 300
```

### 10.3 应用优化

#### 连接池配置

```python
# app/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
```

#### 缓存策略

```python
# app/services/student_cache_service.py

class StudentCacheService:
    # 学生档案缓存：5分钟
    _STUDENT_PROFILE_TTL = 5 * 60

    # 知识图谱缓存：10分钟
    _STUDENT_KG_TTL = 10 * 60

    # 用户信息缓存：5分钟
    _USER_PROFILE_TTL = 5 * 60

    # 班级学生列表缓存：2分钟
    _CLASS_STUDENTS_TTL = 2 * 60
```

### 10.4 前端优化

#### 构建优化配置

```typescript
// vite.config.ts

export default defineConfig({
  build: {
    // 代码分割
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'echarts': ['echarts'],
          'router-store': ['vue-router', 'pinia'],
        }
      }
    },
    // 压缩
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    // CSS 代码分割
    cssCodeSplit: true,
  }
})
```

### 10.5 负载均衡（可选）

#### Nginx 负载均衡配置

```nginx
upstream backend {
    least_conn;  # 最少连接算法

    server 127.0.0.1:8000 weight=1;
    server 10.0.0.2:8000 weight=1;  # 第二个实例
    server 10.0.0.3:8000 weight=1;  # 第三个实例

    keepalive 64;
}

server {
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";

        # 健康检查
        proxy_next_upstream error timeout invalid_header http_500;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }
}
```

---

## 附录

### A. 端口映射

| 服务 | 容器端口 | 主机端口 | 协议 |
|------|---------|---------|------|
| PostgreSQL | 5432 | 5432 | TCP |
| Redis | 6379 | 6379 | TCP |
| Qdrant | 6333 | 6333 | TCP |
| Backend | 8000 | 8000 | TCP |
| Frontend Dev | 5173 | 5173 | TCP |
| Nginx | 80, 443 | 80, 443 | TCP |

### B. 目录结构

```
/opt/ai-english/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── uploads/
│   ├── venv/
│   ├── .env
│   └── docker-compose.yml
│
├── frontend/
│   ├── src/
│   ├── dist/
│   └── node_modules/
│
├── nginx/
│   └── nginx.conf
│
├── scripts/
│   ├── backup_db.sh
│   ├── backup_redis.sh
│   ├── backup_qdrant.sh
│   └── full_backup.sh
│
├── logs/
│   ├── app.log
│   └── app-error.log
│
└── backups/
    ├── postgres/
    ├── redis/
    └── qdrant/
```

### C. 联系信息

**技术支持**：
- 邮箱：support@example.com
- 电话：400-xxx-xxxx

**紧急响应**：
- 7×24 小时响应热线：xxx-xxxx-xxxx

### D. 参考文献

- [FastAPI 官方文档](https://fastapi.tiangolo.com)
- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [Redis 官方文档](https://redis.io/documentation)
- [Qdrant 官方文档](https://qdrant.tech/documentation)
- [Docker 官方文档](https://docs.docker.com)

---

*文档版本: v1.0 | 最后更新: 2026-02-09*
