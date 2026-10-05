import asyncio

from backend.services.storage import TemporaryStorage
from konvertira_mcp.models.files import OpenAIFile
from konvertira_mcp.tools import image_metadata


def test_remove_image_metadata_tool(monkeypatch, tmp_path, jpeg_with_metadata: bytes) -> None:
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
