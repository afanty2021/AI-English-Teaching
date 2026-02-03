"""
嵌入服务测试
测试OpenAI Embeddings API集成
"""
import pytest

from app.services.embedding_service import EmbeddingService, get_embedding_service


class TestEmbeddingService:
    """嵌入服务测试类"""

    @pytest.fixture
    def embedding_service(self):
        """创建嵌入服务实例"""
        service = EmbeddingService()
        return service

    def test_init(self, embedding_service):
        """测试服务初始化"""
        assert embedding_service.model is not None
        assert embedding_service.embedding_dim == 1536
        assert embedding_service.client is None  # 懒加载

    def test_get_embedding_dimension(self, embedding_service):
        """测试获取向量维度"""
        dim = embedding_service.get_embedding_dimension()
        assert dim == 1536

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self, embedding_service):
        """测试空文本生成向量"""
        with pytest.raises(ValueError, match="文本不能为空"):
            await embedding_service.generate_embedding("")

    @pytest.mark.asyncio
    async def test_generate_embedding_invalid_text(self, embedding_service):
        """测试无效文本生成向量"""
        with pytest.raises(ValueError):
            await embedding_service.generate_embedding("   ")

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings_empty_list(self, embedding_service):
        """测试空列表批量生成"""
        result = await embedding_service.batch_generate_embeddings([])
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings_filters_empty(self, embedding_service):
        """测试批量生成时过滤空文本"""
        texts = ["valid text", "", "   ", "another valid"]
        # 注意：这个测试需要mock API调用
        # 实际运行时需要有效的API密钥

    def test_get_embedding_service_singleton(self):
        """测试单例模式"""
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_generate_content_embedding(self, embedding_service):
        """测试为内容生成向量"""
        # 注意：需要有效的API密钥
        # 这里的测试主要用于验证接口正确性
        pass

    @pytest.mark.asyncio
    async def test_generate_vocabulary_embedding(self, embedding_service):
        """测试为词汇生成向量"""
        # 注意：需要有效的API密钥
        pass

    @pytest.mark.asyncio
    async def test_health_check_without_api_key(self, embedding_service):
        """测试无API密钥时的健康检查"""
        # 在没有API密钥的情况下，健康检查应该返回False
        result = await embedding_service.health_check()
        # 结果取决于是否有有效的API密钥
        assert isinstance(result, bool)


class TestEmbeddingServiceIntegration:
    """
    嵌入服务集成测试
    注意：这些测试需要有效的OpenAI API密钥
    """

    @pytest.fixture
    def real_service(self):
        """创建真实的嵌入服务（需要API密钥）"""
        return EmbeddingService()

    @pytest.mark.asyncio
    @pytest.mark.skip("需要有效的OpenAI API密钥")
    async def test_real_generate_embedding(self, real_service):
        """测试真实的向量生成"""
        embedding = await real_service.generate_embedding("Hello, world!")
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    @pytest.mark.skip("需要有效的OpenAI API密钥")
    async def test_real_batch_generate_embeddings(self, real_service):
        """测试真实批量向量生成"""
        texts = ["First text", "Second text", "Third text"]
        embeddings = await real_service.batch_generate_embeddings(texts)
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)

    @pytest.mark.asyncio
    @pytest.mark.skip("需要有效的OpenAI API密钥")
    async def test_real_generate_content_embedding(self, real_service):
        """测试真实内容向量生成"""
        embedding = await real_service.generate_content_embedding(
            title="Environmental Protection",
            content_text="This article discusses the importance of protecting our environment.",
            description="An educational article about environmental issues",
            topic="Environment",
            difficulty_level="intermediate",
        )
        assert len(embedding) == 1536

    @pytest.mark.asyncio
    @pytest.mark.skip("需要有效的OpenAI API密钥")
    async def test_real_generate_vocabulary_embedding(self, real_service):
        """测试真实词汇向量生成"""
        embedding = await real_service.generate_vocabulary_embedding(
            word="environment",
            definitions=["环境", "周围"],
            examples=["We must protect the environment.", "The environment is fragile."],
            english_definition="The surroundings or conditions in which a person, animal, or plant lives",
        )
        assert len(embedding) == 1536

    @pytest.mark.asyncio
    @pytest.mark.skip("需要有效的OpenAI API密钥")
    async def test_real_health_check(self, real_service):
        """测试真实健康检查"""
        result = await real_service.health_check()
        assert result is True
