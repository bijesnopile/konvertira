import asyncio
import io
import zipfile

import pytest
from PIL import Image
from pypdf import PdfReader, PdfWriter

from backend.models.files import ProcessedFile
from backend.services.resource_limits import mcp_resource_limits
from backend.services.storage import TemporaryStorage
from konvertira_mcp.models.files import ImageOutputFormat, OpenAIFile, PdfImageOutputFormat
from konvertira_mcp.server import mcp
from konvertira_mcp.tools import common, workflows


def file_ref(name: str, mime: str) -> OpenAIFile:
    return OpenAIFile(
        download_url="https://files.oaiusercontent.com/example",
        file_id="file-123",
        mime_type=mime,
        file_name=name,
    )


def make_pdf(widths: tuple[int, ...] = (100,)) -> bytes:
    writer = PdfWriter()
    for width in widths:
        writer.add_blank_page(width=width, height=100)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def make_encrypted_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def configure_file_workflow(monkeypatch, tmp_path, content: bytes) -> None:
    async def fake_download(*args, **kwargs):
        return content

    monkeypatch.setattr(workflows, "download_input", fake_download)
    monkeypatch.setattr(common, "mcp_storage", TemporaryStorage(tmp_path, 900))
    mcp_resource_limits.clear()


def stored_content(tmp_path) -> bytes:
    return next(path for path in tmp_path.iterdir() if path.is_file()).read_bytes()


def test_tool_registration_schemas_and_annotations() -> None:
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    assert set(tools) == {
        "remove_image_metadata", "convert_image", "inspect_file_metadata",
        "remove_file_metadata", "merge_pdfs", "extract_pdf_pages",
        "split_pdf", "reorder_pdf_pages", "delete_pdf_pages", "optimize_pdf",
        "remove_image_background",
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
    assert tools["split_pdf"].annotations.read_only_hint is False
    assert tools["split_pdf"].annotations.destructive_hint is False
    assert tools["split_pdf"].annotations.open_world_hint is False
    assert tools["split_pdf"].annotations.idempotent_hint is True
    for name in ("split_pdf", "reorder_pdf_pages", "delete_pdf_pages", "optimize_pdf"):
        assert tools[name].meta["openai/fileParams"] == ["file"]
    target_size = tools["convert_image"].input_schema["properties"]["target_size_bytes"]
    assert target_size["anyOf"][0]["minimum"] == 1024
    background = tools["remove_image_background"]
    assert background.annotations == tools["split_pdf"].annotations
    assert background.meta["openai/fileParams"] == ["file"]
    assert background.input_schema["properties"]["output_format"]["default"] == "png"


def test_openai_file_schema_matches_plugin_file_param_contract() -> None:
    schema = OpenAIFile.model_json_schema()
    assert set(schema["properties"]) == {
        "download_url",
        "file_id",
        "mime_type",
        "file_name",
    }
    assert schema["required"] == ["download_url", "file_id"]
    assert schema["properties"]["download_url"]["type"] == "string"
    assert schema["properties"]["file_id"]["type"] == "string"
    assert schema["properties"]["mime_type"]["type"] == "string"
    assert schema["properties"]["file_name"]["type"] == "string"
    assert schema["additionalProperties"] is False

    omitted_optional = OpenAIFile(
        download_url="https://files.oaiusercontent.com/example",
        file_id="file-123",
    )
    assert omitted_optional.mime_type is None
    assert omitted_optional.file_name is None


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


def test_convert_image_passes_target_size_and_background_to_shared_processor(monkeypatch, tmp_path) -> None:
    captured = {}

    async def fake_download(*args, **kwargs):
        return b"image"

    def fake_process(content, output_format, **kwargs):
        captured.update(kwargs)
        return ProcessedFile(b"converted", "JPEG", width=1, height=1)

    monkeypatch.setattr(workflows, "download_input", fake_download)
    monkeypatch.setattr(workflows, "process_image", fake_process)
    monkeypatch.setattr(common, "mcp_storage", TemporaryStorage(tmp_path, 900))
    mcp_resource_limits.clear()
    asyncio.run(workflows.convert_image(
        file_ref("photo.png", "image/png"),
        ImageOutputFormat.JPEG,
        target_size_bytes=2048,
        background_color="#123456",
    ))
    assert captured["target_size_bytes"] == 2048
    assert captured["background_color"] == "#123456"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"target_size_bytes": 100}, "at least 1 KB"),
        ({"background_color": "not-a-color"}, "Background color is invalid"),
    ],
)
def test_convert_image_rejects_invalid_advanced_options(monkeypatch, tmp_path, kwargs, message) -> None:
    image = Image.new("RGBA", (4, 3), (255, 0, 0, 128))
    source = io.BytesIO()
    image.save(source, format="PNG")
    image.close()
    configure_file_workflow(monkeypatch, tmp_path, source.getvalue())

    with pytest.raises(ValueError, match=message):
        asyncio.run(workflows.convert_image(
            file_ref("photo.png", "image/png"),
            ImageOutputFormat.JPEG,
            **kwargs,
        ))


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


def test_split_pdf_success(monkeypatch, tmp_path) -> None:
    configure_file_workflow(monkeypatch, tmp_path, make_pdf((100, 200)))
    result = asyncio.run(workflows.split_pdf(file_ref("source.pdf", "application/pdf")))

    assert result.filename == "source.zip"
    assert result.content_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(stored_content(tmp_path))) as archive:
        assert archive.namelist() == ["page-0001.pdf", "page-0002.pdf"]


def test_reorder_pdf_pages_success_and_invalid_expression(monkeypatch, tmp_path) -> None:
    configure_file_workflow(monkeypatch, tmp_path, make_pdf((100, 200, 300)))
    asyncio.run(workflows.reorder_pdf_pages(
        file_ref("source.pdf", "application/pdf"), "3,1,2"
    ))
    reader = PdfReader(io.BytesIO(stored_content(tmp_path)))
    assert [int(page.mediabox.width) for page in reader.pages] == [300, 100, 200]

    with pytest.raises(ValueError, match="every page exactly once"):
        asyncio.run(workflows.reorder_pdf_pages(
            file_ref("source.pdf", "application/pdf"), "1,1,2"
        ))


def test_delete_pdf_pages_success_and_rejects_deleting_all(monkeypatch, tmp_path) -> None:
    configure_file_workflow(monkeypatch, tmp_path, make_pdf((100, 200, 300)))
    asyncio.run(workflows.delete_pdf_pages(
        file_ref("source.pdf", "application/pdf"), "2"
    ))
    reader = PdfReader(io.BytesIO(stored_content(tmp_path)))
    assert [int(page.mediabox.width) for page in reader.pages] == [100, 300]

    with pytest.raises(ValueError, match="Deleting every page"):
        asyncio.run(workflows.delete_pdf_pages(
            file_ref("source.pdf", "application/pdf"), "1-3"
        ))


def test_optimize_pdf_success(monkeypatch, tmp_path) -> None:
    configure_file_workflow(monkeypatch, tmp_path, make_pdf((100, 200)))
    result = asyncio.run(workflows.optimize_pdf(file_ref("source.pdf", "application/pdf")))

    assert result.filename == "source.pdf"
    assert "lossless structural" in result.message
    assert len(PdfReader(io.BytesIO(stored_content(tmp_path))).pages) == 2


def test_pdf_workflows_reject_encrypted_input(monkeypatch, tmp_path) -> None:
    configure_file_workflow(monkeypatch, tmp_path, make_encrypted_pdf())

    with pytest.raises(ValueError, match="Encrypted PDFs"):
        asyncio.run(workflows.split_pdf(file_ref("encrypted.pdf", "application/pdf")))


@pytest.mark.parametrize("format", list(PdfImageOutputFormat))
def test_real_pdf_render_mcp_and_result_expiration(monkeypatch, tmp_path, format) -> None:
    from tests.backend.test_pdf_processor import colored_pdf
    configure_file_workflow(monkeypatch, tmp_path, colored_pdf())
    result = asyncio.run(workflows.convert_pdf_to_images(file_ref("source.pdf", "application/pdf"), format, dpi=72, pages="3,1"))
    assert result.success and result.filename == "source.zip"
    assert result.content_type == "application/zip"
    with zipfile.ZipFile(io.BytesIO(stored_content(tmp_path))) as archive:
        extension = "jpg" if format == PdfImageOutputFormat.JPEG else format.value
        assert archive.namelist() == [f"page-0001.{extension}", f"page-0002.{extension}"]
        with Image.open(io.BytesIO(archive.read(archive.namelist()[0]))) as image:
            assert image.size == (300, 60)
    stored = next(tmp_path.iterdir())
    assert common.mcp_storage.cleanup(now=stored.stat().st_mtime + 901) == 1
    assert not list(tmp_path.iterdir())


def test_pdf_render_schema_and_openai_optional_fields_unchanged() -> None:
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    tool = tools["convert_pdf_to_images"]
    assert tool.meta["openai/fileParams"] == ["file"]
    assert tool.annotations == tools["split_pdf"].annotations
    assert tool.input_schema["properties"]["dpi"]["minimum"] == 36
    assert tool.input_schema["properties"]["dpi"]["maximum"] == 200
    assert tool.input_schema["properties"]["dpi"]["default"] == 144
    reference = OpenAIFile(download_url="https://files.oaiusercontent.com/file", file_id="file-123")
    assert reference.mime_type is None and reference.file_name is None
    assert OpenAIFile.model_json_schema()["required"] == ["download_url", "file_id"]
