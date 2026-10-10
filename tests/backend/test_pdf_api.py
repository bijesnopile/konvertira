import io
import zipfile

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader

from backend.services.rate_limit import request_limiter
from main import app
from tests.backend.test_pdf_processor import colored_pdf


@pytest.mark.parametrize("route,data,count", [
    ("extract", {"pages": "3,1"}, 2),
    ("reorder", {"order": "3,1,2"}, 3),
    ("delete-pages", {"pages": "2"}, 2),
    ("remove-metadata", {}, 3),
    ("optimize", {}, 3),
    ("split", {}, 3),
])
def test_pdf_operations_api(route, data, count) -> None:
    request_limiter.clear()
    with TestClient(app) as client:
        response = client.post(f"/pdf/{route}", files={"file": ("source.pdf", colored_pdf(), "application/pdf")}, data=data)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-konvertira-page-count"] == str(count)
    if route == "split":
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            assert archive.namelist() == [f"page-{i:04d}.pdf" for i in range(1, 4)]
    else:
        assert len(PdfReader(io.BytesIO(response.content)).pages) == count


@pytest.mark.parametrize("format,extension", [("png", "png"), ("jpeg", "jpg"), ("webp", "webp")])
def test_pdf_render_api(format, extension) -> None:
    request_limiter.clear()
    with TestClient(app) as client:
        response = client.post("/pdf/to-images", files={"file": ("source.pdf", colored_pdf(), "application/pdf")}, data={"format": format, "dpi": "72", "pages": "3,1"})
    assert response.status_code == 200
    assert 'filename="pdf-images.zip"' in response.headers["content-disposition"]
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.namelist() == [f"page-0001.{extension}", f"page-0002.{extension}"]
        with Image.open(io.BytesIO(archive.read(archive.namelist()[0]))) as image:
            assert image.size == (300, 60)


def test_pdf_inspection_and_invalid_page_api() -> None:
    request_limiter.clear()
    with TestClient(app) as client:
        file = {"file": ("source.pdf", colored_pdf(), "application/pdf")}
        assert client.post("/pdf/inspect-metadata", files=file).json()["page_count"] == 3
        assert client.post("/pdf/to-images", files=file, data={"pages": "99"}).status_code == 422


def test_merge_and_images_to_pdf_api() -> None:
    request_limiter.clear()
    with TestClient(app) as client:
        response = client.post("/pdf/merge", files=[("files", ("one.pdf", colored_pdf(), "application/pdf")), ("files", ("two.pdf", colored_pdf(), "application/pdf"))])
        assert response.status_code == 200
        assert len(PdfReader(io.BytesIO(response.content)).pages) == 6
        with Image.new("RGB", (16, 12), "red") as image, io.BytesIO() as source:
            image.save(source, format="PNG")
            response = client.post("/pdf/images-to-pdf", files=[("files", ("one.png", source.getvalue(), "image/png"))])
        assert response.status_code == 200
        assert len(PdfReader(io.BytesIO(response.content)).pages) == 1
