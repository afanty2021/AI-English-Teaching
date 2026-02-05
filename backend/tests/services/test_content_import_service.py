"""
内容导入服务测试 - AI英语教学系统
"""
import json
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.content_validators import ContentValidator, VocabularyValidator
from app.services.content_deduplication_service import (
    ContentDeduplicationService,
    VocabularyDeduplicationService
)
from app.services.content_import_service import ContentImportService, VocabularyImportService


class TestContentValidator:
    """内容验证器测试"""

    @pytest.fixture
    def content_validator(self):
        """创建内容验证器"""
        schema_path = Path(__file__).parent.parent.parent / "data" / "schemas" / "content.schema.json"
        return ContentValidator(str(schema_path))

    def test_validate_valid_content(self, content_validator):
        """测试有效内容验证"""
        valid_data = {
            "contents": [
                {
                    "title": "Test Article",
                    "description": "A test article",
                    "content_type": "reading",
                    "difficulty_level": "intermediate",
                    "exam_type": "ielts",
                    "topic": "technology",
                    "tags": ["reading", "tech"],
                    "content_text": "This is a test article about technology.",
                    "word_count": 100,
                    "knowledge_points": ["vocabulary", "comprehension"]
                }
            ]
        }
        is_valid, errors = content_validator.validate(valid_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_content_missing_required(self, content_validator):
        """测试无效内容验证 - 缺少必需字段"""
        invalid_data = {
            "contents": [
                {
                    "title": "Test"  # 缺少必需字段
                }
            ]
        }
        is_valid, errors = content_validator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_invalid_content_type(self, content_validator):
        """测试无效内容验证 - 无效的内容类型"""
        invalid_data = {
            "contents": [
                {
                    "title": "Test Article",
                    "content_type": "invalid_type",  # 无效的内容类型
                    "difficulty_level": "intermediate"
                }
            ]
        }
        is_valid, errors = content_validator.validate(invalid_data)
        assert is_valid is False
        assert len(errors) > 0

    def test_validate_empty_contents(self, content_validator):
        """测试空内容列表"""
        data = {"contents": []}
        is_valid, errors = content_validator.validate(data)
        assert is_valid is True

    def test_validate_multiple_contents(self, content_validator):
        """测试多个内容验证"""
        data = {
            "contents": [
                {
                    "title": "Article 1",
                    "content_type": "reading",
                    "difficulty_level": "beginner"
                },
                {
                    "title": "Article 2",
                    "content_type": "listening",
                    "difficulty_level": "advanced"
                },
                {
                    "title": "Article 3",
                    "content_type": "grammar",
                    "difficulty_level": "intermediate"
                }
            ]
        }
        is_valid, errors = content_validator.validate(data)
        assert is_valid is True


class TestVocabularyValidator:
    """词汇验证器测试"""

    @pytest.fixture
    def vocabulary_validator(self):
        """创建词汇验证器"""
        schema_path = Path(__file__).parent.parent.parent / "data" / "schemas" / "vocabulary.schema.json"
        return VocabularyValidator(str(schema_path))

    def test_validate_valid_vocabulary(self, vocabulary_validator):
        """测试有效词汇验证"""
        valid_data = {
            "vocabularies": [
                {
                    "word": "technology",
                    "phonetic": "/tekˈnɒlədʒi/",
                    "part_of_speech": ["n."],
                    "definitions": ["科学技术", "技术学"],
                    "examples": ["Technology is changing our lives."],
                    "difficulty_level": "intermediate",
                    "frequency_level": 7,
                    "synonyms": ["innovation"],
                    "collocations": ["advanced technology"]
                }
            ]
        }
        is_valid, errors = vocabulary_validator.validate(valid_data)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_vocabulary_missing_word(self, vocabulary_validator):
        """测试无效词汇验证 - 缺少单词"""
        invalid_data = {
            "vocabularies": [
                {
                    "phonetic": "/test/",
                    "definitions": ["test"]
                }
            ]
        }
        is_valid, errors = vocabulary_validator.validate(invalid_data)
        assert is_valid is False


class TestContentDeduplicationService:
    """内容去重服务测试"""

    @pytest.fixture
    def mock_embedding_service(self):
        """创建模拟嵌入服务"""
        service = MagicMock()
        service.batch_generate_embeddings = AsyncMock(return_value=[
            [0.1, 0.2, 0.3],  # 第一条
            [0.15, 0.25, 0.35],  # 与第一条相似 (相似度 ~0.99)
            [0.9, 0.8, 0.7],  # 不相似 (相似度 ~0.4)
        ])
        return service

    @pytest.mark.asyncio
    async def test_find_duplicates(self, mock_embedding_service):
        """测试重复检测"""
        service = ContentDeduplicationService(
            embedding_service=mock_embedding_service,
            similarity_threshold=0.90  # 提高阈值确保只有相似的被检测
        )

        texts = [
            "This is an article about technology",
            "This is an article about technology and AI",
            "A completely different topic about sports"
        ]

        duplicates = await service.find_duplicates(texts)

        # 0和1应该被检测为重复
        assert len(duplicates) >= 1
        duplicate_indices = set()
        for group in duplicates:
            duplicate_indices.update(group)

        assert 0 in duplicate_indices
        assert 1 in duplicate_indices

    @pytest.mark.asyncio
    async def test_filter_duplicates(self, mock_embedding_service):
        """测试过滤重复内容"""
        service = ContentDeduplicationService(
            embedding_service=mock_embedding_service,
            similarity_threshold=0.90  # 提高阈值
        )

        contents = [
            {"title": "Article 1", "description": "Tech article", "content_text": "Tech content"},
            {"title": "Article 2", "description": "Tech article with AI", "content_text": "AI content"},
            {"title": "Article 3", "description": "Sports article", "content_text": "Sports content"},
        ]

        filtered = await service.filter_duplicates(contents)

        # 应该有2条内容（过滤掉重复的）
        assert len(filtered) == 2

    @pytest.mark.asyncio
    async def test_empty_contents(self, mock_embedding_service):
        """测试空内容列表"""
        service = ContentDeduplicationService(embedding_service=mock_embedding_service)

        result = await service.filter_duplicates([])
        assert result == []

        result = await service.find_duplicates([])
        assert result == []

    def test_cosine_similarity(self):
        """测试余弦相似度计算"""
        service = ContentDeduplicationService()

        # 完全相同的向量
        vec = [1.0, 0.0, 0.0]
        similarity = service._cosine_similarity(vec, vec)
        assert similarity == 1.0

        # 正交向量
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = service._cosine_similarity(vec1, vec2)
        assert similarity == 0.0

        # 相似向量
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.9, 0.1, 0.0]
        similarity = service._cosine_similarity(vec1, vec2)
        assert similarity > 0.9


class TestVocabularyDeduplicationService:
    """词汇去重服务测试"""

    @pytest.fixture
    def mock_embedding_service(self):
        """创建模拟嵌入服务"""
        service = MagicMock()
        service.batch_generate_embeddings = AsyncMock(return_value=[
            [0.1, 0.2, 0.3],
            [0.12, 0.22, 0.32],  # 非常相似
            [0.9, 0.8, 0.7],  # 不相似
        ])
        return service

    @pytest.mark.asyncio
    async def test_find_vocabulary_duplicates(self, mock_embedding_service):
        """测试词汇重复检测"""
        service = VocabularyDeduplicationService(
            embedding_service=mock_embedding_service,
            similarity_threshold=0.85
        )

        vocabularies = [
            {"word": "happy", "definitions": ["快乐的"]},
            {"word": "happy", "definitions": ["高兴的"]},  # 相似
            {"word": "sad", "definitions": ["悲伤的"]},
        ]

        duplicates = await service.find_duplicates(vocabularies)
        assert len(duplicates) >= 1


class TestContentImportService:
    """内容导入服务测试"""

    @pytest_asyncio.fixture
    async def mock_db(self):
        """创建模拟数据库会话"""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.add = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def sample_content_data(self):
        """示例内容数据"""
        return [
            {
                "title": "Test Reading Article",
                "description": "A test reading article",
                "content_type": "reading",
                "difficulty_level": "intermediate",
                "topic": "technology",
                "content_text": "This is a test article about technology.",
                "word_count": 100,
            }
        ]


# ============================================================================
# 测试数据文件
# ============================================================================

@pytest.fixture
def sample_contents_json(tmp_path):
    """创建示例内容JSON文件"""
    data = {
        "contents": [
            {
                "title": "Sample Reading Article 1",
                "description": "A sample reading article",
                "content_type": "reading",
                "difficulty_level": "intermediate",
                "exam_type": "ielts",
                "topic": "education",
                "tags": ["reading", "ielts"],
                "content_text": "This is a sample reading article about education.",
                "word_count": 300,
                "knowledge_points": ["comprehension", "vocabulary"]
            },
            {
                "title": "Sample Listening Material",
                "description": "A sample listening script",
                "content_type": "listening",
                "difficulty_level": "beginner",
                "exam_type": "general",
                "topic": "daily life",
                "content_text": "Dialogue about daily routines.",
                "duration": 180,
                "word_count": 150
            }
        ]
    }

    file_path = tmp_path / "sample_contents.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return file_path


@pytest.fixture
def sample_vocabularies_json(tmp_path):
    """创建示例词汇JSON文件"""
    data = {
        "vocabularies": [
            {
                "word": "technology",
                "phonetic": "/tekˈnɒlədʒi/",
                "part_of_speech": ["n."],
                "definitions": ["科学技术", "技术学"],
                "examples": ["Technology is advancing rapidly."],
                "difficulty_level": "intermediate",
                "frequency_level": 7
            },
            {
                "word": "innovation",
                "phonetic": "/ˌɪnəˈveɪʃn/",
                "part_of_speech": ["n."],
                "definitions": ["创新", "革新"],
                "examples": ["Innovation is key to progress."],
                "difficulty_level": "intermediate",
                "frequency_level": 6
            }
        ]
    }

    file_path = tmp_path / "sample_vocabularies.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return file_path


@pytest.fixture
def invalid_json_file(tmp_path):
    """创建无效JSON文件"""
    file_path = tmp_path / "invalid.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("{ invalid json }")

    return file_path
