"""
文件存储服务测试
"""
import asyncio
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

    def test_save_file_success(self, storage_service):
        """测试成功保存文件"""
        content = b"test content for file storage"
        path, size = storage_service.save_file(
            content, "test.docx", ExportFormat.WORD
        )

        assert Path(path).exists()
        assert size == len(content)

    def test_save_file_with_unique_name(self, storage_service):
        """测试文件名唯一性"""
        content = b"test content"
        filename = "lesson.docx"

        path1, _ = storage_service.save_file(content, filename, ExportFormat.WORD)
        path2, _ = storage_service.save_file(content, filename, ExportFormat.WORD)

        # 路径应该不同
        assert path1 != path2

        # 文件应该存在
        assert Path(path1).exists()
        assert Path(path2).exists()

    def test_save_file_with_extension(self, storage_service):
        """测试自动添加扩展名"""
        content = b"test content"

        path, _ = storage_service.save_file(content, "test", ExportFormat.PDF)

        assert path.endswith(".pdf")
        assert Path(path).exists()

    def test_save_file_size_limit(self, storage_service, mock_settings):
        """测试文件大小限制"""
        # 创建一个使用较小限制的服务
        small_service = FileStorageService(Path("/tmp/small_exports"))
        # 模拟设置
        with patch.object(small_service._async_storage, 'max_file_size', 100):  # 100 bytes
            large_content = b"x" * 101  # 101 bytes

            with pytest.raises(Exception) as exc_info:
                small_service.save_file(
                    large_content, "test.docx", ExportFormat.WORD
                )

            assert exc_info.value.status_code == 413

    def test_get_file_success(self, storage_service):
        """测试成功读取文件"""
        content = b"test file content for reading"
        save_path, _ = storage_service.save_file(
            content, "read_test.docx", ExportFormat.WORD
        )

        read_content = storage_service.get_file(save_path)

        assert read_content == content

    def test_get_file_not_found(self, storage_service):
        """测试文件不存在"""
        with pytest.raises(Exception) as exc_info:
            storage_service.get_file("/nonexistent/path/file.docx")

        assert exc_info.value.status_code == 404

    def test_delete_file_success(self, storage_service):
        """测试成功删除文件"""
        content = b"file to delete"
        path, _ = storage_service.save_file(content, "delete_test.docx", ExportFormat.WORD)

        assert Path(path).exists()

        result = storage_service.delete_file(path)
        assert result is True
        assert not Path(path).exists()

    def test_delete_nonexistent_file(self, storage_service):
        """测试删除不存在的文件"""
        result = storage_service.delete_file("/nonexistent/file.docx")
        assert result is False

    def test_file_exists_true(self, storage_service, temp_dir):
        """测试文件存在检查（存在）"""
        content = b"test content"
        path = temp_dir / "exists_test.docx"
        path.write_bytes(content)

        assert storage_service.file_exists(str(path)) is True

    def test_file_exists_false(self, storage_service):
        """测试文件存在检查（不存在）"""
        assert storage_service.file_exists("/nonexistent/file.docx") is False

    def test_get_file_size(self, storage_service, temp_dir):
        """测试获取文件大小"""
        content = b"test file size content"
        path = temp_dir / "size_test.docx"
        expected_size = len(content)
        path.write_bytes(content)

        size = storage_service.get_file_size(str(path))

        assert size == expected_size

    def test_get_extension(self, storage_service):
        """测试扩展名映射"""
        # _get_extension 现在是 AsyncFileStorageService 的内部方法
        assert storage_service._async_storage._get_extension(ExportFormat.WORD) == "docx"
        assert storage_service._async_storage._get_extension(ExportFormat.PDF) == "pdf"
        assert storage_service._async_storage._get_extension(ExportFormat.PPTX) == "pptx"
        assert storage_service._async_storage._get_extension(ExportFormat.MARKDOWN) == "md"

    def test_list_files(self, storage_service):
        """测试列出文件"""
        # 创建一些测试文件
        for i in range(3):
            content = f"file {i}".encode()
            storage_service.save_file(content, f"file_{i}.docx", ExportFormat.WORD)

        # 注意：AsyncFileStorageService 将文件保存在按日期组织的子目录中
        # 需要使用递归搜索来找到所有文件
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            files = loop.run_until_complete(
                storage_service._async_storage.list_files_async("*.docx", recursive=True)
            )
        finally:
            loop.close()

        # 至少应该有我们创建的 3 个文件
        assert len(files) >= 3

    def test_list_files_with_pattern(self, storage_service):
        """测试带模式的文件列表"""
        # 创建不同类型的文件
        storage_service.save_file(b"word", "test.docx", ExportFormat.WORD)
        storage_service.save_file(b"pdf", "test.pdf", ExportFormat.PDF)

        # 注意：AsyncFileStorageService 将文件保存在按日期组织的子目录中
        # 需要使用递归搜索来找到所有文件
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            docx_files = loop.run_until_complete(
                storage_service._async_storage.list_files_async("*.docx", recursive=True)
            )
            pdf_files = loop.run_until_complete(
                storage_service._async_storage.list_files_async("*.pdf", recursive=True)
            )
        finally:
            loop.close()

        # 至少应该有我们创建的文件
        assert len(docx_files) >= 1
        assert len(pdf_files) >= 1

    def test_cleanup_old_files(self, storage_service):
        """测试清理旧文件"""
        # 注意：新的 AsyncFileStorageService 没有 cleanup_old_files 方法
        # 这个功能已经不再支持，标记为跳过
        pytest.skip("cleanup_old_files 方法在 AsyncFileStorageService 中不再支持")


class TestFileStorageServiceDirectoryCreation:
    """测试目录创建"""

    @pytest.fixture
    def temp_dir_for_test(self):
        """创建临时目录用于测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def new_temp_dir(self, temp_dir_for_test):
        """使用一个不存在的子目录"""
        # 在临时目录中创建一个不存在的子目录路径
        non_existent = temp_dir_for_test / "non_existent_subdir"
        # 确保它不存在
        if non_existent.exists():
            non_existent.rmdir()
        return non_existent

    def test_creates_directory_if_not_exists(self, new_temp_dir):
        """测试自动创建不存在的目录"""
        # 注意：新的 AsyncFileStorageService 只在保存文件时创建目录
        # 而不是在初始化时创建
        assert not new_temp_dir.exists()

        service = FileStorageService(new_temp_dir)

        # 目录不会在初始化时创建
        # 但保存文件时会自动创建（包括子目录）
        content = b"test"
        path, _ = service.save_file(content, "test.docx", ExportFormat.WORD)
        assert Path(path).exists()

        # 验证目录结构被创建
        # AsyncFileStorageService 按日期组织文件，如 YYYY/MM/DD/
        assert new_temp_dir.exists()
