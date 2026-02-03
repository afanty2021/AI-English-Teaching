"""
ZhipuAI 服务测试脚本
测试智谱AI API连接和基本功能
"""
import asyncio
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.zhipu_service import get_zhipuai_service
from app.services.ai_service import get_ai_service
from app.services.embedding_service import get_embedding_service
from app.core.config import settings


async def test_zhipuai_service():
    """测试智谱AI基础服务"""
    print("=" * 60)
    print("测试 1: 智谱AI基础服务连接")
    print("=" * 60)

    try:
        service = get_zhipuai_service()
        print(f"✅ 服务初始化成功")
        print(f"   API Key: {settings.ZHIPUAI_API_KEY[:10]}...")
        print(f"   模型: {settings.ZHIPUAI_MODEL}")
        print(f"   Embedding模型: {settings.ZHIPUAI_EMBEDDING_MODEL}")
        print(f"   Base URL: {settings.ZHIPUAI_BASE_URL}")

        # 健康检查
        is_healthy = await service.health_check()
        print(f"✅ 健康检查: {'通过' if is_healthy else '失败'}")
        return is_healthy

    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        return False


async def test_chat_completion():
    """测试对话完成"""
    print("\n" + "=" * 60)
    print("测试 2: 对话完成 (glm-4.7)")
    print("=" * 60)

    try:
        service = get_zhipuai_service()

        response = await service.chat_completion(
            messages=[
                {"role": "system", "content": "你是一个专业的英语教学助手。"},
                {"role": "user", "content": "请用一句话介绍什么是CEFR等级。"}
            ],
            temperature=0.7,
            max_tokens=100
        )

        content = response["choices"][0]["message"]["content"]
        print(f"✅ 对话成功")
        print(f"   回复: {content}")
        return True

    except Exception as e:
        print(f"❌ 对话失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding():
    """测试向量生成"""
    print("\n" + "=" * 60)
    print("测试 3: 向量生成 (embedding-3)")
    print("=" * 60)

    try:
        service = get_zhipuai_service()

        text = "英语学习方法"
        embedding = await service.generate_embedding(text)

        print(f"✅ 向量生成成功")
        print(f"   文本: {text}")
        print(f"   向量维度: {len(embedding)}")
        print(f"   前5个值: {embedding[:5]}")

        # 验证维度
        expected_dim = 2048
        if len(embedding) == expected_dim:
            print(f"✅ 向量维度正确 ({expected_dim})")
            return True
        else:
            print(f"❌ 向量维度错误，期望 {expected_dim}，实际 {len(embedding)}")
            return False

    except Exception as e:
        print(f"❌ 向量生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_batch_embeddings():
    """测试批量向量生成"""
    print("\n" + "=" * 60)
    print("测试 4: 批量向量生成")
    print("=" * 60)

    try:
        service = get_zhipuai_service()

        texts = ["词汇学习", "语法练习", "阅读理解", "听力训练"]
        embeddings = await service.batch_generate_embeddings(texts)

        print(f"✅ 批量向量生成成功")
        print(f"   文本数量: {len(texts)}")
        print(f"   向量数量: {len(embeddings)}")
        print(f"   向量维度: {len(embeddings[0])}")

        return True

    except Exception as e:
        print(f"❌ 批量向量生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_json_mode():
    """测试JSON模式"""
    print("\n" + "=" * 60)
    print("测试 5: JSON模式结构化输出")
    print("=" * 60)

    try:
        service = get_zhipuai_service()

        response = await service.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "请返回JSON格式的英语能力分析结果。"
                },
                {
                    "role": "user",
                    "content": "分析一个初级英语学生的能力，返回格式：{\"level\": \"A1\", \"abilities\": {\"listening\": 50, \"reading\": 60}}"
                }
            ],
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"}
        )

        content = response["choices"][0]["message"]["content"]
        print(f"✅ JSON模式成功")
        print(f"   响应: {content}")

        # 尝试解析JSON
        import json
        try:
            parsed = json.loads(content)
            print(f"✅ JSON解析成功")
            print(f"   数据: {parsed}")
            return True
        except json.JSONDecodeError:
            print(f"⚠️  JSON解析失败（响应可能不是有效JSON）")
            return False

    except Exception as e:
        print(f"❌ JSON模式失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ai_service():
    """测试AI服务封装"""
    print("\n" + "=" * 60)
    print("测试 6: AIService多提供商支持")
    print("=" * 60)

    try:
        ai_service = get_ai_service()

        print(f"✅ AIService初始化成功")
        print(f"   当前提供商: {ai_service.provider}")
        print(f"   模型: {ai_service.model}")
        print(f"   Embedding模型: {ai_service.embedding_model}")

        # 测试对话
        response = await ai_service.chat_completion(
            messages=[
                {"role": "user", "content": "用英语介绍雅思考试"}
            ],
            provider="zhipuai"
        )

        print(f"✅ AIService对话成功")
        print(f"   回复: {response[:100]}...")

        return True

    except Exception as e:
        print(f"❌ AIService测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_embedding_service():
    """测试嵌入服务"""
    print("\n" + "=" * 60)
    print("测试 7: EmbeddingService")
    print("=" * 60)

    try:
        emb_service = get_embedding_service()

        print(f"✅ EmbeddingService初始化成功")
        print(f"   当前提供商: {emb_service.provider}")
        print(f"   向量维度: {emb_service.get_embedding_dimension()}")

        # 测试单个向量
        embedding = await emb_service.generate_embedding("test text")
        print(f"✅ 单个向量生成成功，维度: {len(embedding)}")

        # 测试内容向量
        content_emb = await emb_service.generate_content_embedding(
            title="IELTS阅读练习",
            content_text="这是一篇关于环境保护的文章...",
            topic="阅读理解",
            difficulty_level="B1",
            exam_type="IELTS"
        )
        print(f"✅ 内容向量生成成功，维度: {len(content_emb)}")

        # 测试词汇向量
        word_emb = await emb_service.generate_vocabulary_embedding(
            word="abandon",
            definitions=["放弃", "抛弃"],
            examples=["He abandoned his car in the snow."]
        )
        print(f"✅ 词汇向量生成成功，维度: {len(word_emb)}")

        return True

    except Exception as e:
        print(f"❌ EmbeddingService测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print("   ZhipuAI 服务集成测试")
    print("🚀" * 30 + "\n")

    # 检查配置
    if not settings.ZHIPUAI_API_KEY or settings.ZHIPUAI_API_KEY == "your_zhipuai_api_key_here":
        print("❌ 错误: ZHIPUAI_API_KEY 未配置")
        print("   请在 backend/.env 文件中设置有效的API密钥")
        return

    print(f"📋 配置信息:")
    print(f"   AI提供商: {settings.AI_PROVIDER}")
    print(f"   Qdrant向量维度: {settings.QDRANT_VECTOR_SIZE}")
    print(f"   智谱AI模型: {settings.ZHIPUAI_MODEL}")
    print()

    # 运行所有测试
    results = []

    results.append(("服务连接", await test_zhipuai_service()))
    results.append(("对话完成", await test_chat_completion()))
    results.append(("向量生成", await test_embedding()))
    results.append(("批量向量", await test_batch_embeddings()))
    results.append(("JSON模式", await test_json_mode()))
    results.append(("AIService", await test_ai_service()))
    results.append(("EmbeddingService", await test_embedding_service()))

    # 打印测试结果摘要
    print("\n" + "=" * 60)
    print("测试结果摘要")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print()
    print(f"总计: {passed} 通过, {failed} 失败")

    if failed == 0:
        print("\n🎉 所有测试通过！ZhipuAI 集成成功！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查错误信息")


if __name__ == "__main__":
    asyncio.run(main())
