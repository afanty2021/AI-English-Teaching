"""
ZhipuAI 简单测试脚本
避免并发问题，逐个测试功能
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def main():
    """主测试函数"""
    print("=" * 60)
    print("ZhipuAI 基础功能测试")
    print("=" * 60)

    from app.services.zhipu_service import get_zhipuai_service
    from app.core.config import settings

    print(f"\n配置信息:")
    print(f"  API Key: {settings.ZHIPUAI_API_KEY[:10]}...")
    print(f"  模型: {settings.ZHIPUAI_MODEL}")
    print(f"  Embedding模型: {settings.ZHIPUAI_EMBEDDING_MODEL}")

    service = get_zhipuai_service()

    # 测试1: 健康检查
    print("\n" + "-" * 60)
    print("测试1: 健康检查")
    print("-" * 60)

    is_healthy = await service.health_check()
    print(f"结果: {'✅ 通过' if is_healthy else '❌ 失败'}")

    if not is_healthy:
        print("❌ 健康检查失败，请检查API密钥")
        return

    # 等待一下避免速率限制
    await asyncio.sleep(1)

    # 测试2: 简单对话
    print("\n" + "-" * 60)
    print("测试2: 简单对话")
    print("-" * 60)

    try:
        response = await service.chat_completion(
            messages=[
                {"role": "user", "content": "用英语简单介绍IELTS考试，不超过50词。"}
            ],
            temperature=0.7,
            max_tokens=200
        )

        content = response["choices"][0]["message"]["content"]
        print(f"✅ 对话成功")
        print(f"AI回复: {content}")

    except Exception as e:
        print(f"❌ 对话失败: {e}")

    await asyncio.sleep(1)

    # 测试3: 向量生成
    print("\n" + "-" * 60)
    print("测试3: 向量生成 (embedding-3)")
    print("-" * 60)

    try:
        text = "英语教学方法"
        embedding = await service.generate_embedding(text)

        print(f"✅ 向量生成成功")
        print(f"  文本: {text}")
        print(f"  向量维度: {len(embedding)}")

        if len(embedding) == 2048:
            print(f"  ✅ 向量维度正确 (2048)")
        else:
            print(f"  ❌ 向量维度错误，期望 2048，实际 {len(embedding)}")

    except Exception as e:
        print(f"❌ 向量生成失败: {e}")

    await asyncio.sleep(1)

    # 测试4: 批量向量
    print("\n" + "-" * 60)
    print("测试4: 批量向量生成")
    print("-" * 60)

    try:
        texts = ["词汇", "语法", "阅读", "听力"]
        embeddings = await service.batch_generate_embeddings(texts)

        print(f"✅ 批量向量生成成功")
        print(f"  文本数量: {len(texts)}")
        print(f"  向量数量: {len(embeddings)}")
        print(f"  向量维度: {len(embeddings[0])}")

    except Exception as e:
        print(f"❌ 批量向量生成失败: {e}")

    await asyncio.sleep(1)

    # 测试5: 结构化输出 (JSON模式)
    print("\n" + "-" * 60)
    print("测试5: JSON模式")
    print("-" * 60)

    try:
        response = await service.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "总是返回有效的JSON格式。"
                },
                {
                    "role": "user",
                    "content": "返回一个简单的JSON: {\"status\": \"success\", \"value\": 100}"
                }
            ],
            temperature=0.1,
            max_tokens=100,
            response_format={"type": "json_object"}
        )

        content = response["choices"][0]["message"]["content"]
        print(f"原始响应: {repr(content)}")

        if content:
            import json
            try:
                parsed = json.loads(content)
                print(f"✅ JSON解析成功: {parsed}")
            except json.JSONDecodeError:
                print(f"⚠️  JSON解析失败，但这是智谱AI的已知行为")
                print(f"   建议使用提示工程而非JSON模式来确保结构化输出")
        else:
            print("⚠️  响应为空")

    except Exception as e:
        print(f"❌ JSON模式测试失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
