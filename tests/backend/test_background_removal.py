import io
import os
import threading
import asyncio
from dataclasses import replace

import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.models.files import FileProcessingError
from backend.processors import background_removal as processor
from backend.services.rate_limit import request_limiter
from backend.services.resource_limits import McpResourceLimits
from backend.services.storage import TemporaryStorage
from konvertira_mcp.tools import common, workflows
from konvertira_mcp.models.files import OpenAIFile
from main import app
from backend.routers import background_removal as routes


def image_bytes(format="PNG", animated=False):
    output = io.BytesIO()
    image = Image.new("RGB", (8, 6), "red")
    exif = Image.Exif()
    exif[0x010E] = "private"
    if animated:
        image.save(output, format="GIF", save_all=True, append_images=[Image.new("RGB", (8, 6), "blue")])
    else:
        image.save(output, format=format, exif=exif)
    image.close()
    return output.getvalue()


@pytest.fixture
def inference(monkeypatch):
    def mask(image):
        result = Image.new("L", image.size, 255)
        result.putpixel((0, 0), 0)
        return result
    monkeypatch.setattr(processor, "_segment", mask)
    request_limiter.clear()
    return mask


@pytest.mark.parametrize("input_format", ["JPEG", "PNG", "WEBP", "GIF"])
@pytest.mark.parametrize("output_format", ["png", "webp"])
def test_transparent_metadata_free_output(inference, input_format, output_format):
    result = processor.remove_image_background(image_bytes(input_format), output_format=output_format)
    with Image.open(io.BytesIO(result.content)) as image:
        assert image.mode == "RGBA"
        assert image.getchannel("A").getextrema() == (0, 255)
        assert not image.getexif()
        assert "exif" not in image.info


def test_rejections(inference, monkeypatch):
    with pytest.raises(FileProcessingError):
        processor.remove_image_background(b"broken")
    with pytest.raises(FileProcessingError, match="PNG or WebP"):
        processor.remove_image_background(image_bytes(), output_format="jpeg")
    with pytest.raises(FileProcessingError, match="Animated"):
        processor.remove_image_background(image_bytes(animated=True))
    monkeypatch.setattr(processor, "settings", replace(processor.settings, max_image_size=10))
    with pytest.raises(FileProcessingError):
        processor.remove_image_background(image_bytes())
    monkeypatch.setattr(processor, "settings", replace(processor.settings, max_image_size=100000, background_max_pixels=10))
    with pytest.raises(FileProcessingError, match="pixel limit"):
        processor.remove_image_background(image_bytes())


def test_existing_alpha_and_orientation(inference):
    output = io.BytesIO()
    image = Image.new("RGBA", (8, 6), (255, 0, 0, 64))
    exif = Image.Exif()
    exif[274] = 6
    image.save(output, format="PNG", exif=exif)
    result = processor.remove_image_background(output.getvalue())
    with Image.open(io.BytesIO(result.content)) as clean:
        assert clean.size == (6, 8)
        assert clean.getchannel("A").getextrema() == (0, 64)


def test_missing_model_fails_without_download(monkeypatch, tmp_path):
    monkeypatch.setattr(processor, "settings", replace(processor.settings, background_model_dir=tmp_path))
    monkeypatch.setattr(processor, "_session", None)
    with pytest.raises(FileProcessingError, match="unavailable"):
        processor._get_session()


def test_inference_rejects_competing_job():
    processor._inference_lock.acquire()
    try:
        with Image.new("RGBA", (1, 1)) as image, pytest.raises(FileProcessingError, match="busy"):
            processor._segment(image)
    finally:
        processor._inference_lock.release()


@pytest.mark.parametrize("output_format", ["png", "webp"])
def test_api_success_and_bad_inputs(inference, output_format):
    with TestClient(app) as client:
        response = client.post("/images/remove-background", files={"file": ("photo.png", image_bytes(), "image/png")}, data={"output_format": output_format})
        assert response.status_code == 200
        assert response.headers["content-type"] == f"image/{output_format}"
        assert "Automatic segmentation" in response.headers["x-konvertira-privacy-warning"]
        bad = client.post("/images/remove-background", files={"file": ("photo.png", b"broken", "image/png")})
        assert bad.status_code == 400
        wrong = client.post("/images/remove-background", files={"file": ("photo.jpg", image_bytes(), "image/jpeg")})
        assert wrong.status_code == 415
        unsupported = client.post("/images/remove-background", files={"file": ("a.pdf", b"%PDF", "application/pdf")})
        assert unsupported.status_code == 415
        output = client.post("/images/remove-background", files={"file": ("photo.png", image_bytes(), "image/png")}, data={"output_format": "jpeg"})
        assert output.status_code == 422


def test_mcp_output_and_shared_processor(inference, monkeypatch, tmp_path):
    async def download(*args, **kwargs):
        return image_bytes()
    monkeypatch.setattr(workflows, "download_input", download)
    monkeypatch.setattr(common, "mcp_storage", TemporaryStorage(tmp_path, 900))
    common.mcp_resource_limits.clear()
    file = OpenAIFile(download_url="https://files.oaiusercontent.com/example", file_id="file", file_name="a.png", mime_type="image/png")
    result = asyncio.run(workflows.remove_image_background(file, processor.BackgroundOutputFormat.WEBP))
    assert result.success and result.content_type == "image/webp"
    assert result.filename == "a.webp"
    assert "Automatic segmentation" in result.message
    with pytest.raises(ValueError, match="not supported"):
        asyncio.run(workflows.remove_image_background(file.model_copy(update={"file_name": "a.pdf", "mime_type": "application/pdf"})))


def test_mcp_storage_capacity(inference, monkeypatch, tmp_path):
    async def download(*args, **kwargs):
        return image_bytes()
    monkeypatch.setattr(workflows, "download_input", download)
    monkeypatch.setattr(common, "mcp_storage", TemporaryStorage(tmp_path, 900, max_bytes=1))
    common.mcp_resource_limits.clear()
    file = OpenAIFile(download_url="https://files.oaiusercontent.com/example", file_id="file", file_name="a.png", mime_type="image/png")
    with pytest.raises(ValueError, match="storage is currently full"):
        asyncio.run(workflows.remove_image_background(file))


def test_api_rate_limits(inference):
    previous = request_limiter.enabled
    request_limiter.enabled = True
    request_limiter.clear()
    try:
        with TestClient(app) as client:
            responses = [client.post("/images/remove-background", files={"file": ("photo.png", image_bytes(), "image/png")}) for _ in range(6)]
            assert responses[0].status_code == 200
            assert responses[-1].status_code == 429
            assert client.get("/health").status_code == 200
    finally:
        request_limiter.enabled = previous
        request_limiter.clear()


def test_api_timeout_retains_worker_until_finished(inference, monkeypatch):
    from backend.services.rate_limit import processing_capacity
    finish = threading.Event()
    started = threading.Event()
    original = processor.remove_image_background
    def slow(*args, **kwargs):
        started.set()
        finish.wait(2)
        return original(*args, **kwargs)
    monkeypatch.setattr(routes, "remove_image_background", slow)
    monkeypatch.setattr(routes, "settings", replace(routes.settings, background_timeout_seconds=0.05))
    previous = processing_capacity.enabled
    processing_capacity.enabled = True
    try:
        with TestClient(app) as client:
            response = client.post("/images/remove-background", files={"file": ("photo.png", image_bytes(), "image/png")})
            assert response.status_code == 504
            assert started.is_set()
            assert processing_capacity._active_global == 1
            finish.set()
            # A health request leaves the event loop free for worker completion.
            for _ in range(100):
                client.get("/health")
                if processing_capacity._active_global == 0:
                    break
            assert processing_capacity._active_global == 0
    finally:
        finish.set()
        processing_capacity.enabled = previous


def test_mcp_timeout_retains_slot(inference, monkeypatch, tmp_path):
    async def scenario():
        started, finish = threading.Event(), threading.Event()
        def slow(*args, **kwargs):
            started.set()
            finish.wait(2)
            return processor.remove_image_background(image_bytes())
        async def download(*args, **kwargs):
            return image_bytes()
        limits = McpResourceLimits(rate_limit_enabled=False, request_limit=30, heavy_limit=10, global_jobs=1, timeout_seconds=0.05)
        monkeypatch.setattr(common, "mcp_resource_limits", limits)
        monkeypatch.setattr(common, "mcp_storage", TemporaryStorage(tmp_path, 900))
        monkeypatch.setattr(workflows, "download_input", download)
        monkeypatch.setattr(workflows, "process_background", slow)
        file = OpenAIFile(download_url="https://files.oaiusercontent.com/example", file_id="file", file_name="a.png", mime_type="image/png")
        try:
            with pytest.raises(ValueError, match="allowed time"):
                await workflows.remove_image_background(file)
            assert started.is_set() and limits.active_jobs == 1
            with pytest.raises(ValueError, match="too many"):
                await workflows.remove_image_background(file)
        finally:
            finish.set()
            for _ in range(100):
                if limits.active_jobs == 0:
                    break
                await asyncio.sleep(0.01)
        assert limits.active_jobs == 0
    asyncio.run(scenario())


@pytest.mark.skipif(os.environ.get("BACKGROUND_INTEGRATION") != "1", reason="Opt-in real CPU inference; prepare model first")
def test_real_cpu_model():
    result = processor.remove_image_background(image_bytes())
    with Image.open(io.BytesIO(result.content)) as image:
        assert image.mode == "RGBA"
    assert processor._get_session() is processor._get_session()
