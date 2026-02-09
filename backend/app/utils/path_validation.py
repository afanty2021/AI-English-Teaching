"""
路径验证工具 - 防止路径遍历攻击

提供安全的路径验证函数，防止路径遍历（directory traversal）攻击。
"""
import os
from pathlib import Path
from typing import Optional


class PathValidationError(Exception):
    """路径验证错误"""
    pass


def validate_template_path(
    template_path: str,
    allowed_base_dir: Optional[str] = None
) -> str:
    """
    验证模板路径是否安全

    防止路径遍历攻击，确保路径在允许的目录内。

    Args:
        template_path: 用户提供的模板路径
        allowed_base_dir: 允许的基础目录（绝对路径）。
                         如果为 None，则使用项目的 templates 目录

    Returns:
        验证后的安全路径（规范化为相对路径）

    Raises:
        PathValidationError: 路径不安全时

    安全检查:
        1. 拒绝绝对路径（以 / 开头）
        2. 拒绝父目录引用（路径遍历尝试）
        3. 拒绝空路径
        4. 验证路径在允许的目录内（如果提供）
    """
    if not template_path or not template_path.strip():
        raise PathValidationError("模板路径不能为空")

    # 检查反斜杠（Windows路径分隔符）
    if "\\" in template_path:
        raise PathValidationError(
            "模板路径不能包含反斜杠，请使用正斜杠 (/)"
        )

    # 检查绝对路径
    if os.path.isabs(template_path):
        raise PathValidationError(
            "模板路径不能是绝对路径，请使用相对路径"
        )

    # 规范化路径（处理 ./ 和多余的斜杠）
    normalized_path = os.path.normpath(template_path)

    # 检查父目录引用（路径遍历）
    # 必须在规范化前后都进行检查，防止路径遍历攻击
    # 1. 检查原始路径中是否包含 ..（规范化前检查）
    if ".." in template_path:
        raise PathValidationError(
            "模板路径不能包含父目录引用 (..)"
        )

    # 2. 规范化后路径以 .. 开头表示试图访问父目录
    if normalized_path.startswith(".."):
        raise PathValidationError(
            "模板路径不能包含父目录引用 (..)"
        )

    # 如果提供了允许的基础目录，验证最终路径在该目录内
    if allowed_base_dir:
        base_dir = Path(allowed_base_dir).resolve()
        full_path = (base_dir / normalized_path).resolve()

        # 检查解析后的路径是否仍在基础目录内
        try:
            full_path.relative_to(base_dir)
        except ValueError:
            raise PathValidationError(
                f"模板路径必须在 {allowed_base_dir} 目录内"
            )

    return normalized_path


def is_safe_template_path(template_path: str) -> bool:
    """
    快速检查模板路径是否安全

    Args:
        template_path: 要检查的模板路径

    Returns:
        True 如果路径安全，否则 False
    """
    try:
        validate_template_path(template_path)
        return True
    except PathValidationError:
        return False


def sanitize_template_path(template_path: str) -> str:
    """
    清理并验证模板路径

    移除危险字符并进行验证。

    Args:
        template_path: 用户输入的模板路径

    Returns:
        清理后的安全路径

    Raises:
        PathValidationError: 如果路径包含不安全内容
    """
    if not template_path:
        raise PathValidationError("模板路径不能为空")

    # 移除危险字符
    cleaned = template_path.strip()
    cleaned = cleaned.replace("\\", "/")  # 统一使用正斜杠

    # 移除开头的斜杠（转换为相对路径）
    if cleaned.startswith("/"):
        cleaned = cleaned.lstrip("/")

    # 验证清理后的路径
    return validate_template_path(cleaned)
