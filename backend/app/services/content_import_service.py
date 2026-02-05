"""
内容导入服务 - AI英语教学系统
提供从JSON文件导入内容到数据库的功能
"""
import json
import uuid
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content, Vocabulary, ContentType, DifficultyLevel, ExamType
from app.utils.content_validators import get_content_validator, get_vocabulary_validator
from app.services.content_deduplication_service import (
    ContentDeduplicationService,
    VocabularyDeduplicationService
)
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)


class ContentImportService:
    """内容导入服务

    从JSON文件批量导入内容到数据库
    """

    def __init__(
        self,
        db: AsyncSession,
        vector_service: Optional[VectorService] = None,
        skip_duplicates: bool = True
    ):
        """初始化导入服务

        Args:
            db: 数据库会话
            vector_service: 向量服务实例
            skip_duplicates: 是否跳过重复内容
        """
        self.db = db
        self.vector_service = vector_service or VectorService()
        self.validator = get_content_validator()
        self.deduplication_service = ContentDeduplicationService(
            embedding_service=self.vector_service.embedding_service
        )
        self.skip_duplicates = skip_duplicates

    async def import_from_file(
        self,
        file_path: str,
        skip_duplicates: Optional[bool] = None
    ) -> Tuple[int, int]:
        """从JSON文件导入内容

        Args:
            file_path: JSON文件路径
            skip_duplicates: 是否跳过重复内容（None使用默认值）

        Returns:
            (成功数, 失败数)
        """
        skip = skip_duplicates if skip_duplicates is not None else self.skip_duplicates

        # 读取文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return 0, 1
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return 0, 1

        # 验证数据
        contents = data.get('contents', [])
        if not contents:
            logger.warning(f"No contents found in {file_path}")
            return 0, 0

        # 验证格式
        is_valid, errors = self.validator.validate_contents(contents)
        if not is_valid:
            logger.error(f"Validation errors: {errors}")
            return 0, len(contents)

        return await self.import_contents(contents, skip)

    async def import_contents(
        self,
        contents: List[dict],
        skip_duplicates: Optional[bool] = None
    ) -> Tuple[int, int]:
        """批量导入内容

        Args:
            contents: 内容列表
            skip_duplicates: 是否跳过重复内容

        Returns:
            (成功数, 失败数)
        """
        skip = skip_duplicates if skip_duplicates is not None else self.skip_duplicates

        if not contents:
            return 0, 0

        success, failed = 0, 0

        # 语义去重
        if skip:
            contents = await self.deduplication_service.filter_duplicates(contents)

        for item in contents:
            try:
                content = await self._import_single(item)
                success += 1
            except Exception as e:
                logger.error(f"Failed to import: {item.get('title', 'unknown')} - {e}")
                failed += 1

        await self.db.commit()
        return success, failed

    async def _import_single(self, data: dict) -> Content:
        """导入单条内容

        Args:
            data: 内容数据

        Returns:
            Content实例

        Raises:
            ValueError: 如果内容已存在或数据无效
        """
        # 检查是否已存在
        existing = await self.db.execute(
            select(Content).where(Content.title == data['title'])
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Content already exists: {data['title']}")

        # 转换枚举值
        content_type = ContentType(data['content_type'])
        difficulty_level = DifficultyLevel(data['difficulty_level'])
        exam_type = ExamType(data['exam_type']) if data.get('exam_type') else None

        # 创建Content对象
        content = Content(
            id=uuid.uuid4() if not data.get('id') else uuid.UUID(data['id']),
            title=data['title'],
            description=data.get('description'),
            content_type=content_type.value,
            difficulty_level=difficulty_level.value,
            exam_type=exam_type.value if exam_type else None,
            topic=data.get('topic'),
            tags=data.get('tags', []),
            content_text=data.get('content_text'),
            media_url=data.get('media_url'),
            duration=data.get('duration'),
            word_count=data.get('word_count'),
            knowledge_points=data.get('knowledge_points', []),
            is_featured=data.get('is_featured', False),
            is_published=data.get('is_published', True),
            sort_order=data.get('sort_order', 0),
            extra_metadata=data.get('extra_metadata'),
        )

        self.db.add(content)
        return content

    async def get_import_stats(self) -> dict:
        """获取导入统计信息

        Returns:
            统计信息字典
        """
        result = await self.db.execute(
            select(Content.content_type, func.count(Content.id))
            .group_by(Content.content_type)
        )

        stats = {}
        for content_type, count in result.all():
            stats[content_type] = count

        # 添加总计
        total = await self.db.execute(select(func.count(Content.id)))
        stats['_total'] = total.scalar()

        return stats


class VocabularyImportService:
    """词汇导入服务

    从JSON文件批量导入词汇到数据库
    """

    def __init__(
        self,
        db: AsyncSession,
        vector_service: Optional[VectorService] = None,
        skip_duplicates: bool = True
    ):
        """初始化导入服务

        Args:
            db: 数据库会话
            vector_service: 向量服务实例
            skip_duplicates: 是否跳过重复词汇
        """
        self.db = db
        self.vector_service = vector_service or VectorService()
        self.validator = get_vocabulary_validator()
        self.deduplication_service = VocabularyDeduplicationService(
            embedding_service=self.vector_service.embedding_service
        )
        self.skip_duplicates = skip_duplicates

    async def import_from_file(
        self,
        file_path: str,
        skip_duplicates: Optional[bool] = None
    ) -> Tuple[int, int]:
        """从JSON文件导入词汇

        Args:
            file_path: JSON文件路径
            skip_duplicates: 是否跳过重复词汇

        Returns:
            (成功数, 失败数)
        """
        skip = skip_duplicates if skip_duplicates is not None else self.skip_duplicates

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return 0, 1
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            return 0, 1

        vocabularies = data.get('vocabularies', [])
        if not vocabularies:
            logger.warning(f"No vocabularies found in {file_path}")
            return 0, 0

        return await self.import_vocabularies(vocabularies, skip)

    async def import_vocabularies(
        self,
        vocabularies: List[dict],
        skip_duplicates: Optional[bool] = None
    ) -> Tuple[int, int]:
        """批量导入词汇

        Args:
            vocabularies: 词汇列表
            skip_duplicates: 是否跳过重复词汇

        Returns:
            (成功数, 失败数)
        """
        skip = skip_duplicates if skip_duplicates is not None else self.skip_duplicates

        if not vocabularies:
            return 0, 0

        success, failed = 0, 0

        # 语义去重
        if skip:
            duplicates = await self.deduplication_service.find_duplicates(vocabularies)
            duplicate_indices = set()
            for group in duplicates:
                duplicate_indices.update(list(group)[1:])
            vocabularies = [v for i, v in enumerate(vocabularies) if i not in duplicate_indices]

        for item in vocabularies:
            try:
                vocabulary = await self._import_single(item)
                success += 1
            except Exception as e:
                logger.error(f"Failed to import: {item.get('word', 'unknown')} - {e}")
                failed += 1

        await self.db.commit()
        return success, failed

    async def _import_single(self, data: dict) -> Vocabulary:
        """导入单条词汇

        Args:
            data: 词汇数据

        Returns:
            Vocabulary实例
        """
        # 检查是否已存在
        existing = await self.db.execute(
            select(Vocabulary).where(Vocabulary.word == data['word'])
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Vocabulary already exists: {data['word']}")

        vocabulary = Vocabulary(
            id=uuid.uuid4() if not data.get('id') else uuid.UUID(data['id']),
            word=data['word'],
            phonetic=data.get('phonetic'),
            part_of_speech=data.get('part_of_speech', []),
            definitions=data.get('definitions', []),
            english_definition=data.get('english_definition'),
            examples=data.get('examples', []),
            etymology=data.get('etymology'),
            difficulty_level=data.get('difficulty_level'),
            frequency_level=data.get('frequency_level'),
            related_words=data.get('related_words', []),
            synonyms=data.get('synonyms', []),
            antonyms=data.get('antonyms', []),
            collocations=data.get('collocations', []),
            extra_data=data.get('extra_data'),
        )

        self.db.add(vocabulary)
        return vocabulary

    async def get_import_stats(self) -> dict:
        """获取导入统计信息

        Returns:
            统计信息字典
        """
        total = await self.db.execute(select(func.count(Vocabulary.id)))
        return {"total": total.scalar()}
