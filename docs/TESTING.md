# 测试指南

> **AI 英语教学系统 - 测试文档**
> 最后更新: 2026-02-04

## 概述

本项目采用多层次测试策略，确保代码质量和前后端接口一致性。

## 测试架构

```
┌─────────────────────────────────────────────────────────────┐
│                      测试金字塔                              │
├─────────────────────────────────────────────────────────────┤
│  E2E 测试 (端到端)     ← 少量，关键业务流程                  │
│       │                                                     │
│  集成测试                ← 中等，模块间交互                  │
│       │                                                     │
│  ┌─────────┬─────────────┐                                  │
│  │ 单元测试 │ API 契约测试  │ ← 大量，快速反馈                 │
│  └─────────┴─────────────┘                                  │
└─────────────────────────────────────────────────────────────┘
```

## 快速开始

### 后端测试

```bash
cd backend

# 安装测试依赖
pip install -e ".[dev]"

# 运行所有测试
pytest

# 运行特定测试类型
pytest tests/api_contracts/      # API 契约测试
pytest tests/integration/        # 集成测试
pytest tests/unit/               # 单元测试

# 带覆盖率报告
pytest --cov=app --cov-report=html

# 类型检查
mypy app

# 代码检查
ruff check app tests
```

### 前端测试

```bash
cd frontend

# 类型检查（非常重要！）
npm run type-check

# 监听模式类型检查
npm run type-check:watch

# 运行单元测试
npm run test:run

# 完整检查（类型 + Lint + 测试）
npm run check:all

# 构建项目（包含类型检查）
npm run build
```

---

## 1. API 契约测试

### 目的

确保后端 API 响应格式与前端类型定义完全一致，防止运行时错误。

### 问题示例

之前遇到的问题就是因为契约不一致：

```typescript
// 前端 src/api/report.ts
export default reportApi  // 默认导出

// 前端 src/views/student/ReportsView.vue
import { reportApi } from '@/api/report'  // ❌ 错误：命名导入

// 正确应该是：
import reportApi from '@/api/report'  // ✅ 正确：默认导入
```

### 契约定义

后端 `tests/conftest.py` 中的 `APIContractValidator.CONTRACTS` 定义了所有 API 端点的期望格式：

```python
CONTRACTS = {
    "/api/v1/auth/login": {
        "response": {
            "access_token": "string",
            "refresh_token": "string",
            "user": {
                "id": "uuid",
                "username": "string",
                ...
            }
        }
    },
    ...
}
```

### 运行契约测试

```bash
cd backend

# 运行所有契约测试
pytest tests/api_contracts/test_api_contracts.py -v

# 运行特定端点的测试
pytest tests/api_contracts/test_api_contracts.py::TestReportAPIContracts -v
```

### 添加新端点时

1. **后端**: 在 `APIContractValidator.CONTRACTS` 中添加契约定义
2. **前端**: 在 `src/api/*.ts` 中添加对应的 API 函数
3. **测试**: 在 `tests/api_contracts/test_api_contracts.py` 中添加测试

**示例：**

```python
# 1. 在 conftest.py 中添加契约
CONTRACTS["/api/v1/new-endpoint"] = {
    "response": {
        "id": "uuid",
        "name": "string",
        "status": "string"
    }
}
```

```typescript
// 2. 在前端 src/api/newApi.ts 中
const newApi = {
  async getData(): Promise<Response> {
    return request({
      url: '/v1/new-endpoint',  // 注意：不要重复 /api 前缀
      method: 'get'
    })
  }
}
export default newApi  // 使用默认导出
```

---

## 2. 数据库模式同步测试

### 目的

确保 SQLAlchemy 模型定义与实际数据库表结构完全一致。

### 常见问题

```python
# 模型定义
class Practice(Base):
    completed_questions: Mapped[int] = mapped_column(Integer)

# 但数据库表中没有这个列 → 导致运行时错误
# sqlalchemy.exc.ProgrammingError: column practices.completed_questions does not exist
```

### 运行模式同步测试

```bash
cd backend

# 运行所有同步测试
pytest tests/integration/test_schema_sync.py -v

# 测试特定表
pytest tests/integration/test_schema_sync.py::TestDatabaseSchemaSync::test_practice_table_schema -v
```

### 测试覆盖

- ✅ 所有模型都有对应的数据库表
- ✅ 表结构与模型定义一致（列名、类型、约束）
- ✅ 外键关系正确设置
- ✅ JSON 类型列存在且类型正确

### 修复同步问题

如果测试失败：

1. **添加缺失的列**

```sql
ALTER TABLE practices ADD COLUMN completed_questions INTEGER DEFAULT 0;
```

2. **或使用 Alembic 迁移**

```bash
# 创建新迁移
alembic revision --autogenerate -m "add missing columns"

# 应用迁移
alembic upgrade head
```

---

## 3. 前端类型检查

### 目的

在编译时捕获类型错误，而不是运行时。

### 配置文件

`tsconfig.json` 中启用严格检查：

```json
{
  "compilerOptions": {
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noUncheckedIndexedAccess": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

### 运行类型检查

```bash
cd frontend

# 单次检查
npm run type-check

# 监听模式（开发时推荐）
npm run type-check:watch

# 构建时自动检查
npm run build  # 包含 vue-tsc && vite build
```

### 常见类型错误

#### 1. 导入/导出不匹配

```typescript
// ❌ 错误
import { reportApi } from '@/api/report'  // reportApi 是默认导出

// ✅ 正确
import reportApi from '@/api/report'
```

#### 2. 类型断言缺失

```typescript
// ❌ 可能的错误
const data = response.json()
const id = data.id  // TypeScript 不知道 data 的类型

// ✅ 正确
interface Response {
  id: string
  name: string
}
const data: Response = await response.json()
```

#### 3. 可选属性处理

```typescript
// ❌ 错误
const report = getReport()
const status = report.status.toUpperCase()  // report.status 可能是 undefined

// ✅ 正确
const report = getReport()
const status = report.status?.toUpperCase() || ''
```

### 类型测试文件

`tests/api/type-check.test.ts` 包含编译时类型检查：

```bash
cd frontend
npm run test tests/api/type-check.test.ts
```

---

## CI/CD 集成

### GitHub Actions

`.github/workflows/test.yml` 定义了 CI 流程：

```yaml
jobs:
  backend-test:
    - 类型检查 (mypy)
    - 代码检查 (ruff)
    - API 契约测试
    - 数据库同步测试
    - 单元测试 + 覆盖率

  frontend-test:
    - 类型检查 (vue-tsc)
    - 代码检查 (eslint)
    - 单元测试
    - 构建

  integration-test:
    - 完整的端到端测试
```

### 本地 Pre-commit Hook

```bash
# 安装 pre-commit
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行
pre-commit run --all-files
```

---

## 测试覆盖率目标

| 组件 | 目标覆盖率 | 当前状态 |
|------|----------|----------|
| 后端 API | 80%+ | 🔄 提升中 |
| 前端组件 | 70%+ | 🔄 提升中 |
| 关键业务逻辑 | 90%+ | 🔄 提升中 |

---

## 故障排查

### 后端测试失败

**问题**: `ImportError: No module named 'app'`

```bash
# 解决方案
cd backend
pip install -e ".[dev]"
```

**问题**: 数据库连接错误

```bash
# 启动测试数据库
docker-compose -f docker-compose.test.yml up -d

# 或使用 SQLite 内存数据库（测试默认）
export TEST_DATABASE_URL="sqlite+aiosqlite:///:memory:"
```

### 前端类型检查失败

**问题**: `Cannot find module '@/api/xxx'`

```bash
# 检查 tsconfig.json 中的 paths 配置
# 或重启 TypeScript 服务器（VS Code: CMD+Shift+P → "Restart TS Server"）
```

**问题**: vue-tsc 编译很慢

```bash
# 使用增量编译
npm run type-check:watch

# 或临时禁用严格检查（不推荐）
# tsconfig.json: "skipLibCheck": true
```

---

## 最佳实践

### 1. TDD 开发流程

```bash
# 1. 写测试（失败）
# 2. 写代码（通过测试）
# 3. 重构
# 4. 重复

# 后端示例
pytest tests/api_contracts/test_api_contracts.py::TestReportAPIContracts -v --watch

# 前端示例
npm run type-check:watch
```

### 2. 提交前检查清单

- [ ] 后端: `pytest` 全部通过
- [ ] 后端: `mypy app` 无错误
- [ ] 后端: `ruff check app tests` 无错误
- [ ] 前端: `npm run type-check` 无错误
- [ ] 前端: `npm run lint` 无错误（或已修复）
- [ ] 前端: `npm run build` 成功
- [ ] 新增端点已更新 API 契约

### 3. 代码审查重点

- API 响应格式是否与契约一致
- 数据库迁移是否正确
- 类型定义是否完整
- 测试是否覆盖关键路径

---

## 相关文件

| 文件 | 用途 |
|------|------|
| `backend/tests/conftest.py` | pytest 配置和 fixtures |
| `backend/tests/api_contracts/` | API 契约测试 |
| `backend/tests/integration/test_schema_sync.py` | 数据库同步测试 |
| `frontend/tsconfig.json` | TypeScript 配置 |
| `frontend/tests/api/type-check.test.ts` | 前端类型测试 |
| `.github/workflows/test.yml` | CI/CD 配置 |

---

## 获取帮助

- 运行测试遇到问题？查看日志：`pytest -v -s`
- 类型检查不通过？查看具体错误行
- 需要添加新的 API 契约？参考 `conftest.py` 中的示例
