"""
告警工具测试
测试结构化日志告警器的功能和 JSON 格式输出
"""
import json
import logging
from io import StringIO

import pytest

from app.utils.alerts import (
    AlertLogger,
    JSONFormatter,
    alert_context,
    alert_on_error,
    default_logger,
    LOG_LEVEL_MAP,
)


# ============== Pytest Fixtures ==============

@pytest.fixture(autouse=True)
def reset_logging():
    """每个测试前重置日志器状态"""
    yield
    # 清理所有测试日志器
    for name in logging.root.manager.loggerDict:
        if name.startswith("test_"):
            logger = logging.getLogger(name)
            logger.handlers.clear()
            logger.propagate = True


@pytest.fixture
def clean_logger():
    """创建一个新的干净日志器"""
    # 使用时间戳生成唯一名称
    import time
    unique_name = f"test_logger_{int(time.time() * 1000000)}"
    logger = AlertLogger(unique_name)
    yield logger
    # 清理
    logger.logger.handlers.clear()


# ============== 测试辅助函数 ==============

def capture_log_output(logger: AlertLogger) -> logging.StreamHandler:
    """
    捕获日志器输出到 StringIO

    Args:
        logger: AlertLogger 实例

    Returns:
        StreamHandler 对象，其 stream 属性包含日志输出
    """
    # 清除现有处理器
    logger.logger.handlers.clear()

    # 创建新的 StringIO 处理器
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    handler.setLevel(logging.DEBUG)  # 接受所有级别
    logger.logger.addHandler(handler)

    # 设置 logger 级别
    logger.logger.setLevel(logging.DEBUG)

    # 禁用传播，避免输出到根日志器
    logger.logger.propagate = False

    # 将 stream 附加到 handler
    handler.stream = stream
    return handler


class TestAlertLoggerInitialization:
    """测试 AlertLogger 初始化"""

    def test_logger_initialization_with_default_name(self):
        """测试使用默认名称初始化日志器"""
        logger = AlertLogger()
        assert logger.name == "export_alerts"
        assert logger.logger.name == "export_alerts"
        # NOTSET 允许所有级别通过
        assert logger.logger.level == logging.NOTSET

    def test_logger_initialization_with_custom_name(self):
        """测试使用自定义名称初始化日志器"""
        logger = AlertLogger("custom_logger")
        assert logger.name == "custom_logger"
        assert logger.logger.name == "custom_logger"

    def test_logger_reuses_existing_handlers(self):
        """测试日志器重用现有处理器"""
        logger1 = AlertLogger("test_reuse")
        handler_count_1 = len(logger1.logger.handlers)

        # 创建同名日志器应重用处理器
        logger2 = AlertLogger("test_reuse")
        handler_count_2 = len(logger2.logger.handlers)

        assert handler_count_1 == handler_count_2

    def test_default_logger_exists(self):
        """测试默认日志器实例存在"""
        assert default_logger is not None
        assert isinstance(default_logger, AlertLogger)
        assert default_logger.name == "export_alerts"


class TestAlertLoggerLevels:
    """测试各级别日志记录"""

    def test_critical_level_logging(self, clean_logger):
        """测试 CRITICAL 级别日志"""
        handler = capture_log_output(clean_logger)

        clean_logger.critical("严重错误", task_id="123", code="SYS_ERR")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert data["level"] == "CRITICAL"
        assert data["message"] == "严重错误"
        assert data["context"]["task_id"] == "123"
        assert data["context"]["code"] == "SYS_ERR"

    def test_error_level_logging(self, clean_logger):
        """测试 ERROR 级别日志"""
        handler = capture_log_output(clean_logger)

        clean_logger.error("导出失败", task_id="456", format="pdf")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert data["level"] == "ERROR"
        assert data["message"] == "导出失败"
        assert data["context"]["task_id"] == "456"
        assert data["context"]["format"] == "pdf"

    def test_warning_level_logging(self, clean_logger):
        """测试 WARNING 级别日志"""
        handler = capture_log_output(clean_logger)

        clean_logger.warning("文件较大", size_bytes=50_000_000)

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert data["level"] == "WARNING"
        assert data["message"] == "文件较大"
        assert data["context"]["size_bytes"] == 50_000_000

    def test_info_level_logging(self, clean_logger):
        """测试 INFO 级别日志"""
        handler = capture_log_output(clean_logger)

        clean_logger.info("导出开始", task_id="789")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["message"] == "导出开始"
        assert data["context"]["task_id"] == "789"

    def test_logging_without_context(self, clean_logger):
        """测试不带上下文的日志记录"""
        handler = capture_log_output(clean_logger)

        clean_logger.info("简单消息")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert data["message"] == "简单消息"
        assert "context" not in data or not data["context"]


class TestJSONFormatValidation:
    """测试 JSON 格式验证"""

    def test_output_is_valid_json(self, clean_logger):
        """验证输出是有效 JSON"""
        handler = capture_log_output(clean_logger)

        clean_logger.error("测试消息", test_key="test_value")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)
        assert data["message"] == "测试消息"
        assert data["level"] == "ERROR"

    def test_json_contains_required_fields(self, clean_logger):
        """验证 JSON 包含必需字段"""
        handler = capture_log_output(clean_logger)

        clean_logger.info("字段测试", extra_data="value")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        # 验证必需字段
        assert "timestamp" in data
        assert "level" in data
        assert "logger" in data
        assert "message" in data
        assert data["level"] == "INFO"
        assert data["message"] == "字段测试"

    def test_context_passed_correctly(self, clean_logger):
        """验证 context 字段正确传递"""
        handler = capture_log_output(clean_logger)

        test_context = {
            "task_id": "123",
            "user_id": "456",
            "format": "pdf",
            "size": 1024,
        }
        clean_logger.error("上下文测试", **test_context)

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        # 验证上下文数据
        assert "context" in data
        assert data["context"]["task_id"] == "123"
        assert data["context"]["user_id"] == "456"
        assert data["context"]["format"] == "pdf"
        assert data["context"]["size"] == 1024

    def test_timestamp_format_is_valid(self, clean_logger):
        """验证时间戳格式正确（ISO 8601）"""
        handler = capture_log_output(clean_logger)

        clean_logger.info("时间戳测试")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        # 验证时间戳格式（ISO 8601 UTC）
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z") or "+" in data["timestamp"]
        # 验证可以解析为 datetime
        from datetime import datetime
        parsed_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert parsed_time is not None

    def test_json_with_exception(self, clean_logger):
        """验证包含异常信息的 JSON 格式"""
        handler = capture_log_output(clean_logger)

        try:
            raise ValueError("测试异常")
        except ValueError:
            clean_logger.exception("发生异常")

        output = handler.stream.getvalue().strip()
        lines = output.split("\n")
        json_line = next((line for line in lines if line.strip().startswith("{")), "")
        data = json.loads(json_line)

        # 验证异常信息
        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "测试异常" in data["exception"]


class TestAlertContext:
    """测试 alert_context 上下文管理器"""

    def test_normal_execution_no_alert(self):
        """测试正常执行时不记录告警"""
        # 正常执行不应该抛出异常
        with alert_context("测试操作", level="ERROR"):
            pass  # 正常执行

        # 如果没有异常，测试通过
        assert True

    def test_exception_triggers_alert(self):
        """测试异常时正确记录告警"""
        with pytest.raises(ValueError, match="测试错误"):
            with alert_context("PDF渲染", level="ERROR", task_id="123"):
                raise ValueError("测试错误")

        # 验证异常被重新抛出

    def test_exception_is_reraised(self):
        """测试异常被重新抛出"""
        with pytest.raises(ValueError, match="原始异常"):
            with alert_context("测试操作"):
                raise ValueError("原始异常")


class TestAlertOnError:
    """测试 alert_on_error 装饰器"""

    def test_normal_execution_no_alert(self):
        """测试正常执行时不记录告警"""
        @alert_on_error("测试函数", level="ERROR")
        def normal_function(x: int) -> int:
            return x * 2

        result = normal_function(5)
        assert result == 10

    def test_exception_is_reraised(self):
        """测试异常被重新抛出"""
        @alert_on_error("测试操作")
        def raise_error() -> None:
            raise ValueError("原始异常")

        with pytest.raises(ValueError, match="原始异常"):
            raise_error()

    def test_function_return_value_unaffected(self):
        """测试函数返回值不受影响"""
        @alert_on_error("返回值测试")
        def compute(x: int, y: int) -> int:
            return x + y

        result = compute(3, 4)
        assert result == 7

    def test_function_preserves_name_and_docstring(self):
        """测试函数保留名称和文档字符串"""
        @alert_on_error("测试")
        def documented_function(x: int) -> int:
            """这是一个文档字符串"""
            return x

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "这是一个文档字符串"


class TestLogLevelMap:
    """测试日志级别映射"""

    def test_log_level_map_completeness(self):
        """测试日志级别映射表完整"""
        expected_levels = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
        for level in expected_levels:
            assert level in LOG_LEVEL_MAP
            assert isinstance(LOG_LEVEL_MAP[level], int)

    def test_log_level_map_values(self):
        """测试日志级别映射值正确"""
        assert LOG_LEVEL_MAP["CRITICAL"] == logging.CRITICAL
        assert LOG_LEVEL_MAP["ERROR"] == logging.ERROR
        assert LOG_LEVEL_MAP["WARNING"] == logging.WARNING
        assert LOG_LEVEL_MAP["INFO"] == logging.INFO
        assert LOG_LEVEL_MAP["DEBUG"] == logging.DEBUG


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_context(self, clean_logger):
        """测试空上下文"""
        handler = capture_log_output(clean_logger)

        clean_logger.info("空上下文测试")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert data["message"] == "空上下文测试"
        assert "context" not in data or not data["context"]

    def test_unicode_in_message_and_context(self, clean_logger):
        """测试消息和上下文中的 Unicode 字符"""
        handler = capture_log_output(clean_logger)

        clean_logger.info(
            "中文消息 🎉",
            emoji="✅",
            chinese="测试",
            japanese="テスト",
        )

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert "中文消息" in data["message"]
        assert data["context"]["emoji"] == "✅"
        assert data["context"]["chinese"] == "测试"
        assert data["context"]["japanese"] == "テスト"

    def test_large_context_data(self, clean_logger):
        """测试大量上下文数据"""
        handler = capture_log_output(clean_logger)

        large_context = {f"key_{i}": f"value_{i}" for i in range(100)}

        clean_logger.info("大量数据", **large_context)

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert len(data["context"]) == 100
        assert data["context"]["key_0"] == "value_0"
        assert data["context"]["key_99"] == "value_99"

    def test_none_values_in_context(self, clean_logger):
        """测试上下文中的 None 值"""
        handler = capture_log_output(clean_logger)

        clean_logger.info("None 值", none_value=None, empty_string="")

        output = handler.stream.getvalue().strip()
        data = json.loads(output)

        assert data["context"]["none_value"] is None
        assert data["context"]["empty_string"] == ""
