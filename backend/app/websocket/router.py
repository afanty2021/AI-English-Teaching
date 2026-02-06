"""
WebSocket 路由

处理WebSocket连接和消息。
"""
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user_ws
from app.models import User
from app.websocket.manager import manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket端点

    客户端连接示例:
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws?token=YOUR_ACCESS_TOKEN')
    ws.onmessage = (event) => console.log(JSON.parse(event.data))
    """
    # 验证token并获取用户
    try:
        user = await get_current_user_ws(token, db)
    except Exception as e:
        await websocket.close(code=4001, reason=str(e))
        return

    # 建立连接
    await manager.connect(websocket, user.id)

    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "user_id": str(user.id),
            "message": "WebSocket连接已建立"
        })

        # 持续接收消息
        while True:
            data = await websocket.receive_text()
            # 这里可以处理客户端发送的消息
            # 目前主要用于保持连接活跃
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except:
                pass

    except WebSocketDisconnect:
        user_id = manager.disconnect(websocket)
        if user_id:
            print(f"User {user_id} disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
