[根目录](../CLAUDE.md) > **frontend**

# frontend - 前端应用模块

> **模块类型**: Vue3 前端应用
> **主要职责**: 教师端与学生端用户界面
> **技术栈**: Vue3 + Vite + Pinia + Element Plus + ECharts

---

## 变更记录

### 2026-02-06 15:30:00
- 🎉 **性能优化完成**: 迭代3前端优化全部完成
  - **Element Plus按需导入**: 配置 `unplugin-auto-import/vue-components`
  - **打包体积优化**: 减少约30%+（gzipped 343KB）
  - **ECharts内存管理**: 正确实现组件卸载清理
  - **语法修复**: LearningTrendChart.vue 异步await错误修复

### 2026-02-04 08:58:32
- 📊 **文档更新**: 增量更新完成
  - 补充学习报告功能文档（ReportsView、ReportDetailView）
  - 更新 API 客户端文档（report.ts）
  - 新增 ECharts 依赖说明
  - 更新路由结构

### 2026-02-03 21:00:00
- ✨ **新增**: 报告详情页面 (`ReportDetailView.vue`)
  - 完整的学习统计数据展示
  - 能力雷达图（ECharts）
  - 薄弱知识点分析（表格+主题分类）
  - 学习建议列表（按优先级展示）
  - AI 洞察展示
  - 导出功能（PDF/图片）
  - 删除报告功能
- 🔧 **更新**: 添加 ECharts 依赖用于数据可视化

### 2026-02-03 20:00:00
- ✨ **新增**: 学习报告生成功能完整实现
  - 后端：LearningReport 模型、学习报告服务、导出服务、API 路由
  - 前端：报告 API 客户端、报告列表页面、路由配置
  - 功能：实时生成、PDF导出、多种报告类型（周报/月报/自定义）

### 2026-02-03 19:00:00
- 🔧 **修复**: MistakeBookView.vue 导入问题
  - 移除重复的 Document 图标导入
  - 添加 ElLoading 导入

### 2026-02-03 09:49:22
- 创建前端模块文档
- 整理页面组件与路由结构
- 记录状态管理与API客户端

---

## 模块职责

frontend 模块是 AI 赋能英语教学系统的用户界面，提供：

1. **教师端**: 班级管理、学生诊断报告、AI备课助手、教学内容库
2. **学生端**: 我的课程、个性化练习、AI口语对话、进度追踪、学习报告
3. **认证系统**: 登录、注册、密码重置
4. **状态管理**: 用户状态、认证状态、应用全局状态
5. **数据可视化**: ECharts 图表展示（能力雷达图、学习趋势等）

---

## 入口与启动

### 应用入口

- **主应用**: `src/main.ts`
- **根组件**: `src/App.vue`
- **路由入口**: `src/router/index.ts`

### 启动方式

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 预览构建
npm run preview
```

### 服务地址

- 开发服务器: http://localhost:5173
- 生产构建: `dist/` 目录

---

## 对外接口

### 路由结构

```
/                      # 首页
/login                 # 登录页
/register              # 注册页
/teacher               # 教师端
  /teacher/students    # 学生管理
  /teacher/lessons     # 课程管理
  /teacher/plans       # 教案管理
  /teacher/dashboard   # 教师仪表板
  /teacher/ai-planning # AI备课助手
/student               # 学生端
  /student/dashboard   # 学生仪表板
  /student/practice    # 练习页面
  /student/learning    # 课程学习
  /student/mistakes    # 错题本
  /student/speaking    # 口语练习
  /student/conversation       # AI对话
  /student/conversations      # 对话历史
  /student/progress    # 学习进度
  /student/reports     # 学习报告列表 ✨
  /student/reports/:id # 报告详情 ✨
```

### API客户端

**认证API** (`src/api/auth.ts`):
- `authApi.register()` - 用户注册
- `authApi.login()` - 用户登录
- `authApi.getCurrentUser()` - 获取当前用户

**错题API** (`src/api/mistake.ts`):
- `mistakeApi.getMyMistakes()` - 获取错题列表
- `mistakeApi.getStatistics()` - 获取错题统计
- `mistakeApi.analyzeMistake()` - AI分析错题
- `mistakeApi.exportMistakes()` - 导出错题本（PDF/Markdown/Word）
- `mistakeApi.exportSingleMistake()` - 导出单个错题

**学习报告API** (`src/api/report.ts`): ✨
- `reportApi.generateReport()` - 生成学习报告
- `reportApi.getMyReports()` - 获取我的报告列表
- `reportApi.getReportDetail()` - 获取报告详情
- `reportApi.exportReport()` - 导出报告（PDF/图片）
- `reportApi.deleteReport()` - 删除报告

**对话API** (`src/api/conversation.ts`):
- `conversationApi.createConversation()` - 创建对话
- `conversationApi.sendMessage()` - 发送消息
- `conversationApi.getConversations()` - 获取对话历史

**课程API** (`src/api/lesson.ts`):
- `lessonApi.getLessons()` - 获取课程列表
- `lessonApi.getLessonDetail()` - 获取课程详情

---

## 关键依赖与配置

### 项目依赖

**文件**: `package.json`

| 依赖类别 | 主要包 | 版本 |
|---------|-------|------|
| 框架 | Vue, Vue Router, Pinia | ^3.4.0 |
| UI库 | Element Plus, @element-plus/icons-vue | ^2.5.0 |
| 图表库 | ECharts | ^5.6.0 ✨ |
| 构建工具 | Vite, @vitejs/plugin-vue | ^5.0.0 |
| HTTP客户端 | Axios | ^1.6.0 |
| 开发工具 | TypeScript, vue-tsc, Vitest | ^5.3.0 |

### Vite配置

**文件**: `vite.config.ts`

```typescript
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
```

---

## 状态管理

### Pinia Stores

**文件**: `src/stores/auth.ts`

核心状态：
- `user` - 当前用户信息
- `accessToken` - 访问令牌
- `refreshToken` - 刷新令牌
- `isAuthenticated` - 是否已认证
- `isTeacher` - 是否是教师
- `isStudent` - 是否是学生

核心操作：
- `register(data)` - 用户注册
- `login(data)` - 用户登录
- `fetchCurrentUser()` - 获取当前用户
- `logout()` - 退出登录

---

## 页面组件

### 认证页面

| 组件 | 路径 | 描述 |
|------|------|------|
| LoginView | `src/views/LoginView.vue` | 登录页面 |
| RegisterView | `src/views/RegisterView.vue` | 注册页面 |

### 教师端页面

| 组件 | 路径 | 描述 |
|------|------|------|
| DashboardView | `src/views/teacher/DashboardView.vue` | 教师仪表板 |
| StudentsView | `src/views/teacher/StudentsView.vue` | 学生管理 |
| LessonsView | `src/views/teacher/LessonsView.vue` | 课程管理 |
| AIPlanningView | `src/views/teacher/AIPlanningView.vue` | AI备课助手 |

### 学生端页面

| 组件 | 路径 | 描述 |
|------|------|------|
| DashboardView | `src/views/student/DashboardView.vue` | 学生仪表板 |
| LearningView | `src/views/student/LearningView.vue` | 课程学习 |
| MistakeBookView | `src/views/student/MistakeBookView.vue` | 错题本（含PDF导出） |
| SpeakingView | `src/views/student/SpeakingView.vue` | 口语练习 |
| ConversationView | `src/views/student/ConversationView.vue` | AI对话 |
| ConversationHistoryView | `src/views/student/ConversationHistoryView.vue` | 对话历史 |
| ProgressView | `src/views/student/ProgressView.vue` | 学习进度 |
| **ReportsView** | `src/views/student/ReportsView.vue` | **学习报告（生成+查看+导出）** ✨ |
| **ReportDetailView** | `src/views/student/ReportDetailView.vue` | **报告详情（完整统计+图表）** ✨ |

### 通用页面

| 组件 | 路径 | 描述 |
|------|------|------|
| HomeView | `src/views/HomeView.vue` | 首页 |
| NotFoundView | `src/views/NotFoundView.vue` | 404页面 |

### 通用组件

| 组件 | 路径 | 描述 |
|------|------|------|
| ConversationStatus | `src/components/ConversationStatus.vue` | 对话状态 |
| ConversationMessage | `src/components/ConversationMessage.vue` | 对话消息 |
| ConversationFeedbackDrawer | `src/components/ConversationFeedbackDrawer.vue` | 反馈抽屉 |

---

## 类型定义

### 认证类型

**文件**: `src/types/auth.ts`

```typescript
// 用户接口
interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'teacher' | 'student' | 'parent'
  organization_id?: string
  profile?: Record<string, any>
}

// 请求接口
interface RegisterRequest {
  username: string
  email: string
  password: string
  role: 'teacher' | 'student'
  organizationName?: string
}

interface LoginRequest {
  email: string
  password: string
}

// 响应接口
interface AuthResponse {
  user: User
  access_token: string
  refresh_token: string
}
```

### 学习报告类型

**文件**: `src/api/report.ts`

```typescript
// 报告统计
interface ReportStatistics {
  total_practices: number
  completed_practices: number
  completion_rate: number
  avg_correct_rate: number
  total_duration_minutes: number
  total_duration_hours: number
  total_mistakes: number
  mistake_by_type: Record<string, number>
  mistake_by_status: Record<string, number>
  period_days: number
}

// 能力分析
interface AbilityAnalysis {
  current_abilities: Record<string, any>
  ability_radar: Array<{
    name: string
    value: number
    confidence: number
  }>
  strongest_area?: { name: string; level: number }
  weakest_area?: { name: string; level: number }
}

// 薄弱点
interface WeakPoints {
  total_unmastered: number
  knowledge_points: Record<string, number>
  knowledge_point_counts: Record<string, number>
  by_topic: Record<string, number>
  by_difficulty: Record<string, number>
  top_weak_points: Array<{ point: string; count: number }>
}

// 学习建议
interface Recommendation {
  category: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
}

// 学习报告
interface LearningReport {
  id: string
  student_id: string
  report_type: string
  period_start: string
  period_end: string
  status: string
  title?: string
  description?: string
  statistics?: ReportStatistics
  ability_analysis?: AbilityAnalysis
  weak_points?: WeakPoints
  recommendations?: Recommendations
  ai_insights?: any
  created_at: string
  updated_at: string
}
```

---

## 工具函数

### HTTP请求

**文件**: `src/utils/request.ts`

- 基于 Axios 封装
- 自动添加认证 token
- 统一错误处理
- 请求/响应拦截器

### 语音识别

**文件**: `src/utils/voiceRecognition.ts`

- Web Speech API 封装
- 支持中英文语音识别
- 实时转写

### 错误恢复

**文件**: `src/utils/errorRecovery.ts`

- 错误重试机制
- 降级处理策略

---

## 测试与质量

### 测试框架

- **单元测试**: Vitest + Vue Test Utils
- **集成测试**: Vitest
- **E2E测试**: 待配置（建议 Playwright 或 Cypress）

### 测试文件

```
tests/
├── unit/
│   ├── voiceRecognition.spec.ts
│   ├── request.spec.ts
│   └── errorRecovery.spec.ts
├── integration/
│   └── conversation.spec.ts
└── setup.ts
```

### 运行测试

```bash
# 运行测试
npm run test

# 运行测试UI
npm run test:ui

# 运行测试并生成覆盖率
npm run coverage
```

### 代码规范

```bash
# 代码格式化
npm run format

# 代码检查
npm run lint

# 类型检查
npm run type-check
```

---

## 数据可视化

### ECharts集成

**依赖**: `echarts@^5.6.0`

**使用场景**:
- 学习报告能力雷达图（ReportDetailView.vue）
- 学习趋势折线图
- 知识点掌握度柱状图
- 错题分布饼图

**示例**: 能力雷达图

```typescript
import * as echarts from 'echarts'

const option = {
  radar: {
    indicator: [
      { name: '词汇', max: 100 },
      { name: '语法', max: 100 },
      { name: '阅读', max: 100 },
      { name: '听力', max: 100 },
      { name: '口语', max: 100 }
    ]
  },
  series: [{
    type: 'radar',
    data: [{
      value: [80, 70, 85, 65, 75]
    }]
  }]
}
```

---

## 常见问题

### 开发服务器启动失败

```bash
# 清理依赖重装
rm -rf node_modules package-lock.json
npm install
```

### API 请求失败

确认后端服务运行在 http://localhost:8000

### ECharts 图表不显示

- 确认 DOM 元素已挂载
- 检查容器元素是否有宽高
- 使用 `onMounted` 确保组件已渲染

---

## 相关文件清单

### 核心文件

| 文件 | 描述 |
|------|------|
| `package.json` | 项目配置与依赖 |
| `vite.config.ts` | Vite构建配置 |
| `vitest.config.ts` | Vitest测试配置 |
| `tsconfig.json` | TypeScript配置 |
| `index.html` | HTML入口 |

### 源代码文件

| 文件 | 描述 |
|------|------|
| `src/main.ts` | 应用入口 |
| `src/App.vue` | 根组件 |
| `src/router/index.ts` | 路由配置 |
| `src/stores/auth.ts` | 认证状态管理 |
| `src/api/auth.ts` | 认证API客户端 |
| `src/api/mistake.ts` | 错题API客户端 |
| `src/api/report.ts` | 学习报告API客户端 ✨ |
| `src/types/auth.ts` | 认证类型定义 |
| `src/utils/request.ts` | HTTP请求工具 |
| `src/utils/voiceRecognition.ts` | 语音识别工具 |

### 页面组件（教师端）

| 文件 | 描述 |
|------|------|
| `src/views/teacher/DashboardView.vue` | 教师仪表板 |
| `src/views/teacher/StudentsView.vue` | 学生管理 |
| `src/views/teacher/LessonsView.vue` | 课程管理 |
| `src/views/teacher/AIPlanningView.vue` | AI备课助手 |

### 页面组件（学生端）

| 文件 | 描述 |
|------|------|
| `src/views/student/DashboardView.vue` | 学生仪表板 |
| `src/views/student/LearningView.vue` | 课程学习 |
| `src/views/student/MistakeBookView.vue` | 错题本 |
| `src/views/student/SpeakingView.vue` | 口语练习 |
| `src/views/student/ConversationView.vue` | AI对话 |
| `src/views/student/ConversationHistoryView.vue` | 对话历史 |
| `src/views/student/ProgressView.vue` | 学习进度 |
| `src/views/student/ReportsView.vue` | 学习报告列表 ✨ |
| `src/views/student/ReportDetailView.vue` | 报告详情 ✨ |

### 通用组件

| 文件 | 描述 |
|------|------|
| `src/components/ConversationStatus.vue` | 对话状态 |
| `src/components/ConversationMessage.vue` | 对话消息 |
| `src/components/ConversationFeedbackDrawer.vue` | 反馈抽屉 |


<claude-mem-context>
# Recent Activity

<!-- This section is auto-generated by claude-mem. Edit content outside the tags. -->

### Feb 6, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #1164 | 9:24 PM | ✅ | Coverage Directory Added to Gitignore | ~181 |
| #1163 | " | ✅ | 测试覆盖率目录添加到.gitignore | ~74 |
| #1161 | 9:23 PM | 🔵 | 检查前端项目.gitignore配置 | ~160 |
| #1115 | 8:52 PM | 🔵 | Vitest测试配置分析 | ~34 |
| #1046 | 8:23 PM | 🔄 | Vitest测试配置简化 - 移除不必要的插件 | ~78 |
| #1044 | 8:22 PM | 🔄 | Vitest CSS Configuration Simplified | ~114 |
| #1043 | " | 🔵 | CSS模块插件检查 | ~61 |
| #1042 | " | ✅ | Vitest CSS模块配置优化 | ~167 |
| #1038 | 8:21 PM | 🔄 | Vitest配置添加Element Plus自动导入支持 | ~112 |
| #999 | 8:09 PM | 🔵 | 开始规划口语练习AI对话服务 | ~103 |
| #989 | 8:01 PM | ✅ | Project Documentation Updated | ~220 |
</claude-mem-context>