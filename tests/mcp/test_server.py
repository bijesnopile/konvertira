from fastapi.testclient import TestClient

from mcp_server import app


def test_mcp_app_health_route() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
