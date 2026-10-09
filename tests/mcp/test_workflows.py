import asyncio
import io

import pytest
from PIL import Image

from backend.services.resource_limits import mcp_resource_limits
from backend.services.storage import TemporaryStorage
from konvertira_mcp.models.files import ImageOutputFormat, OpenAIFile
from konvertira_mcp.server import mcp
from konvertira_mcp.tools import common, workflows


def file_ref(name: str, mime: str) -> OpenAIFile:
    return OpenAIFile(
        download_url="https://files.oaiusercontent.com/example",
        file_id="file-123",
        mime_type=mime,
        file_name=name,
    )


def test_tool_registration_schemas_and_annotations() -> None:
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    assert set(tools) == {
        "remove_image_metadata", "convert_image", "inspect_file_metadata",
        "remove_file_metadata", "merge_pdfs", "extract_pdf_pages",
        "convert_pdf_to_images", "convert_images_to_pdf", "convert_document",
        "convert_spreadsheet", "convert_presentation",
    }
    assert tools["inspect_file_metadata"].annotations.read_only_hint is True
    assert tools["convert_image"].annotations.destructive_hint is False
    assert tools["convert_image"].annotations.open_world_hint is False
    quality = tools["convert_image"].input_schema["properties"]["quality"]
    assert (quality["minimum"], quality["maximum"]) == (1, 100)
    files = tools["merge_pdfs"].input_schema["properties"]["files"]
    assert (files["minItems"], files["maxItems"]) == (2, 10)


def test_unsupported_conversion_rejects_before_download(monkeypatch) -> None:
    download_started = False

    async def fake_download(*args, **kwargs):
        nonlocal download_started
        download_started = True
        return b"unused"

    monkeypatch.setattr(workflows, "download_input", fake_download)
    mcp_resource_limits.clear()
    with pytest.raises(ValueError, match="not supported"):
        asyncio.run(workflows.convert_image(file_ref("file.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"), ImageOutputFormat.JPEG))
    assert download_started is False


def test_convert_image_uses_shared_processor_and_temporary_storage(monkeypatch, tmp_path) -> None:
    image = Image.new("RGB", (4, 3), "red")
    source = io.BytesIO()
    image.save(source, format="PNG")
    image.close()

    async def fake_download(*args, **kwargs):
        return source.getvalue()

    monkeypatch.setattr(workflows, "download_input", fake_download)
    monkeypatch.setattr(common, "mcp_storage", TemporaryStorage(tmp_path, 900))
    mcp_resource_limits.clear()
    result = asyncio.run(workflows.convert_image(file_ref("photo.png", "image/png"), ImageOutputFormat.JPEG))
    assert result.success is True
    assert result.filename == "photo.jpg"
    assert result.content_type == "image/jpeg"
    assert len(tuple(tmp_path.iterdir())) == 1


def test_merge_count_rejects_before_download(monkeypatch) -> None:
    download_started = False

    async def fake_download(*args, **kwargs):
        nonlocal download_started
        download_started = True
        return b"unused"

    monkeypatch.setattr(workflows, "download_input", fake_download)
    mcp_resource_limits.clear()
    with pytest.raises(ValueError, match="requires 2"):
        asyncio.run(workflows.merge_pdf_files([file_ref("one.pdf", "application/pdf")]))
    assert download_started is False
