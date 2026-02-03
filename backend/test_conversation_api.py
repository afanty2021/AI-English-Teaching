"""
测试 Conversation API 端点
验证创建对话、获取历史、发送消息、完成对话等功能
"""
import asyncio
import httpx
import json
from datetime import datetime


# 配置
BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"

# 测试凭证
TEST_USERNAME = "test_student"
TEST_PASSWORD = "Test1234"


async def login_and_get_token(client: httpx.AsyncClient) -> str:
    """登录并获取访问令牌"""
    print("\n" + "="*60)
    print("步骤 1: 用户登录")
    print("="*60)

    response = await client.post(
        f"{BASE_URL}{API_PREFIX}/auth/login",
        json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        }
    )

    if response.status_code != 200:
        print(f"❌ 登录失败: {response.status_code}")
        print(response.text)
        raise Exception("Login failed")

    data = response.json()
    token = data.get("access_token")
    print(f"✅ 登录成功，获取令牌: {token[:20]}...")
    return token


async def test_get_available_scenarios(client: httpx.AsyncClient, token: str):
    """测试获取可用场景列表"""
    print("\n" + "="*60)
    print("步骤 2: 获取可用对话场景")
    print("="*60)

    response = await client.get(
        f"{BASE_URL}{API_PREFIX}/conversations/scenarios/available",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"❌ 获取场景失败: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    scenarios = data.get("scenarios", [])
    print(f"✅ 获取到 {len(scenarios)} 个可用场景:")
    for s in scenarios[:3]:
        print(f"   - {s['id']}: {s['name']}")
    return scenarios


async def test_create_conversation(client: httpx.AsyncClient, token: str):
    """测试创建新对话"""
    print("\n" + "="*60)
    print("步骤 3: 创建新对话")
    print("="*60)

    response = await client.post(
        f"{BASE_URL}{API_PREFIX}/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "scenario": "daily_greeting",
            "level": "B1"
        }
    )

    if response.status_code != 201:
        print(f"❌ 创建对话失败: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    print(f"✅ 对话创建成功:")
    print(f"   ID: {data['id']}")
    print(f"   场景: {data['scenario']}")
    print(f"   级别: {data['level']}")
    print(f"   状态: {data['status']}")
    return data


async def test_list_conversations(client: httpx.AsyncClient, token: str):
    """测试获取对话列表"""
    print("\n" + "="*60)
    print("步骤 4: 获取对话列表")
    print("="*60)

    response = await client.get(
        f"{BASE_URL}{API_PREFIX}/conversations",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"❌ 获取列表失败: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    print(f"✅ 获取到 {len(data)} 个对话:")
    for c in data[:3]:
        print(f"   - {c['id']}: {c['scenario']} ({c['status']})")
    return data


async def test_send_message(client: httpx.AsyncClient, token: str, conversation_id: str):
    """测试发送消息"""
    print("\n" + "="*60)
    print("步骤 5: 发送消息")
    print("="*60)

    test_messages = [
        "Hello! How are you today?",
        "I'm doing great, thanks for asking!",
        "What's the weather like today?"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n   发送第 {i} 条消息: {message}")

        response = await client.post(
            f"{BASE_URL}{API_PREFIX}/conversations/{conversation_id}/message",
            headers={"Authorization": f"Bearer {token}"},
            json={"message": message}
        )

        if response.status_code != 200:
            print(f"   ❌ 发送失败: {response.status_code}")
            print(response.text)
            continue

        data = response.json()
        ai_content = data.get("content", "")
        print(f"   ✅ AI 回复: {ai_content[:100]}...")

        # 避免请求过快
        await asyncio.sleep(1)

    return True


async def test_get_conversation_detail(client: httpx.AsyncClient, token: str, conversation_id: str):
    """测试获取对话详情"""
    print("\n" + "="*60)
    print("步骤 6: 获取对话详情")
    print("="*60)

    response = await client.get(
        f"{BASE_URL}{API_PREFIX}/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"❌ 获取详情失败: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    messages = data.get("messages", [])
    print(f"✅ 对话详情:")
    print(f"   消息数量: {len(messages)}")
    print(f"   对话状态: {data['status']}")

    print(f"\n   对话记录:")
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:60]
        print(f"   [{role}]: {content}...")

    return data


async def test_complete_conversation(client: httpx.AsyncClient, token: str, conversation_id: str):
    """测试完成对话"""
    print("\n" + "="*60)
    print("步骤 7: 完成对话并获取评分")
    print("="*60)

    response = await client.post(
        f"{BASE_URL}{API_PREFIX}/conversations/{conversation_id}/complete",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code != 200:
        print(f"❌ 完成对话失败: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    scores = data.get("scores", {})
    print(f"✅ 对话完成，评分:")
    print(f"   流利度: {scores.get('fluency_score', 0):.1f}/100")
    print(f"   词汇: {scores.get('vocabulary_score', 0):.1f}/100")
    print(f"   语法: {scores.get('grammar_score', 0):.1f}/100")
    print(f"   总分: {scores.get('overall_score', 0):.1f}/100")
    print(f"   反馈: {scores.get('feedback', 'N/A')[:80]}...")
    print(f"   时长: {data.get('duration_seconds', 0)} 秒")

    return data


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🧪 Conversation API 端点测试")
    print("="*60)
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API 地址: {BASE_URL}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # 步骤 1: 登录
            token = await login_and_get_token(client)

            # 步骤 2: 获取可用场景
            scenarios = await test_get_available_scenarios(client, token)

            # 步骤 3: 创建对话
            conversation = await test_create_conversation(client, token)
            if not conversation:
                print("\n❌ 无法创建对话，测试终止")
                return

            conversation_id = conversation["id"]

            # 步骤 4: 获取对话列表
            await test_list_conversations(client, token)

            # 步骤 5: 发送消息
            await test_send_message(client, token, conversation_id)

            # 步骤 6: 获取对话详情
            await test_get_conversation_detail(client, token, conversation_id)

            # 步骤 7: 完成对话
            await test_complete_conversation(client, token, conversation_id)

            print("\n" + "="*60)
            print("✅ 所有测试完成")
            print("="*60)

        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
