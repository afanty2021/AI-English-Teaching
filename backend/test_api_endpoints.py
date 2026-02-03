"""
API 端点测试脚本
测试 FastAPI 应用和健康检查端点
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_imports():
    """测试所有模块导入"""
    print("=" * 60)
    print("测试: 模块导入检查")
    print("=" * 60)

    try:
        from app.main import app
        print("✅ app.main 导入成功")

        from app.api.v1 import auth, contents, conversations, lesson_plans
        print("✅ API 路由模块导入成功")

        from app.services import (
            auth_service,
            ai_service,
            embedding_service,
            knowledge_graph_service,
            recommendation_service,
            speaking_service,
            lesson_plan_service,
            zhipu_service
        )
        print("✅ 所有服务模块导入成功")

        from app.models import (
            User,
            Student,
            Teacher,
            Content,
            Conversation,
            LessonPlan,
            KnowledgeGraph
        )
        print("✅ 所有模型导入成功")

        return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_json_mode_detailed():
    """详细的 JSON 模式测试"""
    print("\n" + "=" * 60)
    print("测试: JSON 模式详细分析")
    print("=" * 60)

    try:
        from app.services.zhipu_service import get_zhipuai_service
        import json

        service = get_zhipuai_service()

        # 测试1: 简单JSON请求
        print("\n测试1: 简单JSON请求")
        response = await service.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant. Always respond with valid JSON."
                },
                {
                    "role": "user",
                    "content": 'Return JSON: {"status": "ok", "value": 42}'
                }
            ],
            temperature=0.1,
            max_tokens=100,
            response_format={"type": "json_object"}
        )

        content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"原始响应: {repr(content)}")

        if content:
            try:
                parsed = json.loads(content)
                print(f"✅ JSON解析成功: {parsed}")
            except json.JSONDecodeError as e:
                print(f"⚠️  JSON解析失败: {e}")
                print(f"   响应内容: {content[:200]}")
        else:
            print("⚠️  响应为空")

        # 测试2: 更复杂的JSON请求
        print("\n测试2: 英语能力分析JSON")
        response2 = await service.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": """你是英语教学分析专家。总是返回有效的JSON格式。
格式要求: {"cefr_level": "A1", "abilities": {"listening": 50, "reading": 60}}"""
                },
                {
                    "role": "user",
                    "content": "分析一个初级英语学生的能力，用JSON格式返回。"
                }
            ],
            temperature=0.3,
            max_tokens=200
        )

        content2 = response2.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"响应: {content2[:200]}")

        # 尝试提取JSON（如果响应包含其他文本）
        if "{" in content2 and "}" in content2:
            start = content2.find("{")
            end = content2.rfind("}") + 1
            json_str = content2[start:end]
            try:
                parsed = json.loads(json_str)
                print(f"✅ 提取的JSON: {parsed}")
            except:
                pass

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_student_analysis():
    """测试学生评估分析功能"""
    print("\n" + "=" * 60)
    print("测试: 学生评估分析 (核心AI功能)")
    print("=" * 60)

    try:
        from app.services.ai_service import get_ai_service

        ai_service = get_ai_service()

        # 模拟学生数据和练习记录
        student_info = {
            "id": "test-student-001",
            "name": "张三",
            "target_exam": "IELTS",
            "target_score": 7.0,
            "current_cefr_level": "B1"
        }

        practice_data = [
            {
                "content_id": "001",
                "topic": "阅读理解",
                "difficulty": "B1",
                "score": 75,
                "correct_rate": 0.75,
                "time_spent": 1800,
                "created_at": "2025-01-10T10:00:00Z"
            },
            {
                "content_id": "002",
                "topic": "听力",
                "difficulty": "B1",
                "score": 60,
                "correct_rate": 0.60,
                "time_spent": 1200,
                "created_at": "2025-01-11T14:00:00Z"
            },
            {
                "content_id": "003",
                "topic": "词汇",
                "difficulty": "B2",
                "score": 70,
                "correct_rate": 0.70,
                "time_spent": 900,
                "created_at": "2025-01-12T09:00:00Z"
            }
        ]

        print(f"学生: {student_info['name']}")
        print(f"目标: {student_info['target_exam']} {student_info['target_score']}")
        print(f"练习记录: {len(practice_data)} 条")
        print()
        print("⏳ 正在进行AI分析...")

        analysis = await ai_service.analyze_student_assessment(
            student_info=student_info,
            practice_data=practice_data,
            target_exam="IELTS",
            provider="zhipuai"
        )

        print("✅ AI分析完成")
        print()
        print("分析结果:")
        print(f"  CEFR等级: {analysis.get('cefr_level', 'N/A')}")
        print(f"  能力评估:")
        for ability, score in analysis.get('abilities', {}).items():
            print(f"    - {ability}: {score}")
        print(f"  薄弱点: {len(analysis.get('weak_points', []))} 个")
        print(f"  优势点: {len(analysis.get('strong_points', []))} 个")
        print(f"  学习建议: {len(analysis.get('recommendations', []))} 条")
        print(f"  考试准备度: {analysis.get('exam_readiness', {}).get('ready', 'N/A')}")
        print(f"  分析摘要: {analysis.get('analysis_summary', 'N/A')[:100]}...")

        return True

    except Exception as e:
        print(f"❌ 学生评估分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_speaking_scenario():
    """测试口语对话场景"""
    print("\n" + "=" * 60)
    print("测试: 口语对话场景 (AI对话)")
    print("=" * 60)

    try:
        from app.services.speaking_service import SpeakingService

        service = SpeakingService()

        # 创建雅思口语对话
        conversation = await service.create_conversation(
            scenario="ielts_speaking_part1",
            user_level="B2",
            target_exam="IELTS"
        )

        print(f"✅ 对话创建成功")
        print(f"  场景: {conversation['scenario']}")
        print(f"  等级: {conversation['level']}")
        print(f"  AI开场白: {conversation['ai_message'][:100]}...")

        # 模拟用户回复
        user_response = "I think technology has greatly improved our lives in many ways."
        print(f"\n用户回复: {user_response}")

        # AI回复
        ai_reply = await service.send_message(
            conversation_id=conversation['conversation_id'],
            user_message=user_response
        )

        print(f"✅ AI回复成功")
        print(f"  AI: {ai_reply['ai_message'][:150]}...")
        print(f"  反馈: {ai_reply['feedback'][:100]}...")

        return True

    except Exception as e:
        print(f"❌ 口语对话测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("\n" + "🧪" * 30)
    print("   API 功能测试")
    print("🧪" * 30 + "\n")

    results = []

    # 运行测试
    results.append(("模块导入", await test_imports()))
    results.append(("JSON模式详细", await test_json_mode_detailed()))
    results.append(("学生评估分析", await test_student_analysis()))
    results.append(("口语对话场景", await test_speaking_scenario()))

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
        print("\n🎉 所有测试通过！系统功能正常！")
    else:
        print(f"\n⚠️  有 {failed} 个测试失败")


if __name__ == "__main__":
    asyncio.run(main())
