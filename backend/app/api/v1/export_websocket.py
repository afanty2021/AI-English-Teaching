"""
教案导出 WebSocket 路由
提供实时导出进度推送的 WebSocket 端点
"""

import logging

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_ws, get_db
from app.models import User
from app.websocket.export_manager import export_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/lesson-export/{task_id}")
async def export_progress_websocket(
    websocket: WebSocket,
    task_id: str,
    token: str = Query(..., description="JWT 访问令牌"),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    教案导出任务进度 WebSocket 端点

    连接后可以实时接收：
    - 连接确认消息 (type: "connected")
    - 进度更新消息 (type: "progress")
    - 任务完成消息 (type: "completed")
    - 错误通知消息 (type: "error")
    - 任务取消消息 (type: "cancelled")

    连接示例 (JavaScript):
    ```javascript
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/lesson-export/${taskId}?token=${accessToken}`);

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        switch (data.type) {
            case 'connected':
                console.log('WebSocket 已连接');
                break;
            case 'progress':
                console.log(`进度: ${data.progress}% - ${data.message}`);
                break;
            case 'completed':
                console.log('导出完成，下载链接:', data.download_url);
                break;
            case 'error':
                console.error('导出失败:', data.error_message);
                break;
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket 错误:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket 已关闭');
    };
    ```

    Args:
        websocket: WebSocket 连接对象
        task_id: 导出任务ID
        token: JWT 访问令牌
        db: 数据库会话
    """
    # 验证 token 并获取用户
    try:
        current_user: User = await get_current_user_ws(token, db)
    except Exception as e:
        logger.warning(f"WebSocket 认证失败: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # 建立连接
    await export_manager.connect(task_id, websocket)

    try:
        # 发送用户信息
        await websocket.send_json(
            {
                "type": "authenticated",
                "user_id": str(current_user.id),
                "username": current_user.username,
            }
        )

        # 保持连接活跃，接收客户端消息
        while True:
            data = await websocket.receive_text()

            # 处理客户端消息（可用于心跳等）
            try:
                import json

                message = json.loads(data)

                # 心跳响应
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

                # 获取当前状态
                elif message.get("type") == "get_status":
                    # 这里可以查询任务状态并返回
                    await websocket.send_json(
                        {"type": "status", "task_id": task_id, "connected": True}
                    )

            except json.JSONDecodeError:
                logger.debug(f"收到非 JSON 消息: {data}")
            except Exception as e:
                logger.error(f"处理客户端消息失败: {e}", exc_info=e)

    except WebSocketDisconnect:
        export_manager.disconnect(task_id)
        logger.info(f"WebSocket 已断开: task_id={task_id}, user={current_user.username}")
    except Exception as e:
        export_manager.disconnect(task_id)
        logger.error(f"WebSocket 错误: task_id={task_id}, error={e}", exc_info=e)


@router.get("/ws/lesson-export/active-count")
async def get_active_connections(current_user: User = Depends(get_current_user)) -> dict:
    """
    获取当前活跃的 WebSocket 连接数

    Args:
        current_user: 当前认证用户

    Returns:
        dict: 包含活跃连接数和任务ID列表
    """
    return {
        "active_count": export_manager.get_connection_count(),
        "active_tasks": export_manager.get_active_tasks(),
    }
