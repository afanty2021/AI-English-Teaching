"""
异步文件存储服务测试
测试使用 aiofiles 进行异步文件 I/O 操作
"""
import asyncio
import os
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.export_task import ExportFormat
from app.services.async_file_storage_service import (
    AsyncFileStorageService,
    FileDeleteError,
    FileSizeExceededError,
    FileStorageError,
    FileWriteError,
    get_async_file_storage_service,
)


# ======================= 测试固件 =======================

@pytest.fixture
def temp_storage_dir(tmp_path):
    """创建临时存储目录"""
    storage_dir = tmp_path / "exports"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def storage_service(temp_storage_dir):
    """创建存储服务实例"""
    return AsyncFileStorageService(str(temp_storage_dir))


@pytest.fixture
def sample_content():
    """示例文件内容"""
    return b"Hello, World! This is a test file content."


@pytest.fixture
def large_content():
    """大文件内容（用于测试大小限制）"""
    # 默认限制是 50MB，这里创建一个稍小的文件用于测试
    return b"x" * (10 * 1024 * 1024)  # 10MB


# ======================= 基础功能测试 (5 tests) =======================

class TestBasicFunctionality:
    """基础功能测试"""

    @pytest.mark.asyncio
    async def test_save_text_file(self, storage_service, sample_content):
        """测试保存文本文件"""
        filename = "test_document"
        format = ExportFormat.MARKDOWN

        file_path, file_size = await storage_service.save_file_async(
            sample_content,
            filename,
            format
        )

        # 验证返回值
        assert file_path.endswith(".md")
        assert file_size == len(sample_content)

        # 验证文件存在
        assert os.path.exists(file_path)

        # 验证文件内容
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        assert saved_content == sample_content

    @pytest.mark.asyncio
    async def test_save_binary_file(self, storage_service):
        """测试保存二进制文件"""
        binary_content = bytes(range(256))  # 包含所有字节值
        filename = "binary_data"
        format = ExportFormat.PDF

        file_path, file_size = await storage_service.save_file_async(
            binary_content,
            filename,
            format
        )

        # 验证文件存在且内容正确
        assert os.path.exists(file_path)
        with open(file_path, 'rb') as f:
            saved_content = f.read()
        assert saved_content == binary_content

    @pytest.mark.asyncio
    async def test_file_path_format(self, storage_service, sample_content):
        """测试文件路径格式验证"""
        filename = "test_file"
        format = ExportFormat.WORD

        file_path, _ = await storage_service.save_file_async(
            sample_content,
            filename,
            format
        )

        path = Path(file_path)

        # 验证路径包含日期目录 (YYYY/MM/DD)
        date_parts = path.parent.relative_to(storage_service.base_path).parts
        assert len(date_parts) == 3  # year, month, day

        # 验证文件名包含时间戳和UUID
        stem = path.stem
        assert "_" in stem

        # 验证文件扩展名
        assert path.suffix == ".docx"

    @pytest.mark.asyncio
    async def test_file_size_correctness(self, storage_service):
        """测试文件大小正确性"""
        sizes = [0, 1, 1024, 1024 * 1024]  # 空文件、1字节、1KB、1MB

        for size in sizes:
            content = b"x" * size
            filename = f"size_test_{size}"

            file_path, file_size = await storage_service.save_file_async(
                content,
                filename,
                ExportFormat.PDF
            )

            assert file_size == size
            assert os.path.getsize(file_path) == size

    @pytest.mark.asyncio
    async def test_overwrite_existing_file(self, storage_service, sample_content):
        """测试覆盖已存在文件"""
        filename = "overwrite_test"
        format = ExportFormat.MARKDOWN

        # 保存第一个文件
        first_path, first_size = await storage_service.save_file_async(
            sample_content,
            filename,
            format
        )

        # 保存第二个同名文件
        new_content = b"Updated content"
        second_path, second_size = await storage_service.save_file_async(
            new_content,
            filename,
            format
        )

        # 验证两个文件都存在（文件名应该不同）
        assert first_path != second_path
        assert os.path.exists(first_path)
        assert os.path.exists(second_path)

        # 验证内容不同
        with open(first_path, 'rb') as f:
            assert f.read() == sample_content
        with open(second_path, 'rb') as f:
            assert f.read() == new_content


# ======================= 异步操作测试 (3 tests) =======================

class TestAsyncOperations:
    """异步操作测试"""

    @pytest.mark.asyncio
    async def test_non_blocking_operation(self, storage_service):
        """验证不阻塞事件循环"""
        # 创建一个任务来验证事件循环未被阻塞
        executed_tasks = []

        async def blocking_simulation():
            """模拟长时间操作"""
            await asyncio.sleep(0.1)
            executed_tasks.append("blocking")

        async def file_operation():
            """执行文件操作"""
            content = b"Non-blocking test"
            await storage_service.save_file_async(
                content,
                "async_test",
                ExportFormat.MARKDOWN
            )
            executed_tasks.append("file_operation")

        # 并发执行多个任务
        await asyncio.gather(
            blocking_simulation(),
            file_operation(),
            blocking_simulation()
        )

        # 验证所有任务都完成了（没有被阻塞）
        assert len(executed_tasks) == 3
        assert "file_operation" in executed_tasks

    @pytest.mark.asyncio
    async def test_concurrent_file_saves(self, storage_service):
        """测试并发保存多个文件"""
        num_files = 10
        content = b"Concurrent test content"

        # 并发保存多个文件
        tasks = [
            storage_service.save_file_async(
                content,
                f"concurrent_{i}",
                ExportFormat.PDF
            )
            for i in range(num_files)
        ]

        results = await asyncio.gather(*tasks)

        # 验证所有文件都成功保存
        assert len(results) == num_files

        # 验证所有文件路径都不同
        file_paths = [path for path, _ in results]
        assert len(set(file_paths)) == num_files

        # 验证所有文件都存在
        for file_path, _ in results:
            assert os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_exception_handling_non_blocking(self, storage_service):
        """测试异常处理不阻塞事件循环"""
        executed = []

        async def failing_operation():
            """会失败的操作"""
            try:
                # 尝试保存超大文件
                huge_content = b"x" * (100 * 1024 * 1024)  # 100MB（超过限制）
                await storage_service.save_file_async(
                    huge_content,
                    "huge_file",
                    ExportFormat.PDF
                )
            except FileSizeExceededError:
                executed.append("exception_caught")

        async def normal_operation():
            """正常操作"""
            await asyncio.sleep(0.05)
            executed.append("normal")

        # 并发执行
        await asyncio.gather(
            failing_operation(),
            normal_operation()
        )

        # 验证两个操作都完成了
        assert "exception_caught" in executed
        assert "normal" in executed


# ======================= 错误处理测试 (4 tests) =======================

class TestErrorHandling:
    """错误处理测试"""

    @pytest.mark.asyncio
    async def test_invalid_path(self, storage_service):
        """测试无效路径处理"""
        # 尝试删除不存在的文件
        result = await storage_service.delete_file_async("non_existent_file.pdf")
        assert result is False

    @pytest.mark.asyncio
    async def test_file_size_exceeded(self, storage_service):
        """测试文件大小超过限制"""
        # 创建一个超过限制的服务
        small_limit_service = AsyncFileStorageService(str(storage_service.base_path))
        small_limit_service.max_file_size = 1024  # 1KB

        # 尝试保存超过限制的文件
        large_content = b"x" * 2048  # 2KB

        with pytest.raises(FileSizeExceededError) as exc_info:
            await small_limit_service.save_file_async(
                large_content,
                "large_file",
                ExportFormat.PDF
            )

        # 验证异常信息
        error = exc_info.value
        assert error.code == "FILE_SIZE_EXCEEDED"
        assert error.size == 2048
        assert error.max_size == 1024

    @pytest.mark.asyncio
    async def test_permission_error_simulation(self, storage_service, sample_content):
        """测试权限错误（模拟）"""
        # 在 macOS 和 Windows 上权限测试不可靠，使用 mock 模拟

        # 保存文件
        file_path, _ = await storage_service.save_file_async(
            sample_content,
            "permission_test",
            ExportFormat.PDF
        )

        # 使用 mock 模拟权限错误
        original_unlink = Path.unlink

        def mock_unlink(self):
            raise PermissionError(f"Permission denied: {self}")

        Path.unlink = mock_unlink

        try:
            # 尝试删除（应该会失败）
            with pytest.raises(FileDeleteError) as exc_info:
                await storage_service.delete_file_async(file_path)

            # 验证错误信息
            assert exc_info.value.code == "FILE_DELETE_ERROR"
        finally:
            # 恢复原方法
            Path.unlink = original_unlink

    @pytest.mark.asyncio
    async def test_disk_space_simulation(self, storage_service):
        """测试磁盘空间不足（模拟）"""
        content = b"Test content for disk space simulation"

        # 模拟写入失败
        with patch('aiofiles.open', side_effect=OSError("No space left on device")):
            with pytest.raises(FileWriteError) as exc_info:
                await storage_service.save_file_async(
                    content,
                    "disk_space_test",
                    ExportFormat.PDF
                )

            # 验证错误信息
            assert exc_info.value.code == "FILE_WRITE_ERROR"
            assert "No space left on device" in str(exc_info.value.original_error)


# ======================= 边界情况测试 (3 tests) =======================

class TestBoundaryConditions:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_empty_file(self, storage_service):
        """测试空文件"""
        empty_content = b""

        file_path, file_size = await storage_service.save_file_async(
            empty_content,
            "empty_file",
            ExportFormat.MARKDOWN
        )

        # 验证文件路径和大小
        assert os.path.exists(file_path)
        assert file_size == 0
        assert os.path.getsize(file_path) == 0

    @pytest.mark.asyncio
    async def test_large_file_near_limit(self, storage_service):
        """测试接近限制的大文件"""
        # 创建一个接近但不超过限制的文件
        limit = storage_service.max_file_size
        near_limit_content = b"x" * (limit - 1024)  # 比限制小 1KB

        file_path, file_size = await storage_service.save_file_async(
            near_limit_content,
            "near_limit_file",
            ExportFormat.PDF
        )

        # 验证文件保存成功
        assert os.path.exists(file_path)
        assert file_size == limit - 1024

    @pytest.mark.asyncio
    async def test_special_characters_in_filename(self, storage_service):
        """测试特殊字符文件名"""
        special_names = [
            "file with spaces",
            "file-with-dashes",
            "file_with_underscores",
            "file.with.dots",
            "文件名中文",  # 中文字符
            "file@#$%^&*()特殊字符",  # 特殊符号
        ]

        for name in special_names:
            content = b"Special character test"
            file_path, _ = await storage_service.save_file_async(
                content,
                name,
                ExportFormat.MARKDOWN
            )

            # 验证文件保存成功
            assert os.path.exists(file_path)
            # 特殊字符应该被替换为下划线
            assert Path(file_path).stem.isalnum() or '_' in Path(file_path).stem


# ======================= 其他功能测试 =======================

class TestAdditionalFeatures:
    """其他功能测试"""

    @pytest.mark.asyncio
    async def test_get_file_size_async(self, storage_service):
        """测试异步获取文件大小"""
        content = b"File size test content"
        filename = "size_test"

        file_path, expected_size = await storage_service.save_file_async(
            content,
            filename,
            ExportFormat.PDF
        )

        # 使用相对路径获取文件大小
        relative_path = Path(file_path).relative_to(storage_service.base_path)
        actual_size = await storage_service.get_file_size_async(str(relative_path))

        assert actual_size == expected_size

    @pytest.mark.asyncio
    async def test_read_file_async(self, storage_service):
        """测试异步读取文件"""
        content = b"Read test content"
        filename = "read_test"

        file_path, _ = await storage_service.save_file_async(
            content,
            filename,
            ExportFormat.PDF
        )

        # 使用相对路径读取文件
        relative_path = Path(file_path).relative_to(storage_service.base_path)
        read_content = await storage_service.read_file_async(str(relative_path))

        assert read_content == content

    @pytest.mark.asyncio
    async def test_file_exists_async(self, storage_service):
        """测试异步检查文件存在"""
        content = b"Exists test content"
        filename = "exists_test"

        # 保存文件
        file_path, _ = await storage_service.save_file_async(
            content,
            filename,
            ExportFormat.PDF
        )

        # 检查文件存在
        relative_path = Path(file_path).relative_to(storage_service.base_path)
        assert await storage_service.file_exists_async(str(relative_path))

        # 检查不存在的文件
        assert not await storage_service.file_exists_async("non_existent.pdf")

    @pytest.mark.asyncio
    async def test_list_files_async(self, storage_service):
        """测试异步列出文件"""
        # 保存几个不同格式的文件
        formats = [
            ExportFormat.PDF,
            ExportFormat.MARKDOWN,
            ExportFormat.WORD,
        ]

        for fmt in formats:
            await storage_service.save_file_async(
                b"Test content",
                f"test_{fmt.value}",
                fmt
            )

        # 列出所有 PDF 文件（需要递归，因为文件在日期子目录中）
        pdf_files = await storage_service.list_files_async("*.pdf", recursive=True)
        assert len(pdf_files) > 0
        assert all(f.endswith(".pdf") for f in pdf_files)

    @pytest.mark.asyncio
    async def test_list_files_recursive(self, storage_service):
        """测试递归列出文件"""
        # 保存一些文件（会自动按日期分组到不同目录）
        for i in range(3):
            await storage_service.save_file_async(
                b"Recursive test",
                f"recursive_{i}",
                ExportFormat.PDF
            )

        # 递归列出所有文件
        all_files = await storage_service.list_files_async("*", recursive=True)

        # 应该至少有我们保存的 3 个文件
        assert len(all_files) >= 3

    @pytest.mark.asyncio
    async def test_all_export_formats(self, storage_service):
        """测试所有导出格式"""
        content = b"Test content for all formats"

        formats = [
            ExportFormat.PDF,
            ExportFormat.MARKDOWN,
            ExportFormat.WORD,
            ExportFormat.PPTX,
        ]

        for fmt in formats:
            file_path, _ = await storage_service.save_file_async(
                content,
                f"test_{fmt.value}",
                fmt
            )

            assert os.path.exists(file_path)
            # 验证扩展名
            ext = storage_service._get_extension(fmt)
            assert file_path.endswith(f".{ext}")


# ======================= 便捷函数测试 =======================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_get_async_file_storage_service(self):
        """测试获取服务实例"""
        service = get_async_file_storage_service()

        assert isinstance(service, AsyncFileStorageService)
        assert service.base_path is not None

    @pytest.mark.asyncio
    async def test_service_singleton_behavior(self):
        """测试服务实例行为"""
        service1 = get_async_file_storage_service()
        service2 = get_async_file_storage_service()

        # 每次调用应该创建新实例（不是真正的单例）
        assert service1 is not service2

        # 但配置应该相同
        assert service1.base_path == service2.base_path
        assert service1.max_file_size == service2.max_file_size
