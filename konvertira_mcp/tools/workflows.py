"""MCP tools backed exclusively by shared Konvertira processors/services."""

from __future__ import annotations

import asyncio
from typing import Annotated

from pydantic import Field

from backend.processors.document import convert_document as process_document
from backend.processors.image import convert_image as process_image
from backend.processors.office import convert_office
from backend.processors.pdf import extract_pdf_pages, images_to_pdf, merge_pdfs, pdf_to_images
from backend.formats import conversion_capability
from backend.services.metadata import (
    inspect_file_metadata as inspect_file_metadata_service,
    remove_file_metadata as remove_file_metadata_service,
)
from config import settings
from konvertira_mcp.models.files import (
    DocumentOutputFormat,
    ImageOutputFormat,
    MetadataResult,
    OpenAIFile,
    PdfImageOutputFormat,
    PresentationOutputFormat,
    ProcessedResult,
    SpreadsheetOutputFormat,
)
from konvertira_mcp.tools.common import McpWorkflowError, download_input, input_format, run_heavy, stored_result


async def convert_image(
    file: OpenAIFile,
    output_format: ImageOutputFormat,
    quality: Annotated[int, Field(ge=1, le=100)] = 90,
    width: Annotated[int | None, Field(ge=1, le=20000)] = None,
    height: Annotated[int | None, Field(ge=1, le=20000)] = None,
    allow_upscale: bool = False,
) -> ProcessedResult:
    async def operation() -> ProcessedResult:
        definition = input_format(file)
        if definition.category.value != "image" or conversion_capability(definition.id, output_format.value, "server") is None:
            raise McpWorkflowError("This image conversion pair is not supported.")
        content = await download_input(file, settings.max_image_size)
        result = await asyncio.to_thread(
            process_image, content, output_format.value, quality=quality,
            width=width, height=height, allow_upscale=allow_upscale,
        )
        return stored_result(result.content, output_format.value, file.file_name, "The image was converted to a new downloadable copy.")
    return await run_heavy("convert_image", operation)


async def inspect_file_metadata(file: OpenAIFile) -> MetadataResult:
    async def operation() -> MetadataResult:
        definition = input_format(file)
        if not definition.capabilities.inspect_metadata:
            raise McpWorkflowError("Metadata inspection is not supported for this format.")
        limit = settings.max_image_size if definition.category.value == "image" else settings.max_pdf_size if definition.id == "pdf" else settings.max_document_size
        content = await download_input(file, limit)
        result = await asyncio.to_thread(inspect_file_metadata_service, content, definition.id)
        payload = result.as_dict()
        return MetadataResult(**payload)
    return await run_heavy("inspect_file_metadata", operation)


async def remove_file_metadata(file: OpenAIFile) -> ProcessedResult:
    async def operation() -> ProcessedResult:
        definition = input_format(file)
        if not definition.capabilities.remove_metadata:
            raise McpWorkflowError("Metadata removal is not supported for this format.")
        limit = settings.max_image_size if definition.category.value == "image" else settings.max_pdf_size if definition.id == "pdf" else settings.max_document_size
        content = await download_input(file, limit)
        result = await asyncio.to_thread(remove_file_metadata_service, content, definition.id)
        return stored_result(result.content, result.extension, file.file_name, result.warning)
    return await run_heavy("remove_file_metadata", operation)


async def merge_pdf_files(
    files: Annotated[list[OpenAIFile], Field(min_length=2, max_length=10)],
) -> ProcessedResult:
    async def operation() -> ProcessedResult:
        if not 2 <= len(files) <= settings.max_pdf_files:
            raise McpWorkflowError(f"Merge requires 2 to {settings.max_pdf_files} PDFs.")
        for file in files:
            if input_format(file).id != "pdf":
                raise McpWorkflowError("Every merge input must be a PDF.")
        contents = [await download_input(file, settings.max_pdf_size) for file in files]
        result = await asyncio.to_thread(merge_pdfs, contents)
        return stored_result(result.content, ".pdf", "merged.pdf", "The PDFs were merged in the supplied order.")
    return await run_heavy("merge_pdfs", operation)


async def extract_pdf_file_pages(
    file: OpenAIFile,
    pages: Annotated[str, Field(min_length=1, max_length=500)],
) -> ProcessedResult:
    async def operation() -> ProcessedResult:
        if input_format(file).id != "pdf":
            raise McpWorkflowError("The input must be a PDF.")
        content = await download_input(file, settings.max_pdf_size)
        result = await asyncio.to_thread(extract_pdf_pages, content, pages)
        return stored_result(result.content, ".pdf", file.file_name, "The selected pages were extracted to a new PDF.")
    return await run_heavy("extract_pdf_pages", operation)


async def convert_pdf_to_images(
    file: OpenAIFile,
    output_format: PdfImageOutputFormat = PdfImageOutputFormat.PNG,
    dpi: Annotated[int, Field(ge=36, le=200)] = 144,
    pages: Annotated[str | None, Field(max_length=500)] = None,
) -> ProcessedResult:
    async def operation() -> ProcessedResult:
        if input_format(file).id != "pdf":
            raise McpWorkflowError("The input must be a PDF.")
        if dpi > settings.max_pdf_raster_dpi:
            raise McpWorkflowError(f"DPI cannot exceed {settings.max_pdf_raster_dpi}.")
        content = await download_input(file, settings.max_pdf_size)
        result = await asyncio.to_thread(pdf_to_images, content, output_format=output_format.value, dpi=dpi, selection=pages)
        return stored_result(result.content, ".zip", file.file_name, "The selected PDF pages were rendered into a ZIP of generated images.")
    return await run_heavy("convert_pdf_to_images", operation)


async def convert_images_to_pdf(
    files: Annotated[list[OpenAIFile], Field(min_length=1, max_length=10)],
) -> ProcessedResult:
    async def operation() -> ProcessedResult:
        if len(files) > settings.max_pdf_files:
            raise McpWorkflowError(f"At most {settings.max_pdf_files} images can be converted.")
        for file in files:
            definition = input_format(file)
            if definition.category.value != "image" or conversion_capability(definition.id, "pdf", "server") is None:
                raise McpWorkflowError("Every input must be a supported static image for PDF creation.")
        contents = [await download_input(file, settings.max_image_size) for file in files]
        result = await asyncio.to_thread(images_to_pdf, contents)
        return stored_result(result.content, ".pdf", "images.pdf", "The images were added to a new PDF in the supplied order.")
    return await run_heavy("convert_images_to_pdf", operation)


async def convert_document(
    file: OpenAIFile,
    output_format: DocumentOutputFormat,
) -> ProcessedResult:
    async def operation() -> ProcessedResult:
        definition = input_format(file)
        if definition.id not in {"docx", "doc", "odt", "rtf", "txt", "markdown", "html"}:
            raise McpWorkflowError("The input format is not supported by the document tool.")
        if conversion_capability(definition.id, output_format.value, "server") is None:
            raise McpWorkflowError("This document conversion pair is not supported.")
        content = await download_input(file, settings.max_document_size)
        result = await asyncio.to_thread(process_document, content, definition.id, output_format.value)
        return stored_result(result.content, result.extension, file.file_name, result.fidelity_warning or "The document was converted.")
    return await run_heavy("convert_document", operation)


async def convert_spreadsheet(
    file: OpenAIFile,
    output_format: SpreadsheetOutputFormat,
) -> ProcessedResult:
    return await _convert_office_tool("convert_spreadsheet", file, output_format.value, {"xlsx", "xls", "ods", "csv"})


async def convert_presentation(
    file: OpenAIFile,
    output_format: PresentationOutputFormat,
) -> ProcessedResult:
    return await _convert_office_tool("convert_presentation", file, output_format.value, {"pptx", "ppt", "odp"})


async def _convert_office_tool(tool_name: str, file: OpenAIFile, output: str, allowed: set[str]) -> ProcessedResult:
    async def operation() -> ProcessedResult:
        definition = input_format(file)
        if definition.id not in allowed:
            raise McpWorkflowError("The input format is not supported by this tool.")
        content = await download_input(file, settings.max_document_size)
        result = await asyncio.to_thread(convert_office, content, definition.id, output)
        return stored_result(result.content, result.extension, file.file_name, result.warning)
    return await run_heavy(tool_name, operation)
