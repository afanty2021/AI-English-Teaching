"""
文档生成器模块 - AI英语教学系统

提供多种格式的文档生成功能：
- Word文档生成器
- PDF文档生成器 (使用 pdf_renderer_service)
- PPT文档生成器 (使用 ppt_export_service)
"""
from app.services.document_generators.word_generator import WordDocumentGenerator

__all__ = [
    "WordDocumentGenerator",
]
