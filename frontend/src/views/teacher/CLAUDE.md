# 教师端视图模块

> **模块路径**: `frontend/src/views/teacher`
> **主要职责**: 教师端用户界面组件
> **技术栈**: Vue 3 + TypeScript + Element Plus + ECharts + Pinia

---

## 变更记录

### 2026-02-06 19:30:00
- ✨ **重大更新**: 学生管理页面完全重构 (`StudentsView.vue`)
  - 从占位符实现为功能完整的学生诊断中心
  - 集成真实学生数据和知识图谱展示
  - 添加单个和批量诊断功能
  - ECharts能力雷达图可视化
  - 795行代码，完整单元测试覆盖

### 2026-02-06 16:40:00
- ✅ **新增**: 教案分享对话框状态管理
  - 集成分享功能到LessonsView
  - 分享统计和通知集成

---

## 页面组件列表

### 仪表板和概况

| 组件 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| 教师仪表板 | `DashboardView.vue` | 教师工作台概览 | ✅ 已实现 |
| 班级概况 | `ClassOverviewView.vue` | 班级学习数据分析 | ✅ 已实现 |

### 学生管理

| 组件 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| **学生管理** | **`StudentsView.vue`** | **学生列表、知识图谱、诊断** | **✨ 新增** |

### 教案管理

| 组件 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| 教案管理 | `LessonsView.vue` | 教案列表和操作 | ✅ 已实现 |
| 教案模板库 | `TemplateLibraryView.vue` | 模板浏览和使用 | ✅ 已实现 |
| 教案编辑器 | `QuestionEditorView.vue` | 题目编辑器 | ✅ 已实现 |
| 题库管理 | `QuestionBankListView.vue` | 题库列表 | ✅ 已实现 |
| 题库详情 | `QuestionBankDetailView.vue` | 题库详情 | ✅ 已实现 |
| 教案导出 | `LessonExportView.vue` | 教案导出功能 | ✅ 已实现 |

### 学习报告

| 组件 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| 学生报告列表 | `StudentReportsView.vue` | 班级学生报告概览 | ✅ 已实现 |
| 学生报告详情 | `StudentReportDetailView.vue` | 报告详细内容展示 | ✅ 已实现 |
| 报告详情（通用） | `ReportDetailView.vue` | 学习报告详情（学生端） | ✅ 已实现 |

### AI备课

| 组件 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| AI备课助手 | `AIPlanningView.vue` | AI辅助备课 | ✅ 已实现 |

### 教案分享

| 组件 | 文件 | 功能描述 | 状态 |
|------|------|----------|------|
| 分享教案列表 | `SharedLessonsView.vue` | 查看共享教案 | ✅ 已实现 |

---

## 新增组件详细说明

### StudentsView.vue - 学生管理页面

**文件**: `frontend/src/views/teacher/StudentsView.vue`

**代码规模**: 795行

**功能特性**:

#### 1. 学生列表管理
- 表格展示学生信息（头像、姓名、邮箱）
- CEFR等级标签显示
- 目标考试和目标分数
- 分页支持（10/20/50/100条/页）
- 搜索和班级筛选

#### 2. 知识图谱查看
- 右侧抽屉式展示
- 基本信息（CEFR等级、版本、更新时间）
- ECharts能力雷达图（6维能力可视化）
- 考试准备度统计
  - 总练习数
  - 覆盖主题数
  - 近期活跃度（7天）
- 薄弱点分析列表
  - 按优先级排序
  - 显示当前水平
- 学习建议展示
  - 系统建议和AI建议
  - 按优先级分类

#### 3. 单个学生诊断
- 诊断按钮（对未诊断学生）
- 重新诊断按钮（对已诊断学生）
- 诊断确认对话框
- 诊断进度显示
- 诊断完成后自动展示知识图谱

#### 4. 批量诊断功能
- 表格多选支持
- 批量诊断按钮
- 批量诊断进度对话框
  - 进度条显示
  - 实时统计（已完成/失败/总计）
  - 当前诊断学生显示
- 顺序执行（避免服务器过载）
- 结果统计汇总

#### 5. 状态管理
- 学生列表状态
- 知识图谱缓存（Map）
- 诊断状态
- 批量选择状态

#### 6. 辅助功能
- 日期时间格式化
- 优先级类型映射
- 优先级文本映射
- 退出登录确认

#### 组件依赖

```typescript
// 主要依赖
import studentApi from '@/api/student'
import { useAuthStore } from '@/stores/auth'
import * as echarts from 'echarts'

// Element Plus组件
import {
  Search, Refresh, Monitor,
  TrendCharts, DataAnalysis,
  Warning, ReadingLamp
} from '@element-plus/icons-vue'
```

#### 路由配置

```typescript
{
  path: '/teacher/students',
  name: 'StudentsView',
  component: () => import('@/views/teacher/StudentsView.vue'),
  meta: { requiresAuth: true, role: 'teacher' }
}
```

#### 使用示例

```vue
<template>
  <StudentsView />
</template>

<script setup lang="ts">
import StudentsView from '@/views/teacher/StudentsView.vue'
</script>
```

#### ECharts配置

能力雷达图配置：

```typescript
const option = {
  radar: {
    indicator: abilities.map(item => ({
      name: item.name,
      max: 100
    })),
    radius: '60%'
  },
  series: [{
    type: 'radar',
    data: [{
      value: abilities.map(item => item.value),
      name: '能力值',
      areaStyle: {
        color: 'rgba(64, 158, 255, 0.3)'
      }
    }]
  }
}
```

#### 样式特性

- 响应式布局设计
- 卡片阴影效果
- 渐变背景头部
- 表格行悬停效果
- 优先级颜色标签
- 移动端适配

#### 单元测试

**测试文件**: `tests/unit/components/StudentsView.spec.ts`

**测试覆盖**:
- 组件渲染（2个测试）
- 学生列表加载（2个测试）
- 知识图谱查看（3个测试）
- 学生诊断功能（1个测试）
- 批量选择功能（2个测试）
- 辅助方法（3个测试）
- 计算属性（2个测试）

**测试结果**: 15个测试全部通过，82.67%代码覆盖率

---

## 组件开发规范

### 命名规范

- 组件文件名：PascalCase，以 `View` 结尾
- 组件导入：与文件名一致
- 路由路径：kebab-case

### 目录结构

```
teacher/
├── ClassOverviewView.vue
├── DashboardView.vue
├── StudentsView.vue
├── LessonsView.vue
├── TemplateLibraryView.vue/
│   ├── TemplateEditorDialog.vue
│   └── TemplatePreviewDrawer.vue
├── QuestionEditorView.vue
├── QuestionBankListView.vue
├── QuestionBankDetailView.vue
├── LessonExportView.vue/
│   └── LessonSelector.vue
├── StudentReportsView.vue
├── StudentReportDetailView.vue
├── SharedLessonsView.vue
└── AIPlanningView.vue
```

### 代码模板

```vue
<template>
  <div class="component-page">
    <el-container>
      <el-header>
        <!-- 页面标题和导航 -->
      </el-header>

      <el-main>
        <!-- 主要内容 -->
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// 状态
const loading = ref(false)
const data = ref([])

// 方法
async function loadData() {
  // 加载数据
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.component-page {
  min-height: 100vh;
  background: #f5f7fa;
}
</style>
```

---

## 测试

### 测试文件

| 文件 | 描述 | 测试数量 |
|------|------|----------|
| `StudentsView.spec.ts` | 学生管理组件测试 | 15 |

### 运行测试

```bash
# 运行组件测试
npm run test tests/unit/components/StudentsView.spec.ts

# 运行所有教师视图测试
npm run test tests/unit/components/ --coverage
```

### 测试覆盖率

| 组件 | 语句覆盖率 | 状态 |
|------|-----------|------|
| `StudentsView.vue` | 82.67% | ✅ 高覆盖率 |

---

## 相关文件清单

### 核心组件

| 文件 | 描述 | 状态 |
|------|------|------|
| `DashboardView.vue` | 教师仪表板 | ✅ |
| `StudentsView.vue` | **学生管理（新增）** | **✨** |
| `LessonsView.vue` | 教案管理 | ✅ |
| `TemplateLibraryView.vue` | 教案模板库 | ✅ |
| `StudentReportsView.vue` | 学生报告列表 | ✅ |
| `StudentReportDetailView.vue` | 学生报告详情 | ✅ |
| `AIPlanningView.vue` | AI备课助手 | ✅ |

### 共享组件

| 文件 | 描述 |
|------|------|
| `ShareDialog.vue` | 教案分享对话框 |
| `ShareNotificationBell.vue` | 分享通知铃铛 |

### API客户端

| 文件 | 描述 |
|------|------|
| `../api/teacherReport.ts` | 教师报告API |
| `../api/student.ts` | **学生管理API（新增）** |

---

## 开发指南

### 添加新的教师页面

1. 在 `src/views/teacher/` 创建新的Vue组件
2. 实现页面布局和功能
3. 添加路由配置
4. 创建单元测试
5. 更新本模块文档

### 使用ECharts

```typescript
import * as echarts from 'echarts'

// 初始化图表
const chart = echarts.init(domRef.value)
chart.setOption(option)

// 响应式
window.addEventListener('resize', () => chart.resize())

// 清理
chart.dispose()
```

### Element Plus图标

```typescript
import {
  Search, Refresh, Monitor,
  TrendCharts, DataAnalysis,
  Warning, ReadingLamp
} from '@element-plus/icons-vue'

// 在模板中使用
<el-icon :size="20">
  <Search />
</el-icon>
```

---

## 常见问题

### ECharts图表不显示

确保DOM元素已挂载：
```typescript
await nextTick()
const chart = echarts.init(radarChartRef.value)
```

### 表格数据不更新

确保正确处理响应式数据：
```typescript
students.value = data // ✅
students = data    // ❌ 失去响应性
```

### 批量诊断失败

检查后端服务是否支持并发请求，必要时使用顺序执行。

### 路由跳转问题

确保路由meta配置正确：
```typescript
meta: { requiresAuth: true, role: 'teacher' }
```


<claude-mem-context>
# Recent Activity

<!-- This section is auto-generated by claude-mem. Edit content outside the tags. -->

### Feb 6, 2026

| ID | Time | T | Title | Read |
|----|------|---|-------|------|
| #885 | 4:40 PM | ✅ | Share Dialog State Added to LessonsView | ~208 |
</claude-mem-context>