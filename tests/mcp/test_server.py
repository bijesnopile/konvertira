import pytest
from fastapi.testclient import TestClient

from backend.services.resource_limits import McpRateLimitError, mcp_resource_limits
from mcp_server import app


def test_mcp_health_and_independent_transport_rate_limit() -> None:
    previous_enabled = mcp_resource_limits.rate_limits_enabled
    previous_limit = mcp_resource_limits.request_limit
    previous_heavy_limit = mcp_resource_limits.heavy_limit
    mcp_resource_limits.rate_limits_enabled = True
    mcp_resource_limits.request_limit = 5
    mcp_resource_limits.heavy_limit = 1
    mcp_resource_limits.clear()
    try:
        mcp_resource_limits.check_heavy_job("test")
        with pytest.raises(McpRateLimitError):
            mcp_resource_limits.check_heavy_job("test")

        with TestClient(app, follow_redirects=False) as client:
            initial_health = client.get("/health")
            mcp_resource_limits.clear()
            responses = [client.post("/mcp") for _ in range(6)]
            health = client.get("/health")

        assert initial_health.status_code == 200
        assert initial_health.json()["status"] == "ok"
        assert all(response.status_code != 429 for response in responses[:5])
        assert responses[5].status_code == 429
        assert "retry-after" in responses[5].headers
        assert health.status_code == 200
    finally:
        mcp_resource_limits.clear()
        mcp_resource_limits.request_limit = previous_limit
        mcp_resource_limits.heavy_limit = previous_heavy_limit
        mcp_resource_limits.rate_limits_enabled = previous_enabled
