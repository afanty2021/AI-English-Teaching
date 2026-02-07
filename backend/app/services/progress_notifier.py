"""
进度通知服务
提供统一的进度更新、完成通知和错误通知接口
"""

import logging
from typing import Optional

from app.websocket.export_manager import ExportConnectionManager, export_manager

logger = logging.getLogger(__name__)


class ProgressNotifier:
    """
    进度通知服务

    封装 WebSocket 连接管理器，提供简洁的进度通知接口
    """

    def __init__(self, manager: Optional[ExportConnectionManager] = None) -> None:
        """
        初始化进度通知服务

        Args:
            manager: WebSocket 连接管理器，默认使用全局单例
        """
        self.manager = manager or export_manager

    async def notify_progress(self, task_id: str, progress: int, message: str) -> bool:
        """
        通知进度更新

        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 进度描述消息

        Returns:
            bool: 通知是否成功
        """
        try:
            success = await self.manager.broadcast_progress(task_id, progress, message)
            if success:
                logger.debug(f"任务 {task_id} 进度更新: {progress}% - {message}")
            return success
        except Exception as e:
            logger.error(f"通知任务 {task_id} 进度失败: {e}", exc_info=e)
            return False

    async def notify_complete(self, task_id: str, download_url: Optional[str] = None) -> bool:
        """
        通知任务完成

        Args:
            task_id: 任务ID
            download_url: 下载链接（可选）

        Returns:
            bool: 通知是否成功
        """
        try:
            success = await self.manager.notify_complete(task_id, download_url)
            if success:
                logger.info(f"任务 {task_id} 完成通知已发送")
            return success
        except Exception as e:
            logger.error(f"通知任务 {task_id} 完成失败: {e}", exc_info=e)
            return False

    async def notify_error(self, task_id: str, error_message: str) -> bool:
        """
        通知错误

        Args:
            task_id: 任务ID
            error_message: 错误消息

        Returns:
            bool: 通知是否成功
        """
        try:
            success = await self.manager.notify_error(task_id, error_message)
            if success:
                logger.warning(f"任务 {task_id} 错误通知已发送: {error_message}")
            return success
        except Exception as e:
            logger.error(f"通知任务 {task_id} 错误失败: {e}", exc_info=e)
            return False

    async def notify_cancelled(self, task_id: str) -> bool:
        """
        通知任务取消

        Args:
            task_id: 任务ID

        Returns:
            bool: 通知是否成功
        """
        try:
            success = await self.manager.notify_cancelled(task_id)
            if success:
                logger.info(f"任务 {task_id} 取消通知已发送")
            return success
        except Exception as e:
            logger.error(f"通知任务 {task_id} 取消失败: {e}", exc_info=e)
            return False

    def has_connection(self, task_id: str) -> bool:
        """
        检查任务是否有活跃连接

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否有活跃连接
        """
        return self.manager.has_connection(task_id)

    def get_active_count(self) -> int:
        """
        获取当前活跃连接数

        Returns:
            int: 活跃连接数量
        """
        return self.manager.get_connection_count()

    def get_active_tasks(self) -> list[str]:
        """
        获取所有有活跃连接的任务ID列表

        Returns:
            list[str]: 任务ID列表
        """
        return self.manager.get_active_tasks()


# 全局进度通知服务单例
progress_notifier = ProgressNotifier()
