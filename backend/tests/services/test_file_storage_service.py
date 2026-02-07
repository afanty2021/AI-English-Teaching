"""
文件存储服务测试
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.core.config import Settings
from app.models.export_task import ExportFormat
from app.services.file_storage_service import FileStorageService


class TestFileStorageService:
    """文件存储服务测试"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def storage_service(self, temp_dir):
        """创建文件存储服务实例"""
        return FileStorageService(temp_dir)

    @pytest.fixture
    def mock_settings(self):
        """创建模拟配置"""
        settings = MagicMock(spec=Settings)
        settings.EXPORT_DIR = Path("/tmp/test_exports")
        settings.EXPORT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        return settings

    @pytest.mark.asyncio
    async def test_save_file_success(self, storage_service):
        """测试成功保存文件"""
        content = b"test content for file storage"
        path, size = await storage_service.save_file(
            content, "test.docx", ExportFormat.WORD
        )

        assert Path(path).exists()
        assert size == len(content)

    @pytest.mark.asyncio
    async def test_save_file_with_unique_name(self, storage_service):
        """测试文件名唯一性"""
        content = b"test content"
        filename = "lesson.docx"

        path1, _ = await storage_service.save_file(content, filename, ExportFormat.WORD)
        path2, _ = await storage_service.save_file(content, filename, ExportFormat.WORD)

        # 路径应该不同
        assert path1 != path2

        # 文件应该存在
        assert Path(path1).exists()
        assert Path(path2).exists()

    @pytest.mark.asyncio
    async def test_save_file_with_extension(self, storage_service):
        """测试自动添加扩展名"""
        content = b"test content"

        path, _ = await storage_service.save_file(content, "test", ExportFormat.PDF)

        assert path.endswith(".pdf")
        assert Path(path).exists()

    @pytest.mark.asyncio
    async def test_save_file_size_limit(self, storage_service, mock_settings):
        """测试文件大小限制"""
        # 创建一个使用较小限制的服务
        small_service = FileStorageService(Path("/tmp/small_exports"))
        # 模拟设置
        with patch.object(small_service, 'max_file_size', 100):  # 100 bytes
            large_content = b"x" * 101  # 101 bytes

            with pytest.raises(Exception) as exc_info:
                await small_service.save_file(
                    large_content, "test.docx", ExportFormat.WORD
                )

            assert exc_info.value.status_code == 413

    @pytest.mark.asyncio
    async def test_get_file_success(self, storage_service):
        """测试成功读取文件"""
        content = b"test file content for reading"
        save_path, _ = await storage_service.save_file(
            content, "read_test.docx", ExportFormat.WORD
        )

        read_content = await storage_service.get_file(save_path)

        assert read_content == content

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, storage_service):
        """测试文件不存在"""
        with pytest.raises(Exception) as exc_info:
            await storage_service.get_file("/nonexistent/path/file.docx")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_service):
        """测试成功删除文件"""
        content = b"file to delete"
        path, _ = await storage_service.save_file(content, "delete_test.docx", ExportFormat.WORD)

        assert Path(path).exists()

        result = await storage_service.delete_file(path)
        assert result is True
        assert not Path(path).exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage_service):
        """测试删除不存在的文件"""
        result = await storage_service.delete_file("/nonexistent/file.docx")
        assert result is False

    def test_file_exists_true(self, storage_service):
        """测试文件存在检查（存在）"""
        content = b"test content"
        path, _ = storage_service.export_dir / "exists_test.docx"
        path.write_bytes(content)

        assert storage_service.file_exists(str(path)) is True

    def test_file_exists_false(self, storage_service):
        """测试文件存在检查（不存在）"""
        assert storage_service.file_exists("/nonexistent/file.docx") is False

    def test_get_file_size(self, storage_service):
        """测试获取文件大小"""
        content = b"test file size content"
        path, expected_size = storage_service.export_dir / "size_test.docx", len(content)
        path.write_bytes(content)

        size = storage_service.get_file_size(str(path))

        assert size == expected_size

    def test_get_extension(self, storage_service):
        """测试扩展名映射"""
        assert storage_service._get_extension(ExportFormat.WORD) == "docx"
        assert storage_service._get_extension(ExportFormat.PDF) == "pdf"
        assert storage_service._get_extension(ExportFormat.PPTX) == "pptx"
        assert storage_service._get_extension(ExportFormat.MARKDOWN) == "md"

    def test_list_files(self, storage_service):
        """测试列出文件"""
        # 创建一些测试文件
        for i in range(3):
            content = f"file {i}".encode()
            await storage_service.save_file(content, f"file_{i}.docx", ExportFormat.WORD)

        files = storage_service.list_files()

        assert len(files) == 3

    def test_list_files_with_pattern(self, storage_service):
        """测试带模式的文件列表"""
        # 创建不同类型的文件
        await storage_service.save_file(b"word", "test.docx", ExportFormat.WORD)
        await storage_service.save_file(b"pdf", "test.pdf", ExportFormat.PDF)

        docx_files = storage_service.list_files("*.docx")
        pdf_files = storage_service.list_files("*.pdf")

        assert len(docx_files) == 1
        assert len(pdf_files) == 1

    def test_cleanup_old_files(self, storage_service):
        """测试清理旧文件"""
        # 创建一个使用模拟时间的服务
        import time
        from datetime import datetime, timedelta

        # 创建文件
        for i in range(3):
            content = f"old file {i}".encode()
            path = storage_service.export_dir / f"old_{i}.docx"
            path.write_bytes(content)
            # 修改文件修改时间
            old_time = time.time() - (10 * 24 * 60 * 60)  # 10天前
            os.utime(path, (old_time, old_time))

        # 清理7天前的文件
        deleted = storage_service.cleanup_old_files(days=7)

        # 应该删除所有文件
        assert deleted == 3

        remaining_files = storage_service.list_files()
        assert len(remaining_files) == 0


class TestFileStorageServiceDirectoryCreation:
    """测试目录创建"""

    @pytest.fixture
    def new_temp_dir(self):
        """创建新的临时目录（不预先存在）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_creates_directory_if_not_exists(self, new_temp_dir):
        """测试自动创建不存在的目录"""
        assert not new_temp_dir.exists()

        service = FileStorageService(new_temp_dir)

        # 目录应该自动创建
        assert new_temp_dir.exists()
        assert new_temp_dir.is_dir()

        # 应该能保存文件
        content = b"test"
        path, _ = await service.save_file(content, "test.docx", ExportFormat.WORD)
        assert Path(path).exists()
