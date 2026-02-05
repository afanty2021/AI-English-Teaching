"""
内容语义去重服务 - AI英语教学系统
使用向量相似度检测重复内容
"""
import asyncio
import logging
from typing import List, Set, Tuple, Optional

from app.services.vector_service import VectorService
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ContentDeduplicationService:
    """内容语义去重服务

    使用向量相似度检测语义重复的内容
    """

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        similarity_threshold: float = 0.85
    ):
        """初始化去重服务

        Args:
            embedding_service: 嵌入服务实例
            similarity_threshold: 相似度阈值（0-1），超过此值认为重复
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.similarity_threshold = similarity_threshold

    async def find_duplicates(
        self,
        texts: List[str],
        progress_callback: Optional[callable] = None
    ) -> List[Set[int]]:
        """查找语义重复的内容

        Args:
            texts: 要检查的文本列表
            progress_callback: 进度回调函数

        Returns:
            重复内容索引集合列表，例如 [{0, 3, 5}, {1, 2}]
        """
        if not texts:
            return []

        total = len(texts)
        duplicates: List[Set[int]] = []
        processed = set()

        # 生成所有文本的向量
        if progress_callback:
            progress_callback("embedding", 0, total, "Generating embeddings...")

        vectors = await self.embedding_service.batch_generate_embeddings(texts)

        if progress_callback:
            progress_callback("comparing", 0, total, "Comparing texts...")

        # 逐一比较向量
        for i, vec_i in enumerate(vectors):
            if i in processed:
                continue

            current_group = {i}
            for j in range(i + 1, len(vectors)):
                if j in processed:
                    continue

                similarity = self._cosine_similarity(vec_i, vectors[j])
                if similarity >= self.similarity_threshold:
                    current_group.add(j)
                    processed.add(j)

                # 更新进度
                if progress_callback:
                    current = i * total + j
                    total_comparisons = total * (total - 1) // 2
                    progress_callback("comparing", current, total_comparisons, f"Comparing {i} vs {j}")

            if len(current_group) > 1:
                duplicates.append(current_group)
            processed.add(i)

        if progress_callback:
            progress_callback("complete", total, total, f"Found {len(duplicates)} duplicate groups")

        return duplicates

    async def filter_duplicates(
        self,
        contents: List[dict],
        progress_callback: Optional[callable] = None
    ) -> List[dict]:
        """过滤重复内容，保留第一条

        Args:
            contents: 内容列表
            progress_callback: 进度回调函数

        Returns:
            去重后的内容列表
        """
        if not contents:
            return contents

        # 提取用于比较的文本
        texts = [self._extract_text(c) for c in contents]

        # 查找重复
        duplicates = await self.find_duplicates(texts, progress_callback)

        # 收集所有重复的索引
        duplicate_indices = set()
        for group in duplicates:
            # 只保留第一条
            duplicate_indices.update(list(group)[1:])

        # 过滤结果
        result = [c for i, c in enumerate(contents) if i not in duplicate_indices]

        if duplicate_indices:
            logger.info(f"Filtered {len(duplicate_indices)} duplicate contents")

        return result

    def _extract_text(self, content: dict) -> str:
        """提取用于向量化的文本

        Args:
            content: 内容字典

        Returns:
            用于比较的文本字符串
        """
        parts = [content.get('title', '')]

        if content.get('description'):
            parts.append(content['description'])

        if content.get('content_text'):
            # 限制长度以避免向量生成超时
            parts.append(content['content_text'][:500])

        if content.get('topic'):
            parts.append(f"Topic: {content['topic']}")

        if content.get('tags'):
            parts.append(f"Tags: {', '.join(content['tags'])}")

        return ' '.join(parts)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度

        Args:
            vec1: 第一个向量
            vec2: 第二个向量

        Returns:
            余弦相似度 (0-1)
        """
        if not vec1 or not vec2:
            return 0.0

        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    async def check_duplicate_with_existing(
        self,
        new_contents: List[dict],
        existing_contents: List[dict],
        progress_callback: Optional[callable] = None
    ) -> List[bool]:
        """检查新内容是否与已有内容重复

        Args:
            new_contents: 新内容列表
            existing_contents: 已有内容列表
            progress_callback: 进度回调函数

        Returns:
            布尔列表，True表示与已有内容重复
        """
        if not new_contents or not existing_contents:
            return [False] * len(new_contents)

        # 提取文本
        new_texts = [self._extract_text(c) for c in new_contents]
        existing_texts = [self._extract_text(c) for c in existing_contents]

        # 生成向量
        if progress_callback:
            progress_callback("embedding", 0, len(new_texts) + len(existing_texts), "Generating embeddings...")

        new_vectors = await self.embedding_service.batch_generate_embeddings(new_texts)
        existing_vectors = await self.embedding_service.batch_generate_embeddings(existing_texts)

        # 比较
        results = []
        for new_vec in new_vectors:
            is_duplicate = False
            for existing_vec in existing_vectors:
                if self._cosine_similarity(new_vec, existing_vec) >= self.similarity_threshold:
                    is_duplicate = True
                    break
            results.append(is_duplicate)

        return results


class VocabularyDeduplicationService:
    """词汇语义去重服务"""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        similarity_threshold: float = 0.90
    ):
        """初始化去重服务

        Args:
            embedding_service: 嵌入服务实例
            similarity_threshold: 相似度阈值
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.similarity_threshold = similarity_threshold

    async def find_duplicates(self, vocabularies: List[dict]) -> List[Set[int]]:
        """查找语义重复的词汇

        Args:
            vocabularies: 词汇列表

        Returns:
            重复词汇索引集合列表
        """
        if not vocabularies:
            return []

        # 提取词汇文本
        texts = [self._extract_text(v) for v in vocabularies]

        # 生成向量
        vectors = await self.embedding_service.batch_generate_embeddings(texts)

        # 比较
        duplicates: List[Set[int]] = []
        processed = set()

        for i, vec_i in enumerate(vectors):
            if i in processed:
                continue

            current_group = {i}
            for j in range(i + 1, len(vectors)):
                if j in processed:
                    continue

                similarity = self._cosine_similarity(vec_i, vectors[j])
                if similarity >= self.similarity_threshold:
                    current_group.add(j)
                    processed.add(j)

            if len(current_group) > 1:
                duplicates.append(current_group)
            processed.add(i)

        return duplicates

    def _extract_text(self, vocabulary: dict) -> str:
        """提取用于向量化的文本"""
        parts = [vocabulary.get('word', '')]

        if vocabulary.get('definitions'):
            parts.append(' '.join(vocabulary['definitions'][:2]))

        if vocabulary.get('english_definition'):
            parts.append(vocabulary['english_definition'])

        return ' '.join(parts)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0

        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)


# 创建全局单例
_content_deduplication_service: Optional[ContentDeduplicationService] = None


def get_content_deduplication_service(
    similarity_threshold: float = 0.85
) -> ContentDeduplicationService:
    """获取内容去重服务单例"""
    global _content_deduplication_service
    if _content_deduplication_service is None:
        _content_deduplication_service = ContentDeduplicationService(
            similarity_threshold=similarity_threshold
        )
    return _content_deduplication_service
