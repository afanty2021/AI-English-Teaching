"""
向量搜索服务 - AI英语教学系统
使用Qdrant向量数据库进行相似度搜索
"""
import uuid
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import AsyncQdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models import Content, Vocabulary
from app.services.embedding_service import get_embedding_service


class VectorService:
    """
    向量搜索服务类
    提供向量存储、检索、相似度搜索等功能
    """

    # 集合名称
    CONTENT_COLLECTION = "english_content"
    VOCABULARY_COLLECTION = "english_vocabulary"

    def __init__(self):
        """初始化向量服务"""
        self.client: Optional[AsyncQdrantClient] = None
        self.embedding_service = get_embedding_service()
        self.vector_size = settings.QDRANT_VECTOR_SIZE

    def _get_client(self) -> AsyncQdrantClient:
        """获取Qdrant客户端（懒加载）"""
        if self.client is None:
            self.client = AsyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
            )
        return self.client

    async def ensure_collection(
        self,
        collection_name: str = None,
        vector_size: int = None
    ) -> None:
        """
        确保集合存在，不存在则创建

        Args:
            collection_name: 集合名称（默认使用english_content）
            vector_size: 向量维度（默认使用配置的值）

        Note:
            使用COSINE距离度量和优化的索引参数
        """
        client = self._get_client()
        collection = collection_name or self.CONTENT_COLLECTION
        size = vector_size or self.vector_size

        try:
            # 检查集合是否存在
            await client.get_collection(collection)
        except (UnexpectedResponse, Exception):
            # 集合不存在，创建新集合
            await client.create_collection(
                collection_name=collection,
                vectors_config=models.VectorParams(
                    size=size,
                    distance=models.Distance.COSINE,
                    # 优化参数
                    hnsw_config=models.HnswConfigDiff(
                        m=16,  # 每个节点的最大连接数
                        ef_construct=100,  # 构建索引时的搜索范围
                    ),
                ),
                # 优化配置
                optimizers_config=models.OptimizersConfigDiff(
                    indexing_threshold=20000,  # 达到此数量后开始索引
                ),
                # 使用量化来节省内存
                quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=False,
                    ),
                ),
            )

    async def upsert_content(
        self,
        content_id: uuid.UUID,
        vector: List[float],
        metadata: Dict[str, Any],
        collection_name: str = None,
    ) -> str:
        """
        插入或更新内容向量

        Args:
            content_id: 内容ID
            vector: 向量嵌入
            metadata: 元数据（包含title, content_type, difficulty_level等）
            collection_name: 集合名称

        Returns:
            str: Qdrant中的点ID

        Note:
            使用content_id作为点ID，确保唯一性
        """
        client = self._get_client()
        collection = collection_name or self.CONTENT_COLLECTION

        # 确保集合存在
        await self.ensure_collection(collection)

        # 使用content_id作为点ID
        point_id = str(content_id)

        # 构建点数据
        point = models.PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "content_id": str(content_id),
                **metadata
            }
        )

        # 插入或更新
        await client.upsert(
            collection_name=collection,
            points=[point],
        )

        return point_id

    async def upsert_content_from_db(
        self,
        db: AsyncSession,
        content: Content,
        collection_name: str = None,
    ) -> str:
        """
        从数据库内容对象生成向量并插入

        Args:
            db: 数据库会话
            content: Content模型实例
            collection_name: 集合名称

        Returns:
            str: Qdrant点ID
        """
        # 生成向量
        vector = await self.embedding_service.generate_content_embedding(
            title=content.title,
            content_text=content.content_text,
            description=content.description,
            topic=content.topic,
            difficulty_level=content.difficulty_level.value if content.difficulty_level else None,
            exam_type=content.exam_type.value if content.exam_type else None,
        )

        # 构建元数据
        metadata = {
            "title": content.title,
            "content_type": content.content_type.value,
            "difficulty_level": content.difficulty_level.value,
            "exam_type": content.exam_type.value if content.exam_type else None,
            "topic": content.topic,
            "tags": content.tags or [],
            "is_published": content.is_published,
        }

        # 插入向量
        point_id = await self.upsert_content(
            content_id=content.id,
            vector=vector,
            metadata=metadata,
            collection_name=collection_name,
        )

        # 更新数据库中的vector_id
        content.vector_id = point_id
        await db.commit()

        return point_id

    async def search_similar(
        self,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: str = None,
    ) -> List[Dict[str, Any]]:
        """
        向量相似度搜索

        Args:
            query_vector: 查询向量
            limit: 返回结果数量
            score_threshold: 相似度阈值（0-1）
            filters: 过滤条件（如：{"difficulty_level": "intermediate", "exam_type": "ielts"}）
            collection_name: 集合名称

        Returns:
            List[Dict]: 搜索结果，包含id、score、payload等

        Example:
            >>> results = await vector_service.search_similar(
            ...     query_vector=embedding,
            ...     limit=5,
            ...     filters={"difficulty_level": "intermediate"}
            ... )
        """
        client = self._get_client()
        collection = collection_name or self.CONTENT_COLLECTION

        # 构建过滤条件
        filter_conditions = None
        if filters:
            must_conditions = []
            for key, value in filters.items():
                if value is not None:
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                    )
            if must_conditions:
                filter_conditions = models.Filter(must=must_conditions)

        # 执行搜索（使用 query_points API）
        query_response = await client.query_points(
            collection_name=collection,
            query=query_vector,
            query_filter=filter_conditions,
            limit=limit,
            score_threshold=score_threshold,
        )

        # 格式化结果
        results = []
        for result in query_response.points:
            results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            })

        return results

    async def search_by_text(
        self,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: str = None,
    ) -> List[Dict[str, Any]]:
        """
        通过文本查询相似内容

        Args:
            query_text: 查询文本
            limit: 返回结果数量
            score_threshold: 相似度阈值
            filters: 过滤条件
            collection_name: 集合名称

        Returns:
            List[Dict]: 搜索结果

        Example:
            >>> results = await vector_service.search_by_text(
            ...     query_text="关于环境保护的文章",
            ...     filters={"content_type": "reading", "difficulty_level": "intermediate"}
            ... )
        """
        # 生成查询向量
        query_vector = await self.embedding_service.generate_embedding(query_text)

        # 执行搜索
        return await self.search_similar(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filters=filters,
            collection_name=collection_name,
        )

    async def recommend_content(
        self,
        content_id: uuid.UUID,
        limit: int = 5,
        exclude_current: bool = True,
        filters: Optional[Dict[str, Any]] = None,
        collection_name: str = None,
    ) -> List[Dict[str, Any]]:
        """
        基于内容ID推荐相似内容

        Args:
            content_id: 参考内容ID
            limit: 返回结果数量
            exclude_current: 是否排除当前内容
            filters: 过滤条件
            collection_name: 集合名称

        Returns:
            List[Dict]: 推荐内容列表
        """
        client = self._get_client()
        collection = collection_name or self.CONTENT_COLLECTION

        # 获取参考内容的向量
        try:
            records = await client.retrieve(
                collection_name=collection,
                ids=[str(content_id)],
                with_vectors=True,
            )
            if not records:
                return []
            query_vector = records[0].vector
            if not query_vector:
                return []
            query_vector = point[0].vector
        except Exception:
            return []

        # 执行搜索（使用 query_points API）
        query_response = await client.query_points(
            collection_name=collection,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="content_id",
                        match=models.MatchValue(value=str(content_id))
                    )
                ]
            ) if exclude_current else None,
            limit=limit + 1 if exclude_current else limit,
        )

        # 格式化结果
        formatted_results = []
        for result in query_response.points:
            if exclude_current and result.id == str(content_id):
                continue
            formatted_results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            })

        return formatted_results[:limit]

    async def delete_content(
        self,
        content_id: uuid.UUID,
        collection_name: str = None,
    ) -> bool:
        """
        删除内容向量

        Args:
            content_id: 内容ID
            collection_name: 集合名称

        Returns:
            bool: 删除成功返回True
        """
        client = self._get_client()
        collection = collection_name or self.CONTENT_COLLECTION

        try:
            await client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(
                    points=[str(content_id)]
                ),
            )
            return True
        except Exception:
            return False

    async def delete_batch(
        self,
        content_ids: List[uuid.UUID],
        collection_name: str = None,
    ) -> int:
        """
        批量删除内容向量

        Args:
            content_ids: 内容ID列表
            collection_name: 集合名称

        Returns:
            int: 成功删除的数量
        """
        client = self._get_client()
        collection = collection_name or self.CONTENT_COLLECTION

        try:
            await client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(
                    points=[str(cid) for cid in content_ids]
                ),
            )
            return len(content_ids)
        except Exception:
            return 0

    async def get_collection_info(
        self,
        collection_name: str = None,
    ) -> Dict[str, Any]:
        """
        获取集合信息

        Args:
            collection_name: 集合名称

        Returns:
            Dict: 集合信息（向量数量、维度等）
        """
        client = self._get_client()
        collection = collection_name or self.CONTENT_COLLECTION

        try:
            info = await client.get_collection(collection)
            return {
                "name": collection,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "status": info.status,
                "optimizer_status": info.optimizer_status,
            }
        except Exception:
            return {
                "name": collection,
                "status": "not_found"
            }

    async def health_check(self) -> bool:
        """
        健康检查：验证Qdrant连接

        Returns:
            bool: 连接正常返回True
        """
        try:
            client = self._get_client()
            await client.get_collections()
            return True
        except Exception:
            return False

    async def sync_content_to_vector(
        self,
        db: AsyncSession,
        content_id: uuid.UUID,
        collection_name: str = None,
    ) -> bool:
        """
        同步数据库内容到向量数据库

        Args:
            db: 数据库会话
            content_id: 内容ID
            collection_name: 集合名称

        Returns:
            bool: 同步成功返回True
        """
        try:
            # 从数据库获取内容
            result = await db.execute(
                select(Content).where(Content.id == content_id)
            )
            content = result.scalar_one_or_none()

            if not content:
                return False

            # 插入或更新向量
            await self.upsert_content_from_db(db, content, collection_name)
            return True
        except Exception:
            return False


# 创建全局单例
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """
    获取向量服务单例

    Returns:
        VectorService: 向量服务实例
    """
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
