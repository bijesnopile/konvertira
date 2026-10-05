from fastapi.testclient import TestClient

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
