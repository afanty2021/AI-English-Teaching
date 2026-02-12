"""
API负载测试

使用pytest和httpx进行API负载测试。
"""
import asyncio
import time
from typing import Dict, List
from decimal import Decimal

import pytest
import httpx

from app.core.config import settings

# API 基础 URL 常量
API_BASE = "http://localhost:8000"


@pytest.mark.performance
class TestAPILoad:
    """API负载测试套件"""

    async def test_concurrent_login_requests(self):
        """
        测试并发登录请求

        验证系统在高并发登录下的表现。
        注意：由于存在速率限制（5次/分钟），此测试使用较低并发级别。
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{API_BASE}/api/v1/auth/login"

            # 测试不同的并发级别（降低以避免触发速率限制）
            concurrency_levels = [1, 2, 3]
            results = {}

            for concurrency in concurrency_levels:
                start = time.time()

                async def login_request():
                    try:
                        response = await client.post(url, json={
                            "username": "test_student",
                            "password": "Test1234"
                        })
                        # 处理速率限制
                        if response.status_code == 429:
                            return 429, None
                        return response.status_code, response.json() if response.status_code < 500 else None
                    except Exception as e:
                        return 500, str(e)

                # 执行并发请求
                responses = await asyncio.gather(*[login_request() for _ in range(concurrency)])

                total_time = time.time() - start
                successful = sum(1 for status, _ in responses if status == 200)
                failed = concurrency - successful

                results[concurrency] = {
                    "total_time": total_time,
                    "successful": successful,
                    "failed": failed,
                    "success_rate": successful / concurrency if concurrency > 0 else 0,
                    "throughput": concurrency / total_time
                }

                print(f"Concurrency: {concurrency}")
                print(f"  Total time: {total_time:.2f} s")
                print(f"  Successful: {successful}")
                print(f"  Failed: {failed}")
                if concurrency > 0:
                    print(f"  Success rate: {successful / concurrency * 100:.2f}%")
                print(f"  Throughput: {concurrency / total_time:.2f} requests/sec")
                print()

                # 断言：在3并发下成功率应大于70%（考虑速率限制的影响）
                if concurrency <= 3:
                    assert results[concurrency]["success_rate"] > 0.70, \
                        f"Success rate too low at concurrency {concurrency}"

    async def test_api_response_times(self):
        """
        测试API端点响应时间

        测量各个端点的响应时间并验证在可接受范围内。
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 首先登录获取token
            login_response = await client.post(f"{API_BASE}/api/v1/auth/login", json={
                "username": "test_student",
                "password": "Test1234"
            })
            # 处理可能的错误响应
            if login_response.status_code != 200:
                pytest.skip(f"Login failed: {login_response.status_code}")
            token_data = login_response.json()
            token = token_data.get("access_token")
            if not token:
                pytest.skip("No access token in response")
            headers = {"Authorization": f"Bearer {token}"}

            # 测试端点列表
            endpoints = [
                ("GET", "/api/v1/auth/me", None),
                ("GET", "/api/v1/mistakes/me", None),
                ("GET", "/api/v1/reports/me", None),
                ("POST", "/api/v1/reports/generate", {
                    "report_type": "weekly",
                    "period_start": "2024-01-01",
                    "period_end": "2024-01-07"
                })
            ]

            results = {}

            for method, endpoint, data in endpoints:
                url = f"{API_BASE}{endpoint}"
                times = []

                # 每个端点测试10次
                for _ in range(10):
                    start = time.time()

                    if method == "GET":
                        response = await client.get(url, headers=headers)
                    elif method == "POST":
                        response = await client.post(url, json=data, headers=headers)

                    end = time.time()
                    times.append((end - start) * 1000)

                avg = sum(times) / len(times)
                min_t = min(times)
                max_t = max(times)
                p95 = sorted(times)[int(len(times) * 0.95)]

                results[endpoint] = {
                    "avg_ms": avg,
                    "min_ms": min_t,
                    "max_ms": max_t,
                    "p95_ms": p95
                }

                print(f"{endpoint}:")
                print(f"  Avg: {avg:.2f} ms")
                print(f"  Min: {min_t:.2f} ms")
                print(f"  Max: {max_t:.2f} ms")
                print(f"  P95: {p95:.2f} ms")

                # 断言：P95响应时间应该小于1秒
                assert p95 < 1000, f"P95 response time for {endpoint} too high"

    async def test_sustained_load(self):
        """
        测试持续负载

        模拟持续一段时间的负载，验证系统稳定性。
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 登录
            login_response = await client.post(f"{API_BASE}/api/v1/auth/login", json={
                "username": "test_student",
                "password": "Test1234"
            })
            if login_response.status_code != 200:
                pytest.skip(f"Login failed: {login_response.status_code}")
            token_data = login_response.json()
            token = token_data.get("access_token")
            if not token:
                pytest.skip("No access token in response")
            headers = {"Authorization": f"Bearer {token}"}

            # 持续负载测试参数
            duration_seconds = 30
            requests_per_second = 10
            total_requests = duration_seconds * requests_per_second

            results = {
                "successful": 0,
                "failed": 0,
                "response_times": []
            }

            start_time = time.time()
            request_times = []

            async def make_request(request_num):
                """执行单个请求"""
                req_start = time.time()
                try:
                    response = await client.get(
                        f"{API_BASE}/api/v1/auth/me",
                        headers=headers
                    )
                    req_end = time.time()
                    request_times.append(req_end - req_start)

                    if response.status_code == 200:
                        results["successful"] += 1
                    else:
                        results["failed"] += 1
                except Exception as e:
                    results["failed"] += 1
                    req_end = time.time()
                    request_times.append(req_end - req_start)

            # 生成请求任务
            tasks = []
            for i in range(total_requests):
                # 计算每个请求的延迟时间，维持目标RPS
                delay = i / requests_per_second
                tasks.append(make_request(i))

            # 执行请求（尽可能接近目标RPS）
            batch_size = requests_per_second
            for i in range(0, len(tasks), batch_size):
                batch = tasks[i:i+batch_size]
                await asyncio.gather(*batch)
                # 等待以维持目标RPS
                await asyncio.sleep(0.95)

            end_time = time.time()
            actual_duration = end_time - start_time
            actual_rps = total_requests / actual_duration

            print(f"Sustained load test ({duration_seconds}s):")
            print(f"  Target RPS: {requests_per_second}")
            print(f"  Actual RPS: {actual_rps:.2f}")
            print(f"  Successful: {results['successful']}")
            print(f"  Failed: {results['failed']}")
            print(f"  Success rate: {results['successful'] / total_requests * 100:.2f}%")

            if request_times:
                avg_response_time = sum(request_times) / len(request_times)
                print(f"  Avg response time: {avg_response_time * 1000:.2f} ms")

            # 断言：成功率应该大于99%
            assert results["successful"] / total_requests > 0.99, "Success rate too low"

    async def test_memory_leak_detection(self):
        """
        测试内存泄漏检测

        执行大量请求后检查内存使用是否稳定增长。
        """
        import psutil
        import gc

        process = psutil.Process()
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 登录
            login_response = await client.post(f"{API_BASE}/api/v1/auth/login", json={
                "username": "test_student",
                "password": "Test1234"
            })
            if login_response.status_code != 200:
                pytest.skip(f"Login failed: {login_response.status_code}")
            token_data = login_response.json()
            token = token_data.get("access_token")
            if not token:
                pytest.skip("No access token in response")
            headers = {"Authorization": f"Bearer {token}"}

            # 记录初始内存
            gc.collect()
            initial_memory = process.memory_info().rss

            memory_samples = [initial_memory]
            iterations = 100

            for i in range(iterations):
                # 执行请求
                await client.get(f"{API_BASE}/api/v1/auth/me", headers=headers)

                # 每10次采样一次内存
                if i % 10 == 0:
                    gc.collect()
                    current_memory = process.memory_info().rss
                    memory_samples.append(current_memory)

            # 记录最终内存
            gc.collect()
            final_memory = process.memory_info().rss
            memory_samples.append(final_memory)

            # 分析内存增长
            memory_growth_mb = (final_memory - initial_memory) / 1024 / 1024
            print(f"Memory growth over {iterations} requests: {memory_growth_mb:.2f} MB")

            # 计算趋势（线性回归斜率）
            if len(memory_samples) > 2:
                x = list(range(len(memory_samples)))
                y = [m / 1024 / 1024 for m in memory_samples]

                # 简单线性回归
                n = len(x)
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(xi * yi for xi, yi in zip(x, y))
                sum_x2 = sum(xi ** 2 for xi in x)

                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

                print(f"Memory growth trend: {slope:.4f} MB/iteration")

                # 断言：内存增长趋势应该较小
                # 允许每请求0.01 MB的增长（考虑缓存等合理因素）
                assert slope < 0.01, f"Potential memory leak detected: slope={slope}"


@pytest.mark.performance
async def test_concurrent_recommendation_requests():
    """
    测试并发推荐请求

    验证推荐API在并发下的性能表现。
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 登录
        login_response = await client.post(f"{API_BASE}/api/v1/auth/login", json={
            "username": "test_student",
            "password": "Test1234"
        })

        if login_response.status_code != 200:
            pytest.skip("Test user not available")

        token_data = login_response.json()
        user_data = token_data.get("user", {})
        user_id = user_data.get("id")
        token = token_data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        if not user_id:
            pytest.skip("No user ID available")

        # 测试并发推荐请求
        concurrency = 20
        url = f"{API_BASE}/api/v1/students/{user_id}/recommendations"

        start = time.time()

        async def get_recommendations():
            try:
                response = await client.get(url, headers=headers, timeout=10.0)
                return response.status_code, time.time()
            except Exception as e:
                return 500, time.time()

        results = await asyncio.gather(*[get_recommendations() for _ in range(concurrency)])

        total_time = time.time() - start
        successful = sum(1 for status, _ in results if status == 200)

        print(f"Concurrent recommendations ({concurrency} requests):")
        print(f"  Total time: {total_time:.2f} s")
        print(f"  Successful: {successful}/{concurrency}")
        print(f"  Success rate: {successful / concurrency * 100:.2f}%")

        # 分析响应时间
        times = [t - start for _, t in results]
        if times:
            print(f"  Avg response time: {sum(times) / len(times) * 1000:.2f} ms")
            print(f"  P95 response time: {sorted(times)[int(len(times) * 0.95)] * 1000:.2f} ms")


@pytest.mark.performance
async def test_file_upload_performance():
    """
    测试文件上传性能

    测试各种大小文件的上传性能。
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 登录
        login_response = await client.post(f"{API_BASE}/api/v1/auth/login", json={
            "username": "test_teacher",
            "password": "Test1234"
        })

        if login_response.status_code != 200:
            pytest.skip("Teacher user not available")

        token_data = login_response.json()
        token = token_data.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}

        # 测试不同大小的文件
        file_sizes = [1024, 10240, 102400, 1048576]  # 1KB, 10KB, 100KB, 1MB

        for size in file_sizes:
            # 生成测试数据
            test_data = b"x" * size
            files = {"file": ("test.txt", test_data, "text/plain")}
            data = {"title": f"Test upload {size} bytes"}

            start = time.time()
            try:
                response = await client.post(
                    f"{API_BASE}/api/v1/file/upload",
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30.0
                )
                upload_time = time.time() - start

                print(f"Upload {size} bytes:")
                print(f"  Time: {upload_time:.2f} s")
                print(f"  Throughput: {size / upload_time / 1024:.2f} KB/s")
                print(f"  Status: {response.status_code}")

            except Exception as e:
                print(f"Upload {size} bytes failed: {e}")
