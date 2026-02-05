# 推荐系统联调测试运行指南

## 测试文件清单

### Phase 1: 测试开发 ✅ 已完成

| 文件 | 路径 | 描述 |
|------|------|------|
| 后端集成测试 | `backend/tests/integration/test_recommendation_loop.py` | 推荐系统闭环集成测试 |
| 前端E2E测试 | `frontend/e2e/recommendation-loop.spec.ts` | 推荐系统闭环E2E测试 |
| 前端性能测试 | `frontend/e2e/performance.spec.ts` | 性能测试 |
| 学生认证Fixture | `frontend/e2e/student-auth.fixture.ts` | 学生认证fixture |
| 全局设置 | `frontend/e2e/global-setup.ts` | 更新以支持学生认证 |
| Playwright配置 | `frontend/playwright.config.ts` | 添加学生认证项目 |
| 文档更新 | `frontend/e2e/CLAUDE.md` | 更新测试文档 |

## 环境准备

### 1. 启动后端服务

```bash
cd backend

# 启动Docker服务
docker-compose up -d

# 安装依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/integration/test_recommendation_loop.py -v
```

### 2. 启动前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 安装Playwright浏览器
npx playwright install --with-deps chromium
```

### 3. 运行全局设置

```bash
# 生成认证状态文件
node e2e/global-setup.ts
```

## 运行测试

### 后端集成测试

```bash
cd backend

# 运行所有集成测试
pytest tests/integration/test_recommendation_loop.py -v

# 运行并生成覆盖率报告
pytest tests/integration/test_recommendation_loop.py \
  --cov=app.services.recommendation_service \
  --cov=app.services.knowledge_graph_service \
  --cov-report=term-missing
```

### 前端E2E测试

```bash
cd frontend

# 运行推荐系统闭环测试
npx playwright test e2e/recommendation-loop.spec.ts --project=chromium-student

# 运行性能测试
npx playwright test e2e/performance.spec.ts

# 运行所有E2E测试
npx playwright test
```

### 生成测试报告

```bash
# HTML报告
npx playwright test --reporter=html
open playwright-report/index.html

# JUnit报告
npx playwright test --reporter=junit --outputFile=test-results/junit.xml
```

## 测试场景说明

### 后端测试场景

1. **test_full_recommendation_practice_loop**
   - 测试完整的推荐-练习-图谱更新闭环
   - 验证数据流正确性

2. **test_weak_point_targeted_practice**
   - 测试薄弱点针对性练习
   - 验证推荐包含薄弱点相关内容

3. **test_recommendation_reflects_updated_graph**
   - 测试推荐反映更新后的图谱
   - 验证二次推荐的正确性

4. **test_recommendation_response_time**
   - 测试推荐API响应时间
   - 预期: < 2秒

### 前端E2E测试场景

1. **推荐页面 → 开始练习 → 完成 → 图谱更新**
   - 验证完整用户流程

2. **薄弱点针对性练习**
   - 验证薄弱点推荐和练习

3. **二次推荐验证**
   - 验证推荐内容变化

### 性能测试

1. **页面加载性能**
   - 预期: < 5秒

2. **API响应时间**
   - 预期: < 2秒

3. **内存使用**
   - 监控内存泄漏

4. **并发请求**
   - 测试系统并发处理能力

## 预期输出

### 后端测试报告

```
backend/htmlcov/index.html
```

### 前端测试报告

```
frontend/playwright-report/index.html
```

## 常见问题

### Q1: 后端测试连接数据库失败

```bash
# 确保Docker服务运行
docker-compose ps

# 启动PostgreSQL
docker-compose up -d postgres
```

### Q2: 前端测试认证失败

```bash
# 重新生成认证状态
npx playwright install
node e2e/global-setup.ts
```

### Q3: 测试超时

```bash
# 增加超时时间
npx playwright test --timeout=60000
```

## 相关文档

- [推荐系统联调计划](../docs/plans/recommendation-integration-plan.md)
- [后端测试指南](../backend/tests/README.md)
- [前端测试指南](../frontend/tests/README.md)
