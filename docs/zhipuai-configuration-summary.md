# ZhipuAI 集成配置摘要

> **更新时间**: 2026-02-02
> **配置状态**: 已完成代码集成，待配置API密钥

---

## 📋 配置概览

### 已配置的AI服务

| 服务提供商 | 状态 | 模型 | 用途 |
|-----------|------|------|------|
| **智谱AI (ZhipuAI)** | ✅ 主要 | glm-4.7, embedding-3 | 对话生成、向量化 |
| **OpenAI** | 🔄 备用 | gpt-4-turbo-preview, text-embedding-3-small | 降级备用 |

### 核心配置

```env
# 智谱AI (主要AI服务提供商)
ZHIPUAI_API_KEY=your_zhipuai_api_key_here  # ⚠️ 需要配置
ZHIPUAI_MODEL=glm-4.7
ZHIPUAI_EMBEDDING_MODEL=embedding-3
ZHIPUAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4
ZHIPUAI_TEMPERATURE=0.7
ZHIPUAI_MAX_TOKENS=2000
ZHIPUAI_TOP_P=1
ZHIPUAI_TOP_K=1

# 向量数据库配置 (已更新为2048维)
QDRANT_VECTOR_SIZE=2048  # 智谱embedding-3向量维度

# AI提供商选择
AI_PROVIDER=zhipuai  # zhipuai, openai, anthropic
```

---

## 📁 已修改/创建的文件

### 新创建的文件

1. **`backend/app/services/zhipu_service.py`**
   - 完整的智谱AI API封装
   - 支持对话完成 (chat_completion)
   - 支持向量生成 (generate_embedding)
   - 支持批量向量化 (batch_generate_embeddings)
   - 健康检查方法 (health_check)

### 已更新的文件

2. **`backend/.env`**
   - 添加智谱AI配置项
   - 更新向量维度为2048
   - 设置AI_PROVIDER为zhipuai

3. **`backend/app/core/config.py`**
   - 添加智谱AI配置字段
   - 添加AI_PROVIDER选择器
   - 更新QDRANT_VECTOR_SIZE为2048

4. **`backend/app/services/embedding_service.py`**
   - 支持多提供商 (智谱AI/OpenAI)
   - 自动降级机制
   - 批量向量化优化

5. **`backend/app/services/ai_service.py`**
   - 支持多提供商对话
   - 支持JSON mode结构化输出
   - 学生评估分析支持提供商选择
   - 健康检查支持多服务

---

## 🔄 工作流程

### 请求处理流程

```
┌─────────────┐
│   API请求   │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ AIService/          │
│ EmbeddingService    │
│ (provider=zhipuai)  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐     成功     ┌──────────────┐
│   尝试智谱AI调用     │──────────────▶│  返回结果    │
└──────┬──────────────┘              └──────────────┘
       │
       │ 失败
       ▼
┌─────────────────────┐     成功     ┌──────────────┐
│   降级到OpenAI      │──────────────▶│  返回结果    │
└──────┬──────────────┘              └──────────────┘
       │
       │ 失败
       ▼
┌─────────────────────┐
│   抛出异常          │
└─────────────────────┘
```

### 向量维度对照

| 提供商 | 模型 | 向量维度 | Qdrant配置 |
|--------|------|----------|------------|
| 智谱AI | embedding-3 | **2048** | ✅ 已配置 |
| OpenAI | text-embedding-3-small | 1536 | ⚠️ 不兼容 |

> **重要**: 由于智谱AI的向量维度为2048，与OpenAI的1536不同，请确保Qdrant集合配置为2048维。

---

## ⚙️ 服务接口

### ZhipuAIService 类

```python
from app.services.zhipu_service import get_zhipuai_service

# 获取服务实例
service = get_zhipuai_service()

# 对话完成
response = await service.chat_completion(
    messages=[{"role": "user", "content": "你好"}],
    temperature=0.7,
    max_tokens=2000,
    response_format={"type": "json_object"}  # 支持JSON mode
)

# 生成向量
embedding = await service.generate_embedding("要生成向量的文本")

# 批量生成向量
embeddings = await service.batch_generate_embeddings([
    "文本1", "文本2", "文本3"
])

# 健康检查
is_healthy = await service.health_check()
```

### AIService 类 (多提供商支持)

```python
from app.services.ai_service import get_ai_service

# 获取服务实例 (默认使用配置的提供商)
ai_service = get_ai_service()

# 或指定提供商
# ai_service = AIService(provider="zhipuai")

# 对话完成 (自动选择提供商)
response = await ai_service.chat_completion(
    messages=[{"role": "user", "content": "分析学生能力"}]
)

# 结构化输出
result = await ai_service.chat_completion_structured(
    messages=[{"role": "user", "content": "..."}],
    response_model=DiagnosisResult
)

# 学生评估分析
analysis = await ai_service.analyze_student_assessment(
    student_info={...},
    practice_data=[...],
    target_exam="IELTS"
)

# 健康检查
health = await ai_service.health_check()
# 返回: {"zhipuai": True, "openai": False}
```

### EmbeddingService 类 (多提供商支持)

```python
from app.services.embedding_service import get_embedding_service

# 获取服务实例
embedding_service = get_embedding_service()

# 生成向量
embedding = await embedding_service.generate_embedding("文本")

# 批量生成向量
embeddings = await embedding_service.batch_generate_embeddings([
    "文本1", "文本2", "文本3"
], batch_size=100)

# 为内容生成向量
content_embedding = await embedding_service.generate_content_embedding(
    title="IELTS阅读练习",
    content_text="...",
    topic="阅读理解",
    difficulty_level="B1",
    exam_type="IELTS"
)

# 为词汇生成向量
word_embedding = await embedding_service.generate_vocabulary_embedding(
    word="abandon",
    definitions=["放弃", "抛弃"],
    examples=["He abandoned his car."],
    english_definition="to leave behind"
)

# 获取向量维度
dim = embedding_service.get_embedding_dimension()  # 2048
```

---

## 🧪 测试步骤

### 1. 配置API密钥

编辑 `backend/.env` 文件，将你的智谱AI API密钥填入：

```env
ZHIPUAI_API_KEY=你的实际API密钥
```

### 2. 启动服务

```bash
cd /Users/berton/Github/AI-English-Teaching-System/backend

# 启动Docker服务 (PostgreSQL, Redis, Qdrant)
docker-compose up -d

# 激活虚拟环境
source venv/bin/activate

# 安装依赖 (如果需要)
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head
```

### 3. 测试API连接

```bash
# 启动FastAPI服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 健康检查

访问 `http://localhost:8000/api/v1/health` 或使用curl：

```bash
curl http://localhost:8000/api/v1/health
```

预期响应：
```json
{
  "status": "healthy",
  "ai_services": {
    "zhipuai": true,
    "openai": false
  },
  "database": "connected",
  "redis": "connected",
  "qdrant": "connected"
}
```

---

## 📊 费用预估

### 智谱AI 定价 (参考)

| 模型 | 输入价格 | 输出价格 |
|------|----------|----------|
| glm-4.7 | ¥0.50/百万tokens | ¥2.00/百万tokens |
| embedding-3 | ¥0.10/百万tokens | - |

### 月度成本估算 (基于1000学生)

| 功能 | 月调用量 | 预估费用 |
|------|----------|----------|
| 初始诊断 (AI) | 1000次 × 2000tokens | ¥0.02 |
| 日常更新 (规则) | 90,000次 | ¥0 |
| 周评分析 (AI) | 4,000次 × 1500tokens | ¥0.12 |
| 内容推荐 (向量) | 300,000次 | ¥0.03 |
| 对话练习 | 50,000次 × 500tokens | ¥0.15 |
| **总计** | | **~¥0.32/月** |

> **成本优化**: 由于使用本地向量搜索 + 规则引擎，相比纯AI方案节省约90%+成本。

---

## 🔧 故障排查

### 问题1: 401 认证失败

**错误**: `智谱AI API错误: 401 - {"error":{"message":"Invalid API key"}}`

**解决**: 检查 `.env` 文件中的 `ZHIPUAI_API_KEY` 是否正确配置。

### 问题2: 向量维度不匹配

**错误**: `Qdrant报错: Vector dimension mismatch. Expected: 1536, Actual: 2048`

**解决**: 确保Qdrant集合配置为2048维：

```python
from app.services.qdrant_service import get_qdrant_service

qdrant = get_qdrant_service()
await qdrant.recreate_collection(vector_size=2048)
```

### 问题3: 降级到OpenAI失败

**错误**: `没有可用的AI服务提供商`

**解决**: 配置至少一个有效的API密钥 (智谱AI或OpenAI)。

---

## ✅ 后续步骤

1. **[ ] 配置API密钥**
   - 将智谱AI API密钥填入 `.env` 文件

2. **[ ] 运行数据库迁移**
   ```bash
   cd backend
   alembic revision --autogenerate -m "初始化AI英语教学系统数据库"
   alembic upgrade head
   ```

3. **[ ] 测试健康检查**
   - 启动服务后访问 `/api/v1/health`

4. **[ ] 测试对话功能**
   - 使用 `/api/v1/conversations` 端点测试AI对话

5. **[ ] 测试内容推荐**
   - 使用 `/api/v1/contents/recommend` 测试推荐系统

6. **[ ] 测试学生评估**
   - 使用 `/api/v1/students/{id}/diagnosis` 测试AI诊断

---

## 📚 相关文档

- [智谱AI API文档](https://open.bigmodel.cn/dev/api)
- [glm-4.7 模型文档](https://open.bigmodel.cn/dev/howuse/model)
- [embedding-3 文档](https://open.bigmodel.cn/dev/api#embedding)
- [项目API文档](http://localhost:8000/docs) (FastAPI自动生成)

---

**配置完成!** 系统已准备好使用智谱AI服务。请配置API密钥后开始测试。
