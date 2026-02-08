"""
异步文件存储服务 - AI英语教学系统
使用 aiofiles 实现异步文件 I/O 操作，避免阻塞事件循环
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiofiles

from app.core.config import get_settings
from app.models.export_task import ExportFormat


class FileStorageError(Exception):
    """文件存储错误基类"""

    def __init__(self, message: str, code: str = "FILE_STORAGE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class FileSizeExceededError(FileStorageError):
    """文件大小超过限制"""

    def __init__(self, size: int, max_size: int):
        max_mb = max_size / 1024 / 1024
        actual_mb = size / 1024 / 1024
        super().__init__(
            f"文件大小 {actual_mb:.2f}MB 超过限制 {max_mb:.0f}MB",
            code="FILE_SIZE_EXCEEDED"
        )
        self.size = size
        self.max_size = max_size


class FileWriteError(FileStorageError):
    """文件写入错误"""

    def __init__(self, path: str, original_error: Optional[Exception] = None):
        message = f"文件写入失败: {path}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message, code="FILE_WRITE_ERROR")
        self.path = path
        self.original_error = original_error


class FileDeleteError(FileStorageError):
    """文件删除错误"""

    def __init__(self, path: str, original_error: Optional[Exception] = None):
        message = f"文件删除失败: {path}"
        if original_error:
            message += f" - {str(original_error)}"
        super().__init__(message, code="FILE_DELETE_ERROR")
        self.path = path
        self.original_error = original_error


class AsyncFileStorageService:
    """
    异步文件存储服务

    使用 aiofiles 实现异步文件 I/O 操作，避免阻塞事件循环。
    支持按日期分组存储、文件大小验证、原子写入等特性。

    Attributes:
        base_path: 基础存储路径
        max_file_size: 最大文件大小（字节）
    """

    # 格式到扩展名的映射
    _EXTENSION_MAP = {
        ExportFormat.WORD: "docx",
        ExportFormat.PDF: "pdf",
        ExportFormat.PPTX: "pptx",
        ExportFormat.MARKDOWN: "md",
    }

    def __init__(self, base_path: Optional[str] = None):
        """
        初始化异步文件存储服务

        Args:
            base_path: 基础存储路径，如果为None则使用配置中的路径
        """
        settings = get_settings()
        self.base_path = Path(base_path or settings.EXPORT_DIR)
        self.max_file_size = settings.EXPORT_MAX_FILE_SIZE

    def _get_extension(self, format: ExportFormat) -> str:
        """
        获取文件扩展名

        Args:
            format: 导出格式

        Returns:
            str: 文件扩展名
        """
        return self._EXTENSION_MAP.get(format, format.value)

    def _generate_filename(self, original_name: str, format: ExportFormat) -> str:
        """
        生成唯一文件名

        文件名格式: YYYY/MM/DD/HHMMSS_UUID_原始名称.扩展名

        Args:
            original_name: 原始文件名
            format: 导出格式

        Returns:
            str: 生成的唯一文件名
        """
        now = datetime.now(timezone.utc)
        ext = self._get_extension(format)

        # 清理原始文件名中的特殊字符
        safe_name = "".join(c if c.isalnum() or c in ('-', '_', '.') else '_' for c in original_name)
        if safe_name.endswith(f'.{ext}'):
            safe_name = safe_name[:-len(f'.{ext}')]

        # 生成唯一标识
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]

        # 组合文件名
        filename = f"{timestamp}_{unique_id}_{safe_name}.{ext}"

        # 按日期组织路径
        date_path = now.strftime("%Y/%m/%d")

        return str(Path(date_path) / filename)

    async def _ensure_directory(self, directory: Path) -> None:
        """
        确保目录存在（异步创建）

        Args:
            directory: 目录路径
        """
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

    async def save_file_async(
        self,
        content: bytes,
        filename: str,
        format: ExportFormat
    ) -> tuple[str, int]:
        """
        异步保存文件

        使用原子写入模式：先写入临时文件，然后重命名。
        这样可以避免写入过程中被读取到不完整的内容。

        Args:
            content: 文件内容（字节）
            filename: 原始文件名
            format: 导出格式

        Returns:
            tuple[str, int]: (文件完整路径, 文件大小)

        Raises:
            FileSizeExceededError: 文件大小超过限制
            FileWriteError: 文件写入失败
        """
        # 验证文件大小
        content_size = len(content)
        if content_size > self.max_file_size:
            raise FileSizeExceededError(content_size, self.max_file_size)

        # 生成文件路径
        relative_path = self._generate_filename(filename, format)
        full_path = self.base_path / relative_path

        # 确保目录存在
        await self._ensure_directory(full_path.parent)

        # 使用原子写入：先写临时文件
        temp_path = full_path.with_suffix(f'.tmp_{uuid.uuid4().hex}')

        try:
            # 异步写入临时文件
            async with aiofiles.open(temp_path, 'wb') as f:
                await f.write(content)

            # 验证写入后的文件大小
            if temp_path.stat().st_size != content_size:
                raise FileWriteError(
                    str(temp_path),
                    Exception(f"写入大小不匹配: 预期 {content_size}, 实际 {temp_path.stat().st_size}")
                )

            # 原子重命名
            temp_path.replace(full_path)

            return str(full_path), content_size

        except Exception as e:
            # 清理临时文件
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

            if isinstance(e, FileStorageError):
                raise
            raise FileWriteError(str(full_path), e)

    async def delete_file_async(self, file_path: str) -> bool:
        """
        异步删除文件

        Args:
            file_path: 文件路径（可以是相对路径或绝对路径）

        Returns:
            bool: 删除成功返回True，文件不存在返回False

        Raises:
            FileDeleteError: 删除操作失败（权限错误等）
        """
        path = Path(file_path)

        # 如果是相对路径，则基于 base_path 解析
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            return False

        if not path.is_file():
            raise FileDeleteError(str(path), Exception("路径不是文件"))

        try:
            path.unlink()
            return True
        except Exception as e:
            raise FileDeleteError(str(path), e)

    async def get_file_size_async(self, file_path: str) -> int:
        """
        异步获取文件大小

        注意：虽然 os.stat() 是同步操作，但由于它是系统调用，
        执行时间极短（微秒级），在大多数情况下不会显著阻塞事件循环。
        如果需要完全异步，可以使用 run_in_executor 包装。

        Args:
            file_path: 文件路径

        Returns:
            int: 文件大小（字节）

        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)

        # 如果是相对路径，则基于 base_path 解析
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not path.is_file():
            raise ValueError(f"路径不是文件: {file_path}")

        return path.stat().st_size

    async def read_file_async(self, file_path: str) -> bytes:
        """
        异步读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            bytes: 文件内容

        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)

        # 如果是相对路径，则基于 base_path 解析
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        async with aiofiles.open(path, 'rb') as f:
            return await f.read()

    async def file_exists_async(self, file_path: str) -> bool:
        """
        异步检查文件是否存在

        Args:
            file_path: 文件路径

        Returns:
            bool: 文件存在返回True
        """
        path = Path(file_path)

        # 如果是相对路径，则基于 base_path 解析
        if not path.is_absolute():
            path = self.base_path / path

        return path.exists() and path.is_file()

    async def list_files_async(
        self,
        pattern: str = "*",
        recursive: bool = False
    ) -> list[str]:
        """
        异步列出文件

        Args:
            pattern: 文件名匹配模式（如 "*.pdf"）
            recursive: 是否递归搜索子目录

        Returns:
            list[str]: 文件路径列表（相对路径）
        """
        if recursive:
            files = self.base_path.rglob(pattern)
        else:
            files = self.base_path.glob(pattern)

        # 过滤出文件（排除目录）
        return [
            str(f.relative_to(self.base_path))
            for f in files
            if f.is_file()
        ]


# 创建模块级别的便捷函数
def get_async_file_storage_service() -> AsyncFileStorageService:
    """
    获取异步文件存储服务实例

    Returns:
        AsyncFileStorageService: 异步文件存储服务实例
    """
    settings = get_settings()
    return AsyncFileStorageService(str(settings.EXPORT_DIR))
