"""
智谱 AI 服务真实集成测试
验证 ZhipuAI API 调用是否正常工作
"""
import asyncio
import os
import sys
import time

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.services.zhipu_service import ZhipuAIService, get_zhipuai_service
from app.services.embedding_service import EmbeddingService, get_embedding_service


async def test_zhipuai_health_check():
    """测试智谱 AI 健康检查"""
    print("\n" + "="*60)
    print("测试 1: 智谱 AI 健康检查")
    print("="*60)

    service = get_zhipuai_service()
    start = time.time()

    try:
        is_healthy = await service.health_check()
        elapsed = time.time() - start

        print(f"✅ 健康检查: {'通过' if is_healthy else '失败'}")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")
        return is_healthy
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


async def test_chat_completion():
    """测试对话生成"""
    print("\n" + "="*60)
    print("测试 2: 智谱 AI 对话生成")
    print("="*60)

    service = get_zhipuai_service()
    messages = [
        {"role": "system", "content": "你是一个英语教学助手。"},
        {"role": "user", "content": "请用简单英语解释什么是现在完成时？用不超过50个单词回答。"}
    ]

    start = time.time()
    try:
        response = await service.chat_completion(messages=messages)
        elapsed = time.time() - start

        # 从响应中提取内容
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        print(f"✅ 对话生成成功")
        print(f"📝 响应: {content[:200]}...")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")

        # 验证内容非空
        if content:
            return True
        else:
            print(f"⚠️  响应内容为空")
            return False
    except Exception as e:
        print(f"❌ 对话生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding_generation():
    """测试向量生成"""
    print("\n" + "="*60)
    print("测试 3: 智谱 AI 向量生成 (embedding-3)")
    print("="*60)

    service = get_zhipuai_service()
    test_text = "The present perfect tense connects the past to the present."

    start = time.time()
    try:
        embedding = await service.generate_embedding(text=test_text)
        elapsed = time.time() - start

        print(f"✅ 向量生成成功")
        print(f"📊 向量维度: {len(embedding)}")
        print(f"🔢 前5个值: {embedding[:5]}")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")

        # 验证向量维度
        if len(embedding) == 2048:
            print(f"✅ 向量维度正确 (2048)")
            return True
        else:
            print(f"⚠️  向量维度不匹配，期望 2048，实际 {len(embedding)}")
            return False
    except Exception as e:
        print(f"❌ 向量生成失败: {e}")
        return False


async def test_batch_embeddings():
    """测试批量向量生成"""
    print("\n" + "="*60)
    print("测试 4: 批量向量生成")
    print("="*60)

    service = get_zhipuai_service()
    texts = [
        "English grammar is important for learning the language.",
        "Vocabulary building requires consistent practice.",
        "Reading comprehension improves with daily reading.",
    ]

    start = time.time()
    try:
        embeddings = await service.batch_generate_embeddings(texts=texts)
        elapsed = time.time() - start

        print(f"✅ 批量向量生成成功")
        print(f"📊 生成数量: {len(embeddings)}")
        print(f"📊 每个向量维度: {len(embeddings[0]) if embeddings else 0}")
        print(f"⏱️  总响应时间: {elapsed:.2f} 秒")
        print(f"⏱️  平均每个: {elapsed/len(texts):.2f} 秒")
        return True
    except Exception as e:
        print(f"❌ 批量向量生成失败: {e}")
        return False


async def test_embedding_service_integration():
    """测试嵌入服务集成"""
    print("\n" + "="*60)
    print("测试 5: 嵌入服务与 Qdrant 集成")
    print("="*60)

    try:
        embedding_service = get_embedding_service()
        test_text = "Test English content for embedding."

        # 生成向量
        start = time.time()
        embedding = await embedding_service.generate_embedding(text=test_text)
        elapsed = time.time() - start

        print(f"✅ 嵌入服务调用成功")
        print(f"📊 向量维度: {len(embedding)}")
        print(f"⏱️  响应时间: {elapsed:.2f} 秒")

        # 检查是否使用了正确的 AI 提供商
        from app.core.config import settings
        print(f"🔧 当前 AI 提供商: {settings.AI_PROVIDER}")

        return True
    except Exception as e:
        print(f"❌ 嵌入服务集成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_rate_limiter():
    """测试速率限制器"""
    print("\n" + "="*60)
    print("测试 6: 速率限制器 (连续 5 个请求)")
    print("="*60)

    service = get_zhipuai_service()
    texts = ["Test text " + str(i) for i in range(5)]

    start = time.time()
    success_count = 0

    for i, text in enumerate(texts, 1):
        try:
            _ = await service.generate_embedding(text=text)
            elapsed = time.time() - start
            print(f"  请求 {i}: ✅ 成功 (总耗时: {elapsed:.2f}s)")
            success_count += 1
        except Exception as e:
            elapsed = time.time() - start
            print(f"  请求 {i}: ❌ 失败 - {e} (总耗时: {elapsed:.2f}s)")

    total_elapsed = time.time() - start
    print(f"\n📊 总结: {success_count}/{len(texts)} 成功")
    print(f"⏱️  总耗时: {total_elapsed:.2f} 秒")
    print(f"⚠️  注意: 当前速率限制配置较高（5 req/s），小批量测试可能不明显")

    # 只要所有请求成功就认为测试通过
    return success_count == len(texts)


async def test_json_response():
    """测试 JSON 格式响应"""
    print("\n" + "="*60)
    print("测试 7: JSON 格式响应生成")
    print("="*60)

    service = get_zhipuai_service()

    prompt = """分析以下英语学习者的水平并返回 JSON 格式：

学生信息：
- 学习目标：CET4
- 当前水平：中级
- 薄弱项：语法

请以 JSON 格式返回分析结果，包含：
- cefr_level: CEFR 等级
- abilities: 各项能力评分
- recommendations: 学习建议

只返回 JSON，不要其他内容。"""

    messages = [
        {"role": "user", "content": prompt}
    ]

    try:
        import json
        response = await service.chat_completion(messages=messages)

        # 从响应中提取内容
        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

        # 尝试解析为 JSON（去除可能的 markdown 代码块标记）
        json_str = content.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        result = json.loads(json_str)

        print(f"✅ JSON 响应生成成功")
        print(f"📝 解析后的数据:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return True
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"📝 原始内容: {json_str[:500]}")
        return False
    except Exception as e:
        print(f"❌ JSON 响应生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 智谱 AI 服务真实集成测试")
    print("="*60)
    print(f"📅 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 运行所有测试
    tests = [
        ("健康检查", test_zhipuai_health_check),
        ("对话生成", test_chat_completion),
        ("向量生成", test_embedding_generation),
        ("批量向量生成", test_batch_embeddings),
        ("嵌入服务集成", test_embedding_service_integration),
        ("速率限制器", test_rate_limiter),
        ("JSON 响应", test_json_response),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

        # 测试之间稍作延迟，避免触发速率限制
        await asyncio.sleep(1)

    # 打印总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")
    print(f"📅 结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
