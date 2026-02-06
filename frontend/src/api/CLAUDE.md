# API 客户端模块

> **模块路径**: `frontend/src/api`
> **主要职责**: 封装后端API调用，提供类型安全的接口
> **技术栈**: TypeScript + Axios + Vitest

---

## 变更记录

### 2026-02-06 19:00:00
- ✨ **新增**: 学生管理API客户端 (`student.ts`)
  - 学生列表查询（支持分页、班级筛选）
  - 学生详情获取
  - 知识图谱获取
  - 触发AI诊断
  - 学习进度查询
  - 完整TypeScript类型定义

### 2026-02-06 18:30:00
- ✨ **新增**: 通知偏好API客户端 (`notification.ts`)
  - 通知偏好获取/更新
  - WebSocket订阅管理
  - 类型定义完整

---

## API客户端列表

### 对话服务

| 文件 | 描述 | 端点数量 |
|------|------|----------|
| `conversation.ts` | 口语对话API | 3 |

### 内容管理

| 文件 | 描述 | 端点数量 |
|------|------|----------|
| `lesson.ts` | 课程管理API | 5+ |
| `lessonTemplate.ts` | 教案模板API | - |
| `lessonExport.ts` | 教案导出API | - |
| `question.ts` | 题目API | - |
| `questionBank.ts` | 题库API | - |

### 学习管理

| 文件 | 描述 | 端点数量 |
|------|------|----------|
| `practiceSession.ts` | 练习会话API | - |
| `mistake.ts` | 错题本API | 8 |
| `report.ts` | 学习报告API | 5 |

### 用户管理

| 文件 | 描述 | 端点数量 |
|------|------|----------|
| `student.ts` | **学生管理API（新增）** | **5** |
| `notification.ts` | **通知偏好API（新增）** | **3** |
| `user.ts` | 用户API | - |
| `auth.ts` | 认证API | 3 |

### 教师专用

| 文件 | 描述 | 端点数量 |
|------|------|----------|
| `teacherReport.ts` | 教师报告API | 6 |
| `recommendation.ts` | 内容推荐API | - |

---

## 新增API详细说明

### student.ts - 学生管理API

**文件**: `frontend/src/api/student.ts`

**功能**: 提供学生管理和知识图谱诊断的API接口

#### 类型定义

```typescript
// 学生档案
interface StudentProfile {
  id: string
  user_id: string
  username: string
  email: string
  target_exam?: string
  target_score?: number
  study_goal?: string
  current_cefr_level?: string
  grade?: string
  created_at: string
}

// 知识图谱数据
interface KnowledgeGraph {
  student_id: string
  nodes: Array<{
    id: string
    type: string
    label: string
    value?: number
    level?: string
    readiness?: boolean
  }>
  edges: Array<{
    source: string
    target: string
    type: string
  }>
  abilities: Record<string, number>
  cefr_level?: string
  exam_coverage: {
    total_practices: number
    topics_covered: number
    recent_activity: number
  }
  ai_analysis: {
    weak_points?: Array<{...}>
    recommendations?: Array<{...}>
  }
  last_ai_analysis_at?: string
  version: number
  created_at: string
  updated_at: string
}

// 学生进度
interface StudentProgress {
  student_id: string
  target_exam?: string
  target_score?: number
  current_cefr_level?: string
  conversation_count: number
  practice_count: number
  average_score: number
}
```

#### API方法

| 方法 | 端点 | 描述 |
|------|------|------|
| `getStudents(params?)` | `GET /api/v1/students` | 获取学生列表 |
| `getStudent(id)` | `GET /api/v1/students/{id}` | 获取学生详情 |
| `getKnowledgeGraph(id)` | `GET /api/v1/students/{id}/knowledge-graph` | 获取知识图谱 |
| `diagnoseStudent(id, data?)` | `POST /api/v1/students/{id}/diagnose` | 触发AI诊断 |
| `getStudentProgress(id)` | `GET /api/v1/students/{id}/progress` | 获取学习进度 |

#### 使用示例

```typescript
import studentApi from '@/api/student'

// 获取学生列表
const students = await studentApi.getStudents({
  skip: 0,
  limit: 20,
  classId: 'class-1'
})

// 获取知识图谱
const graph = await studentApi.getKnowledgeGraph('student-1')
console.log(graph.abilities) // { listening: 75, reading: 80, ... }

// 触发诊断
const result = await studentApi.diagnoseStudent('student-1')
console.log(result.cefr_level) // 'B1'
```

---

### notification.ts - 通知偏好API

**文件**: `frontend/src/api/notification.ts`

**功能**: 提供用户通知偏好设置的API接口

#### API方法

| 方法 | 端点 | 描述 |
|------|------|------|
| `getPreferences()` | `GET /api/v1/notifications/preferences` | 获取通知偏好 |
| `updatePreferences(data)` | `PUT /api/v1/notifications/preferences` | 更新通知偏好 |
| `subscribeNotifications(type)` | `WS /ws/notifications/{type}` | 订阅WebSocket通知 |

#### 使用示例

```typescript
import notificationApi from '@/api/notification'

// 获取通知偏好
const prefs = await notificationApi.getPreferences()

// 更新通知偏好
await notificationApi.updatePreferences({
  share_notifications: true,
  share_channel: { in_app: true, email: false }
})
```

---

## 测试

### 测试文件

| 文件 | 描述 | 测试数量 |
|------|------|----------|
| `student.spec.ts` | 学生API测试 | 10 |
| 其他API测试 | - | - |

### 运行测试

```bash
# 运行所有API测试
npm run test tests/unit/student.spec.ts

# 生成覆盖率报告
npm run test tests/unit/ --coverage
```

### 测试覆盖率

| 模块 | 语句覆盖率 | 状态 |
|------|-----------|------|
| `student.ts` | 100% | ✅ 完全覆盖 |

---

## 开发指南

### 添加新的API客户端

1. 在 `src/api/` 目录创建新的TypeScript文件
2. 定义接口类型
3. 封装API调用
4. 使用 `request` 工具进行HTTP请求
5. 添加对应的测试文件

### 请求工具

所有API客户端使用 `@/utils/request` 中的请求方法：

```typescript
import { get, post } from '@/utils/request'

// GET请求
const data = await get<ResponseType>('/api/endpoint')

// POST请求
const result = await post<ResponseType>('/api/endpoint', { data })
```

---

## 相关文件清单

### 核心文件

| 文件 | 描述 |
|------|------|
| `auth.ts` | 认证API客户端 |
| `student.ts` | **学生管理API（新增）** |
| `notification.ts` | **通知偏好API（新增）** |
| `mistake.ts` | 错题本API客户端 |
| `report.ts` | 学习报告API客户端 |
| `conversation.ts` | 对话API客户端 |
| `lesson.ts` | 课程API客户端 |

### 类型定义文件

| 文件 | 描述 |
|------|------|
| `../types/auth.ts` | 认证类型定义 |
| `../types/conversation.ts` | 对话类型定义 |
| `../types/question.ts` | 题目类型定义 |

---

## 常见问题

### API请求失败

检查后端服务是否运行：
```bash
curl http://localhost:8000/api/v1/students
```

### 类型错误

确保TypeScript配置正确：
```bash
npm run type-check
```

### 测试失败

运行特定测试文件并查看详细输出：
```bash
npm run test tests/unit/student.spec.ts --reporter=verbose
```
