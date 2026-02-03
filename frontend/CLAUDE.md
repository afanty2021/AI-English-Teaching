[根目录](../CLAUDE.md) > **frontend**

# frontend - 前端应用模块

> **模块类型**: Vue3 前端应用
> **主要职责**: 教师端与学生端用户界面
> **技术栈**: Vue3 + Vite + Pinia + Element Plus

---

## 模块职责

frontend 模块是 AI 赋能英语教学系统的用户界面，提供：

1. **教师端**: 班级管理、学生诊断报告、AI备课助手、教学内容库
2. **学生端**: 我的课程、个性化练习、AI口语对话、进度追踪
3. **认证系统**: 登录、注册、密码重置
4. **状态管理**: 用户状态、认证状态、应用全局状态

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
/student               # 学生端
  /student/dashboard   # 学生仪表板
  /student/practice    # 练习页面
  /student/progress    # 学习进度
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
- `mistakeApi.exportMistakes()` - 导出错题本（PDF/Markdown/Word）✨
- `mistakeApi.exportSingleMistake()` - 导出单个错题 ✨

---

## 关键依赖与配置

### 项目依赖

**文件**: `package.json`

| 依赖类别 | 主要包 | 版本 |
|---------|-------|------|
| 框架 | Vue, Vue Router, Pinia | ^3.4.0 |
| UI库 | Element Plus, @element-plus/icons-vue | ^2.5.0 |
| 构建工具 | Vite, @vitejs/plugin-vue | ^5.0.0 |
| HTTP客户端 | Axios | ^1.6.0 |
| 开发工具 | TypeScript, vue-tsc | ^5.3.0 |

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
| StudentsView | `src/views/teacher/StudentsView.vue` | 学生管理 |
| LessonsView | `src/views/teacher/LessonsView.vue` | 课程管理 |

### 学生端页面

| 组件 | 路径 | 描述 |
|------|------|------|
| DashboardView | `src/views/student/DashboardView.vue` | 学生仪表板 |
| LearningView | `src/views/student/LearningView.vue` | 课程学习 |
| **MistakeBookView** | `src/views/student/MistakeBookView.vue` | **错题本（含PDF导出）** ✨ |
| SpeakingView | `src/views/student/SpeakingView.vue` | 口语练习 |
| ConversationView | `src/views/student/ConversationView.vue` | AI对话 |
| ConversationHistoryView | `src/views/student/ConversationHistoryView.vue` | 对话历史 |
| ProgressView | `src/views/student/ProgressView.vue` | 学习进度 |

### 通用页面

| 组件 | 路径 | 描述 |
|------|------|------|
| HomeView | `src/views/HomeView.vue` | 首页 |
| NotFoundView | `src/views/NotFoundView.vue` | 404页面 |

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

---

## 测试与质量

### 测试框架

待配置（计划使用 Vitest + Vue Test Utils）。

### 代码规范

```bash
# 代码格式化
npm run format

# 代码检查
npm run lint
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

---

## 相关文件清单

### 核心文件

| 文件 | 描述 |
|------|------|
| `package.json` | 项目配置与依赖 |
| `vite.config.ts` | Vite构建配置 |
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
| `src/types/auth.ts` | 认证类型定义 |

### 页面组件

| 文件 | 描述 |
|------|------|
| `src/views/LoginView.vue` | 登录页面 |
| `src/views/RegisterView.vue` | 注册页面 |
| `src/views/HomeView.vue` | 首页 |
| `src/views/teacher/StudentsView.vue` | 学生管理 |
| `src/views/teacher/LessonsView.vue` | 课程管理 |
| `src/views/student/ProgressView.vue` | 学习进度 |

---

## 变更记录

### 2026-02-03 19:00:00
- 🔧 **修复**: MistakeBookView.vue 导入问题
  - 移除重复的 Document 图标导入
  - 添加 ElLoading 导入
- 📝 **文档**: 更新错题导出功能说明
  - API 层支持 PDF/Markdown/Word 三种格式导出
  - UI 层完整实现批量导出和单个错题导出

### 2026-02-03 09:49:22
- 创建前端模块文档
- 整理页面组件与路由结构
- 记录状态管理与API客户端
