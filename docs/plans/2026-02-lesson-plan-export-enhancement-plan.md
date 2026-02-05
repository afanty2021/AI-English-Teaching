# 教案导出功能完善实施计划

> **创建日期**: 2026-02-05
> **计划工期**: 5-7天
> **优先级**: 高 (MVP发布前必须完成)

---

## 📋 任务概述

基于现有AI教案生成系统，完善教案导出功能，包括PDF格式教案导出、PPT大纲生成和教案模板库扩充三大核心功能。

### 🎯 项目目标

1. **PDF格式教案导出**: 将AI生成的教案导出为专业PDF格式
2. **PPT大纲生成**: 智能生成并导出PPT大纲
3. **教案模板库扩充**: 提供丰富的教案模板，支持快速创建

---

## 📊 现状分析

### ✅ 已完成部分

**后端基础架构**:
- ✅ `LessonPlan` 模型 - 完整的教案数据模型
- ✅ `LessonPlanTemplate` 模型 - 教案模板基础模型
- ✅ `LessonPlanService` - 教案生成服务
  - 已实现 `generate_lesson_plan()` - AI教案生成
  - 已实现 `generate_ppt_outline()` - PPT大纲生成
  - 已实现 `generate_difficulty_levels()` - 分层材料生成
  - 已实现 `generate_exercises()` - 练习题生成
- ✅ `pdf_renderer_service.py` - PDF渲染服务 (markdown2 + weasyprint)
- ✅ PDF辅助工具 - 跨平台字体支持

**前端基础**:
- ✅ 教案API客户端 - `frontend/src/api/lesson.ts`
- ✅ 教案类型定义 - `frontend/src/types/lesson.ts`
- ✅ 已有教案相关页面结构

### ❌ 待完善部分

1. **教案导出服务缺失**:
   - 缺少专门的教案导出服务
   - 缺少PDF模板和样式
   - 缺少PPT导出功能

2. **API端点不完整**:
   - 缺少教案导出API端点
   - 缺少模板管理API端点

3. **前端功能缺失**:
   - 缺少教案导出页面
   - 缺少模板管理页面
   - 缺少PPT预览功能

4. **模板库为空**:
   - 系统缺少预设教案模板
   - 缺少模板分类和搜索

---

## 🎨 实施方案

### Phase 1: 教案导出服务开发 (Day 1-2)

#### 1.1 创建教案导出服务

**文件**: `backend/app/services/lesson_plan_export_service.py`

**核心功能**:
```python
class LessonPlanExportService:
    """教案导出服务"""

    async def export_as_pdf() -> bytes
    """导出教案为PDF格式"""

    async def export_ppt_outline() -> dict
    """导出PPT大纲为结构化数据"""

    async def export_as_markdown() -> str
    """导出教案为Markdown格式"""

    async def create_presentation_slides() -> List[dict]
    """创建PPT幻灯片数据"""
```

**实现要点**:
- 使用现有的 `pdf_renderer_service.py` 进行PDF渲染
- 基于Jinja2模板生成教案内容
- 支持中文字体和样式
- 支持图片、表格、分页等复杂内容

#### 1.2 创建教案PDF模板

**文件**: `backend/app/templates/lesson_plan_report.md.j2`

**模板内容**:
- 教案封面（标题、教师、日期、等级）
- 教学目标（知识、技能、策略）
- 教学流程（6个阶段详细描述）
- 核心词汇表（带音标、释义、例句）
- 语法点详解（规则、例句、易错点）
- 分层阅读材料（如有）
- 练习题集（如有）
- PPT大纲概览
- 教学资源和素材

**样式设计**:
- 专业教学文档风格
- 清晰的章节结构
- 表格和列表美化
- 重点内容高亮

#### 1.3 创建PPT导出服务

**文件**: `backend/app/services/ppt_export_service.py`

**核心功能**:
```python
class PPTExportService:
    """PPT导出服务"""

    async def generate_ppt_from_outline() -> dict
    """从PPT大纲生成完整的PPT数据"""

    async def export_as_pptx() -> bytes
    """导出为PPTX格式文件"""

    async def export_as_html() -> str
    """导出为HTML格式（在线预览）"""
```

**技术方案**:
- 使用 `python-pptx` 库生成PPTX文件
- 支持多种布局（标题页、内容页、总结页等）
- 自动配色方案和字体
- 支持图片和图表插入

### Phase 2: API端点开发 (Day 2-3)

#### 2.1 扩展教案API

**文件**: `backend/app/api/v1/lesson_plans.py`

**新增端点**:
```python
# 导出教案
POST /api/v1/lesson-plans/{lesson_plan_id}/export/pdf
POST /api/v1/lesson-plans/{lesson_plan_id}/export/markdown

# PPT导出
POST /api/v1/lesson-plans/{lesson_plan_id}/export/ppt
GET  /api/v1/lesson-plans/{lesson_plan_id}/ppt/preview

# 模板管理
GET  /api/v1/lesson-plan-templates
POST /api/v1/lesson-plan-templates
GET  /api/v1/lesson-plan-templates/{template_id}
PUT  /api/v1/lesson-plan-templates/{template_id}
DELETE /api/v1/lesson-plan-templates/{template_id}

# 模板应用
POST /api/v1/lesson-plans/from-template/{template_id}
```

#### 2.2 API实现细节

**导出端点**:
- 验证教案存在性和权限
- 调用导出服务生成文件
- 返回文件下载或预览链接
- 支持异步导出（大型教案）

**模板管理端点**:
- 支持分页查询和筛选
- 权限控制（教师只能管理自己的模板）
- 预设系统模板只读

### Phase 3: 教案模板库扩充 (Day 3-4)

#### 3.1 创建系统预设模板

**模板分类**:

**按等级分类**:
1. **A1-A2 (初级)**:
   - 日常问候与介绍
   - 数字与颜色
   - 家庭与朋友
   - 食物与饮料
   - 时间与日程

2. **B1-B2 (中级)**:
   - 旅游与交通
   - 工作与职业
   - 健康与运动
   - 环境与科技
   - 文化与娱乐

3. **C1-C2 (高级)**:
   - 学术讨论
   - 商务沟通
   - 社会议题
   - 文学赏析
   - 专业英语

**按考试类型分类**:
1. **通用英语**:
   - 日常交流场景
   - 社交互动
   - 兴趣爱好

2. **学术英语**:
   - 论文写作
   - 学术报告
   - 课堂讨论

3. **商务英语**:
   - 会议沟通
   - 商务谈判
   - 邮件写作

#### 3.2 模板数据初始化

**创建初始化脚本**: `backend/scripts/init_lesson_templates.py`

**功能**:
- 创建50+个预设教案模板
- 覆盖各个等级和场景
- 包含完整的教学流程和资源
- 支持一键导入到数据库

#### 3.3 模板数据结构

**模板字段**:
```python
class LessonPlanTemplate(Base):
    # 基础信息
    name: str              # 模板名称
    description: str        # 模板描述
    level: str             # 适用等级 (A1-C2)
    target_exam: str       # 目标考试 (可选)

    # 模板结构 (JSONB)
    template_structure: dict  # 教案结构模板
    default_objectives: dict  # 默认教学目标
    vocabulary_examples: dict  # 词汇示例
    grammar_examples: list    # 语法示例
    exercise_templates: dict  # 练习题模板

    # 元数据
    is_system: bool         # 是否系统模板
    usage_count: int        # 使用次数
    tags: list             # 标签
```

### Phase 4: 前端页面开发 (Day 4-5)

#### 4.1 教案导出页面

**文件**: `frontend/src/views/teacher/LessonPlanExportView.vue`

**功能布局**:
```
┌─────────────────────────────────────────┐
│ 教案导出 - {教案标题}                      │
├─────────────────────────────────────────┤
│                                         │
│  [📄 PDF导出]    [📝 Markdown导出]      │
│  [📊 PPT导出]     [👁  预览]           │
│                                         │
│ 导出设置:                                │
│ ☑️ 包含教学目标                           │
│ ☑️ 包含教学流程                           │
│ ☑️ 包含词汇表                             │
│ ☑️ 包含语法点                             │
│ ☑️ 包含练习题                             │
│ ☑️ 包含PPT大纲                           │
│                                         │
│         [开始导出]                       │
└─────────────────────────────────────────┘
```

#### 4.2 教案模板库页面

**文件**: `frontend/src/views/teacher/LessonTemplateLibraryView.vue`

**功能布局**:
```
┌─────────────────────────────────────────┐
│ 教案模板库                                │
├─────────────────────────────────────────┤
│ 筛选: [等级▼] [考试类型▼] [主题搜索]       │
├─────────────────────────────────────────┤
│ 模板卡片:                                │
│ ┌─────────────────────┐                 │
│ │ 日常问候与介绍       │                 │
│ │ A1-A2 | 通用英语   │                 │
│ │ 使用次数: 45       │                 │
│ │ [预览] [使用模板]  │                 │
│ └─────────────────────┘                 │
│ ┌─────────────────────┐                 │
│ │ 商务会议沟通       │                 │
│ │ B2-C1 | 商务英语   │                 │
│ │ 使用次数: 32       │                 │
│ │ [预览] [使用模板]  │                 │
│ └─────────────────────┘                 │
└─────────────────────────────────────────┘
```

#### 4.3 PPT预览组件

**文件**: `frontend/src/components/lesson/PPTPreviewModal.vue`

**功能**:
- 幻灯片缩略图列表
- 支持全屏预览
- 导出为PPTX按钮
- 幻灯片备注显示

#### 4.4 API客户端扩展

**文件**: `frontend/src/api/lessonExport.ts`

```typescript
interface LessonExportApi {
  // 教案导出
  exportAsPDF(lessonPlanId: string, options: ExportOptions): Promise<Blob>
  exportAsMarkdown(lessonPlanId: string): Promise<string>
  exportAsPPT(lessonPlanId: string): Promise<Blob>

  // 模板管理
  getTemplates(params: TemplateQuery): Promise<PagedResult<LessonTemplate>>
  createTemplate(template: CreateTemplateRequest): Promise<LessonTemplate>
  updateTemplate(id: string, updates: UpdateTemplateRequest): Promise<LessonTemplate>
  deleteTemplate(id: string): Promise<void>

  // 从模板创建
  createFromTemplate(templateId: string, params: CreateFromTemplateRequest): Promise<LessonPlan>
}
```

### Phase 5: 测试与优化 (Day 5-6)

#### 5.1 单元测试

**后端测试**:
- `tests/services/test_lesson_plan_export_service.py` (30+ 测试用例)
- `tests/services/test_ppt_export_service.py` (20+ 测试用例)
- `tests/api/test_lesson_plans_export.py` (25+ 测试用例)

**前端测试**:
- `tests/unit/LessonExportView.spec.ts` (15+ 测试用例)
- `tests/unit/LessonTemplateLibrary.spec.ts` (20+ 测试用例)

#### 5.2 集成测试

**测试场景**:
- 完整教案生成→导出流程测试
- 模板创建→应用→导出流程测试
- PPT生成→预览→导出流程测试

#### 5.3 性能优化

- PDF渲染优化（大文档分页处理）
- 图片压缩和懒加载
- 异步导出队列
- 缓存优化（重复导出）

---

## 📐 技术实现细节

### PDF导出技术栈

```
教案数据 → Jinja2模板 → Markdown → HTML → PDF (weasyprint)
```

**优势**:
- 利用现有的PDF渲染服务
- 模板灵活，易于定制
- 支持复杂布局和样式
- 跨平台兼容性好

**模板示例**:
```markdown
# {{ lesson_plan.title }}

**教师**: {{ teacher.name }}
**等级**: {{ lesson_plan.level }}
**时长**: {{ lesson_plan.duration }}分钟
**主题**: {{ lesson_plan.topic }}

## 教学目标

{% for category, objectives in lesson_plan.objectives.items() %}
### {{ category }}
{% for obj in objectives %}
- {{ obj }}
{% endfor %}
{% endfor %}
```

### PPT导出技术栈

```
PPT大纲 → python-pptx → PPTX文件
```

**功能特性**:
- 10+种专业布局模板
- 自动配色方案（可自定义）
- 图表和图片支持
- 演讲者备注

### 模板系统设计

**三层模板体系**:
1. **系统模板** - 预置的高质量模板，只读
2. **教师模板** - 教师创建的私有模板
3. **共享模板** - 教师分享的优质模板

**模板继承**:
```
系统模板 (基础结构)
    ↓
教师模板 (个性化修改)
    ↓
具体教案 (实际应用)
```

---

## 📊 开发任务分解

### Task 1.1: 后端教案导出服务 (8小时)
- [ ] 创建 `LessonPlanExportService` 类
- [ ] 实现PDF导出功能
- [ ] 实现Markdown导出功能
- [ ] 创建教案PDF模板
- [ ] 测试和调试

### Task 1.2: PPT导出服务 (6小时)
- [ ] 创建 `PPTExportService` 类
- [ ] 实现PPTX生成功能
- [ ] 实现HTML预览功能
- [ ] 创建PPT样式模板
- [ ] 测试和调试

### Task 1.3: API端点开发 (6小时)
- [ ] 扩展教案API路由
- [ ] 实现导出端点
- [ ] 实现模板管理端点
- [ ] 权限控制实现
- [ ] API文档更新

### Task 1.4: 模板库初始化 (4小时)
- [ ] 设计50+个教案模板
- [ ] 创建初始化脚本
- [ ] 批量导入模板数据
- [ ] 模板验证和测试

### Task 1.5: 前端教案导出页面 (8小时)
- [ ] 创建 `LessonPlanExportView.vue`
- [ ] 实现导出选项UI
- [ ] 实现文件下载功能
- [ ] 实现预览功能
- [ ] 样式和交互优化

### Task 1.6: 前端模板库页面 (8小时)
- [ ] 创建 `LessonTemplateLibraryView.vue`
- [ ] 实现模板筛选和搜索
- [ ] 实现模板预览功能
- [ ] 实现模板应用功能
- [ ] 样式和交互优化

### Task 1.7: PPT预览组件 (6小时)
- [ ] 创建 `PPTPreviewModal.vue`
- [ ] 实现幻灯片预览
- [ ] 实现全屏查看
- [ ] 实现导出功能

### Task 1.8: 测试和优化 (8小时)
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 性能测试和优化
- [ ] Bug修复

**总计**: 54小时 (约7个工作日)

---

## 🎯 验收标准

### 功能验收
- ✅ PDF导出功能完整，支持所有教案内容
- ✅ PPT导出功能正常，样式美观
- ✅ 教案模板库包含50+个预设模板
- ✅ 模板筛选、搜索、应用功能正常
- ✅ 前端界面美观，操作流畅

### 性能验收
- ✅ PDF导出时间 < 10秒 (50页教案)
- ✅ PPT导出时间 < 5秒 (20页PPT)
- ✅ 模板加载时间 < 2秒
- ✅ 页面响应时间 < 1秒

### 质量验收
- ✅ 代码覆盖率 > 85%
- ✅ 单元测试全部通过
- ✅ 集成测试全部通过
- ✅ 无严重级别以上Bug

---

## 📦 依赖和资源

### 后端依赖
```python
# 新增依赖
python-pptx>=0.6.23        # PPT生成
markdown2>=2.4.12           # Markdown处理 (已有)
weasyprint>=61.2           # PDF渲染 (已有)
```

### 前端依赖
```json
{
  "file-saver": "^2.0.5",  // 文件下载
  "vue-pdf": "^4.3.0"      // PDF预览 (可选)
}
```

### 设计资源
- 教案PDF模板设计稿
- PPT布局模板
- UI组件设计

---

## 🔄 风险评估与应对

### 高风险
1. **PDF中文字体问题**
   - 风险: 中文字符显示异常
   - 应对: 使用现有 `pdf_helpers.py` 字体检测工具

2. **PPT生成性能问题**
   - 风险: 大型PPT生成耗时过长
   - 应对: 异步生成 + 进度提示

### 中风险
1. **模板数据一致性**
   - 风险: 模板结构与教案模型不匹配
   - 应对: 严格的数据验证和单元测试

2. **前端文件下载兼容性**
   - 风险: 不同浏览器下载行为差异
   - 应对: 使用成熟的文件下载库

### 低风险
1. **API向后兼容性**
   - 风险: 新增API影响现有功能
   - 应对: 只新增不修改现有API

---

## 📅 项目时间线

| 日期 | 阶段 | 主要任务 | 交付物 |
|------|------|----------|--------|
| Day 1 | Phase 1 | 教案导出服务开发 | 导出服务 + PDF模板 |
| Day 2 | Phase 1-2 | PPT导出 + API开发 | PPT服务 + API端点 |
| Day 3 | Phase 2-3 | API完善 + 模板库 | 完整API + 模板数据 |
| Day 4 | Phase 4 | 前端页面开发 | 导出页面 + 模板库页面 |
| Day 5 | Phase 4 | 前端组件开发 | PPT预览 + API客户端 |
| Day 6 | Phase 5 | 测试和优化 | 测试报告 + 性能优化 |
| Day 7 | 缓冲 | Bug修复 + 文档完善 | 完整功能 + 文档 |

---

## 📚 相关文档

- [现有教案系统文档](../backend/CLAUDE.md#lesson-plan-教案服务)
- [PDF渲染服务文档](../backend/CLAUDE.md#pdf渲染服务)
- [前端开发规范](../frontend/CLAUDE.md)
- [API设计规范](../docs/api-design.md)

---

## 🎉 项目收益

### 对教师的价值
1. **提高效率**: 一键生成专业教案，节省90%备课时间
2. **标准化**: 统一教案格式，便于管理和分享
3. **多样化**: 丰富的模板库，适应不同教学场景
4. **可视化**: PPT预览，直观展示教学流程

### 对学生的价值
1. **内容质量**: AI生成的教案内容科学、系统和有趣
2. **个性化**: 基于学生水平的差异化教学
3. **互动性**: 丰富的练习和活动设计

### 对平台的价值
1. **差异化**: 强大的AI备课功能形成竞争壁垒
2. **用户粘性**: 教师依赖度高，迁移成本高
3. **数据价值**: 教案数据可用于AI模型优化

---

**下一步**: 开始Phase 1开发，创建教案导出服务和PDF模板。
