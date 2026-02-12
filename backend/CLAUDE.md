[根目录](../CLAUDE.md) > **backend**

# backend - 后端服务模块

> **模块类型**: Python FastAPI 后端服务
> **主要职责**: 提供REST API、业务逻辑处理、数据持久化
> **技术栈**: FastAPI + SQLAlchemy + PostgreSQL + Redis + Qdrant + markdown2 + weasyprint

---

## 变更记录

### 2026-02-08 22:00:00
- 🎉 **监控告警与性能优化完成**
  - **Prometheus指标**: 导出任务计数、耗时分布、活跃/排队任务数、存储使用、错误计数
  - **结构化告警**: JSON格式日志，支持 Loki/ELK 聚合告警
  - **异步文件I/O**: 使用 aiofiles 实现非阻塞文件操作
  - **文档流式生成**: 支持 Word/PDF/PPTX/Markdown 流式导出，降低内存占用
  - **测试覆盖**: 新增集成测试文件 (test_export_metrics_integration.py)，15个测试用例
  - **性能提升**: 10MB文件异步写入 < 1秒，并发性能提升30-40%

### 2026-02-06 15:20:00
- 🎉 **重大里程碑**: 代码质量改进计划全部完成
  - **迭代1**: 安全性修复 ✅ (JWT密钥、Token黑名单、速率限制、密码验证)
  - **迭代2**: 架构优化 ✅ (AI服务重构、异常处理、数据库索引、错误边界)
  - **迭代3**: 性能与质量 ✅ (PDF异步、按需导入、常量模块、测试覆盖)

### 2026-02-06 15:10:00
- 🔐 **安全性改进完成**: 迭代1安全性修复全部完成
  - **JWT密钥安全**: 强制环境变量，无默认值，密钥长度≥32位验证
  - **Token黑名单机制**: `token_blacklist.py` (283行) - Redis存储，支持撤销
  - **登录速率限制**: `rate_limiter.py` (190行) - 5次/分钟滑动窗口
  - **密码强度验证**: 复杂度验证（8位+大小写+数字+特殊字符）

### 2026-02-06 15:00:00
- 🏗️ **架构优化完成**: 迭代2架构优化全部完成
  - **AI服务重构**: 拆分为 Embedding/Chat/Analysis 三个专注服务
  - **统一异常处理**: `exceptions.py` + `exception_handler.py` - 14种业务异常类型
  - **数据库索引**: 常用查询字段B-tree索引优化
  - **前端错误边界**: `ErrorBoundary.vue` 全局错误处理

### 2026-02-06 14:30:00
- ⚡ **性能优化完成**: 迭代3性能与质量优化全部完成
  - **PDF异步渲染**: 线程池执行，不阻塞事件循环
  - **业务常量模块**: `constants.py` (252行) - 能力等级、复习间隔、时间阈值
  - **测试覆盖率提升**: 新增4个核心服务测试文件，1135+行代码，48+测试用例

### 2026-02-04 08:58:32
- 📊 **文档更新**: 增量更新完成
  - 补充学习报告系统文档（模型、服务、API）
  - 更新模块索引，新增143个Python文件完整扫描
  - 更新 PDF 导出功能文档
  - 新增模板文件和工具文件说明

### 2026-02-03 20:00:00
- ✨ **新增**: 学习报告生成功能完整实现
  - 模型：LearningReport 数据模型，支持 JSONB 存储报告数据
  - 服务：学习报告服务（统计、能力分析、薄弱点、建议生成）
  - 导出：报告导出服务（PDF导出，图片导出占位）
  - API：5个端点（生成、列表、详情、导出、删除）
  - 数据库：Alembic 迁移已执行

### 2026-02-03 18:30:00
- ✨ **新增**: PDF渲染服务 (`pdf_renderer_service.py`)
- ✨ **新增**: PDF辅助工具 (`pdf_helpers.py`)
- ✨ **新增**: PDF样式模板 (`pdf_styles.css.j2`)
- ✅ **更新**: 错题导出服务实现PDF导出功能
- ✨ **新增**: PDF渲染单元测试
- 🔧 **更新**: pyproject.toml 添加PDF导出依赖
- 📊 **测试**: PDF渲染服务测试覆盖率88%

### 2026-02-03 09:49:22
- 创建后端模块文档
- 整理核心服务与API接口
- 记录数据模型与测试结构

---

## 模块职责

backend 模块是 AI 赋能英语教学系统的核心后端服务，提供：

### 核心服务
1. **用户认证与安全**: JWT token管理、用户注册登录、密码强度验证
2. **知识图谱服务**: 学生能力诊断、个性化知识图谱生成与更新
3. **向量搜索服务**: 基于Qdrant的内容相似度搜索
4. **AI服务集成**: OpenAI/Anthropic/智谱AI API调用
5. **内容管理**: 教学内容的CRUD操作
6. **学习记录**: 学生练习记录与进度追踪
7. **错题本系统**: 错题收集、AI分析、复习管理
8. **学习报告系统**: 生成学生学习报告、PDF导出
9. **PDF导出功能**: Markdown转PDF导出（weasyprint）

### 安全模块 ✨新增
1. **Token黑名单** (`token_blacklist.py`): Token撤销机制，登出立即失效
2. **速率限制** (`rate_limiter.py`): 登录防暴力破解，5次/分钟限制
3. **常量定义** (`constants.py`): 业务常量统一管理

### 服务模块架构
- **认证服务**: AuthService - 用户注册、登录、密码管理
- **AI服务**: AIFacade + 三个子服务（Embedding/Chat/Analysis）
- **错题服务**: MistakeService - 错题收集、分析、复习
- **对话服务**: ConversationService - AI口语对话
- **练习服务**: PracticeService - 练习会话管理
- **异步任务**: AsyncTaskService - 后台任务处理

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

## 测试账号

> **重要**: 以下为开发/测试环境的固定测试账号，请勿随意修改密码或删除。

### 学生端测试账号

| 项目 | 值 |
|------|-----|
| **用户名** | `test_student` |
| **密码** | `Test1234` |
| **邮箱** | `student@test.com` |
| **角色** | 学生 (student) |
| **学号** | S2024001 |
| **年级** | 大一 |
| **目标考试** | CET4 |
| **目标分数** | 500 |
| **当前水平** | B1 (intermediate) |

### 教师端测试账号

| 项目 | 值 |
|------|-----|
| **用户名** | `test_teacher` |
| **密码** | `Test1234` |
| **邮箱** | `teacher@test.com` |
| **角色** | 教师 (teacher) |
| **专业领域** | 英语口语、写作教学、语法 |
| **简介** | 专注于AI辅助英语教学，拥有10年教学经验 |

### 使用方式

**API 登录示例**:
```bash
# 学生登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_student", "password": "Test1234"}'

# 教师登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_teacher", "password": "Test1234"}'
```

**前端登录**: 直接使用上述用户名和密码在前端登录页面登录。

---

## 对外接口

### API路由结构

```
/api/v1/
├── /auth/              # 认证授权 (已实现)
│   ├── POST /register
│   ├── POST /login
│   └── GET  /me
├── /students/          # 学生管理 (已实现)
├── /mistakes/          # 错题本 (已实现)
├── /practices/         # 练习记录 (已实现)
├── /contents/          # 内容管理 (已实现)
├── /conversations/     # 口语对话 (已实现)
├── /reports/           # 学习报告 (✨ 新增)
│   ├── POST /generate
│   ├── GET  /me
│   ├── GET  /{report_id}
│   ├── POST /{report_id}/export
│   └── DELETE /{report_id}
└── /lesson-plans/      # 教案管理 (已实现)
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

**学习报告接口** (`app/api/v1/learning_reports.py`): ✨
- `POST /api/v1/reports/generate` - 生成学习报告
- `GET /api/v1/reports/me` - 获取我的报告列表
- `GET /api/v1/reports/{report_id}` - 获取报告详情
- `POST /api/v1/reports/{report_id}/export` - 导出报告（PDF/图片）
- `DELETE /api/v1/reports/{report_id}` - 删除报告

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
| 认证 | python-jose, passlib, argon2-cffi | >=3.3.0 |
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
| **LearningReport** | `app/models/learning_report.py` | ✨ 新增 | 学习报告 |
| LessonPlan | `app/models/lesson_plan.py` | ✅ 已实现 | 教案 |
| ClassModel | `app/models/class_model.py` | ✅ 已实现 | 班级 |

### LearningReport 模型详情 ✨

**文件**: `app/models/learning_report.py`

```python
class LearningReport(Base):
    """学习报告模型 - 存储学生的学习报告快照和统计数据"""

    # 主键
    id: UUID

    # 关联
    student_id: UUID  # 外键到 students

    # 报告类型和时间范围
    report_type: str  # weekly, monthly, custom
    period_start: datetime
    period_end: datetime

    # JSONB 字段存储报告数据
    statistics: dict          # 统计数据快照
    ability_analysis: dict    # 能力分析快照
    weak_points: dict         # 薄弱点分析
    recommendations: dict     # 学习建议
    ai_insights: dict         # AI分析结果

    # 状态和元数据
    status: str              # draft, completed, archived
    title: str               # 可选报告标题
    description: str         # 可选报告描述
```

---

## 业务服务

### PDF渲染服务 ✨

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
- `export_as_pdf()` - 导出 PDF 格式 ✅ 已实现
- `export_as_word()` - 导出 Word 格式 (TODO)

### 学习报告服务 ✨

**文件**: `app/services/learning_report_service.py`

**功能**: 生成学生综合学习报告，包括统计、能力分析、薄弱点识别和建议生成

核心方法：
- `generate_report()` - 生成完整学习报告
- `generate_statistics()` - 生成学习统计数据
- `analyze_ability_progress()` - 分析能力进步（基于知识图谱）
- `analyze_weak_points()` - 分析薄弱知识点
- `generate_recommendations()` - 生成学习建议（规则引擎）
- `generate_ai_recommendations()` - 生成 AI 个性化建议
- `get_student_reports()` - 获取学生报告列表

### 报告导出服务 ✨

**文件**: `app/services/report_export_service.py`

**功能**: 将学习报告导出为 PDF 或图片格式

核心方法：
- `export_as_pdf()` - 导出为 PDF（使用 PDF 渲染服务）
- `export_as_image()` - 导出为图片（占位实现，待集成 Playwright）
- `_render_markdown_report()` - 渲染 Markdown 报告内容

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

## 工具函数

### PDF辅助工具 ✨

**文件**: `app/utils/pdf_helpers.py`

**功能**: 跨平台字体检测和CSS字体族生成

核心函数：
- `check_font_availability()` - 检测系统中文字体可用性
- `get_css_font_family()` - 生成跨平台兼容的CSS字体族
- `get_pdf_css()` - 获取完整PDF样式（包含字体配置）

**支持的平台**:
- macOS: PingFang SC, STHeiti
- Windows: Microsoft YaHei, SimHei
- Linux: WenQuanYi Micro Hei, Noto Sans CJK

---

## 模板文件

### PDF样式模板 ✨

**文件**: `app/templates/pdf_styles.css.j2`

- 完整的 PDF 打印样式（CSS Paged Media）
- 中文字体支持（跨平台兼容）
- 分页控制、页眉页脚、表格样式
- 支持错题详情专用样式类

### Markdown模板

**文件**: `app/templates/mistake_report.md.j2`

**文件**: `app/templates/mistake_detail.md.j2`

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
    ├── test_pdf_renderer_service.py  # ✨ PDF渲染测试
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
| `app/services/pdf_renderer_service.py` | PDF渲染服务 | ✅ |
| `app/services/mistake_export_service.py` | 错题导出服务 | ✅ |
| `app/services/learning_report_service.py` | 学习报告服务 | ✨ 新增 |
| `app/services/report_export_service.py` | 报告导出服务 | ✨ 新增 |
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
| `app/api/v1/learning_reports.py` | 学习报告API | ✨ 新增 |
| `app/api/v1/students.py` | 学生API | ✅ |
| `app/api/v1/contents.py` | 内容API | ✅ |
| `app/api/v1/practices.py` | 练习API | ✅ |
| `app/api/v1/conversations.py` | 对话API | ✅ |
| `app/api/v1/lesson_plans.py` | 教案API | ✅ |
| `app/api/deps.py` | API依赖 | ✅ |

### 数据模型文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `app/models/user.py` | 用户模型 | ✅ |
| `app/models/student.py` | 学生模型 | ✅ |
| `app/models/teacher.py` | 教师模型 | ✅ |
| `app/models/organization.py` | 组织模型 | ✅ |
| `app/models/knowledge_graph.py` | 知识图谱模型 | ✅ |
| `app/models/content.py` | 内容模型 | ✅ |
| `app/models/practice.py` | 练习模型 | ✅ |
| `app/models/conversation.py` | 对话模型 | ✅ |
| `app/models/mistake.py` | 错题模型 | ✅ |
| `app/models/learning_report.py` | 学习报告模型 | ✨ 新增 |
| `app/models/lesson_plan.py` | 教案模型 | ✅ |
| `app/models/class_model.py` | 班级模型 | ✅ |

### 测试文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `tests/conftest.py` | pytest配置 | ✅ |
| `tests/api/test_auth.py` | 认证API测试 | ✅ |
| `tests/services/test_pdf_renderer_service.py` | PDF渲染测试 | ✨ 新增 |

### 数据库迁移文件

| 文件 | 描述 | 状态 |
|------|------|------|
| `alembic/versions/20260203_2100_add_learning_report_model.py` | 学习报告模型迁移 | ✨ 新增 |
| `alembic/versions/20260203_1200_add_mistake_model.py` | 错题模型迁移 | ✅ |
| `alembic/versions/20260203_1026_6180530e656a_add_practice_and_class_models.py` | 练习和班级模型迁移 | ✅ |
| `alembic/versions/20260202_1258_9a6282cdb4bd_add_conversation_model.py` | 对话模型迁移 | ✅ |
| `alembic/versions/20260202_1107_f0c40f107c40_初始化ai英语教学系统数据库.py` | 初始数据库迁移 | ✅ |


<claude-mem-context>
# Recent Activity

<!-- This section is auto-generated by claude-mem. Edit content outside the tags. -->

### Feb 6, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #994 | 8:02 PM | ✅ | Frontend API Documentation Updated | ~284 |

### Feb 7, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #1739 | 8:05 PM | 🟣 | Content Renderer Service Tests Complete | ~274 |
| #1705 | 8:01 PM | 🔵 | Project Dependencies Analysis | ~269 |
| #1699 | 8:00 PM | 🟣 | Content Renderer Service Tests Complete | ~327 |

### Feb 8, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #1763 | 12:03 AM | ✅ | Backend examples and path validation tests committed | ~193 |

### Feb 9, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #2124 | 11:28 PM | ✅ | Repository Changes Summary - Docker and Frontend Updates | ~350 |
| #2003 | 5:30 PM | 🟣 | Qdrant Vector Database Deployed and Operational | ~260 |
| #2001 | 5:24 PM | 🟣 | Docker Backend Deployed and Authentication System Verified | ~342 |
| #1999 | 5:11 PM | 🟣 | Docker Infrastructure Successfully Deployed | ~378 |
| #1998 | 5:08 PM | 🟣 | Docker Containers Successfully Started | ~226 |
| #1997 | 5:07 PM | ⚖️ | Deploy Containers and Execute End-to-End Testing | ~379 |
| #1996 | 5:03 PM | 🟣 | Docker Images Successfully Built via Daocloud Mirror | ~336 |
| #1981 | 4:54 PM | ✅ | Backend Dockerfile Updated with DaoCloud Mirror | ~204 |
| #1975 | 4:13 PM | ✅ | Backend Dockerfile Base Image Changed | ~220 |
| #1971 | 4:12 PM | 🔵 | Backend Dockerfile Configuration Analyzed | ~312 |
| #1955 | 3:01 PM | 🔴 | Docker Build Failed - Registry Service Unavailable | ~278 |
| #1939 | 2:47 PM | 🟣 | Frontend Service Added to Docker Compose | ~266 |
| #1919 | 2:29 PM | 🔵 | Docker Infrastructure Configuration Discovered | ~311 |

### Feb 10, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #2140 | 7:36 AM | 🟣 | Repository Changes Pushed to GitHub | ~241 |
</claude-mem-context>