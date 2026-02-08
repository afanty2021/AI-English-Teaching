"""
文件存储服务 - AI英语教学系统
管理导出文件的存储、读取和删除

提供向后兼容的同步API，内部使用AsyncFileStorageService实现。
"""
import asyncio
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from app.core.config import get_settings
from app.models.export_task import ExportFormat
from app.services.async_file_storage_service import (
    AsyncFileStorageService,
    FileSizeExceededError,
    FileStorageError,
)


class FileStorageService:
    """
    文件存储服务 - 向后兼容的同步包装器

    管理导出文件的存储、读取和删除操作。
    支持文件大小限制、唯一文件名生成和自动目录创建。

    注意：这是 AsyncFileStorageService 的同步包装器，
    用于保持向后兼容性。内部使用 asyncio.run() 来运行异步方法。
    """

    def __init__(self, export_dir: Optional[Path] = None):
        """
        初始化文件存储服务

        Args:
            export_dir: 导出目录路径，如果为None则使用配置中的路径
        """
        settings = get_settings()
        self.export_dir = export_dir or settings.EXPORT_DIR
        # 使用异步存储服务
        self._async_storage = AsyncFileStorageService(str(self.export_dir))

    def save_file(
        self,
        content: bytes,
        filename: str,
        format: ExportFormat
    ) -> tuple[str, int]:
        """
        同步保存文件 - 包装异步方法

        Args:
            content: 文件内容（字节）
            filename: 原始文件名
            format: 导出格式

        Returns:
            tuple[str, int]: (文件路径, 文件大小)

        Raises:
            HTTPException: 文件大小超过限制时抛出 413 错误
        """
        try:
            # 在新的事件循环中运行异步方法
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._async_storage.save_file_async(content, filename, format)
                )
            finally:
                loop.close()
        except FileSizeExceededError as e:
            raise HTTPException(status_code=413, detail=e.message)
        except FileStorageError as e:
            raise HTTPException(status_code=500, detail=e.message)

    def get_file(self, file_path: str) -> bytes:
        """
        同步读取文件 - 包装异步方法

        Args:
            file_path: 文件路径

        Returns:
            bytes: 文件内容

        Raises:
            HTTPException: 文件不存在时抛出 404 错误
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._async_storage.read_file_async(file_path)
                )
            finally:
                loop.close()
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except FileStorageError as e:
            raise HTTPException(status_code=500, detail=e.message)

    def delete_file(self, file_path: str) -> bool:
        """
        同步删除文件 - 包装异步方法

        Args:
            file_path: 文件路径

        Returns:
            bool: 删除成功返回True，文件不存在返回False
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._async_storage.delete_file_async(file_path)
                )
            finally:
                loop.close()
        except FileStorageError:
            return False

    def file_exists(self, file_path: str) -> bool:
        """
        同步检查文件是否存在 - 包装异步方法

        Args:
            file_path: 文件路径

        Returns:
            bool: 文件存在返回True
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._async_storage.file_exists_async(file_path)
            )
        finally:
            loop.close()

    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        同步获取文件大小 - 包装异步方法

        Args:
            file_path: 文件路径

        Returns:
            Optional[int]: 文件大小（字节），不存在返回None
        """
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self._async_storage.get_file_size_async(file_path)
                )
            finally:
                loop.close()
        except (FileNotFoundError, FileStorageError):
            return None

    def list_files(self, pattern: Optional[str] = None) -> list[str]:
        """
        同步列出文件 - 包装异步方法

        Args:
            pattern: 可选的文件名匹配模式

        Returns:
            list[str]: 文件路径列表（相对路径）
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._async_storage.list_files_async(pattern or "*", recursive=False)
            )
        finally:
            loop.close()


# 创建模块级别的便捷函数
def get_file_storage_service() -> FileStorageService:
    """
    获取文件存储服务实例

    Returns:
        FileStorageService: 文件存储服务实例
    """
    settings = get_settings()
    return FileStorageService(settings.EXPORT_DIR)
