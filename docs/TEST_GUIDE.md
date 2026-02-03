# AI 英语教学系统 - 演示测试指南

> 更新时间：2026-02-02

## 🚀 服务状态

### 运行中的服务
- ✅ **前端** (Vue 3): http://localhost:5174/
- ✅ **后端** (FastAPI): http://localhost:8000/
- ✅ **PostgreSQL**: localhost:5432/english_teaching
- ✅ **Redis**: localhost:6379
- ✅ **Qdrant**: localhost:6333

### API 文档
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

---

## 👥 测试账号

### 教师账号
- **用户名**: `teacher`
- **密码**: `test123`
- **角色**: 教师端
- **功能**: AI 备课、教案管理、学生管理

### 学生账号
- **用户名**: `student`
- **密码**: `test123`
- **角色**: 学生端
- **功能**: 学习内容、口语练习、学习进度

---

## 📋 演示流程

### A. 教师端演示流程

#### 1. 登录系统
1. 访问 http://localhost:5174/
2. 选择"教师登录"
3. 输入用户名：`teacher`
4. 输入密码：`test123`
5. 点击"登录"

#### 2. 教师仪表板
登录后自动跳转到教师仪表板，可以查看：
- **统计卡片**：学生总数、教案数量、今日活跃、本周生成
- **最近教案**：查看最近创建的教案列表
- **快速操作**：AI 生成教案、管理教案、学生管理
- **趋势图表**：本周教案生成趋势

#### 3. AI 生成教案（核心功能）
1. 点击顶部菜单"AI 备课"
2. 填写教案信息：
   - **教案标题**：日常对话教学
   - **主题**：daily_conversation
   - **难度级别**：B1（进阶）
   - **时长**：45 分钟
   - **学生人数**：10 人
   - **教学重点**：勾选"口语"
3. 点击"AI 生成教案"按钮
4. 等待 30-40 秒，AI 会生成完整教案
5. 查看生成的教案内容：
   - 教学目标
   - 核心词汇
   - 语法点
   - 教学流程
6. 点击"保存"或"编辑"进行后续操作

#### 4. 教案管理
1. 点击顶部菜单"教案管理"
2. 查看所有已创建的教案
3. 可以编辑、删除、发布教案

---

### B. 学生端演示流程

#### 1. 登录系统
1. 访问 http://localhost:5174/
2. 选择"学生登录"
3. 输入用户名：`student`
4. 输入密码：`test123`
5. 点击"登录"

#### 2. 学生仪表板
登录后自动跳转到学生仪表板，可以查看：
- **学习统计**：今日学习时长、完成练习、口语对话、学习积分
- **今日推荐**：智能推荐的学习内容
- **学习动态**：最近的学习活动时间线
- **本周目标**：学习目标完成进度

#### 3. 学习内容
1. 点击顶部菜单"学习内容"
2. 查看今日推荐阅读：
   - **At the Restaurant** (elementary)
   - **Daily Greeting** (beginner)
3. 点击任意内容卡片查看详情
4. 阅读内容后可以点击"标记为已完成"获得积分

#### 4. 口语练习
1. 点击顶部菜单"口语练习"
2. 选择对话场景：
   - 日常问候 (A1-A2)
   - 购物场景 (A2-B1)
   - 餐厅点餐 (A2-B1)
   - 问路指路 (B1-B2)
   - 求职面试 (B2-C1)
   - 商务会议 (C1-C2)
3. 点击"开始对话"
4. 与 AI 进行场景对话练习
5. 完成后查看对话历史记录

---

## 🔑 核心 API 端点

### 认证相关
```bash
# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher","password":"test123"}'

# 获取当前用户信息
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 教案相关
```bash
# 创建教案（AI 生成）
curl -X POST http://localhost:8000/api/v1/lesson-plans/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "日常对话教学",
    "topic": "daily_conversation",
    "level": "B1",
    "duration": 45,
    "student_count": 10,
    "focus_areas": ["speaking"]
  }'

# 获取教案列表
curl http://localhost:8000/api/v1/lesson-plans/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 获取单个教案详情
curl http://localhost:8000/api/v1/lesson-plans/{id} \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 内容推荐
```bash
# 获取个性化推荐内容
curl http://localhost:8000/api/v1/contents/recommend \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 对话练习
```bash
# 开始新对话
curl -X POST http://localhost:8000/api/v1/conversations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scenario": "daily_greeting"}'

# 发送消息
curl -X POST http://localhost:8000/api/v1/conversations/{id}/messages \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello! How are you?"}'
```

---

## 🎯 演示要点

### 教师端
1. **AI 生成教案的速度**：约 30-40 秒生成完整教案
2. **教案内容质量**：包含教学目标、词汇、语法、流程
3. **用户体验**：直观的表单填写，实时生成反馈

### 学生端
1. **个性化推荐**：基于学生水平的 i+1 理论推荐
2. **智能场景对话**：6 种不同难度的对话场景
3. **学习追踪**：统计和目标进度可视化

---

## 🐛 常见问题

### Q: 登录后提示认证失败？
A: 清除浏览器缓存，重新登录。确保使用正确的测试账号。

### Q: AI 生成教案超时？
A: 检查后端服务是否正常运行，查看 ZhipuAI API 密钥是否有效。

### Q: 内容推荐返回空？
A: 确保学生档案已创建（level 字段有值）。

### Q: 前端页面显示异常？
A: 刷新页面或检查浏览器控制台错误信息。

---

## 📊 技术架构

### 前端技术栈
- **框架**: Vue 3 + TypeScript
- **UI 组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **构建工具**: Vite

### 后端技术栈
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL 17
- **缓存**: Redis
- **向量数据库**: Qdrant
- **AI 服务**: ZhipuAI GLM-4.7

### 核心算法
- **i+1 理论**: 内容难度匹配
- **三阶段检索**: 向量 → 规则 → AI 重排序
- **知识图谱**: 学生能力诊断

---

## 🚀 下一步计划

### 选项 B：深度开发
- 接入真实 AI 对话 API（GPT-4/Claude）
- 完善学习进度追踪系统
- 实现学生管理功能

### 选项 C：优化完善
- 教案 PPT 导出功能
- 增加单元测试覆盖率
- 性能优化和错误处理

---

**祝演示顺利！** 🎉

如有问题，请查看后端日志：`/private/tmp/claude-501/-Users-berton-Github/tasks/b4eca28.output`
