"""
文件存储服务 - AI英语教学系统
管理导出文件的存储、读取和删除
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from app.core.config import get_settings
from app.models.export_task import ExportFormat


class FileStorageService:
    """
    文件存储服务

    管理导出文件的存储、读取和删除操作。
    支持文件大小限制、唯一文件名生成和自动目录创建。
    """

    # 格式到扩展名的映射
    _EXTENSION_MAP = {
        ExportFormat.WORD: "docx",
        ExportFormat.PDF: "pdf",
        ExportFormat.PPTX: "pptx",
        ExportFormat.MARKDOWN: "md",
    }

    def __init__(self, export_dir: Optional[Path] = None):
        """
        初始化文件存储服务

        Args:
            export_dir: 导出目录路径，如果为None则使用配置中的路径
        """
        settings = get_settings()
        self.export_dir = export_dir or settings.EXPORT_DIR
        self.max_file_size = settings.EXPORT_MAX_FILE_SIZE
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """确保导出目录存在"""
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        content: bytes,
        filename: str,
        format: ExportFormat
    ) -> tuple[str, int]:
        """
        保存文件并返回(路径, 大小)

        Args:
            content: 文件内容（字节）
            filename: 原始文件名
            format: 导出格式

        Returns:
            tuple[str, int]: (文件路径, 文件大小)

        Raises:
            HTTPException: 文件大小超过限制时抛出 413 错误
        """
        # 验证文件大小
        content_size = len(content)
        if content_size > self.max_file_size:
            max_mb = self.max_file_size / 1024 / 1024
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制 {max_mb:.0f}MB"
            )

        # 生成唯一文件名
        ext = self._get_extension(format)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
        if not unique_name.lower().endswith(f".{ext}"):
            unique_name = f"{unique_name}.{ext}"

        file_path = self.export_dir / unique_name

        # 保存文件
        with open(file_path, "wb") as f:
            f.write(content)

        return str(file_path), content_size

    async def get_file(self, file_path: str) -> bytes:
        """
        读取文件内容

        Args:
            file_path: 文件路径

        Returns:
            bytes: 文件内容

        Raises:
            HTTPException: 文件不存在时抛出 404 错误
        """
        path = Path(file_path)

        if not path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")

        if not path.is_file():
            raise HTTPException(status_code=404, detail="文件路径不是文件")

        with open(path, "rb") as f:
            return f.read()

    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 删除成功返回True，文件不存在返回False
        """
        path = Path(file_path)

        if path.exists() and path.is_file():
            path.unlink()
            return True

        return False

    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在

        Args:
            file_path: 文件路径

        Returns:
            bool: 文件存在返回True
        """
        path = Path(file_path)
        return path.exists() and path.is_file()

    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        获取文件大小

        Args:
            file_path: 文件路径

        Returns:
            Optional[int]: 文件大小（字节），不存在返回None
        """
        path = Path(file_path)
        if path.exists() and path.is_file():
            return path.stat().st_size
        return None

    def _get_extension(self, format: ExportFormat) -> str:
        """
        获取文件扩展名

        Args:
            format: 导出格式

        Returns:
            str: 文件扩展名
        """
        return self._EXTENSION_MAP.get(format, format.value)

    def list_files(self, pattern: Optional[str] = None) -> list[Path]:
        """
        列出导出目录中的文件

        Args:
            pattern: 可选的文件名匹配模式

        Returns:
            list[Path]: 文件路径列表
        """
        if pattern:
            return list(self.export_dir.glob(pattern))
        return list(self.export_dir.glob("*"))

    def cleanup_old_files(self, days: int) -> int:
        """
        清理指定天数之前的文件

        Args:
            days: 保留天数，超过此天数的文件将被删除

        Returns:
            int: 删除的文件数量
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0

        for file_path in self.export_dir.iterdir():
            if file_path.is_file():
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < cutoff:
                    file_path.unlink()
                    deleted_count += 1

        return deleted_count


# 创建模块级别的便捷函数
def get_file_storage_service() -> FileStorageService:
    """
    获取文件存储服务实例

    Returns:
        FileStorageService: 文件存储服务实例
    """
    settings = get_settings()
    return FileStorageService(settings.EXPORT_DIR)
