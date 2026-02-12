"""
内存和CPU性能测试

监控系统资源使用情况。
"""
import asyncio
import gc
import pytest
import psutil
import time
from typing import List


@pytest.mark.performance
class TestResourceUsage:
    """资源使用测试套件"""

    def test_process_memory_baseline(self):
        """
        测试进程内存基线

        测量应用在空闲状态下的内存使用。
        """
        process = psutil.Process()

        # 强制垃圾回收
        gc.collect()

        # 获取内存信息
        mem_info = process.memory_info()

        rss_mb = mem_info.rss / 1024 / 1024  # 常驻内存集
        vms_mb = mem_info.vms / 1024 / 1024  # 虚拟内存大小

        print(f"Baseline memory usage:")
        print(f"  RSS: {rss_mb:.2f} MB")
        print(f"  VMS: {vms_mb:.2f} MB")
        print(f"  Percent: {process.memory_percent():.2f}%")

        # 断言：基线内存使用应小于256MB
        assert rss_mb < 256, f"Baseline RSS memory ({rss_mb:.2f} MB) exceeds threshold"

    def test_cpu_baseline(self):
        """
        测试CPU使用基线

        测量应用在空闲状态下的CPU使用。
        """
        process = psutil.Process()

        # 测量CPU使用率（间隔1秒）
        cpu_percent = process.cpu_percent(interval=1.0)

        print(f"Baseline CPU usage: {cpu_percent:.2f}%")

        # 断言：空闲CPU使用应小于10%
        assert cpu_percent < 10, f"Baseline CPU ({cpu_percent:.2f}%) too high"

    @pytest.mark.asyncio
    async def test_memory_under_load(self):
        """
        测试负载下的内存使用

        模拟负载并检查内存是否稳定。
        """
        import httpx

        process = psutil.Process()
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 登录
            login_response = await client.post("http://localhost:8000/api/v1/auth/login", json={
                "username": "test_student",
                "email": "student@test.com",
                "password": "Test1234"
            })

            if login_response.status_code != 200:
                pytest.skip("Cannot login test user")

            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # 记录初始内存
            gc.collect()
            initial_memory = process.memory_info().rss

            memory_samples: List[float] = []
            num_requests = 500

            # 执行请求
            for i in range(num_requests):
                await client.get("http://localhost:8000/api/v1/auth/me", headers=headers)

                # 每50次采样
                if i % 50 == 0:
                    gc.collect()
                    current_memory = process.memory_info().rss
                    memory_mb = current_memory / 1024 / 1024
                    memory_samples.append(memory_mb)
                    print(f"Request {i}: Memory = {memory_mb:.2f} MB")

            # 记录最终内存
            gc.collect()
            final_memory = process.memory_info().rss
            memory_samples.append(final_memory / 1024 / 1024)

            # 分析内存增长
            memory_growth = (final_memory - initial_memory) / 1024 / 1024
            print(f"Memory growth: {memory_growth:.2f} MB")

            # 计算趋势（检测内存泄漏）
            if len(memory_samples) > 2:
                x = list(range(len(memory_samples)))
                y = memory_samples

                # 线性回归
                n = len(x)
                sum_x = sum(x)
                sum_y = sum(y)
                sum_xy = sum(xi * yi for xi, yi in zip(x, y))
                sum_x2 = sum(xi ** 2 for xi in x)

                slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

                print(f"Memory trend: {slope:.4f} MB/sample")

                # 断言：内存增长趋势应较小
                # 允许每请求0.02 MB的增长（考虑缓存等合理因素）
                assert slope < 0.02, f"Potential memory leak detected: slope={slope}"

    @pytest.mark.asyncio
    async def test_cpu_under_load(self):
        """
        测试负载下的CPU使用

        模拟负载并检查CPU使用是否合理。
        """
        import httpx

        process = psutil.Process()
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 登录
            login_response = await client.post("http://localhost:8000/api/v1/auth/login", json={
                "username": "test_student",
                "email": "student@test.com",
                "password": "Test1234"
            })

            if login_response.status_code != 200:
                pytest.skip("Cannot login test user")

            token = login_response.json().get("access_token")
            headers = {"Authorization": f"Bearer {token}"}

            # 启动CPU监控
            cpu_samples: List[float] = []

            async def monitor_cpu():
                """后台监控CPU使用"""
                while True:
                    cpu = process.cpu_percent(interval=0.1)
                    cpu_samples.append(cpu)
                    await asyncio.sleep(0.5)

            # 启动监控任务
            monitor_task = asyncio.create_task(monitor_cpu())

            # 执行负载测试
            num_requests = 100
            start = time.time()

            for _ in range(num_requests):
                await client.get("http://localhost:8000/api/v1/auth/me", headers=headers)

            duration = time.time() - start

            # 停止监控
            monitor_task.cancel()

            # 分析CPU使用
            if cpu_samples:
                avg_cpu = sum(cpu_samples) / len(cpu_samples)
                max_cpu = max(cpu_samples)
                throughput = num_requests / duration

                print(f"CPU under load ({num_requests} requests):")
                print(f"  Average: {avg_cpu:.2f}%")
                print(f"  Max: {max_cpu:.2f}%")
                print(f"  Throughput: {throughput:.2f} req/s")

                # 断言：平均CPU使用应小于80%（留有缓冲）
                assert avg_cpu < 80, f"Average CPU usage ({avg_cpu:.2f}%) too high"

    def test_thread_count(self):
        """
        测试线程数

        验证应用使用的线程数在合理范围。
        """
        process = psutil.Process()
        num_threads = process.num_threads()

        print(f"Thread count: {num_threads}")

        # 断言：线程数应小于200
        assert num_threads < 200, f"Thread count ({num_threads}) too high"

    def test_file_descriptor_count(self):
        """
        测试文件描述符数量

        验证应用使用的文件描述符数量在合理范围。
        """
        try:
            process = psutil.Process()
            num_fds = process.num_fds()

            print(f"File descriptor count: {num_fds}")

            # 断言：FD数量应小于1000
            assert num_fds < 1000, f"File descriptor count ({num_fds}) too high"
        except NotImplementedError:
            # Windows不支持num_fds
            pytest.skip("num_fds not supported on this platform")

    def test_connection_tracking(self):
        """
        测试网络连接跟踪

        验证应用的网络连接状态。
        """
        process = psutil.Process()

        try:
            connections = process.connections(kind='inet')
            print(f"Network connections: {len(connections)}")

            # 分析连接状态
            established = sum(1 for c in connections if c.status == 'ESTABLISHED')
            time_wait = sum(1 for c in connections if c.status == 'TIME_WAIT')

            print(f"  ESTABLISHED: {established}")
            print(f"  TIME_WAIT: {time_wait}")

            # 断言：TIME_WAIT连接不应太多（避免端口耗尽）
            assert time_wait < 100, f"Too many TIME_WAIT connections: {time_wait}"

        except psutil.AccessDenied:
            pytest.skip("Need elevated permissions to check connections")


@pytest.mark.performance
def test_gc_performance():
    """
    测试垃圾回收性能

    验证Python垃圾回收不会造成长时间停顿。
    """
    import gc

    # 创建一些临时对象
    objects = []
    for _ in range(10000):
        objects.append({"data": "x" * 1000})

    # 测量GC时间
    gc_times = []

    for _ in range(10):
        start = time.perf_counter()
        gc.collect()
        end = time.perf_counter()
        gc_times.append((end - start) * 1000)  # 转换为毫秒

    avg_gc_time = sum(gc_times) / len(gc_times)
    max_gc_time = max(gc_times)

    print(f"Garbage collection performance:")
    print(f"  Avg: {avg_gc_time:.2f} ms")
    print(f"  Max: {max_gc_time:.2f} ms")

    # 断言：GC时间不应太长
    assert max_gc_time < 100, f"GC pause too long: {max_gc_time:.2f} ms"
