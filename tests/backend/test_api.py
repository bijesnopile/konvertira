from fastapi.testclient import TestClient

from backend.services.rate_limit import request_limiter
from main import app


def test_fastapi_health_and_startup() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_remove_metadata_endpoint(jpeg_with_metadata: bytes) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/images/remove-metadata",
            files={"file": ("photo.jpg", jpeg_with_metadata, "image/jpeg")},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/jpeg")
    assert "clean_photo.jpg" in response.headers["content-disposition"]


def test_public_conversion_endpoint(jpeg_with_metadata: bytes) -> None:
    with TestClient(app) as client:
        response = client.post(
            "/images/convert",
            files={"file": ("photo.jpg", jpeg_with_metadata, "image/jpeg")},
            data={"format": "png"},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")


def test_heavy_endpoint_returns_429_and_health_stays_available(
    jpeg_with_metadata: bytes,
) -> None:
    previous_enabled = request_limiter.enabled
    request_limiter.enabled = True
    request_limiter.clear()
    try:
        with TestClient(app) as client:
            responses = [
                client.post(
                    "/images/remove-metadata",
                    files={"file": ("photo.jpg", jpeg_with_metadata, "image/jpeg")},
                )
                for _ in range(6)
            ]
            health = client.get("/health")

        assert all(response.status_code == 200 for response in responses[:5])
        assert responses[5].status_code == 429
        assert int(responses[5].headers["retry-after"]) >= 1
        assert responses[5].json()["detail"].startswith("Too many requests")
        assert health.status_code == 200
    finally:
        request_limiter.clear()
        request_limiter.enabled = previous_enabled
