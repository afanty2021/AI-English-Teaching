# AI赋能英语教学系统 - 完整设计文档

> **文档版本**: v1.0
> **创建日期**: 2026-02-01
> **架构类型**: 混合架构（平衡开发速度与成本控制）
> **项目目标**: 用AI技术实现"素养打底，考点融入"的个性化英语教学

---

## 目录

1. [项目概述](#一项目概述)
2. [系统架构设计](#二系统架构设计)
3. [核心模块设计](#三核心模块设计)
4. [数据模型设计](#四数据模型设计)
5. [API接口设计](#五api接口设计)
6. [技术栈选型](#六技术栈选型)
7. [部署架构](#七部署架构)
8. [成本优化策略](#八成本优化策略)
9. [开发路线图](#九开发路线图)

---

## 一、项目概述

### 1.1 项目背景

当前英语教育市场面临的核心矛盾：**"遵循二语习得理论培养长期语言素养"** 与 **"满足家长对短期应试提分的迫切需求"**。

AI技术的发展为破解这一难题提供了强大且可操作性的工具和思维框架，能够将"素养"与"分数"转化为相互促进的闭环。

### 1.2 解决方案

本系统通过AI技术实现：

| 维度 | 解决方案 |
|------|----------|
| **教学理念** | 构建AI驱动的"输入-输出-反馈"沉浸式习得环境 |
| **课程设计** | 打造"素养打底，考点融入"的双轨制学习路径 |
| **课堂实施** | AI作为教师的"超级助教"，释放创造力 |
| **家校沟通** | 用数据说话，化解焦虑，赢得信任 |

### 1.3 核心功能

1. **智能分级推送**: 基于i+1理论，动态推送难度适配的学习内容
2. **知识图谱诊断**: 构建学生个性化知识画像，精准定位薄弱环节
3. **AI口语陪练**: 零压力的AI对话环境，提升口语表达能力
4. **AI辅助备课**: 自动生成教案、课件、练习，提高教师备课效率

### 1.4 目标用户

- **主要用户**: 学校教师、教育培训机构
- **次要用户**: 学生（学习者）、家长
- **核心价值**: 个性化学习路径

---

## 二、系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        前端层 (Vue3)                                │
├─────────────────────────────────────────────────────────────────────┤
│  教师端                              学生端                        │
│  - 班级管理                          - 我的课程                     │
│  - 学生诊断报告                      - 个性化练习                   │
│  - AI备课助手                        - AI口语对话                   │
│  - 教学内容库                        - 进度追踪                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API / WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        应用层 (FastAPI)                              │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  用户服务   │  │  内容服务   │  │  学习服务   │  │  AI服务   │ │
│  │             │  │             │  │             │  │           │ │
│  │ - 认证授权  │  │ - 素材管理  │  │ - 能力诊断  │  │ - 智能路由│ │
│  │ - 角色管理  │  │ - 难度分级  │  │ - 知识图谱  │  │ - 提示优化│ │
│  │ - 组织架构  │  │ - 标签体系  │  │ - 进度追踪  │  │ - 成本控制│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘ │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     智能缓存层                               │   │
│  │  - Redis: 会话/热点数据/队列                                │   │
│  │  - 向量搜索: 内容相似度匹配（本地完成，减少AI调用）          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        数据层 (Data Layer)                           │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────────┐  │
│  │   PostgreSQL    │  │     Redis       │  │   向量数据库      │  │
│  │                 │  │                 │  │                   │  │
│  │ - 用户/组织     │  │ - 缓存          │  │ - 内容向量        │  │
│  │ - 学习记录      │  │ - 会话          │  │ - 题目向量        │  │
│  │ - 知识图谱      │  │ - 队列          │  │ - 学生画像向量    │  │
│  │ - 内容库        │  │ - 锁           │  │                   │  │
│  └─────────────────┘  └─────────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        AI服务层 (AI Services)                        │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ OpenAI API  │  │ 语音服务    │  │ 本地模型    │                 │
│  │             │  │             │  │ (可选)      │                 │
│  │ - GPT-4     │  │ - TTS/STT   │  │ - 嵌入      │                 │
│  │ - Embeddings│  │ - 评测      │  │ - 轻量生成  │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 架构特点

| 特性 | 说明 |
|------|------|
| **前端** | Vue3 + Vite，教师端与学生端分离 |
| **后端** | FastAPI，异步支持，高性能 |
| **数据存储** | PostgreSQL + Redis + 向量数据库 |
| **AI服务** | 混合架构：本地向量搜索 + 云端AI生成 |
| **成本优化** | 90%内容匹配本地完成，仅10%调用云端AI |

### 2.3 架构优势

1. **开发速度快**: 2-3个月可上线MVP
2. **成本可控**: 混合架构大幅降低AI调用成本
3. **可扩展性强**: 模块化设计，易于扩展
4. **运维简单**: 初期单机部署，逐步扩展

---

## 三、核心模块设计

### 3.1 知识图谱诊断模块

**模块定位**: 系统的"大脑"，构建每个学生的个性化知识画像

#### 3.1.1 模块架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      知识图谱诊断模块                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  输入层                      处理层                    输出层        │
│  ┌─────────┐              ┌─────────────┐             ┌─────────┐  │
│  │初始测评 │    ──────►   │  AI分析引擎 │    ──────►  │知识图谱 │  │
│  │- 词汇量 │              │             │             │         │  │
│  │- 语法   │              │ - 难度评估  │             │- 节点   │  │
│  │- 听说读写│              │ - 薄弱点挖掘│             │- 关系   │  │
│  └─────────┘              │ - 趋势预测  │             │- 权重   │  │
│  ┌─────────┐              └─────────────┘             └─────────┘  │
│  │持续练习 │                    │                                │
│  │- 作业   │                    ▼                                │
│  │- 测试   │              ┌─────────────┐                        │
│  │- 对话   │              │  规则引擎   │                        │
│  └─────────┘              │ - CEFR映射  │                        │
│                            │ - 考点关联  │                        │
│                            │ - 难度计算  │                        │
│                            └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 核心功能

1. **多维度能力评估**: 词汇、语法、听力、口语、阅读、写作六维诊断
2. **CEFR等级映射**: 自动映射到A1-C2国际标准等级
3. **考点关联分析**: 将能力点与具体考试题型关联
4. **动态更新**: 每次练习后实时更新知识图谱

#### 3.1.3 技术实现

```python
class KnowledgeGraphService:
    def diagnose_initial(self, student_id: str) -> Graph:
        """初始诊断 - 使用AI深度分析"""
        assessment = self.get_latest_assessment(student_id)
        analysis = await self.ai_client.analyze(assessment)
        nodes = self.build_nodes(analysis)
        edges = self.build_edges(nodes)
        self.map_to_standards(nodes, edges)
        return Graph(nodes=nodes, edges=edges)

    def update_from_practice(self, student_id: str, practice: Practice):
        """持续练习更新 - 使用规则引擎（零成本）"""
        graph = self.get_graph(student_id)
        updates = self.rule_engine.analyze(practice)
        graph.apply(updates)
        self.save_graph(graph)
```

#### 3.1.4 成本优化策略

- **初始诊断**: 使用AI深度分析（一次性成本）
- **日常更新**: 使用规则引擎（几乎零成本）
- **定期复盘**: 每周/每月才进行一次AI全面复盘
- **成本降低**: 90%以上

---

### 3.2 智能分级推送模块

**模块定位**: 系统的"心脏"，实现i+1理论的核心引擎

#### 3.2.1 模块架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      智能分级推送模块 (i+1 Recommendation)            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     推荐引擎                                 │   │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │   │
│  │  │用户画像 │    │内容画像 │    │i+1匹配 │    │多样性   │  │   │
│  │  │- 当前  │    │- 难度   │    │算法    │    │控制     │  │   │
│  │  │  等级  │    │- 话题   │    │        │    │         │  │   │
│  │  │- 兴趣  │    │- 长度   │    │        │    │         │  │   │
│  │  │- 目标  │    │- 考点   │    │        │    │         │  │   │
│  │  └────┬───┘    └────┬───┘    └────┬───┘    └────┬───┘  │   │
│  └───────┼────────────┼────────────┼────────────┼────────┘   │
│          │            │            │            │              │
│          ▼            ▼            ▼            ▼              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              向量召回 + AI精排                          │    │
│  │  Step 1: 向量相似度召回（本地，0.01秒，无成本）          │    │
│  │  Step 2: 规则过滤（难度范围、已读过滤、考点匹配）        │    │
│  │  Step 3: AI精排Top 10（云端，1秒，产生内容推荐理由）    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                    │
│                              ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                      输出                                │    │
│  │  - 今日推荐阅读（3篇，难度循序渐进）                     │    │
│  │  - 针对性练习（2组，聚焦薄弱考点）                       │    │
│  │  - 口语话题（1个，结合当前水平和兴趣）                   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.2.2 核心算法

```python
class ContentRecommendationService:
    def recommend_daily(self, student_id: str) -> DailyContent:
        profile = self.get_student_profile(student_id)

        # Step 1: 向量召回（快速、低成本）
        candidate_ids = self.vector_db.search(
            query_vector=profile.to_vector(),
            top_k=100,
            filters={
                "min_difficulty": profile.level - 0.2,
                "max_difficulty": profile.level + 0.3,
                "exclude_read": profile.read_history
            }
        )

        # Step 2: 规则过滤
        candidates = self.content_db.get_by_ids(candidate_ids)
        filtered = self.rule_engine.filter(candidates, profile)

        # Step 3: AI精排（仅对Top 20）
        top_20 = filtered[:20]
        ranked = await self.ai_client.rank_contents(
            contents=top_20,
            profile=profile,
            criteria=["difficulty_fit", "interest_match", "exam_coverage"]
        )

        return self.format_daily_content(self.diversify(ranked[:10]))
```

#### 3.2.3 三段式召回策略

| 阶段 | 技术手段 | 成本 | 响应时间 |
|------|----------|------|----------|
| 向量召回 | 本地向量数据库 | 几乎为零 | <0.01秒 |
| 规则过滤 | 硬规则裁剪 | 零 | <0.1秒 |
| AI精排 | 云端API | 低 | ~1秒 |

---

### 3.3 AI口语陪练模块

**模块定位**: 系统的"嘴巴"，实现零压力输出的关键

#### 3.3.1 模块架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                      AI口语陪练模块 (Speaking Practice)              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    对话管理器                               │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │              场景库 (Scenario Library)               │   │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│   │   │
│  │  │  │日常问候 │  │餐厅点餐 │  │问路指路 │  │购物砍价 ││   │   │
│  │  │  │A1-A2   │  │A2-B1   │  │B1-B2   │  │B2+     ││   │   │
│  │  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘│   │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐            │   │   │
│  │  │  │自我介绍 │  │描述经历 │  │观点表达 │  ...更多   │   │   │
│  │  │  └─────────┘  └─────────┘  └─────────┘            │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   AI对话引擎                                │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │              多轮对话管理                            │   │   │
│  │  │  - 上下文记忆（最近5-10轮）                          │   │   │
│  │  │  - 对话目标追踪（是否完成交际任务）                  │   │   │
│  │  │  - 动态难度调整（根据学生表现）                      │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │              智能反馈生成                            │   │   │
│  │  │  - 实时纠错（语法、发音）                            │   │   │
│  │  │  - 更好表达建议（词汇升级、句式优化）                │   │   │
│  │  │  - 鼓励机制（正向强化）                              │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   语音服务层                                │   │
│  │  ┌─────────────┐              ┌─────────────┐              │   │
│  │  │  STT（语音  │  ────────►   │  TTS（语音  │              │   │
│  │  │   识别）    │              │   合成）    │              │   │
│  │  │  - 中文/英文 │              │  - 多种声音 │              │   │
│  │  │  - 实时流式 │              │  - 情感表达 │              │   │
│  │  └─────────────┘              └─────────────┘              │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.3.2 技术实现

```python
class SpeakingPracticeService:
    async def handle_conversation(self, student_id: str, audio_data: bytes):
        profile = await self.get_student_profile(student_id)
        session = await self.get_active_session(student_id)

        # 1. 语音转文字
        user_text = await self.stt_client.transcribe(audio_data)

        # 2. 发音评测（本地轻量模型）
        pronunciation_score = self.pronunciation_checker.evaluate(
            audio_data, user_text
        )

        # 3. AI生成回复
        messages = self.build_messages(
            session_history=session.history,
            user_input=user_text,
            student_level=profile.level
        )
        ai_response = await self.llm_client.chat(
            messages=messages,
            system_prompt=self.get_system_prompt(profile.level, session.scenario)
        )

        # 4. 语音合成
        audio_response = await self.tts_client.synthesize(ai_response.text)

        return ConversationResponse(
            audio=audio_response,
            text=ai_response.text,
            feedback=ai_response.feedback
        )

    def get_system_prompt(self, level: str, scenario: str) -> str:
        return f"""你是一位友好的英语对话练习伙伴，正在与{level}水平的学生练习"{scenario}"场景。

对话要求：
1. 使用{level}水平的词汇和句型
2. 每轮回复控制在2-3句话
3. 如果学生有严重语法错误，在回复中用自然的对话方式纠正
4. 保持鼓励和支持的态度
5. 引导对话朝向完成交际任务的目标
"""
```

#### 3.3.3 成本优化技巧

1. **发音评测本地化**: 使用轻量本地模型
2. **System Prompt缓存**: 相同配置复用
3. **流式响应**: 边说边合成
4. **会话时长限制**: 5-10分钟

---

### 3.4 AI辅助备课模块

**模块定位**: 教师的"超级助教"，从重复性劳动中解放

#### 3.4.1 模块架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI辅助备课模块 (AI Lesson Planner)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      输入向导                               │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │   │
│  │  │主题输入 │  │难度选择 │  │课时长度 │  │考点要求 │        │   │
│  │  │自由文本 │  │A1-C2   │  │30-90min │  │多选标签 │        │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    AI备课引擎                               │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │              内容生成模块                            │   │   │
│  │  │  - 核心词汇表（带释义、例句、搭配）                  │   │   │
│  │  │  - 语法点讲解（规则、例句、易错点）                  │   │   │
│  │  │  - 阅读材料（多难度版本自动生成）                   │   │   │
│  │  │  - 练习题（根据考点自动生成）                       │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │              结构化模块                              │   │   │
│  │  │  - 教学流程设计（热身→呈现→练习→产出）              │   │   │
│  │  │  - 时间分配建议                                      │   │   │
│  │  │  - 活动设计（互动游戏、角色扮演等）                  │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │              课件生成模块                            │   │   │
│  │  │  - PPT大纲自动生成                                  │   │   │
│  │  │  - 板书设计建议                                      │   │   │
│  │  │  - 课后作业设计                                      │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                      输出                                   │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │   │
│  │  │完整教案 │  │PPT课件  │  │练习题库 │  │分层材料 │        │   │
│  │  │(可编辑) │  │(可导出) │  │(可打印) │  │(A1/B1/C1)│        │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

#### 3.4.2 技术实现

```python
class LessonPlanService:
    async def generate_lesson_plan(self, request: LessonPlanRequest) -> LessonPlan:
        # Step 1: 检索相关教学资源
        resources = await self.content_db.search(
            topic=request.topic,
            level=request.level,
            exam_points=request.exam_points
        )

        # Step 2: AI生成教案主体
        lesson_plan = await self.llm_client.generate(
            prompt=self.build_lesson_prompt(request, resources),
            response_format="json",
            schema=LessonPlanSchema
        )

        # Step 3: 生成分层阅读材料
        reading_materials = await self.generate_difficulty_levels(
            base_content=lesson_plan.reading,
            levels=["A1", "B1", "C1"]
        )

        # Step 4: 生成练习题
        exercises = await self.generate_exercises(
            content=lesson_plan,
            exam_points=request.exam_points
        )

        return LessonPlan(
            metadata=request,
            plan=lesson_plan,
            reading_materials=reading_materials,
            exercises=exercises
        )
```

---

## 四、数据模型设计

### 4.1 数据库选型架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                        数据存储架构                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              PostgreSQL (主数据库)                           │   │
│  │  - 用户与组织数据                                          │   │
│  │  - 内容与素材库                                            │   │
│  │  - 学习记录与知识图谱                                      │   │
│  │  - 教案与课件                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Qdrant / Weaviate (向量数据库)                 │   │
│  │  - 内容向量 embedding（用于相似度匹配）                     │   │
│  │  - 学生画像向量                                            │   │
│  │  - 题目向量                                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Redis (缓存与队列)                             │   │
│  │  - 会话数据                                                │   │
│  │  - 热点内容缓存                                            │   │
│  │  - 实时对话上下文                                          │   │
│  │  - 任务队列                                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                     │
│                              ▼                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              S3 / OSS (对象存储)                            │   │
│  │  - 音频文件                                                │   │
│  │  - 视频文件                                                │   │
│  │  - 课件文件                                                │   │
│  │  - 学生上传文件                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 核心实体ER图

```
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│ Organization │           │    User      │           │   Student    │
│  (机构/学校) │1         *│   (用户)     │1         1│   (学生)     │
│              │───────────│              │───────────│              │
│  - id        │           │  - id        │           │  - id        │
│  - name      │           │  - username  │           │  - user_id   │
│  - type      │           │  - email     │           │  - student_no│
│  - settings  │           │  - role      │           │  - grade     │
└──────────────┘           └──────────────┘           └──────────────┘
                                                                    │
                                                                    │ has
                                                                    ▼
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│   Content    │           │ KnowledgeGraph│          │  Practice    │
│  (内容/素材) │*         *│ (知识图谱)   │1         *│ (练习记录)   │
│              │───────────│              │───────────│              │
│  - id        │           │  - id        │           │  - id        │
│  - type      │           │  - student_id│           │  - student_id│
│  - title     │           │  - nodes     │           │  - content_id│
│  - level     │           │  - edges     │           │  - score     │
│  - exam_tags │           │  - updated_at│           │  - answers   │
└──────────────┘           └──────────────┘           └──────────────┘
           │                                                        │
           │ used_for                                               │ creates
           ▼                                                        ▼
┌──────────────┐           ┌──────────────┐           ┌──────────────┐
│  LessonPlan  │           │ Conversation  │          │  Diagnostic  │
│  (教案)      │           │ (对话会话)   │          │  (诊断报告)   │
│              │           │              │           │              │
│  - id        │           │  - id        │           │  - id        │
│  - teacher_id│           │  - student_id│           │  - student_id│
│  - content_id│           │  - scenario  │           │  - type      │
│  - structure │           │  - messages  │           │  - result    │
│  - exercises │           │  - started_at│           │  - analysis  │
│  - materials │           │  - ended_at  │           │  - created_at│
└──────────────┘           └──────────────┘           └──────────────┘
```

### 4.3 核心数据表结构

#### 4.3.1 用户与组织相关

```sql
-- 机构/学校表
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    profile JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 学生档案表
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES users(id),
    student_no VARCHAR(50) UNIQUE,
    grade VARCHAR(50),
    class_id UUID,
    parent_ids UUID[] REFERENCES users(id),
    target_exam VARCHAR(100),
    target_score INTEGER,
    study_goal TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 4.3.2 内容与素材相关

```sql
-- 内容库表
CREATE TABLE contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    level VARCHAR(20),
    level_score DECIMAL(3,2),
    subjects VARCHAR(100)[],
    exam_tags VARCHAR(100)[],
    grammar_points VARCHAR(100)[],
    vocabulary_count INTEGER,
    word_count INTEGER,
    difficulty_analysis JSONB DEFAULT '{}',
    vector_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'draft',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 4.3.3 学习与练习相关

```sql
-- 知识图谱表
CREATE TABLE knowledge_graphs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID UNIQUE NOT NULL REFERENCES students(id),
    nodes JSONB DEFAULT '[]',
    edges JSONB DEFAULT '[]',
    abilities JSONB DEFAULT '{}',
    cefr_level VARCHAR(10),
    exam_coverage JSONB DEFAULT '{}',
    ai_analysis JSONB DEFAULT '{}',
    last_ai_analysis_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 练习记录表
CREATE TABLE practices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    content_id UUID REFERENCES contents(id),
    practice_type VARCHAR(50) NOT NULL,
    questions JSONB NOT NULL,
    answers JSONB NOT NULL,
    score DECIMAL(5,2),
    time_spent INTEGER,
    analysis JSONB DEFAULT '{}',
    graph_updates JSONB DEFAULT '{}',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 对话会话表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID NOT NULL REFERENCES students(id),
    scenario VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,
    messages JSONB DEFAULT '[]',
    pronunciation_score DECIMAL(5,2),
    grammar_score DECIMAL(5,2),
    fluency_score DECIMAL(5,2),
    feedback JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP
);
```

---

## 五、API接口设计

### 5.1 API总体结构

```
/api/v1/
├── /auth/                  # 认证授权
├── /students/              # 学生管理
├── /contents/              # 内容管理
├── /practices/             # 练习记录
├── /conversations/         # 口语对话
├── /lesson-plans/          # 教案管理
└── /analytics/             # 数据分析
```

### 5.2 核心API示例

#### 5.2.1 获取学生知识图谱

```yaml
GET /api/v1/students/{student_id}/graph
Response:
  {
    "code": 200,
    "data": {
      "abilities": {
        "vocabulary": { "level": "B1", "score": 0.65 },
        "grammar": { "level": "B2", "score": 0.72 }
      },
      "cefr_level": "B1",
      "weak_points": ["grammar_past_perfect"],
      "exam_coverage": {
        "cet4": { "coverage": 0.75, "ready": true }
      }
    }
  }
```

#### 5.2.2 获取每日推荐

```yaml
GET /api/v1/contents/recommend?student_id={student_id}
Response:
  {
    "code": 200,
    "data": {
      "reading": [...],
      "exercises": [...],
      "speaking": {...}
    }
  }
```

#### 5.2.3 口语对话

```yaml
POST /api/v1/conversations/{id}/message
Request:
  - audio: (binary)
Response:
  {
    "code": 200,
    "data": {
      "ai_response": {
        "text": "...",
        "audio_url": "...",
        "feedback": "..."
      }
    }
  }
```

### 5.3 统一响应格式

```json
{
  "code": 200,
  "data": { ... },
  "message": "操作成功",
  "timestamp": "2026-02-01T10:30:00Z"
}
```

---

## 六、技术栈选型

### 6.1 技术栈总览

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 前端 | Vue3 + Vite + Pinia | 组合式API，状态管理 |
| 后端 | FastAPI | 高性能异步API框架 |
| 数据库 | PostgreSQL 15+ | 关系型主数据库 |
| 缓存 | Redis 7+ | 会话、热点数据 |
| 向量库 | Qdrant | 向量相似度搜索 |
| AI服务 | OpenAI/Anthropic | GPT-4, Claude |
| 语音 | Azure/阿里云 | STT/TTS服务 |
| 存储 | S3/OSS | 对象存储 |
| 部署 | Docker + K8s | 容器化部署 |

### 6.2 前端技术栈

```json
{
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.0",
    "pinia": "^2.1.0",
    "axios": "^1.6.0",
    "element-plus": "^2.4.0",
    "@vueuse/core": "^10.7.0"
  }
}
```

### 6.3 后端技术栈

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.0
asyncpg==0.29.0
redis==5.0.1
qdrant-client==1.7.0
openai==1.10.0
pydantic==2.5.3
python-jose[cryptography]==3.3.0
```

---

## 七、部署架构

### 7.1 部署架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                           负载均衡                                  │
│                    (Nginx / AWS ALB)                                │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │  App Pod  │   │  App Pod  │   │  App Pod  │
            │  (FastAPI)│   │  (FastAPI)│   │  (FastAPI)│
            └───────────┘   └───────────┘   └───────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            ▼                       ▼                       ▼
    ┌───────────┐           ┌───────────┐           ┌───────────┐
    │PostgreSQL │           │   Redis   │           │  Qdrant   │
    │  (Primary)│           │  Cluster  │           │  Cluster  │
    └───────────┘           └───────────┘           └───────────┘
            │
            ▼
    ┌───────────┐
    │PostgreSQL │
    │ (Standby) │
    └───────────┘
```

### 7.2 部署清单

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

---

## 八、成本优化策略

### 8.1 成本优化汇总

| 优化项 | 策略 | 成本降低 |
|--------|------|----------|
| 内容推荐 | 本地向量召回 + 规则过滤 | 95% |
| 知识图谱更新 | 规则引擎替代AI | 90% |
| 发音评测 | 本地模型替代API | 100% |
| Prompt缓存 | 复用相似Prompt | 30% |
| 批量处理 | 合并API调用 | 40% |

### 8.2 成本估算

| 组件 | 月活用户 | 单用户成本 | 月成本 |
|------|----------|------------|--------|
| OpenAI API | 1000 | ¥2 | ¥2,000 |
| 语音服务 | 1000 | ¥1 | ¥1,000 |
| 云资源 | 1000 | ¥1.5 | ¥1,500 |
| **合计** | **1000** | **¥4.5** | **¥4,500** |

---

## 九、开发路线图

### 9.1 MVP阶段 (3个月)

| 阶段 | 内容 | 产出 |
|------|------|------|
| 第1月 | 基础架构 + 用户系统 | 登录注册、权限管理 |
| 第2月 | 知识图谱 + 内容推荐 | 诊断评估、个性化推荐 |
| 第3月 | 口语陪练 + AI备课 | 对话功能、教案生成 |

### 9.2 产品化阶段 (3个月)

| 阶段 | 内容 | 产出 |
|------|------|------|
| 第4月 | 数据分析 + 报告 | 可视化报表、进度追踪 |
| 第5月 | 家校端 + 移动端 | 家长看板、小程序 |
| 第6月 | 性能优化 + 上线准备 | 压力测试、安全加固 |

---

## 附录

### A. 术语表

| 术语 | 说明 |
|------|------|
| CEFR | 欧洲语言共同参考框架，A1-C2 |
| i+1 | 可理解性输入理论 |
| STT | 语音转文字 |
| TTS | 文字转语音 |

### B. 参考文档

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Vue3官方文档](https://vuejs.org/)
- [OpenAI API文档](https://platform.openai.com/docs)

---

*本文档由 AI 辅助生成，版本: v1.0 | 最后更新: 2026-02-01*
