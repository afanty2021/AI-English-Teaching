"""
结构化日志告警工具

提供 JSON 格式的结构化日志记录，用于导出监控系统告警。
支持上下文管理器和装饰器，简化异常捕获和告警记录。

示例:
    >>> from app.utils.alerts import AlertLogger, alert_context, alert_on_error
    >>>
    >>> # 使用 AlertLogger 直接记录
    >>> logger = AlertLogger("export_service")
    >>> logger.error("导出失败", task_id="123", user_id="456", format="pdf")
    >>>
    >>> # 使用上下文管理器
    >>> with alert_context("导出处理", level="ERROR", task_id="123"):
    ...     risky_operation()
    >>>
    >>> # 使用装饰器
    >>> @alert_on_error("PDF渲染", level="CRITICAL", format="pdf")
    ... def render_pdf(content: str) -> bytes:
    ...     ...
"""
import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Generator, TypeVar

from app.core.config import settings

# ============== 类型定义 ==============

T = TypeVar("T")

# ============== 日志级别映射 ==============

LOG_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}


# ============== JSON 格式化器 ==============

class JSONFormatter(logging.Formatter):
    """
    JSON 格式化器

    将日志记录格式化为 JSON 格式，包含时间戳、级别、消息和上下文数据。
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        格式化日志记录为 JSON

        Args:
            record: 日志记录对象

        Returns:
            JSON 格式的日志字符串
        """
        # 创建基础日志数据
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 添加异常信息（如果有）
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加上下文数据（如果有）
        if hasattr(record, "context") and record.context:
            log_data["context"] = record.context

        # 添加其他标准字段
        if record.pathname:
            log_data["file"] = record.pathname
        if record.lineno:
            log_data["line"] = record.lineno
        if record.funcName:
            log_data["function"] = record.funcName

        return json.dumps(log_data, ensure_ascii=False)


# ============== AlertLogger 类 ==============

class AlertLogger:
    """
    结构化日志告警器

    提供 JSON 格式的日志记录，支持结构化上下文数据。

    Attributes:
        name: 日志器名称
        logger: Python logging.Logger 实例

    Example:
        >>> logger = AlertLogger("export_service")
        >>> logger.error("导出失败", task_id="123", user_id="456")
    """

    def __init__(self, name: str = "export_alerts") -> None:
        """
        初始化告警器

        Args:
            name: 日志器名称，默认为 "export_alerts"
        """
        self.name = name
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        设置日志器

        创建并配置带有 JSON 格式化器的日志器。

        Returns:
            配置好的 logging.Logger 实例
        """
        logger = logging.getLogger(self.name)

        # 如果已有处理器，直接返回
        if logger.handlers:
            return logger

        # 设置日志级别为 NOTSET，允许所有级别通过
        logger.setLevel(logging.NOTSET)

        # 创建控制台处理器
        handler = logging.StreamHandler()
        # 处理器级别也设为 NOTSET，允许所有级别通过
        handler.setLevel(logging.NOTSET)

        # 设置 JSON 格式化器
        formatter = JSONFormatter()
        handler.setFormatter(formatter)

        # 添加处理器
        logger.addHandler(handler)

        # 允许传播到根日志器（这样测试中的 caplog 才能捕获）
        logger.propagate = True

        return logger

    def _log(
        self,
        level: str,
        message: str,
        **context: Any,
    ) -> None:
        """
        内部日志记录方法

        Args:
            level: 日志级别（CRITICAL, ERROR, WARNING, INFO, DEBUG）
            message: 日志消息
            **context: 上下文数据
        """
        log_level = LOG_LEVEL_MAP.get(level.upper(), logging.INFO)

        # 创建额外记录
        extra: dict[str, Any] = {}
        if context:
            extra["context"] = context

        # 如果没有处理器，添加一个（避免在测试中自动添加）
        # 注意：测试中应该通过 capture_log_output 预先设置处理器
        self.logger.log(log_level, message, extra=extra)

    def critical(self, message: str, **context: Any) -> None:
        """
        记录 CRITICAL 级别告警

        用于严重错误，需要立即关注。

        Args:
            message: 告警消息
            **context: 上下文数据（如 task_id, user_id, format 等）

        Example:
            >>> logger.critical("系统崩溃", task_id="123", error="memory_error")
        """
        self._log("CRITICAL", message, **context)

    def error(self, message: str, **context: Any) -> None:
        """
        记录 ERROR 级别告警

        用于错误事件，但系统仍可继续运行。

        Args:
            message: 告警消息
            **context: 上下文数据

        Example:
            >>> logger.error("导出失败", task_id="123", format="pdf")
        """
        self._log("ERROR", message, **context)

    def warning(self, message: str, **context: Any) -> None:
        """
        记录 WARNING 级别告警

        用于警告事件，可能需要注意但不影响运行。

        Args:
            message: 告警消息
            **context: 上下文数据

        Example:
            >>> logger.warning("文件较大", task_id="123", size_bytes=50_000_000)
        """
        self._log("WARNING", message, **context)

    def info(self, message: str, **context: Any) -> None:
        """
        记录 INFO 级别日志

        用于常规信息记录。

        Args:
            message: 日志消息
            **context: 上下文数据

        Example:
            >>> logger.info("导出开始", task_id="123", format="pdf")
        """
        self._log("INFO", message, **context)

    def exception(self, message: str, **context: Any) -> None:
        """
        记录异常日志（包含堆栈跟踪）

        用于记录异常信息，自动包含堆栈跟踪。

        Args:
            message: 日志消息
            **context: 上下文数据

        Example:
            >>> try:
            ...     risky_operation()
            ... except Exception:
            ...     logger.exception("操作失败", task_id="123")
        """
        log_level = LOG_LEVEL_MAP.get("ERROR", logging.ERROR)

        # 创建额外记录
        extra: dict[str, Any] = {}
        if context:
            extra["context"] = context

        # 使用 logging.exception 的方式记录，自动包含堆栈跟踪
        self.logger.log(log_level, message, exc_info=True, extra=extra)


# ============== 上下文管理器 ==============

@contextmanager
def alert_context(
    operation: str,
    level: str = "ERROR",
    **context: Any,
) -> Generator[AlertLogger, None, None]:
    """
    捕获异常并记录告警的上下文管理器

    自动捕获代码块中的异常并记录告警日志。

    Args:
        operation: 操作描述（如 "PDF渲染", "文件写入"）
        level: 日志级别（默认 ERROR）
        **context: 额外的上下文数据

    Yields:
        AlertLogger 实例，可用于手动记录

    Raises:
        原始异常：不会抑制异常，只记录告警

    Example:
        >>> with alert_context("PDF导出", level="ERROR", task_id="123"):
        ...     risky_pdf_operation()
    """
    logger = AlertLogger()

    try:
        yield logger
    except Exception as e:
        # 构建告警消息
        message = f"{operation}失败: {type(e).__name__}"

        # 添加异常信息到上下文
        error_context = {
            "operation": operation,
            "exception_type": type(e).__name__,
            "exception_message": str(e),
            **context,
        }

        # 记录告警
        log_method = getattr(logger, level.lower(), logger.error)
        log_method(message, **error_context)

        # 重新抛出异常
        raise


# ============== 装饰器 ==============

def alert_on_error(
    operation: str,
    level: str = "ERROR",
    **context: Any,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    捕获函数异常并记录告警的装饰器

    自动捕获被装饰函数的异常并记录告警日志。

    Args:
        operation: 操作描述
        level: 日志级别（默认 ERROR）
        **context: 额外的上下文数据

    Returns:
        装饰器函数

    Example:
        >>> @alert_on_error("PDF渲染", level="CRITICAL", format="pdf")
        ... def render_pdf(content: str) -> bytes:
        ...     # 渲染逻辑
        ...     return pdf_bytes
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            logger = AlertLogger()
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 构建告警消息
                message = f"{operation}失败: {type(e).__name__}"

                # 添加异常信息到上下文
                error_context = {
                    "operation": operation,
                    "function": func.__name__,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e),
                    **context,
                }

                # 记录告警
                log_method = getattr(logger, level.lower(), logger.error)
                log_method(message, **error_context)

                # 重新抛出异常
                raise

        return wrapper

    return decorator


# ============== 默认导出 ==============

# 默认告警器实例
default_logger = AlertLogger()
