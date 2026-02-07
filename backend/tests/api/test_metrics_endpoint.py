"""
测试 /metrics 端点

验证 Prometheus 监控指标端点的正确性。
"""
import pytest
from httpx import AsyncClient


class TestMetricsEndpoint:
    """测试 /metrics 端点"""

    async def test_metrics_endpoint_exists(
        self, test_client: AsyncClient
    ) -> None:
        """测试端点存在，返回 200"""
        response = await test_client.get("/metrics")
        assert response.status_code == 200
        assert isinstance(response.content, bytes)

    async def test_metrics_content_type(
        self, test_client: AsyncClient
    ) -> None:
        """测试返回正确的 content-type"""
        response = await test_client.get("/metrics")
        assert response.status_code == 200
        # Prometheus content-type 是 text/plain 的变种
        content_type = response.headers.get("content-type", "")
        assert "text/plain" in content_type
        # 应该包含版本信息
        assert "version" in content_type

    async def test_metrics_format(
        self, test_client: AsyncClient
    ) -> None:
        """测试返回内容包含所有指标名称"""
        response = await test_client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        # 验证包含导出相关的指标
        assert "export_tasks_total" in content
        assert "export_task_duration_seconds" in content
        assert "export_tasks_active" in content
        assert "export_tasks_queued" in content
        assert "export_storage_bytes" in content
        assert "export_errors_total" in content

    async def test_metrics_include_help_and_type(
        self, test_client: AsyncClient
    ) -> None:
        """测试包含 HELP 和 TYPE 信息"""
        response = await test_client.get("/metrics")
        assert response.status_code == 200
        content = response.text

        # 验证包含 HELP 指令（指标说明）
        assert "# HELP" in content

        # 验证包含 TYPE 指令（指标类型）
        assert "# TYPE" in content

        # 验证具体的指标类型
        assert 'export_tasks_total counter' in content
        assert 'export_task_duration_seconds histogram' in content
        assert 'export_tasks_active gauge' in content
        assert 'export_tasks_queued gauge' in content
        assert 'export_storage_bytes gauge' in content
        assert 'export_errors_total counter' in content

    async def test_metrics_not_in_schema(
        self, test_client: AsyncClient
    ) -> None:
        """测试端点不在 OpenAPI schema 中"""
        # 获取 OpenAPI schema
        response = await test_client.get("/api/openapi.json")
        assert response.status_code == 200
        openapi_schema = response.json()

        # 验证 /metrics 不在 paths 中
        assert "/metrics" not in openapi_schema.get("paths", {})

        # 验证常规端点仍在 schema 中
        assert "/health" in openapi_schema.get("paths", {})

    async def test_metrics_endpoint_after_api_routes(
        self, test_client: AsyncClient
    ) -> None:
        """测试在访问其他路由后仍可用"""
        # 先访问其他路由
        await test_client.get("/health")
        await test_client.get("/")

        # 然后访问 metrics
        response = await test_client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        assert "export_tasks_total" in content
