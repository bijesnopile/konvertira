import asyncio

import pytest

from backend.services.storage import TemporaryStorage
from backend.services.resource_limits import mcp_resource_limits
from konvertira_mcp.models.files import OpenAIFile
from konvertira_mcp.tools import image_metadata


def test_remove_image_metadata_tool(monkeypatch, tmp_path, jpeg_with_metadata: bytes) -> None:
    mcp_resource_limits.clear()
    async def fake_download(_: str) -> bytes:
        return jpeg_with_metadata

    monkeypatch.setattr(image_metadata, "download_openai_file", fake_download)
    monkeypatch.setattr(image_metadata, "mcp_storage", TemporaryStorage(tmp_path, 900))

    result = asyncio.run(
        image_metadata.remove_image_metadata(
            OpenAIFile(
                download_url="https://files.oaiusercontent.com/example",
                file_id="file-123",
                mime_type="image/jpeg",
                file_name="photo.jpg",
            )
        )
    )

    assert result.success is True
    assert result.filename == "clean_photo.jpg"
    assert result.content_type == "image/jpeg"
    assert len(tuple(tmp_path.iterdir())) == 1
    assert mcp_resource_limits.active_jobs == 0


def test_heavy_quota_rejects_before_remote_download(monkeypatch) -> None:
    download_started = False

    async def fake_download(_: str) -> bytes:
        nonlocal download_started
        download_started = True
        return b"unused"

    previous_limit = mcp_resource_limits.heavy_limit
    mcp_resource_limits.heavy_limit = 0
    mcp_resource_limits.clear()
    monkeypatch.setattr(image_metadata, "download_openai_file", fake_download)
    try:
        with pytest.raises(ValueError, match="Too many processing requests"):
            asyncio.run(
                image_metadata.remove_image_metadata(
                    OpenAIFile(
                        download_url="https://files.oaiusercontent.com/example",
                        file_id="file-123",
                        mime_type="image/jpeg",
                        file_name="photo.jpg",
                    )
                )
            )
    finally:
        mcp_resource_limits.heavy_limit = previous_limit
        mcp_resource_limits.clear()

    assert download_started is False


def test_unexpected_tool_failure_returns_generic_error(monkeypatch) -> None:
    async def broken_download(_: str) -> bytes:
        raise KeyError("internal detail that must not reach the caller")

    mcp_resource_limits.clear()
    monkeypatch.setattr(image_metadata, "download_openai_file", broken_download)

    with pytest.raises(RuntimeError) as error:
        asyncio.run(
            image_metadata.remove_image_metadata(
                OpenAIFile(
                    download_url="https://files.oaiusercontent.com/example",
                    file_id="file-123",
                    mime_type="image/jpeg",
                    file_name="photo.jpg",
                )
            )
        )

    assert str(error.value) == "Konvertira could not process this image. Please try again."
