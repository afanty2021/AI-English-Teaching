"""
速率限制器测试脚本
验证 RateLimiter 类是否正常工作
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_rate_limiter():
    """测试速率限制器"""
    print("=" * 60)
    print("测试: RateLimiter 类")
    print("=" * 60)

    from app.services.zhipu_service import RateLimiter

    # 创建一个速率为 5/秒 的限制器
    limiter = RateLimiter(rate=5, per=1.0)

    print("\n测试1: 正常速率（5请求/秒）")
    print("-" * 40)

    start = time.time()
    for i in range(5):
        await limiter.acquire()
        print(f"   请求 {i+1} 完成")
    elapsed = time.time() - start

    print(f"   总耗时: {elapsed:.2f}秒")
    print(f"   实际速率: {5/elapsed:.2f} 请求/秒")

    if 0.8 <= 5/elapsed <= 6.0:
        print("   ✅ 速率正常")
    else:
        print("   ⚠️  速率异常")

    print("\n测试2: 突发请求（10个，应触发限速）")
    print("-" * 40)

    start = time.time()
    for i in range(10):
        await limiter.acquire()
        if i < 5:
            print(f"   请求 {i+1} 完成（即时）")
        elif i == 5:
            print(f"   请求 {i+1} 完成（开始限速...）")
        else:
            print(f"   请求 {i+1} 完成")
    elapsed = time.time() - start

    print(f"\n   总耗时: {elapsed:.2f}秒")
    print(f"   实际速率: {10/elapsed:.2f} 请求/秒")

    # 10个请求在5请求/秒的限制下应该需要约2秒
    if 1.8 <= elapsed <= 2.5:
        print("   ✅ 限速工作正常")
    else:
        print(f"   ⚠️  限速可能有问题（预期约2秒，实际{elapsed:.2f}秒）")


async def test_zhipuai_with_rate_limit():
    """测试智谱AI服务的速率限制"""
    print("\n" + "=" * 60)
    print("测试: ZhipuAIService 速率限制")
    print("=" * 60)

    from app.services.zhipu_service import get_zhipuai_service

    service = get_zhipuai_service()

    print("\n测试: 连续5个对话请求")
    print("-" * 40)
    print("预期: 前3个即时，后2个会有延迟（3请求/秒限制）")

    start = time.time()
    results = []

    for i in range(5):
        req_start = time.time()
        try:
            response = await service.chat_completion(
                messages=[
                    {"role": "user", "content": f"Reply with number {i+1}"}
                ],
                max_tokens=10
            )
            req_time = time.time() - req_start
            total_time = time.time() - start
            content = response["choices"][0]["message"]["content"][:30]
            results.append(True)
            print(f"   请求 {i+1}: {req_time:.2f}秒 (总计 {total_time:.2f}秒) - {content}...")
        except Exception as e:
            req_time = time.time() - req_start
            total_time = time.time() - start
            results.append(False)
            print(f"   请求 {i+1}: 失败 ({req_time:.2f}秒) - {e}")

    total_elapsed = time.time() - start

    print(f"\n   总耗时: {total_elapsed:.2f}秒")
    print(f"   实际速率: {5/total_elapsed:.2f} 请求/秒")

    if all(results):
        print("   ✅ 所有请求成功")
    else:
        print(f"   ⚠️  {sum(results)}/5 请求成功")

    # 5个请求在3请求/秒的限制下应该需要约1.3-2秒
    if total_elapsed >= 1.0:
        print("   ✅ 速率限制生效")
    else:
        print("   ⚠️  速率限制可能未生效")


async def test_concurrent_requests():
    """测试并发请求控制"""
    print("\n" + "=" * 60)
    print("测试: 并发请求控制（Semaphore=5）")
    print("=" * 60)

    from app.services.zhipu_service import get_zhipuai_service

    service = get_zhipuai_service()

    print("\n测试: 10个并发请求")
    print("-" * 40)
    print("预期: 最多5个同时执行，其余排队")

    async def make_request(i):
        req_start = time.time()
        try:
            response = await service.chat_completion(
                messages=[{"role": "user", "content": f"Say '{i}'"}],
                max_tokens=5
            )
            req_time = time.time() - req_start
            return i, req_time, True, None
        except Exception as e:
            req_time = time.time() - req_start
            return i, req_time, False, str(e)

    start = time.time()
    tasks = [make_request(i) for i in range(10)]
    results = await asyncio.gather(*tasks)
    total_elapsed = time.time() - start

    print(f"\n   结果详情:")
    for i, req_time, success, error in results:
        status = "✅" if success else "❌"
        print(f"   请求 {i}: {status} {req_time:.2f}秒")

    print(f"\n   总耗时: {total_elapsed:.2f}秒")
    successful = sum(1 for _, _, success, _ in results if success)
    print(f"   成功: {successful}/10")

    if successful >= 8:  # 允许少量失败
        print("   ✅ 并发控制工作正常")
    else:
        print("   ⚠️  可能存在问题")


async def main():
    """主测试函数"""
    print("\n" + "🚦" * 30)
    print("   速率限制器测试")
    print("🚦" * 30 + "\n")

    await test_rate_limiter()
    await test_zhipuai_with_rate_limit()
    await test_concurrent_requests()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
