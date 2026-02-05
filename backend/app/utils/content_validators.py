"""
内容数据验证器 - AI英语教学系统
提供JSON Schema验证功能，确保内容数据格式正确
"""
import json
import logging
from pathlib import Path
from typing import List, Tuple

import jsonschema

logger = logging.getLogger(__name__)


class ContentValidator:
    """内容数据验证器

    使用JSON Schema验证内容数据格式
    """

    def __init__(self, schema_path: str):
        """初始化验证器

        Args:
            schema_path: JSON Schema文件路径
        """
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> dict:
        """加载JSON Schema"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Schema file not found: {self.schema_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            raise

    def validate(self, data: dict) -> Tuple[bool, List[str]]:
        """验证数据

        Args:
            data: 要验证的数据

        Returns:
            (是否成功, 错误列表)
        """
        errors = []
        try:
            jsonschema.validate(data, self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(f"Validation error: {e.message} at {' -> '.join(str(p) for p in e.path)}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return False, errors

    def validate_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """验证JSON文件

        Args:
            file_path: JSON文件路径

        Returns:
            (是否成功, 错误列表)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.validate(data)
        except FileNotFoundError:
            return False, [f"File not found: {file_path}"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
        except Exception as e:
            return False, [f"Unexpected error: {str(e)}"]

    def validate_contents(self, contents: List[dict]) -> Tuple[bool, List[str]]:
        """验证内容列表

        Args:
            contents: 内容列表

        Returns:
            (是否成功, 错误列表)
        """
        wrapper = {"contents": contents}
        errors = []

        try:
            jsonschema.validate(wrapper, self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(f"Validation error: {e.message}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return False, errors


class VocabularyValidator:
    """词汇数据验证器

    使用JSON Schema验证词汇数据格式
    """

    def __init__(self, schema_path: str):
        """初始化验证器

        Args:
            schema_path: JSON Schema文件路径
        """
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> dict:
        """加载JSON Schema"""
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Schema file not found: {self.schema_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            raise

    def validate(self, data: dict) -> Tuple[bool, List[str]]:
        """验证数据

        Args:
            data: 要验证的数据

        Returns:
            (是否成功, 错误列表)
        """
        errors = []
        try:
            jsonschema.validate(data, self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(f"Validation error: {e.message} at {' -> '.join(str(p) for p in e.path)}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return False, errors

    def validate_file(self, file_path: str) -> Tuple[bool, List[str]]:
        """验证JSON文件

        Args:
            file_path: JSON文件路径

        Returns:
            (是否成功, 错误列表)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self.validate(data)
        except FileNotFoundError:
            return False, [f"File not found: {file_path}"]
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {e}"]
        except Exception as e:
            return False, [f"Unexpected error: {str(e)}"]

    def validate_vocabularies(self, vocabularies: List[dict]) -> Tuple[bool, List[str]]:
        """验证词汇列表

        Args:
            vocabularies: 词汇列表

        Returns:
            (是否成功, 错误列表)
        """
        wrapper = {"vocabularies": vocabularies}
        errors = []

        try:
            jsonschema.validate(wrapper, self.schema)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(f"Validation error: {e.message}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected error: {str(e)}")
            return False, errors


def get_content_validator() -> ContentValidator:
    """获取内容验证器

    Returns:
        ContentValidator实例
    """
    # 路径：backend/app/utils/content_validators.py -> backend/data/schemas/
    import os
    backend_path = Path(__file__).resolve().parent.parent.parent
    schema_path = backend_path / "data" / "schemas" / "content.schema.json"
    return ContentValidator(str(schema_path))


def get_vocabulary_validator() -> VocabularyValidator:
    """获取词汇验证器

    Returns:
        VocabularyValidator实例
    """
    import os
    backend_path = Path(__file__).resolve().parent.parent.parent
    schema_path = backend_path / "data" / "schemas" / "vocabulary.schema.json"
    return VocabularyValidator(str(schema_path))
