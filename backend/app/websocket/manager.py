"""
WebSocket 连接管理器

管理WebSocket连接，实现消息广播功能。
"""
import json
import uuid
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[uuid.UUID, Set[WebSocket]] = {}
        # connection_id -> user_id mapping (for debugging)
        self.connection_ids: Dict[id, uuid.UUID] = {}

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID) -> None:
        """接受WebSocket连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        self.connection_ids[id(websocket)] = user_id

    def disconnect(self, websocket: WebSocket) -> uuid.UUID | None:
        """断开WebSocket连接"""
        user_id = self.connection_ids.get(id(websocket))
        if user_id and user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        if id(websocket) in self.connection_ids:
            del self.connection_ids[id(websocket)]
        return user_id

    async def send_personal_message(self, message: dict, user_id: uuid.UUID) -> None:
        """发送个人消息"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error sending message: {e}")
                    disconnected.add(connection)
            # 清理断开的连接
            for conn in disconnected:
                self.disconnect(conn)

    async def broadcast_to_user(self, message: dict, user_id: uuid.UUID) -> None:
        """向指定用户广播消息"""
        await self.send_personal_message(message, user_id)

    async def broadcast_to_all(self, message: dict) -> None:
        """向所有连接的用户广播消息"""
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(message, user_id)

    def get_connection_count(self, user_id: uuid.UUID) -> int:
        """获取用户的连接数"""
        return len(self.active_connections.get(user_id, set()))

    def get_total_connections(self) -> int:
        """获取总连接数"""
        return sum(len(conns) for conns in self.active_connections.values())


# 全局连接管理器单例
manager = ConnectionManager()
