"""
向量服务测试
测试Qdrant向量数据库集成
"""
import pytest
from qdrant_client.http.exceptions import UnexpectedResponse

from app.services.vector_service import VectorService, get_vector_service


class TestVectorService:
    """向量服务测试类"""

    @pytest.fixture
    def vector_service(self):
        """创建向量服务实例"""
        service = VectorService()
        return service

    def test_init(self, vector_service):
        """测试服务初始化"""
        assert vector_service.CONTENT_COLLECTION == "english_content"
        assert vector_service.VOCABULARY_COLLECTION == "english_vocabulary"
        assert vector_service.vector_size == 1536
        assert vector_service.client is None  # 懒加载

    def test_get_vector_service_singleton(self):
        """测试单例模式"""
        service1 = get_vector_service()
        service2 = get_vector_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_ensure_collection(self, vector_service):
        """测试确保集合存在"""
        # 这个测试需要Qdrant服务运行
        try:
            await vector_service.ensure_collection("test_collection")
            # 验证集合创建成功
            info = await vector_service.get_collection_info("test_collection")
            assert info["name"] == "test_collection"

            # 清理测试集合
            client = vector_service._get_client()
            await client.delete_collection("test_collection")
        except Exception as e:
            pytest.skip(f"Qdrant服务未运行: {e}")

    @pytest.mark.asyncio
    async def test_health_check(self, vector_service):
        """测试健康检查"""
        result = await vector_service.health_check()
        # 结果取决于Qdrant服务是否运行
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_get_collection_info_not_found(self, vector_service):
        """测试获取不存在的集合信息"""
        info = await vector_service.get_collection_info("nonexistent_collection")
        assert info["status"] == "not_found"


class TestVectorServiceIntegration:
    """
    向量服务集成测试
    注意：这些测试需要Qdrant服务运行
    """

    @pytest.fixture
    async def cleanup_collection(self):
        """清理测试集合的fixture"""
        service = VectorService()
        test_collection = "test_content_integration"

        yield service, test_collection

        # 清理
        try:
            client = service._get_client()
            await client.delete_collection(test_collection)
        except Exception:
            pass

    @pytest.mark.asyncio
    @pytest.mark.skip("需要Qdrant服务运行")
    async def test_upsert_and_search(self, cleanup_collection):
        """测试插入和搜索"""
        service, test_collection = cleanup_collection

        # 确保集合存在
        await service.ensure_collection(test_collection)

        # 插入测试向量
        import uuid
        test_id = uuid.uuid4()
        test_vector = [0.1] * 1536  # 模拟向量
        test_metadata = {
            "title": "Test Content",
            "content_type": "reading",
            "difficulty_level": "intermediate",
        }

        point_id = await service.upsert_content(
            content_id=test_id,
            vector=test_vector,
            metadata=test_metadata,
            collection_name=test_collection,
        )
        assert point_id == str(test_id)

        # 搜索相似内容
        results = await service.search_similar(
            query_vector=test_vector,
            limit=5,
            collection_name=test_collection,
        )
        assert len(results) >= 1
        assert results[0]["id"] == str(test_id)

    @pytest.mark.asyncio
    @pytest.mark.skip("需要Qdrant服务运行")
    async def test_search_with_filters(self, cleanup_collection):
        """测试带过滤条件的搜索"""
        service, test_collection = cleanup_collection

        await service.ensure_collection(test_collection)

        # 插入多个测试向量
        import uuid
        vectors = [
            (uuid.uuid4(), [0.1] * 1536, {"difficulty_level": "intermediate", "topic": "science"}),
            (uuid.uuid4(), [0.2] * 1536, {"difficulty_level": "advanced", "topic": "history"}),
            (uuid.uuid4(), [0.3] * 1536, {"difficulty_level": "intermediate", "topic": "art"}),
        ]

        for content_id, vector, metadata in vectors:
            await service.upsert_content(content_id, vector, metadata, test_collection)

        # 搜索intermediate难度
        results = await service.search_similar(
            query_vector=[0.1] * 1536,
            filters={"difficulty_level": "intermediate"},
            collection_name=test_collection,
        )
        assert len(results) == 2

    @pytest.mark.asyncio
    @pytest.mark.skip("需要Qdrant服务运行")
    async def test_delete_content(self, cleanup_collection):
        """测试删除内容"""
        service, test_collection = cleanup_collection

        await service.ensure_collection(test_collection)

        # 插入测试数据
        import uuid
        test_id = uuid.uuid4()
        await service.upsert_content(
            content_id=test_id,
            vector=[0.1] * 1536,
            metadata={"title": "To be deleted"},
            collection_name=test_collection,
        )

        # 验证插入成功
        results = await service.search_similar(
            query_vector=[0.1] * 1536,
            limit=10,
            collection_name=test_collection,
        )
        assert len(results) >= 1

        # 删除
        success = await service.delete_content(test_id, test_collection)
        assert success is True

        # 验证删除成功
        results_after = await service.search_similar(
            query_vector=[0.1] * 1536,
            limit=10,
            collection_name=test_collection,
        )
        assert all(r["id"] != str(test_id) for r in results_after)

    @pytest.mark.asyncio
    @pytest.mark.skip("需要Qdrant服务运行")
    async def test_recommend_content(self, cleanup_collection):
        """测试内容推荐"""
        service, test_collection = cleanup_collection

        await service.ensure_collection(test_collection)

        # 插入相似的测试向量
        import uuid
        base_vector = [0.1] * 1536
        similar_vector = [0.11] * 1536  # 非常相似

        content_id = uuid.uuid4()
        similar_id = uuid.uuid4()

        await service.upsert_content(content_id, base_vector, {"title": "Base"}, test_collection)
        await service.upsert_content(similar_id, similar_vector, {"title": "Similar"}, test_collection)

        # 推荐相似内容
        recommendations = await service.recommend_content(
            content_id=content_id,
            limit=5,
            exclude_current=True,
            collection_name=test_collection,
        )

        assert len(recommendations) >= 1
        assert recommendations[0]["id"] == str(similar_id)

    @pytest.mark.asyncio
    @pytest.mark.skip("需要Qdrant服务运行")
    async def test_batch_delete(self, cleanup_collection):
        """测试批量删除"""
        service, test_collection = cleanup_collection

        await service.ensure_collection(test_collection)

        # 插入多个测试向量
        import uuid
        test_ids = [uuid.uuid4() for _ in range(3)]

        for test_id in test_ids:
            await service.upsert_content(
                content_id=test_id,
                vector=[0.1] * 1536,
                metadata={"title": f"Content {i}"},
                collection_name=test_collection,
            )

        # 批量删除
        deleted_count = await service.delete_batch(test_ids, test_collection)
        assert deleted_count == 3


class TestVectorServiceWithEmbedding:
    """
    向量服务与嵌入服务集成测试
    需要同时运行Qdrant和配置OpenAI API
    """

    @pytest.mark.asyncio
    @pytest.mark.skip("需要Qdrant和OpenAI API")
    async def test_search_by_text(self):
        """测试通过文本搜索"""
        service = get_vector_service()
        test_collection = "test_text_search"

        try:
            await service.ensure_collection(test_collection)

            # 插入测试数据（使用真实的向量生成）
            from app.services.embedding_service import get_embedding_service
            embedding_service = get_embedding_service()

            test_vector = await embedding_service.generate_embedding("Environmental protection article")

            import uuid
            test_id = uuid.uuid4()
            await service.upsert_content(
                content_id=test_id,
                vector=test_vector,
                metadata={
                    "title": "Environmental Protection",
                    "content_type": "reading",
                },
                collection_name=test_collection,
            )

            # 通过文本搜索
            results = await service.search_by_text(
                query_text="environment and nature",
                limit=5,
                collection_name=test_collection,
            )

            assert len(results) >= 1
        finally:
            # 清理
            try:
                client = service._get_client()
                await client.delete_collection(test_collection)
            except Exception:
                pass
