"""
教案导出 WebSocket 测试
测试 WebSocket 连接、认证、进度通知等功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.websocket.export_manager import ExportConnectionManager, export_manager
from app.services.progress_notifier import ProgressNotifier, progress_notifier
from app.models.export_task import TaskStatus


class TestExportConnectionManager:
    """测试导出连接管理器"""

    @pytest.fixture
    def manager(self) -> ExportConnectionManager:
        """创建新的连接管理器实例（避免全局单例影响测试）"""
        return ExportConnectionManager()

    @pytest.fixture
    def mock_websocket(self) -> MagicMock:
        """创建模拟 WebSocket 连接"""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """测试连接建立"""
        task_id = str(uuid4())

        await manager.connect(task_id, mock_websocket)

        # 验证 WebSocket 已接受
        mock_websocket.accept.assert_called_once()

        # 验证连接确认消息已发送
        mock_websocket.send_json.assert_called_with(
            {"type": "connected", "task_id": task_id, "status": "pending"}
        )

        # 验证连接已记录
        assert manager.has_connection(task_id)
        assert manager.get_connection_count() == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """测试连接断开"""
        task_id = str(uuid4())

        # 先建立连接
        await manager.connect(task_id, mock_websocket)
        assert manager.has_connection(task_id)

        # 断开连接
        manager.disconnect(task_id)

        # 验证连接已移除
        assert not manager.has_connection(task_id)
        assert manager.get_connection_count() == 0

    @pytest.mark.asyncio
    async def test_send_message(self, manager, mock_websocket):
        """测试发送消息"""
        task_id = str(uuid4())
        message = {"type": "test", "data": "value"}

        # 建立连接
        await manager.connect(task_id, mock_websocket)

        # 发送消息
        result = await manager.send_message(task_id, message)

        # 验证消息已发送
        assert result is True
        mock_websocket.send_json.assert_called_with(message)

    @pytest.mark.asyncio
    async def test_send_message_no_connection(self, manager):
        """测试向不存在的连接发送消息"""
        task_id = str(uuid4())
        message = {"type": "test"}

        # 向不存在的连接发送消息
        result = await manager.send_message(task_id, message)

        # 验证返回 False
        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_progress(self, manager, mock_websocket):
        """测试广播进度更新"""
        task_id = str(uuid4())

        await manager.connect(task_id, mock_websocket)

        # 广播进度
        result = await manager.broadcast_progress(task_id, 50, "处理中...")

        # 验证消息格式
        assert result is True
        mock_websocket.send_json.assert_called_with(
            {"type": "progress", "task_id": task_id, "progress": 50, "message": "处理中..."}
        )

    @pytest.mark.asyncio
    async def test_broadcast_progress_clamp(self, manager, mock_websocket):
        """测试进度值限制在 0-100 范围"""
        task_id = str(uuid4())

        await manager.connect(task_id, mock_websocket)

        # 测试超出范围的值
        await manager.broadcast_progress(task_id, 150, "过高")
        assert mock_websocket.send_json.call_args[0][0]["progress"] == 100

        await manager.broadcast_progress(task_id, -50, "过低")
        assert mock_websocket.send_json.call_args[0][0]["progress"] == 0

    @pytest.mark.asyncio
    async def test_notify_complete(self, manager, mock_websocket):
        """测试通知完成"""
        task_id = str(uuid4())
        download_url = f"/downloads/{task_id}.docx"

        await manager.connect(task_id, mock_websocket)

        # 通知完成
        result = await manager.notify_complete(task_id, download_url)

        # 验证消息格式
        assert result is True
        mock_websocket.send_json.assert_called_with(
            {
                "type": "completed",
                "task_id": task_id,
                "status": "completed",
                "download_url": download_url,
            }
        )

    @pytest.mark.asyncio
    async def test_notify_error(self, manager, mock_websocket):
        """测试通知错误"""
        task_id = str(uuid4())
        error_msg = "导出失败：文件不存在"

        await manager.connect(task_id, mock_websocket)

        # 通知错误
        result = await manager.notify_error(task_id, error_msg)

        # 验证消息格式
        assert result is True
        mock_websocket.send_json.assert_called_with(
            {"type": "error", "task_id": task_id, "status": "failed", "error_message": error_msg}
        )

    @pytest.mark.asyncio
    async def test_notify_cancelled(self, manager, mock_websocket):
        """测试通知取消"""
        task_id = str(uuid4())

        await manager.connect(task_id, mock_websocket)

        # 通知取消
        result = await manager.notify_cancelled(task_id)

        # 验证消息格式
        assert result is True
        mock_websocket.send_json.assert_called_with(
            {"type": "cancelled", "task_id": task_id, "status": "cancelled"}
        )

    @pytest.mark.asyncio
    async def test_send_message_failure_handling(self, manager, mock_websocket):
        """测试发送失败时的处理"""
        task_id = str(uuid4())

        await manager.connect(task_id, mock_websocket)

        # 模拟发送失败
        mock_websocket.send_json.side_effect = Exception("Connection lost")

        # 发送消息（应该捕获异常并断开连接）
        result = await manager.send_message(task_id, {"type": "test"})

        # 验证返回 False 且连接已断开
        assert result is False
        assert not manager.has_connection(task_id)

    @pytest.mark.asyncio
    async def test_get_active_tasks(self, manager, mock_websocket):
        """测试获取活跃任务列表"""
        task_ids = [str(uuid4()) for _ in range(3)]

        # 建立多个连接
        for task_id in task_ids:
            await manager.connect(task_id, mock_websocket)

        # 获取活跃任务列表
        active_tasks = manager.get_active_tasks()

        # 验证结果
        assert len(active_tasks) == 3
        for task_id in task_ids:
            assert task_id in active_tasks


class TestProgressNotifier:
    """测试进度通知服务"""

    @pytest.fixture
    def notifier(self) -> ProgressNotifier:
        """创建新的进度通知服务实例"""
        return ProgressNotifier(ExportConnectionManager())

    @pytest.fixture
    def mock_websocket(self) -> MagicMock:
        """创建模拟 WebSocket 连接"""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_notify_progress(self, notifier, mock_websocket):
        """测试通知进度"""
        task_id = str(uuid4())

        # 建立连接
        await notifier.manager.connect(task_id, mock_websocket)

        # 通知进度
        result = await notifier.notify_progress(task_id, 75, "导出中...")

        # 验证
        assert result is True
        # send_json 应该被调用两次：连接确认 + 进度通知
        assert mock_websocket.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_notify_complete(self, notifier, mock_websocket):
        """测试通知完成"""
        task_id = str(uuid4())

        await notifier.manager.connect(task_id, mock_websocket)

        result = await notifier.notify_complete(task_id, "/download/file.docx")

        assert result is True

    @pytest.mark.asyncio
    async def test_notify_error(self, notifier, mock_websocket):
        """测试通知错误"""
        task_id = str(uuid4())

        await notifier.manager.connect(task_id, mock_websocket)

        result = await notifier.notify_error(task_id, "文件格式不支持")

        assert result is True

    @pytest.mark.asyncio
    async def test_notify_cancelled(self, notifier, mock_websocket):
        """测试通知取消"""
        task_id = str(uuid4())

        await notifier.manager.connect(task_id, mock_websocket)

        result = await notifier.notify_cancelled(task_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_has_connection(self, notifier, mock_websocket):
        """测试检查连接是否存在"""
        task_id = str(uuid4())

        # 未连接时
        assert not notifier.has_connection(task_id)

        # 连接后
        await notifier.manager.connect(task_id, mock_websocket)
        assert notifier.has_connection(task_id)

    @pytest.mark.asyncio
    async def test_get_active_count(self, notifier, mock_websocket):
        """测试获取活跃连接数"""
        # 初始为 0
        assert notifier.get_active_count() == 0

        # 添加连接
        await notifier.manager.connect(str(uuid4()), mock_websocket)
        assert notifier.get_active_count() == 1

        await notifier.manager.connect(str(uuid4()), mock_websocket)
        assert notifier.get_active_count() == 2


class TestWebSocketIntegration:
    """WebSocket 集成测试"""

    @pytest.mark.asyncio
    async def test_export_progress_flow(self):
        """测试完整的导出进度流程"""
        manager = ExportConnectionManager()
        notifier = ProgressNotifier(manager)

        # 创建模拟 WebSocket
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        task_id = str(uuid4())
        download_url = f"/api/v1/lesson-export/download/{task_id}"

        # 1. 建立连接
        await manager.connect(task_id, mock_ws)
        assert mock_ws.send_json.call_count == 1  # 连接确认

        # 2. 进度更新
        await notifier.notify_progress(task_id, 25, "准备导出...")
        await notifier.notify_progress(task_id, 50, "生成内容中...")
        await notifier.notify_progress(task_id, 75, "格式化文档...")
        assert mock_ws.send_json.call_count == 4  # 连接 + 3次进度

        # 3. 通知完成
        await notifier.notify_complete(task_id, download_url)
        assert mock_ws.send_json.call_count == 5  # 连接 + 3次进度 + 完成

        # 验证最后一条消息是完成消息
        last_call = mock_ws.send_json.call_args_list[-1]
        assert last_call[0][0]["type"] == "completed"
        assert last_call[0][0]["download_url"] == download_url

    @pytest.mark.asyncio
    async def test_export_error_flow(self):
        """测试导出失败流程"""
        manager = ExportConnectionManager()
        notifier = ProgressNotifier(manager)

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        task_id = str(uuid4())

        # 建立连接并开始导出
        await manager.connect(task_id, mock_ws)
        await notifier.notify_progress(task_id, 30, "开始导出...")

        # 发生错误
        await notifier.notify_error(task_id, "模板文件不存在")

        # 验证最后一条消息是错误消息
        last_call = mock_ws.send_json.call_args_list[-1]
        assert last_call[0][0]["type"] == "error"
        assert "模板文件不存在" in last_call[0][0]["error_message"]

    @pytest.mark.asyncio
    async def test_export_cancel_flow(self):
        """测试导出取消流程"""
        manager = ExportConnectionManager()
        notifier = ProgressNotifier(manager)

        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_json = AsyncMock()

        task_id = str(uuid4())

        # 建立连接并开始导出
        await manager.connect(task_id, mock_ws)
        await notifier.notify_progress(task_id, 10, "开始导出...")

        # 用户取消
        await notifier.notify_cancelled(task_id)

        # 验证最后一条消息是取消消息
        last_call = mock_ws.send_json.call_args_list[-1]
        assert last_call[0][0]["type"] == "cancelled"
        assert last_call[0][0]["status"] == "cancelled"


# =============================================================================
# 全局单例测试（确保不影响其他测试）
# =============================================================================


class TestGlobalSingletons:
    """测试全局单例"""

    def test_export_manager_singleton(self):
        """测试 export_manager 是全局单例"""
        from app.websocket.export_manager import export_manager as em1
        from app.websocket.export_manager import export_manager as em2

        assert em1 is em2
        assert em1.get_connection_count() == 0

    def test_progress_notifier_singleton(self):
        """测试 progress_notifier 是全局单例"""
        from app.services.progress_notifier import progress_notifier as pn1
        from app.services.progress_notifier import progress_notifier as pn2

        assert pn1 is pn2
        assert pn1.get_active_count() == 0
