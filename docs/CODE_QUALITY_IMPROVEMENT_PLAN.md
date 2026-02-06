# AI 赋能英语教学系统 - 代码质量改进规划

> **规划日期**: 2026-02-06
> **基于**: CODE_REVIEW_REPORT.md (2026-02-05)
> **规划周期**: 3 个迭代（约 6-8 周）

---

## 一、改进目标

| 指标 | 当前状态 | 目标状态 | 改进方向 |
|------|----------|----------|----------|
| 🔴 严重安全问题 | 8 个 | 0 个 | 立即处理 |
| 🟡 中等问题 | 12 个 | ≤4 个 | 2-4 周 |
| 🔵 改进建议 | 15 个 | ≤8 个 | 持续优化 |
| 测试覆盖率 | 未知 | ≥80% | 编写测试 |
| 技术债务 | 91 小时 | ≤40 小时 | 分批消除 |

---

## 二、迭代规划总览

```
迭代 1（第1-2周）🔴 安全性修复
├── JWT 密钥安全
├── Token 黑名单
├── 登录速率限制
└── 密码强度验证

迭代 2（第3-4周）🟡 架构优化
├── AI 服务重构
├── 统一异常处理
├── 数据库索引
└── 前端错误边界

迭代 3（第5-8周）🔵 性能与质量
├── PDF 渲染优化
├── Element Plus 按需导入
├── ECharts 内存管理
├── 虚拟滚动
└── 消除魔法数字
```

---

## 三、迭代 1：安全性修复（🔴 高优先级）

### 目标：消除所有 🔴 严重安全问题

### 3.1 JWT 密钥安全改进

**问题**：默认密钥硬编码，可被攻击者破解

**改进方案**：
```
文件: backend/app/core/config.py
├── 移除默认值，强制从环境变量读取
├── 添加密钥生成工具函数
└── 启动时验证密钥强度
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 移除 JWT 默认密钥 | `config.py` | 0.5h | 无默认值，必须从环境变量读取 |
| 添加密钥验证 | `config.py` | 1h | 密钥长度 ≥256 位检查 |
| 更新环境变量示例 | `.env.example` | 0.5h | 添加密钥生成说明 |

**代码示例**：

```python
# backend/app/core/config.py
class SecurityConfig:
    # 强制从环境变量读取，不提供默认值
    JWT_SECRET_KEY: str = Field(
        description="JWT密钥，必须通过环境变量设置"
    )
    JWT_ALGORITHM: str = Field(default="HS256")

    @validator("JWT_SECRET_KEY")
    def validate_secret_key(cls, v):
        if not v or len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @classmethod
    def from_env(cls):
        secret = os.getenv("JWT_SECRET_KEY")
        if not secret:
            raise RuntimeError(
                "JWT_SECRET_KEY not set. "
                "Generate with: openssl rand -hex 32"
            )
        return cls(JWT_SECRET_KEY=secret)
```

---

### 3.2 Token 黑名单机制

**问题**：登出后 Token 仍然有效

**改进方案**：
```
文件: backend/app/core/security.py + backend/app/api/v1/auth.py
├── 使用 Redis 存储 Token 黑名单
├── 实现 Token 刷新版本控制
└── 添加黑名单检查中间件
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 创建 Token 黑名单服务 | `token_blacklist.py` | 2h | 支持 add/check/delete 操作 |
| 修改登录返回版本号 | `auth.py` | 0.5h | 返回 token_version |
| 实现黑名单中间件 | `deps.py` | 1h | 自动检查 Token 有效性 |
| 添加登出接口 | `auth.py` | 0.5h | 将 Token 加入黑名单 |

**代码示例**：

```python
# backend/app/core/token_blacklist.py
from redis import Redis
from typing import Optional
from datetime import datetime, timezone

class TokenBlacklist:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = "token:blacklist:"
        self.ttl = 86400 * 7  # 7 天过期

    def add(self, jti: str, user_id: str, reason: str = "logout") -> None:
        """将 Token 加入黑名单"""
        key = f"{self.prefix}{jti}"
        self.redis.hset(key, mapping={
            "user_id": user_id,
            "reason": reason,
            "revoked_at": datetime.now(timezone.utc).isoformat()
        })
        self.redis.expire(key, self.ttl)

    def is_revoked(self, jti: str) -> bool:
        """检查 Token 是否已被撤销"""
        return self.redis.exists(f"{self.prefix}{jti}") > 0

    def revoke_all_user_tokens(self, user_id: str) -> int:
        """撤销用户的所有 Token（用于密码修改等）"""
        pattern = f"{self.prefix}:user:{user_id}:*"
        # 实现用户级 Token 撤销
```

---

### 3.3 登录速率限制

**问题**：登录接口无限制，易受暴力破解

**改进方案**：
```
文件: backend/app/api/v1/auth.py + backend/app/core/rate_limit.py
├── 使用 slowapi 实现滑动窗口限流
├── 登录失败添加验证码触发
└── 实现 IP 黑名单机制
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 创建速率限制中间件 | `rate_limit.py` | 2h | 支持滑动窗口算法 |
| 添加登录限流装饰器 | `auth.py` | 1h | 5 次/分钟限制 |
| 实现失败计数 | `auth.py` | 1h | 连续失败 5 次触发验证码 |
| 添加 IP 黑名单 | `deps.py` | 1h | 自动封禁恶意 IP |

**代码示例**：

```python
# backend/app/core/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],  # 默认全局限制
    storage_uri="redis://localhost:6379/1"
)

# backend/app/api/v1/auth.py
from app.core.rate_limit import limiter

@router.post("/login")
@limiter.limit("5/minute")  # 登录限流：5次/分钟
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # 登录逻辑
    pass
```

---

### 3.4 密码强度验证

**问题**：缺少密码复杂度检查

**改进方案**：
```
文件: backend/app/services/auth_service.py + backend/app/utils/password.py
├── 添加密码复杂度正则验证
├── 实现常见密码黑名单
└── 添加密码历史检查
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 创建密码验证工具 | `password.py` | 1.5h | 复杂度 + 黑名单检查 |
| 添加注册时验证 | `auth_service.py` | 0.5h | 不符合规则返回错误 |
| 添加密码历史记录 | `user.py` 模型 | 1h | 防止重复使用最近密码 |

**代码示例**：

```python
# backend/app/utils/password.py
import re
from typing import Tuple

# 常见弱密码黑名单
COMMON_PASSWORDS = {
    "password", "123456", "12345678", "qwerty", "abc123",
    "password123", "admin", "letmein", "welcome"
}

PASSWORD_REQUIREMENTS = {
    "min_length": 8,
    "max_length": 128,
    "require_uppercase": True,
    "require_lowercase": True,
    "require_digit": True,
    "require_special": True,
    "special_chars": "!@#$%^&*()_+-=[]{}|;':\",./<>?"
}

def validate_password(password: str) -> Tuple[bool, str]:
    """验证密码强度，返回 (是否通过, 错误信息)"""
    # 检查长度
    if len(password) < PASSWORD_REQUIREMENTS["min_length"]:
        return False, f"密码长度至少 {PASSWORD_REQUIREMENTS['min_length']} 位"

    # 检查常见弱密码
    if password.lower() in COMMON_PASSWORDS:
        return False, "密码过于简单，请使用更复杂的密码"

    # 检查复杂度
    if PASSWORD_REQUIREMENTS["require_uppercase"] and not re.search(r"[A-Z]", password):
        return False, "密码必须包含大写字母"

    if PASSWORD_REQUIREMENTS["require_digit"] and not re.search(r"\d", password):
        return False, "密码必须包含数字"

    if PASSWORD_REQUIREMENTS["require_special"] and not any(c in password for c in PASSWORD_REQUIREMENTS["special_chars"]):
        return False, f"密码必须包含特殊字符: {PASSWORD_REQUIREMENTS['special_chars']}"

    return True, ""
```

---

### 3.5 迭代 1 总结

| 任务 | 预估工作量 | 负责人 | 完成标准 |
|------|-----------|--------|----------|
| JWT 密钥安全 | 2h | - | 无默认密钥，强制环境变量 |
| Token 黑名单 | 4h | - | 登出后 Token 立即失效 |
| 登录速率限制 | 5h | - | 暴力破解防护 |
| 密码强度验证 | 3h | - | 复杂度过低拒绝注册 |
| **迭代 1 总计** | **14h** | | |

---

## 四、迭代 2：架构优化（🟡 中优先级）

### 目标：解决架构层面的技术债务

### 4.1 AI 服务重构

**问题**：`ai_service.py` 文件过大（577 行）

**改进方案**：
```
文件: backend/app/services/ai_service.py
├── EmbeddingService (向量生成)
├── ChatService (对话完成)
├── AnalysisService (分析服务)
└── AIFacade (统一入口)
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 创建 EmbeddingService | `embedding_service.py` | 4h | 向量生成独立 |
| 创建 ChatService | `chat_service.py` | 4h | 对话完成独立 |
| 创建 AnalysisService | `analysis_service.py` | 4h | 分析服务独立 |
| 创建 AIFacade | `ai_service.py` | 2h | 统一调度 |
| 更新调用方代码 | `*.py` | 2h | 适配新服务 |

**重构结构**：

```python
# backend/app/services/ai/
__init__.py          # 导出统一接口
embedding_service.py  # 向量生成
chat_service.py       # 对话完成
analysis_service.py   # 分析服务
base.py              # 抽象基类

# backend/app/services/ai_service.py (重命名为 facade)
class AIFacade:
    """AI 服务统一入口"""

    def __init__(
        self,
        embedding: EmbeddingService,
        chat: ChatService,
        analysis: AnalysisService
    ):
        self.embedding = embedding
        self.chat = chat
        self.analysis = analysis

    async def analyze_student_assessment(self, ...):
        return await self.analysis.analyze_student_assessment(...)
```

---

### 4.2 统一异常处理

**问题**：缺少统一的异常处理基类

**改进方案**：
```
文件: backend/app/core/exceptions.py
├── 定义业务异常基类
├── 定义认证异常
├── 定义业务异常
└── 添加全局异常处理器
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 创建异常基类 | `exceptions.py` | 2h | 定义完整异常体系 |
| 添加异常处理器 | `main.py` | 1h | 全局捕获返回标准格式 |
| 更新服务代码 | `*.py` | 3h | 使用统一异常 |

**代码示例**：

```python
# backend/app/core/exceptions.py
from fastapi import HTTPException, status
from typing import Any, Optional

class BaseException(HTTPException):
    """业务异常基类"""
    def __init__(
        self,
        detail: str = "",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = self.__class__.__name__

class AuthenticationError(BaseException):
    """认证异常"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "认证失败"

class TokenExpiredError(AuthenticationError):
    default_message = "Token 已过期"

class InvalidTokenError(AuthenticationError):
    default_message = "无效的 Token"

class BusinessError(BaseException):
    """业务异常"""
    status_code = status.HTTP_400_BAD_REQUEST

class ResourceNotFoundError(BusinessError):
    default_message = "资源不存在"

class ValidationError(BusinessError):
    default_message = "数据验证失败"

# backend/app/core/exception_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse

async def global_exception_handler(request: Request, exc: BaseException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.detail
            }
        },
        headers=exc.headers
    )
```

---

### 4.3 数据库索引优化

**问题**：缺少数据库索引，查询性能差

**改进方案**：
```
文件: backend/app/models/*.py
├── User 模型索引 (email, username)
├── Student 模型索引 (user_id, target_exam)
├── Practice 模型索引 (student_id, created_at)
├── Mistake 模型索引 (student_id, status)
└── KnowledgeGraph 模型索引
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 添加 User 索引 | `user.py` | 0.5h | email, username |
| 添加 Student 索引 | `student.py` | 0.5h | user_id, target_exam |
| 添加 Practice 索引 | `practice.py` | 0.5h | student_id, created_at |
| 添加 Mistake 索引 | `mistake.py` | 0.5h | student_id, status, topic |
| 添加 KnowledgeGraph 索引 | `knowledge_graph.py` | 0.5h | student_id |
| 生成数据库迁移 | `alembic/` | 1h | 索引迁移脚本 |

**代码示例**：

```python
# backend/app/models/user.py
class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        # 邮箱唯一索引
        Index('ix_users_email', 'email', unique=True),
        # 用户名索引
        Index('ix_users_username', 'username'),
    )

# backend/app/models/mistake.py
class Mistake(Base):
    __tablename__ = "mistakes"

    __table_args__ = (
        # 学生错题列表索引
        Index('ix_mistakes_student_status', 'student_id', 'status'),
        # 错题类型索引
        Index('ix_mistakes_topic', 'topic'),
        # 复习时间索引
        Index('ix_mistakes_next_review', 'next_review_at'),
    )
```

---

### 4.4 前端错误边界

**问题**：前端组件缺少错误边界

**改进方案**：
```
文件: frontend/src/components/ErrorBoundary.vue
├── 捕获子组件渲染错误
├── 显示友好的错误提示
└── 提供错误重置功能
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 创建错误边界组件 | `ErrorBoundary.vue` | 2h | 捕获渲染错误 |
| 添加全局错误处理 | `main.ts` | 0.5h | 全局 Vue 错误处理 |
| 应用到页面组件 | `*.vue` | 1.5h | 包裹可能出错的组件 |

**代码示例**：

```vue
<!-- frontend/src/components/ErrorBoundary.vue -->
<template>
  <div v-if="error" class="error-boundary">
    <el-result
      icon="error"
      title="页面出错了"
      :sub-title="error.message"
    >
      <template #extra>
        <el-button type="primary" @click="handleRetry">
          刷新重试
        </el-button>
        <el-button @click="handleReload">
          重新加载页面
        </el-button>
      </template>
    </el-result>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'

const error = ref<Error | null>(null)

onErrorCaptured((err) => {
  error.value = err
  console.error('Error captured by boundary:', err)
  return false  // 阻止错误继续传播
})

const handleRetry = () => {
  error.value = null
}

const handleReload = () => {
  window.location.reload()
}
</script>
```

---

### 4.5 迭代 2 总结

| 任务 | 预估工作量 | 负责人 | 完成标准 |
|------|-----------|--------|----------|
| AI 服务重构 | 16h | - | 拆分为 3+ 服务 |
| 统一异常处理 | 6h | - | 完整异常体系 |
| 数据库索引 | 4h | - | 常用查询有索引 |
| 前端错误边界 | 4h | - | 全局错误处理 |
| **迭代 2 总计** | **30h** | | |

---

## 五、迭代 3：性能与质量（🔵 低优先级）

### 目标：持续优化性能和代码质量

### 5.1 PDF 渲染优化

**问题**：同步操作阻塞事件循环

**改进方案**：
```
文件: backend/app/services/pdf_renderer_service.py
├── 使用 run_in_executor 异步执行
└── 添加渲染任务队列
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 异步 PDF 渲染 | `pdf_renderer_service.py` | 3h | 不阻塞主进程 |
| 添加任务队列 | `tasks/pdf_tasks.py` | 3h | 异步处理导出 |

---

### 5.2 Element Plus 按需导入

**问题**：完整导入导致打包体积大

**改进方案**：
```
文件: frontend/src/main.ts
├── 使用 unplugin-element-plus 自动按需导入
└── 配置 AutoImport 减少手动导入
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 配置按需导入 | `vite.config.ts` | 1h | 自动按需导入 |
| 清理手动导入 | `main.ts` | 0.5h | 移除组件手动导入 |
| 验证打包体积 | - | 0.5h | 体积减少 30%+ |

---

### 5.3 ECharts 内存管理

**问题**：组件销毁时未销毁图表

**改进方案**：
```
文件: frontend/src/views/student/ReportDetailView.vue
├── 在 onBeforeUnmount 中调用 chart.dispose()
└── 使用 Vue 生命周期钩子管理
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 销毁 ECharts 实例 | `ReportDetailView.vue` | 0.5h | 无内存泄漏 |
| 通用图表组件 | `EChart.vue` | 1h | 封装复用 |

---

### 5.4 虚拟滚动优化

**问题**：长列表未使用虚拟滚动

**改进方案**：
```
文件: frontend/src/views/student/MistakeBookView.vue
├── 使用 el-table-v2 虚拟滚动
└── 实现分页加载
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 配置虚拟滚动 | `MistakeBookView.vue` | 3h | 万级数据流畅滚动 |
| 实现分页 | `mistake.ts` API | 2h | 后端支持分页 |

---

### 5.5 消除魔法数字

**问题**：代码中存在硬编码数字

**改进方案**：
```
文件: 多个文件
├── 定义能力等级常量
├── 定义复习间隔常量
├── 定义时间阈值常量
└── 使用语义化常量替代
```

**详细任务**：

| 任务 | 文件 | 工作量 | 验收标准 |
|------|------|--------|----------|
| 能力等级常量 | `ability_levels.py` | 1h | 定义等级常量 |
| 复习间隔常量 | `review_intervals.py` | 0.5h | 艾宾浩斯间隔 |
| 时间阈值常量 | `time_thresholds.py` | 0.5h | 过期判定 |
| 替换魔法数字 | `*.py` | 4h | 无硬编码数字 |

**代码示例**：

```python
# backend/app/core/constants.py

# 能力等级
ABILITY_LEVELS = {
    'EXCELLENT': 90,
    'GOOD': 75,
    'INTERMEDIATE': 60,
    'BASIC': 40,
    'NEEDS_IMPROVEMENT': 20,
}

# 复习间隔 (艾宾浩斯遗忘曲线)
REVIEW_INTERVALS = {
    'FIRST': 1,      # 1 天
    'SECOND': 3,     # 3 天
    'THIRD': 7,      # 7 天
    'FOURTH': 14,    # 14 天
    'FIFTH': 30,     # 30 天
    'MAX': 30,       # 最大间隔
}

# 时间阈值 (小时)
TIME_THRESHOLDS = {
    'URGENT_REVIEW': 24,      # 紧急复习阈值
    'OVERDUE判定': 1,         # 过期判定（超过间隔即为过期）
    'NEW_MISTAKE': 24,        # 新错题定义（24小时内）
    'RECENT_REVIEW': 72,      # 最近复习（3天内）
}

# 优先级分数权重
PRIORITY_WEIGHTS = {
    'OVERDUE_PER_HOUR': 10,
    'MISTAKE_COUNT': 6,
    'REVIEW_COUNT': -5,
    'NEW_MISTAKE_BONUS': 10,
}
```

---

### 5.6 迭代 3 总结

| 任务 | 预估工作量 | 负责人 | 完成标准 |
|------|-----------|--------|----------|
| PDF 渲染优化 | 6h | - | 异步处理 |
| Element Plus 按需导入 | 2h | - | 体积减少 30% |
| ECharts 内存管理 | 1.5h | - | 无内存泄漏 |
| 虚拟滚动 | 5h | - | 万级数据流畅 |
| 消除魔法数字 | 6h | - | 无硬编码数字 |
| **迭代 3 总计** | **20.5h** | | |

---

## 六、实施路线图

### 时间线

```
第 1 周                    第 2 周                    第 3-4 周                   第 5-8 周
┌────────────────┬───────┬────────────────┬───────┬────────────────┬─────────┬────────────────┬─────────┐
│ JWT 密钥安全    │ Token 黑名单    │ AI 服务重构     │ PDF 渲染优化    │
│ +------------+ │ +------------+ │ +------------+ │ +------------+ │
│ │ 2h         │ │ │ 4h         │ │ │ 16h        │ │ │ 6h         │ │
│ └────────────┘ │ └────────────┘ │ └────────────┘ │ └────────────┘ │
├────────────────┴────────────────┴────────────────┴────────────────┤
│                      迭代 1-2: 核心修复 (44h)                       │
├────────────────────────────────────────────────────────────────────┤
│                      迭代 3: 持续优化 (20.5h)                       │
├────────────────────────────────────────────────────────────────────┤
│ 里程碑: 安全问题清零                                             │
│ 里程碑: 测试覆盖率 ≥80%                                          │
│ 里程碑: 技术债务 ≤40h                                            │
└────────────────────────────────────────────────────────────────────┘
```

### 里程碑

| 里程碑 | 时间点 | 验收标准 |
|--------|--------|----------|
| M1: 安全基础 | 第 2 周末 | 8 个 🔴 问题 → 0 |
| M2: 架构优化 | 第 4 周末 | AI 服务重构完成，索引添加 |
| M3: 性能达标 | 第 6 周末 | PDF 异步，虚拟滚动 |
| M4: 质量验收 | 第 8 周末 | 测试 ≥80%，魔法数字消除 |

---

## 七、风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 改动范围过大 | 可能引入新 bug | 分批迭代，每次合并前测试 |
| API 兼容性 | 客户端需要适配 | 版本号管理，渐进式迁移 |
| 数据库迁移 | 可能丢失数据 | 备份先行，迁移脚本测试 |
| 开发资源不足 | 进度延迟 | 优先完成 🔴 问题 |

---

## 八、验收清单

### 迭代 1 验收

- [ ] JWT 密钥强制环境变量，无默认值
- [ ] Token 黑名单生效，登出后立即失效
- [ ] 登录速率限制生效（5次/分钟）
- [ ] 密码强度验证生效（不符合规则拒绝）
- [ ] 所有 🔴 严重问题已解决

### 迭代 2 验收

- [ ] AI 服务拆分为 Embedding/Chat/Analysis
- [ ] 统一异常处理生效
- [ ] 数据库索引添加完成
- [ ] 前端错误边界生效
- [ ] 中等问题 ≤4 个

### 迭代 3 验收

- [x] PDF 渲染不阻塞主进程 ✅
- [x] Element Plus 按需导入 ✅
- [x] ECharts 无内存泄漏 ✅
- [x] 虚拟滚动生效 ✅
- [x] 魔法数字消除 ✅
- [ ] 测试覆盖率 ≥80%

---

*本规划基于 CODE_REVIEW_REPORT.md 制定，建议根据实际情况调整优先级。*
