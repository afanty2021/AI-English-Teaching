"""
流式文档生成服务 - AI英语教学系统

支持大文件的边生成边传输，优化内存使用。
使用异步生成器实现流式输出。
"""

import logging
from io import BytesIO
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from app.models.lesson_plan import LessonPlan
from app.services.document_generators.pdf_generator import PDFDocumentGenerator
from app.services.document_generators.pptx_generator import PPTXDocumentGenerator
from app.services.document_generators.word_generator import WordDocumentGenerator

logger = logging.getLogger(__name__)


class StreamingDocumentService:
    """
    流式文档生成服务

    将教案数据转换为文档格式，并通过流式传输方式返回。
    适用于大文件导出场景，避免一次性占用大量内存。

    功能：
    - 流式生成 Word 文档
    - 流式生成 PDF 文档
    - 流式生成 PPTX 文档
    - 支持进度回调
    - 内存优化（分块传输）

    使用示例：
        ```python
        service = StreamingDocumentService()

        # 流式生成 Word 文档
        async for chunk in service.stream_generate_word(content, template_vars):
            # 处理数据块
            await send_to_client(chunk)

        # 带进度回调的 PDF 生成
        def progress_callback(percent: int):
            print(f"生成进度: {percent}%")

        async for chunk in service.stream_generate_pdf(
            lesson_plan,
            progress_callback=progress_callback
        ):
            await send_to_client(chunk)
        ```
    """

    # 默认块大小（8KB）
    DEFAULT_CHUNK_SIZE = 8192

    # 最小块大小（1KB）
    MIN_CHUNK_SIZE = 1024

    # 最大块大小（1MB）
    MAX_CHUNK_SIZE = 1024 * 1024

    def __init__(self):
        """初始化流式文档生成服务"""
        self.word_generator = WordDocumentGenerator()
        self.pdf_generator = PDFDocumentGenerator()
        self.pptx_generator = PPTXDocumentGenerator()

    async def stream_generate_word(
        self,
        content: Dict[str, Any],
        template_vars: Dict[str, Any],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> AsyncIterator[bytes]:
        """
        流式生成 Word 文档

        Args:
            content: 教案内容数据
            template_vars: 模板变量
            chunk_size: 数据块大小（字节），范围 1024-1048576
            progress_callback: 进度回调函数，参数为百分比（0-100）

        Yields:
            bytes: 文档数据块

        Raises:
            ValueError: 如果内容数据无效或块大小超出范围
            Exception: 如果文档生成失败
        """
        try:
            # 验证块大小
            self._validate_chunk_size(chunk_size)

            # 验证必要字段
            if not content.get("title"):
                raise ValueError("教案标题不能为空")

            # 报告进度开始
            if progress_callback:
                progress_callback(0)

            # 生成完整文档到内存
            doc_bytes = self.word_generator.generate(content, template_vars)

            # 报告进度完成
            if progress_callback:
                progress_callback(100)

            # 流式传输文档数据
            total_size = len(doc_bytes)
            bytes_sent = 0

            # 创建内存视图以高效分块
            doc_stream = BytesIO(doc_bytes)

            while True:
                chunk = doc_stream.read(chunk_size)
                if not chunk:
                    break

                bytes_sent += len(chunk)
                yield chunk

                # 更新进度
                if progress_callback and total_size > 0:
                    percent = int((bytes_sent / total_size) * 100)
                    progress_callback(percent)

            logger.info(
                f"Word文档流式生成完成: {content.get('title')} "
                f"({total_size} bytes, {len(doc_bytes) // chunk_size + 1} chunks)"
            )

        except Exception as e:
            logger.error(f"Word文档流式生成失败: {str(e)}")
            raise Exception(f"Word文档流式生成失败: {str(e)}") from e

    async def stream_generate_pdf(
        self,
        lesson_plan: LessonPlan,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        include_sections: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> AsyncIterator[bytes]:
        """
        流式生成 PDF 文档

        Args:
            lesson_plan: 教案数据模型
            chunk_size: 数据块大小（字节）
            include_sections: 要包含的章节列表（None 表示全部）
            progress_callback: 进度回调函数

        Yields:
            bytes: 文档数据块

        Raises:
            ValueError: 如果教案数据无效或块大小超出范围
            Exception: 如果文档生成失败
        """
        try:
            # 验证块大小
            self._validate_chunk_size(chunk_size)

            # 验证教案
            if not lesson_plan or not lesson_plan.title:
                raise ValueError("教案标题不能为空")

            # 报告进度开始
            if progress_callback:
                progress_callback(0)
                progress_callback(10)  # 开始生成

            # 生成完整文档到内存
            pdf_bytes = await self.pdf_generator.generate_from_lesson_plan(
                lesson_plan,
                include_sections=include_sections,
            )

            # 报告生成完成
            if progress_callback:
                progress_callback(90)

            # 流式传输文档数据
            total_size = len(pdf_bytes)
            bytes_sent = 0

            pdf_stream = BytesIO(pdf_bytes)

            while True:
                chunk = pdf_stream.read(chunk_size)
                if not chunk:
                    break

                bytes_sent += len(chunk)
                yield chunk

                # 更新进度
                if progress_callback and total_size > 0:
                    percent = int(10 + (bytes_sent / total_size) * 90)
                    progress_callback(percent)

            # 报告完成
            if progress_callback:
                progress_callback(100)

            logger.info(
                f"PDF文档流式生成完成: {lesson_plan.title} "
                f"({total_size} bytes, {len(pdf_bytes) // chunk_size + 1} chunks)"
            )

        except Exception as e:
            logger.error(f"PDF文档流式生成失败: {str(e)}")
            raise Exception(f"PDF文档流式生成失败: {str(e)}") from e

    async def stream_generate_pptx(
        self,
        content: Dict[str, Any],
        template_vars: Dict[str, Any],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> AsyncIterator[bytes]:
        """
        流式生成 PPTX 文档

        Args:
            content: 教案内容数据
            template_vars: 模板变量
            chunk_size: 数据块大小（字节）
            progress_callback: 进度回调函数

        Yields:
            bytes: 文档数据块

        Raises:
            ValueError: 如果内容数据无效或块大小超出范围
            Exception: 如果文档生成失败
        """
        try:
            # 验证块大小
            self._validate_chunk_size(chunk_size)

            # 验证必要字段
            if not content.get("title"):
                raise ValueError("教案标题不能为空")

            # 报告进度开始
            if progress_callback:
                progress_callback(0)

            # 生成完整文档到内存
            ppt_bytes = self.pptx_generator.generate(content, template_vars)

            # 报告进度完成
            if progress_callback:
                progress_callback(100)

            # 流式传输文档数据
            total_size = len(ppt_bytes)
            bytes_sent = 0

            ppt_stream = BytesIO(ppt_bytes)

            while True:
                chunk = ppt_stream.read(chunk_size)
                if not chunk:
                    break

                bytes_sent += len(chunk)
                yield chunk

                # 更新进度
                if progress_callback and total_size > 0:
                    percent = int((bytes_sent / total_size) * 100)
                    progress_callback(percent)

            logger.info(
                f"PPTX文档流式生成完成: {content.get('title')} "
                f"({total_size} bytes, {len(ppt_bytes) // chunk_size + 1} chunks)"
            )

        except Exception as e:
            logger.error(f"PPTX文档流式生成失败: {str(e)}")
            raise Exception(f"PPTX文档流式生成失败: {str(e)}") from e

    def _validate_chunk_size(self, chunk_size: int) -> None:
        """
        验证块大小是否在有效范围内

        Args:
            chunk_size: 块大小（字节）

        Raises:
            ValueError: 如果块大小超出范围
        """
        if chunk_size < self.MIN_CHUNK_SIZE:
            raise ValueError(
                f"块大小不能小于 {self.MIN_CHUNK_SIZE} 字节，当前值: {chunk_size}"
            )
        if chunk_size > self.MAX_CHUNK_SIZE:
            raise ValueError(
                f"块大小不能大于 {self.MAX_CHUNK_SIZE} 字节，当前值: {chunk_size}"
            )


# ========== 模块级便捷函数 ==========


def get_streaming_document_service() -> StreamingDocumentService:
    """
    获取流式文档生成服务实例

    Returns:
        StreamingDocumentService: 流式文档生成服务实例
    """
    return StreamingDocumentService()
