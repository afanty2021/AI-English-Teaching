[根目录](../CLAUDE.md) > **backend**

# backend - 后端服务模块

> **模块类型**: Python FastAPI 后端服务
> **主要职责**: 提供REST API、业务逻辑处理、数据持久化
> **技术栈**: FastAPI + SQLAlchemy + PostgreSQL + Redis + Qdrant + markdown2 + weasyprint

---

## 模块职责

backend 模块是 AI 赋能英语教学系统的核心后端服务，提供：

1. **用户认证与授权**: JWT token管理、用户注册登录
2. **知识图谱服务**: 学生能力诊断、个性化知识图谱生成与更新
3. **向量搜索服务**: 基于Qdrant的内容相似度搜索
4. **AI服务集成**: OpenAI/Anthropic API调用
5. **内容管理**: 教学内容的CRUD操作
6. **学习记录**: 学生练习记录与进度追踪
7. **错题本系统**: 错题收集、AI分析、复习管理
8. **PDF导出功能**: Markdown转PDF导出（weasyprint）

---

## 入口与启动

### 应用入口

- **主应用**: `app/main.py`
- **当前状态**: 核心服务已实现，API 路由已注册

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
├── /auth/              # 认证授权 (已实现)
│   ├── POST /register
│   ├── POST /login
│   └── GET  /me
├── /students/         # 学生管理 (已实现)
├── /mistakes/         # 错题本 (已实现)
├── /practices/        # 练习记录 (已实现)
├── /contents/         # 内容管理 (已实现)
├── /conversations/    # 口语对话 (已实现)
└── /lesson-plans/     # 教案管理 (已实现)
```

### 核心API端点

**认证接口** (`app/api/v1/auth.py`):
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息

**错题接口** (`app/api/v1/mistakes.py`):
- `POST /api/v1/mistakes/` - 创建错题记录
- `POST /api/v1/mistakes/collect/{practice_id}` - 从练习收集错题
- `GET /api/v1/mistakes/me` - 获取当前学生的错题列表
- `GET /api/v1/mistakes/me/statistics` - 获取错题统计
- `POST /api/v1/mistakes/{mistake_id}/analyze` - AI分析错题
- `POST /api/v1/mistakes/batch-analyze` - 批量AI分析
- `POST /api/v1/mistakes/export` - 导出错题本 (支持 markdown/pdf/word)
- `POST /api/v1/mistakes/{mistake_id}/export` - 导出单个错题

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
| 模板引擎 | Jinja2 | >=3.1.3 |
| **PDF导出** | markdown2, weasyprint, CairoSVG | >=2.4.12, >=60.0,<62.0 |

### PDF导出特定依赖

```toml
# PDF Export (markdown2 + weasyprint)
"markdown2>=2.4.12",
"weasyprint>=60.0,<62.0",    # 使用 61.2
"pydyf==0.8.0",               # 精确版本
"CairoSVG>=2.7.1",
"tinycss2>=1.3.0",
"html5lib>=1.1",
```

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

| 模型 | 文件路径 | 状态 | 描述 |
|------|----------|------|------|
| User | `app/models/user.py` | ✅ 已实现 | 用户基础信息 |
| Student | `app/models/student.py` | ✅ 已实现 | 学生档案 |
| Teacher | `app/models/teacher.py` | ✅ 已实现 | 教师档案 |
| Organization | `app/models/organization.py` | ✅ 已实现 | 组织机构 |
| KnowledgeGraph | `app/models/knowledge_graph.py` | ✅ 已实现 | 知识图谱 |
| Content | `app/models/content.py` | ✅ 已实现 | 教学内容 |
| Practice | `app/models/practice.py` | ✅ 已实现 | 练习记录 |
| Conversation | `app/models/conversation.py` | ✅ 已实现 | 口语对话 |
| Mistake | `app/models/mistake.py` | ✅ 已实现 | 错题本 |
| LessonPlan | `app/models/lesson_plan.py` | ✅ 已实现 | 教案 |
| ClassModel | `app/models/class_model.py` | ✅ 已实现 | 班级 |

---

## 业务服务

### PDF渲染服务 (NEW)

**文件**: `app/services/pdf_renderer_service.py`

**功能**: 使用 markdown2 + weasyprint 实现 Markdown 到 PDF 的转换

核心方法：
- `markdown_to_html()` - Markdown 转 HTML（markdown2）
- `apply_pdf_styles()` - 应用 PDF 样式
- `html_to_pdf()` - HTML 转 PDF（weasyprint）
- `render_markdown_to_pdf()` - 完整渲染流程
- `render_template_to_pdf()` - 从 Jinja2 模板渲染 PDF

### 错题导出服务

**文件**: `app/services/mistake_export_service.py`

**功能**: 错题数据收集、Markdown生成、PDF/Word导出

核心方法：
- `prepare_export_data()` - 准备导出数据
- `render_markdown_report()` - 渲染 Markdown 报告
- `export_as_markdown()` - 导出 Markdown 格式
- `export_as_pdf()` - 导出 PDF 格式 ✨ 已实现
- `export_as_word()` - 导出 Word 格式 (TODO)

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

### AI服务

**文件**: `app/services/ai_service.py`

核心方法：
- `generate_embedding()` - 生成文本向量
- `chat_completion()` - AI 对话完成
- `analyze_student_assessment()` - 学生评估分析

### 规则引擎

**文件**: `app/services/graph_rules.py`

核心方法：
- `analyze_practice()` - 分析练习记录
- `calculate_ability_update()` - 计算能力值更新
- `identify_weak_points()` - 识别薄弱点
- `detect_anomalies()` - 检测异常情况

### 口语服务

**文件**: `app/services/speaking_service.py`

核心方法：
- `create_conversation()` - 创建对话会话
- `send_message()` - 发送消息并获取AI回复

### 教案服务

**文件**: `app/services/lesson_plan_service.py`

核心方法：
- `generate_lesson_plan()` - AI 生成教案

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
    ├── test_pdf_renderer_service.py  # NEW - PDF渲染测试
    └── test_embedding_service.py
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/services/test_pdf_renderer_service.py -v

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

### 测试覆盖率

| 模块 | 覆盖率 | 状态 |
|------|--------|------|
| `pdf_renderer_service.py` | 88% | ✅ |
| `pdf_helpers.py` | 71% | ✅ |

---

## 模板文件

### PDF样式模板

**文件**: `app/templates/pdf_styles.css.j2`

- 完整的 PDF 打印样式（CSS Paged Media）
- 中文字体支持（跨平台兼容）
- 分页控制、页眉页脚、表格样式
- 支持错题详情专用样式类

### Markdown模板

**文件**: `app/templates/mistake_report.md.j2`

**文件**: `app/templates/mistake_detail.md.j2`

---

## 常见问题

### PDF导出问题

确认 PDF 依赖已安装：
```bash
pip list | grep -E "markdown2|weasyprint|pydyf"
```

版本要求：
- weasyprint: 61.2 (必须)
- pydyf: 0.8.0 (精确版本)

### 中文字体问题

字体检测工具位于 `app/utils/pdf_helpers.py`：

```python
from app.utils.pdf_helpers import check_font_availability
font_info = check_font_availability()
print(font_info)
```

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

---

## 相关文件清单

### 核心文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `pyproject.toml` | 项目配置与依赖 | ✅ 已更新 |
| `alembic.ini` | 数据库迁移配置 | ✅ |
| `docker-compose.yml` | Docker服务编排 | ✅ |
| `app/core/config.py` | 配置管理 | ✅ |
| `app/core/security.py` | 认证与安全 | ✅ |
| `app/db/base.py` | 数据库基类 | ✅ |
| `app/main.py` | 主应用入口 | ✅ |

### 服务文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `app/services/pdf_renderer_service.py` | PDF渲染服务 | ✨ 新增 |
| `app/services/mistake_export_service.py` | 错题导出服务 | ✅ 已更新 |
| `app/services/knowledge_graph_service.py` | 知识图谱服务 | ✅ |
| `app/services/vector_service.py` | 向量搜索服务 | ✅ |
| `app/services/ai_service.py` | AI服务 | ✅ |
| `app/services/graph_rules.py` | 规则引擎 | ✅ |
| `app/services/speaking_service.py` | 口语服务 | ✅ |
| `app/services/lesson_plan_service.py` | 教案服务 | ✅ |

### 工具文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `app/utils/pdf_helpers.py` | PDF辅助工具 | ✨ 新增 |
| `app/utils/__init__.py` | 工具模块初始化 | ✨ 新增 |

### 模板文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `app/templates/pdf_styles.css.j2` | PDF样式模板 | ✨ 新增 |
| `app/templates/mistake_report.md.j2` | 错题报告模板 | ✅ |
| `app/templates/mistake_detail.md.j2` | 错题详情模板 | ✅ |

### API文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `app/api/v1/auth.py` | 认证API | ✅ |
| `app/api/v1/mistakes.py` | 错题API | ✅ |
| `app/api/v1/students.py` | 学生API | ✅ |
| `app/api/v1/contents.py` | 内容API | ✅ |
| `app/api/v1/practices.py` | 练习API | ✅ |
| `app/api/v1/conversations.py` | 对话API | ✅ |
| `app/api/v1/lesson_plans.py` | 教案API | ✅ |
| `app/api/deps.py` | API依赖 | ✅ |

### 测试文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `tests/conftest.py` | pytest配置 | ✅ |
| `tests/api/test_auth.py` | 认证API测试 | ✅ |
| `tests/services/test_pdf_renderer_service.py` | PDF渲染测试 | ✨ 新增 |

---

## 变更记录

### 2026-02-03 18:30:00
- ✨ **新增**: PDF渲染服务 (`pdf_renderer_service.py`)
- ✨ **新增**: PDF辅助工具 (`pdf_helpers.py`)
- ✨ **新增**: PDF样式模板 (`pdf_styles.css.j2`)
- ✅ **更新**: 错题导出服务实现PDF导出功能
- ✅ **新增**: PDF渲染单元测试
- 🔧 **更新**: pyproject.toml 添加PDF导出依赖
- 📊 **测试**: PDF渲染服务测试覆盖率88%

### 2026-02-03 09:49:22
- 创建后端模块文档
- 整理核心服务与API接口
- 记录数据模型与测试结构
