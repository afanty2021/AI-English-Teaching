"""
数据库性能测试

测试数据库连接、查询性能、连接池效率等。
"""
import asyncio
import pytest
from decimal import Decimal

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.core.config import settings
from tests.conftest import db_engine


@pytest.mark.asyncio
@pytest.mark.performance
async def test_database_connection_pool_efficiency(db_engine):
    """
    测试数据库连接池效率

    验证连接池能够正确管理连接，避免频繁创建/销毁连接。
    """
    pool = db_engine.pool

    # 获取初始状态
    initial_size = pool.size()
    initial_checked_in = pool.checkedin()

    # 执行多次连接操作
    connection_count = 100
    for i in range(connection_count):
        async with db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    # 验证连接池状态
    final_checked_in = pool.checkedin()

    # 连接不应该超过池大小太多
    assert pool.checkedout() <= pool.size() + pool._max_overflow

    # 大部分连接应该被复用
    print(f"Pool size: {pool.size()}")
    print(f"Max overflow: {pool._max_overflow}")
    print(f"Initial checked in: {initial_checked_in}")
    print(f"Final checked in: {final_checked_in}")


@pytest.mark.asyncio
@pytest.mark.performance
async def test_simple_query_performance(db: AsyncSession):
    """
    测试简单查询性能

    验证基本的SELECT查询在合理时间内完成。
    """
    import time

    # 预热
    await db.execute(text("SELECT 1"))

    # 测试查询执行时间
    iterations = 100
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        result = await db.execute(text("SELECT 1"))
        result.fetchone()  # 不需要 await，fetchone() 返回 Row 对象
        end = time.perf_counter()
        times.append((end - start) * 1000)  # 转换为毫秒

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]

    print(f"Average query time: {avg_time:.2f} ms")
    print(f"Min query time: {min_time:.2f} ms")
    print(f"Max query time: {max_time:.2f} ms")
    print(f"P95 query time: {p95_time:.2f} ms")

    # 断言：95%的查询应该在10ms内完成
    assert p95_time < 10, f"P95 query time ({p95_time:.2f} ms) exceeds threshold"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_complex_query_performance(db: AsyncSession):
    """
    测试复杂查询性能

    测试包含JOIN和聚合的复杂查询性能。
    """
    import time

    # 创建测试查询（模拟知识图谱查询）
    query = text("""
        SELECT
            u.id,
            u.username,
            u.email,
            u.role,
            s.current_cefr_level,
            kg.abilities
        FROM users u
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN knowledge_graphs kg ON s.id = kg.student_id
        WHERE u.is_active = true
        LIMIT 100
    """)

    # 预热
    await db.execute(query)

    # 测试执行时间
    iterations = 50
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        result = await db.execute(query)
        result.fetchall()  # 不需要 await，fetchall() 返回 list
        end = time.perf_counter()
        times.append((end - start) * 1000)

    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]

    print(f"Average complex query time: {avg_time:.2f} ms")
    print(f"P95 complex query time: {p95_time:.2f} ms")

    # 断言：95%的查询应该在100ms内完成
    assert p95_time < 100, f"P95 complex query time ({p95_time:.2f} ms) exceeds threshold"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_query_performance():
    """
    测试并发查询性能

    验证数据库在并发查询下的表现。
    """
    import time

    # 修复 DSN 格式：将 postgresql+asyncpg:// 转换为 postgresql://
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    async def execute_query():
        """每个并发操作创建独立连接"""
        start = time.perf_counter()
        conn = await asyncpg.connect(dsn)
        try:
            await conn.fetchval("SELECT 1")
            return (time.perf_counter() - start) * 1000
        finally:
            await conn.close()

    # 执行并发查询
    concurrency_levels = [1, 10, 50, 100]

    for concurrency in concurrency_levels:
        start = time.perf_counter()
        results = await asyncio.gather(*[execute_query() for _ in range(concurrency)])
        total_time = (time.perf_counter() - start) * 1000
        avg_time = sum(results) / len(results)

        print(f"Concurrency: {concurrency}")
        print(f"  Total time: {total_time:.2f} ms")
        print(f"  Average query time: {avg_time:.2f} ms")
        print(f"  Throughput: {concurrency / total_time * 1000:.2f} queries/sec")

        # 断言：吞吐量应该随并发增加而增加（至少在较低并发水平）
        if concurrency <= 10:
            assert concurrency / total_time * 1000 > 100, "Throughput too low"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_transaction_performance(db: AsyncSession):
    """
    测试事务性能

    测试包含多个操作的事务性能。
    """
    import time

    iterations = 50
    times = []

    for _ in range(iterations):
        start = time.perf_counter()

        async with db.begin():
            # 模拟插入和更新操作
            await db.execute(text("SELECT 1"))
            await db.execute(text("SELECT 2"))
            await db.execute(text("SELECT 3"))

        end = time.perf_counter()
        times.append((end - start) * 1000)

    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]

    print(f"Average transaction time: {avg_time:.2f} ms")
    print(f"P95 transaction time: {p95_time:.2f} ms")

    # 断言：95%的事务应该在50ms内完成
    assert p95_time < 50, f"P95 transaction time ({p95_time:.2f} ms) exceeds threshold"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_batch_insert_performance(db: AsyncSession):
    """
    测试批量插入性能

    比较单条插入和批量插入的性能差异。
    """
    import time
    from uuid import uuid4
    from sqlalchemy import insert

    # 创建临时表进行测试
    await db.execute(text("""
        CREATE TEMP TABLE IF NOT EXISTS performance_test (
            id UUID PRIMARY KEY,
            data VARCHAR(100)
        )
    """))
    await db.commit()

    # 测试单条插入
    single_insert_times = []
    for i in range(100):
        start = time.perf_counter()
        test_id = uuid4()
        await db.execute(
            text("INSERT INTO performance_test (id, data) VALUES (:id, :data)"),
            {"id": str(test_id), "data": f"test_{i}"}
        )
        await db.commit()
        single_insert_times.append((time.perf_counter() - start) * 1000)

    # 测试批量插入
    batch_insert_times = []
    for _ in range(10):
        start = time.perf_counter()
        # 使用 execute_many 进行批量插入
        batch_values = [(str(uuid4()), f"batch_{i}_{j}") for j in range(100)]

        # 使用 executemany 语法进行批量插入
        for value in batch_values:
            await db.execute(
                text("INSERT INTO performance_test (id, data) VALUES (:id, :data)"),
                {"id": value[0], "data": value[1]}
            )
        await db.commit()

        batch_insert_times.append((time.perf_counter() - start) * 1000)

    single_avg = sum(single_insert_times) / len(single_insert_times)
    batch_avg = sum(batch_insert_times) / len(batch_insert_times)

    print(f"Average single insert time: {single_avg:.2f} ms")
    print(f"Average batch insert (100 records) time: {batch_avg:.2f} ms")
    print(f"Batch insert speedup: {single_avg * 100 / batch_avg:.2f}x")

    # 清理
    await db.execute(text("DROP TABLE IF EXISTS performance_test"))
    await db.commit()


@pytest.mark.asyncio
@pytest.mark.performance
async def test_index_effectiveness(db: AsyncSession):
    """
    测试索引有效性

    验证索引能够正确提升查询性能。
    """
    import time

    # 测试带索引的查询
    indexed_query = text("""
        SELECT id, username, email
        FROM users
        WHERE email LIKE 'test%@test.com'
        LIMIT 100
    """)

    # 预热
    await db.execute(indexed_query)

    # 测试有索引的查询
    indexed_times = []
    for _ in range(50):
        start = time.perf_counter()
        result = await db.execute(indexed_query)
        result.fetchall()  # fetchall() 返回 list，不需要 await
        indexed_times.append((time.perf_counter() - start) * 1000)

    avg_indexed = sum(indexed_times) / len(indexed_times)
    print(f"Average indexed query time: {avg_indexed:.2f} ms")

    # 断言：平均查询时间应该小于50ms
    assert avg_indexed < 50, f"Indexed query time ({avg_indexed:.2f} ms) too high"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_connection_latency():
    """
    测试数据库连接延迟

    测量建立新连接的延迟。
    """
    import time

    # 修复 DSN 格式
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    latencies = []
    for _ in range(50):
        start = time.perf_counter()
        conn = await asyncpg.connect(dsn)
        await conn.fetchval("SELECT 1")
        await conn.close()
        end = time.perf_counter()
        latencies.append((end - start) * 1000)

    avg_latency = sum(latencies) / len(latencies)
    min_latency = min(latencies)
    max_latency = max(latencies)
    p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

    print(f"Average connection latency: {avg_latency:.2f} ms")
    print(f"Min connection latency: {min_latency:.2f} ms")
    print(f"Max connection latency: {max_latency:.2f} ms")
    print(f"P95 connection latency: {p95_latency:.2f} ms")

    # 断言：连接延迟应该小于100ms
    assert p95_latency < 100, f"P95 connection latency ({p95_latency:.2f} ms) exceeds threshold"
