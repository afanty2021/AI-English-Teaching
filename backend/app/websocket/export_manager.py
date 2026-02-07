"""
教案导出 WebSocket 连接管理器
管理导出任务的 WebSocket 连接，实现实时进度推送
"""

import logging
from typing import Dict, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ExportConnectionManager:
    """
    导出任务 WebSocket 连接管理器

    管理导出任务的 WebSocket 连接，支持：
    - 连接建立与断开
    - 进度广播
    - 任务完成通知
    - 错误通知
    """

    def __init__(self) -> None:
        # task_id -> WebSocket 连接映射
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, task_id: str, websocket: WebSocket) -> None:
        """
        连接到指定任务的 WebSocket

        Args:
            task_id: 任务ID
            websocket: WebSocket 连接对象
        """
        await websocket.accept()
        self.active_connections[task_id] = websocket

        # 发送连接确认消息
        await self.send_message(
            task_id, {"type": "connected", "task_id": task_id, "status": "pending"}
        )
        logger.info(f"WebSocket 已连接到任务: {task_id}")

    def disconnect(self, task_id: str) -> None:
        """
        断开指定任务的连接

        Args:
            task_id: 任务ID
        """
        if task_id in self.active_connections:
            del self.active_connections[task_id]
            logger.info(f"WebSocket 已断开任务: {task_id}")

    async def send_message(self, task_id: str, message: dict) -> bool:
        """
        发送消息到指定任务的客户端

        Args:
            task_id: 任务ID
            message: 要发送的消息字典

        Returns:
            bool: 发送是否成功
        """
        if task_id not in self.active_connections:
            logger.warning(f"任务 {task_id} 没有活跃的 WebSocket 连接")
            return False

        try:
            await self.active_connections[task_id].send_json(message)
            return True
        except Exception as e:
            logger.error(f"发送消息到任务 {task_id} 失败: {e}", exc_info=e)
            # 发送失败时断开连接
            self.disconnect(task_id)
            return False

    async def broadcast_progress(self, task_id: str, progress: int, message: str) -> bool:
        """
        广播进度更新

        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度描述消息

        Returns:
            bool: 发送是否成功
        """
        return await self.send_message(
            task_id,
            {
                "type": "progress",
                "task_id": task_id,
                "progress": min(100, max(0, progress)),  # 确保在 0-100 范围内
                "message": message,
            },
        )

    async def notify_complete(self, task_id: str, download_url: Optional[str] = None) -> bool:
        """
        通知任务完成

        Args:
            task_id: 任务ID
            download_url: 下载链接（可选）

        Returns:
            bool: 发送是否成功
        """
        return await self.send_message(
            task_id,
            {
                "type": "completed",
                "task_id": task_id,
                "status": "completed",
                "download_url": download_url,
            },
        )

    async def notify_error(self, task_id: str, error_message: str) -> bool:
        """
        通知错误

        Args:
            task_id: 任务ID
            error_message: 错误消息

        Returns:
            bool: 发送是否成功
        """
        return await self.send_message(
            task_id,
            {
                "type": "error",
                "task_id": task_id,
                "status": "failed",
                "error_message": error_message,
            },
        )

    async def notify_cancelled(self, task_id: str) -> bool:
        """
        通知任务取消

        Args:
            task_id: 任务ID

        Returns:
            bool: 发送是否成功
        """
        return await self.send_message(
            task_id, {"type": "cancelled", "task_id": task_id, "status": "cancelled"}
        )

    def has_connection(self, task_id: str) -> bool:
        """
        检查任务是否有活跃连接

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否有活跃连接
        """
        return task_id in self.active_connections

    def get_connection_count(self) -> int:
        """
        获取当前活跃连接数

        Returns:
            int: 活跃连接数量
        """
        return len(self.active_connections)

    def get_active_tasks(self) -> list[str]:
        """
        获取所有有活跃连接的任务ID列表

        Returns:
            list[str]: 任务ID列表
        """
        return list(self.active_connections.keys())


# 全局连接管理器单例
export_manager = ExportConnectionManager()
