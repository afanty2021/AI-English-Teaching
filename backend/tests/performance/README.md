# 性能优化与压力测试指南

> **创建日期**: 2026-02-12
> **版本**: v1.0
> **状态**: ✅ 已完成

---

## 概述

本文档描述AI英语教学系统的性能测试框架和优化指南。

## 目录

1. [测试工具](#测试工具)
2. [快速开始](#快速开始)
3. [性能测试类型](#性能测试类型)
4. [性能基准](#性能基准)
5. [优化建议](#优化建议)

---

## 测试工具

### 1. Locust - 分布式压力测试

**安装**:
```bash
pip install locust>=2.15.0
```

**运行**:
```bash
# Web界面模式
locust -f tests/performance/locustfile.py --host http://localhost:8000

# 无头模式（CI/CD）
locust -f tests/performance/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 60s --host http://localhost:8000
```

### 2. Pytest - 性能与负载测试

**运行性能测试**:
```bash
# 运行所有性能测试
pytest tests/performance/ -v -m performance

# 运行特定测试
pytest tests/performance/test_db_performance.py -v
pytest tests/performance/test_api_load.py -v
pytest tests/performance/test_memory_cpu.py -v
```

### 3. 自动化测试脚本

```bash
# 运行完整测试套件
python tests/performance/run_tests.py

# 跳过某些测试
python tests/performance/run_tests.py --skip-db --skip-locust

# 自定义Locust参数
python tests/performance/run_tests.py --locust-users 200 --locust-duration 120
```

---

## 快速开始

### 1. 准备测试环境

```bash
# 确保后端服务运行
cd backend
uvicorn app.main:app --reload

# 在另一个终端启动数据库
docker-compose up -d
```

### 2. 运行快速性能检查

```bash
# 数据库性能测试
pytest tests/performance/test_db_performance.py::test_simple_query_performance -v

# API负载测试
pytest tests/performance/test_api_load.py::TestAPILoad::test_api_response_times -v
```

### 3. 运行完整测试套件

```bash
# 使用自动化脚本
python tests/performance/run_tests.py
```

---

## 性能测试类型

### 1. 数据库性能测试

**文件**: `tests/performance/test_db_performance.py`

| 测试 | 描述 | 目标 |
|------|------|------|
| `test_database_connection_pool_efficiency` | 连接池效率 | 验证连接复用 |
| `test_simple_query_performance` | 简单查询性能 | P95 < 10ms |
| `test_complex_query_performance` | 复杂查询性能 | P95 < 100ms |
| `test_concurrent_query_performance` | 并发查询 | 验证吞吐量 |
| `test_transaction_performance` | 事务性能 | P95 < 50ms |
| `test_index_effectiveness` | 索引有效性 | 平均 < 50ms |

### 2. API负载测试

**文件**: `tests/performance/test_api_load.py`

| 测试 | 描述 | 目标 |
|------|------|------|
| `test_concurrent_login_requests` | 并发登录 | 成功率 > 95% |
| `test_api_response_times` | 端点响应时间 | 见阈值表 |
| `test_sustained_load` | 持续负载 | 30秒@10RPS |
| `test_memory_leak_detection` | 内存泄漏检测 | 无持续增长 |

### 3. 资源监控测试

**文件**: `tests/performance/test_memory_cpu.py`

| 测试 | 描述 | 目标 |
|------|------|------|
| `test_process_memory_baseline` | 内存基线 | < 256MB |
| `test_cpu_baseline` | CPU基线 | < 10% |
| `test_memory_under_load` | 负载内存 | 无泄漏 |
| `test_cpu_under_load` | 负载CPU | < 80% |

---

## 性能基准

### API响应时间阈值

| 端点类型 | P50 (中位数) | P95 (95分位) | P99 (99分位) |
|----------|-------------|---------------|---------------|
| 认证 (login) | 200ms | 500ms | 1000ms |
| 用户信息 (me) | 50ms | 100ms | 200ms |
| 推荐 (recommend) | 500ms | 1000ms | 2000ms |
| 错题本 (mistakes) | 200ms | 300ms | 500ms |
| 报告生成 (generate) | 2000ms | 5000ms | 10000ms |
| 健康检查 (health) | 20ms | 50ms | 100ms |

### 数据库性能阈值

| 查询类型 | P95阈值 |
|----------|---------|
| 简单SELECT | 10ms |
| 复杂JOIN | 100ms |
| 事务操作 | 50ms |
| 连接延迟 | 100ms |

### 资源使用阈值

| 资源 | 阈值 |
|------|------|
| 内存使用 | < 512MB |
| CPU使用 | < 80% (负载) |
| 线程数 | < 200 |
| 文件描述符 | < 1000 |

---

## 优化建议

### 数据库优化

1. **索引优化**
   - 为常用查询字段添加索引
   - 使用复合索引优化多条件查询
   - 定期运行 `VACUUM ANALYZE`

2. **连接池配置**
   ```python
   # 推荐配置
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=20,        # 连接池大小
       max_overflow=10,      # 最大溢出
       pool_pre_ping=True,   # 连接健康检查
       pool_recycle=3600     # 回收时间（秒）
   )
   ```

3. **查询优化**
   - 使用 `select_only()` 减少数据传输
   - 避免N+1查询问题
   - 使用异步批量操作

### API优化

1. **缓存策略**
   - Redis缓存热点数据（用户信息、推荐结果）
   - 设置合理的TTL
   - 使用缓存预热

2. **异步操作**
   - 所有IO操作使用异步
   - 并发独立操作
   - 使用 `asyncio.gather()`

3. **响应优化**
   - 使用流式响应（StreamingResponse）
   - 压缩大响应（gzip）
   - 分页返回大数据集

### 内存优化

1. **避免内存泄漏**
   - 及时关闭连接和文件
   - 使用弱引用（weakref）
   - 避免循环引用

2. **数据结构优化**
   - 使用生成器替代列表
   - 选择合适的数据类型
   - 避免不必要的深拷贝

3. **监控建议**
   - 定期检查内存使用趋势
   - 使用 `memory_profiler` 分析
   - 关注GC频率和时间

---

## 文件结构

```
tests/performance/
├── __init__.py                    # 模块初始化
├── locustfile.py                   # Locust压力测试脚本
├── performance_config.py            # 性能阈值配置
├── performance_monitor.py          # 运行时性能监控
├── performance_analyzer.py         # 报告生成工具
├── run_tests.py                   # 测试运行脚本
├── test_db_performance.py          # 数据库性能测试
├── test_api_load.py              # API负载测试
└── test_memory_cpu.py             # 资源监控测试
```

---

## 报告输出

测试完成后，报告将保存在 `test_results/` 目录：

- `performance_report.md` - Markdown格式报告
- `performance_report.json` - JSON格式报告
- `locust_report.html` - Locust HTML报告

---

## CI/CD集成

### GitHub Actions 示例

```yaml
name: Performance Tests

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e '.[dev]'

      - name: Start services
        run: docker-compose up -d

      - name: Run performance tests
        run: python tests/performance/run_tests.py

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: performance-reports
          path: test_results/
```

---

## 常见问题

### 1. 测试数据库连接失败

**问题**: `psycopg2.operationalerror: connection refused`

**解决**:
```bash
# 确保Docker服务运行
docker-compose ps

# 启动服务
docker-compose up -d
```

### 2. Locust测试失败

**问题**: `Connection refused` 错误

**解决**:
```bash
# 确保后端运行在正确端口
curl http://localhost:8000/health

# 或指定host
locust -f locustfile.py --host http://localhost:8000
```

### 3. 内存测试显示泄漏

**问题**: 内存趋势斜率为正

**解决步骤**:
1. 使用 `memory_profiler` 定位泄漏源
2. 检查全局变量和缓存
3. 确保连接正确关闭
4. 验证异步任务正确清理

---

## 参考资源

- [Locust 官方文档](https://docs.locust.io/)
- [Pytest 性能测试](https://docs.pytest.org/en/stable/how-to/performance.html)
- [SQLAlchemy 性能优化](https://docs.sqlalchemy.org/en/20/core/performance.html)
- [FastAPI 性能最佳实践](https://fastapi.tiangolo.com/tutorial/performance/)

---

*最后更新: 2026-02-12*
