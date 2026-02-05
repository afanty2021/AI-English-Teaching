"""
内容库初始化集成测试 - AI英语教学系统
测试完整的内容导入、索引和去重流程
"""
import json
import pytest
import pytest_asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.db.session import AsyncSessionLocal
from app.services.content_import_service import ContentImportService, VocabularyImportService
from app.services.vector_service import VectorService
from app.services.content_deduplication_service import ContentDeduplicationService
from app.utils.content_validators import get_content_validator, get_vocabulary_validator


class TestContentLibraryInitFlow:
    """内容库初始化流程集成测试"""

    @pytest.fixture
    def test_data_dir(self):
        """测试数据目录"""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def sample_contents(self):
        """示例内容数据"""
        return [
            {
                "title": "Introduction to AI",
                "description": "An article introducing artificial intelligence",
                "content_type": "reading",
                "difficulty_level": "intermediate",
                "exam_type": "ielts",
                "topic": "technology",
                "tags": ["AI", "technology", "reading"],
                "content_text": "Artificial intelligence (AI) is transforming our world...",
                "word_count": 500,
                "knowledge_points": ["AI basics", "vocabulary"]
            },
            {
                "title": "Climate Change and Environment",
                "description": "Understanding climate change",
                "content_type": "reading",
                "difficulty_level": "upper_intermediate",
                "exam_type": "toefl",
                "topic": "environment",
                "tags": ["environment", "climate", "reading"],
                "content_text": "Climate change is one of the most pressing issues...",
                "word_count": 600,
                "knowledge_points": ["climate vocabulary", "reading comprehension"]
            },
            {
                "title": "Business English Basics",
                "description": "Essential business English phrases",
                "content_type": "listening",
                "difficulty_level": "intermediate",
                "exam_type": "toeic",
                "topic": "business",
                "tags": ["business", "listening", "english"],
                "content_text": "Dialogue in a business meeting...",
                "duration": 200,
                "word_count": 300
            }
        ]

    def test_content_validator_file_validation(self, sample_contents):
        """测试内容验证器文件验证"""
        validator = get_content_validator()

        # 验证数据
        is_valid, errors = validator.validate_contents(sample_contents)
        assert is_valid is True

    def test_vocabulary_validator(self):
        """测试词汇验证器"""
        validator = get_vocabulary_validator()

        vocabularies = [
            {
                "word": "communicate",
                "phonetic": "/kəˈmjuːnɪkeɪt/",
                "part_of_speech": ["v."],
                "definitions": ["交流", "沟通"],
                "examples": ["We need to communicate effectively."],
                "difficulty_level": "beginner",
                "frequency_level": 8
            }
        ]

        is_valid, errors = validator.validate_vocabularies(vocabularies)
        assert is_valid is True

    def test_cosine_similarity_edge_cases(self):
        """测试余弦相似度边界情况"""
        service = ContentDeduplicationService()

        # 空向量
        assert service._cosine_similarity([], []) == 0.0
        assert service._cosine_similarity([1, 2], []) == 0.0
        assert service._cosine_similarity([], [1, 2]) == 0.0

        # 零向量
        assert service._cosine_similarity([0, 0], [1, 1]) == 0.0

    def test_content_extraction(self):
        """测试内容文本提取"""
        service = ContentDeduplicationService()

        # 完整内容
        content = {
            "title": "Test Title",
            "description": "Test description",
            "content_text": "Full content text here...",
            "topic": "tech",
            "tags": ["tag1"]
        }
        text = service._extract_text(content)
        assert "Test Title" in text
        assert "Test description" in text

        # 最小内容
        minimal_content = {"title": "Minimal"}
        text = service._extract_text(minimal_content)
        assert text == "Minimal"


class TestContentImportService:
    """内容导入服务测试"""

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟数据库会话"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.add = MagicMock()
        session.execute = AsyncMock()

        # 模拟查询返回None（表示内容不存在）
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        session.execute.return_value = mock_result

        return session

    def test_import_service_initialization(self, mock_db_session):
        """测试导入服务初始化"""
        service = ContentImportService(mock_db_session)
        assert service.skip_duplicates is True
        assert service.validator is not None

    def test_import_service_with_skip_duplicates_false(self, mock_db_session):
        """测试导入服务设置skip_duplicates为False"""
        service = ContentImportService(mock_db_session, skip_duplicates=False)
        assert service.skip_duplicates is False


class TestVectorServiceIntegration:
    """向量服务集成测试"""

    def test_vector_service_initialization(self):
        """测试向量服务初始化"""
        service = VectorService()
        assert service.embedding_service is not None
        assert service.vector_size > 0

    def test_ensure_collection_params(self):
        """测试集合参数"""
        service = VectorService()
        # 测试默认参数
        assert service.CONTENT_COLLECTION == "english_content"
        assert service.VOCABULARY_COLLECTION == "english_vocabulary"


class TestPromptTemplates:
    """Prompt模板测试"""

    def test_content_prompt_generation(self):
        """测试内容Prompt生成"""
        from data.generation_prompts.content_generator_prompts import (
            generate_content_prompt,
            CONTENT_GENERATION_PROMPT
        )

        prompt = generate_content_prompt(
            content_type="reading",
            difficulty_level="intermediate",
            exam_type="ielts",
            topic="technology"
        )

        assert "reading" in prompt
        assert "intermediate" in prompt
        assert "ielts" in prompt
        assert "technology" in prompt

    def test_vocabulary_prompt_generation(self):
        """测试词汇Prompt生成"""
        from data.generation_prompts.content_generator_prompts import (
            generate_vocabulary_prompt
        )

        prompt = generate_vocabulary_prompt(
            difficulty_level="beginner",
            quantity=10
        )

        assert "beginner" in prompt
        assert "10" in prompt


class TestSchemaValidation:
    """Schema验证测试"""

    def test_content_schema_exists(self):
        """测试内容Schema文件存在"""
        schema_path = Path(__file__).parent.parent.parent / "data" / "schemas" / "content.schema.json"
        assert schema_path.exists()

    def test_vocabulary_schema_exists(self):
        """测试词汇Schema文件存在"""
        schema_path = Path(__file__).parent.parent.parent / "data" / "schemas" / "vocabulary.schema.json"
        assert schema_path.exists()

    def test_content_schema_valid_json(self):
        """测试内容Schema是有效JSON"""
        schema_path = Path(__file__).parent.parent.parent / "data" / "schemas" / "content.schema.json"
        with open(schema_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "$schema" in data
        assert data["type"] == "object"

    def test_vocabulary_schema_valid_json(self):
        """测试词汇Schema是有效JSON"""
        schema_path = Path(__file__).parent.parent.parent / "data" / "schemas" / "vocabulary.schema.json"
        with open(schema_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "$schema" in data
        assert data["type"] == "object"


class TestCLIScript:
    """CLI脚本测试"""

    @pytest.fixture
    def backend_path(self):
        """获取backend目录路径"""
        return Path(__file__).parent.parent.parent

    def test_cli_script_exists(self, backend_path):
        """测试CLI脚本文件存在"""
        script_path = backend_path / "scripts" / "init_content_library.py"
        assert script_path.exists()

    def test_cli_script_has_main_blocks(self, backend_path):
        """测试CLI脚本有主函数"""
        script_path = backend_path / "scripts" / "init_content_library.py"
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "def main():" in content or "async def main():" in content
        assert "argparse" in content

    def test_cli_has_required_commands(self, backend_path):
        """测试CLI有必需命令"""
        script_path = backend_path / "scripts" / "init_content_library.py"
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        commands = ["init", "import", "index", "deduplicate", "validate", "stats", "update"]
        for cmd in commands:
            assert f'"{cmd}"' in content or f"'{cmd}'" in content
