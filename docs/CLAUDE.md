[根目录](../CLAUDE.md) > **docs**

# docs - 文档模块

> **模块类型**: Markdown 文档
> **主要职责**: 项目设计文档与实施计划
> **格式**: Markdown (.md)

---

## 模块职责

docs 模块包含 AI 赋能英语教学系统的完整文档体系：

1. **设计文档**: 系统设计、核心模块设计
2. **实施计划**: MVP阶段实施计划
3. **技术规范**: API规范、数据模型规范
4. **用户文档**: 用户手册、部署指南

---

## 文档结构

```
docs/
├── design/                       # 设计文档
│   ├── system-design.md         # 系统设计文档
│   └── core-modules-design.md   # 核心模块设计
└── plans/                        # 实施计划
    └── 2026-02-01-mvp-implementation-plan.md
```

---

## 核心文档

### 系统设计文档

**文件**: `design/system-design.md`

内容概览：
- 项目概述与背景
- 系统架构设计
- 核心模块设计
- 数据模型设计
- API接口设计
- 技术栈选型
- 部署架构
- 成本优化策略
- 开发路线图

### 核心模块设计

**文件**: `design/core-modules-design.md`

内容概览：
- 知识图谱诊断模块
- 智能分级推送模块
- AI口语陪练模块
- AI辅助备课模块
- 各模块技术实现细节
- 成本优化策略

### MVP实施计划

**文件**: `plans/2026-02-01-mvp-implementation-plan.md`

内容概览：
- 第1个月：基础架构与用户系统
- 第2个月：知识图谱与内容推荐
- 第3个月：口语陪练与AI备课
- 详细的任务分解与代码示例

---

## 快速导航

### 架构理解

1. 先阅读 [系统设计文档](design/system-design.md) 了解整体架构
2. 再阅读 [核心模块设计](design/core-modules-design.md) 了解各模块细节
3. 最后参考 [MVP实施计划](plans/2026-02-01-mvp-implementation-plan.md) 了解开发进度

### 开发参考

- **API设计**: 参考 `design/system-design.md` 的"API接口设计"章节
- **数据模型**: 参考 `design/system-design.md` 的"数据模型设计"章节
- **技术选型**: 参考 `design/system-design.md` 的"技术栈选型"章节

---

## 文档维护

### 更新规范

- 代码变更时同步更新相关文档
- 重大设计变更需要更新 `design/` 下的文档
- 进度变更需要更新 `plans/` 下的文档

### 版本控制

每个文档顶部包含版本信息：
```markdown
> **文档版本**: v1.0
> **创建日期**: 2026-02-01
> **最后更新**: 2026-02-01
```

---

## 相关文件清单

### 设计文档

| 文件 | 描述 |
|------|------|
| `design/system-design.md` | 完整系统设计文档 |
| `design/core-modules-design.md` | 核心模块详细设计 |

### 实施计划

| 文件 | 描述 |
|------|------|
| `plans/2026-02-01-mvp-implementation-plan.md` | MVP阶段3个月实施计划 |

---

## 变更记录

### 2026-02-03 09:49:22
- 创建文档模块索引
- 整理设计文档与实施计划
