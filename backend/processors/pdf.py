"""Bounded, in-memory PDF transformations shared by HTTP and MCP."""

from __future__ import annotations

import io
import math
import zipfile
from dataclasses import dataclass
from typing import Iterable, Sequence

import pymupdf as fitz
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from backend.models.files import FileProcessingError, ProcessingErrorCode
from config import settings

register_heif_opener()


@dataclass(frozen=True, slots=True)
class PdfResult:
    content: bytes
    page_count: int
    extension: str = ".pdf"
    content_type: str = "application/pdf"


def _reader(content: bytes, *, max_size: int | None = None) -> PdfReader:
    limit = max_size or settings.max_pdf_size
    if not content:
        raise FileProcessingError("The PDF is empty.")
    if len(content) > limit:
        raise FileProcessingError("The PDF exceeds the configured size limit.", 413, ProcessingErrorCode.FILE_TOO_LARGE)
    try:
        reader = PdfReader(io.BytesIO(content), strict=True)
        if reader.is_encrypted:
            raise FileProcessingError("Encrypted PDFs are not supported.", 422, ProcessingErrorCode.UNSUPPORTED_FEATURE)
        if not reader.pages:
            raise FileProcessingError("The PDF does not contain any pages.")
        if len(reader.pages) > settings.max_pdf_pages:
            raise FileProcessingError("The PDF exceeds the page-count limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
        return reader
    except FileProcessingError:
        raise
    except (PdfReadError, ValueError, OSError) as exc:
        raise FileProcessingError("The file is not a valid supported PDF.") from exc


def _write(writer: PdfWriter) -> bytes:
    output = io.BytesIO()
    try:
        writer.write(output)
    except Exception as exc:
        raise FileProcessingError("The PDF could not be generated.", 500, ProcessingErrorCode.CONVERSION_FAILED) from exc
    content = output.getvalue()
    if not content:
        raise FileProcessingError("The PDF could not be generated.", 500, ProcessingErrorCode.CONVERSION_FAILED)
    if len(content) > settings.max_pdf_output_size:
        raise FileProcessingError("The generated PDF exceeds the output size limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
    return content


def parse_page_selection(value: str, page_count: int) -> list[int]:
    """Parse one-based values such as ``1-3,5`` into unique zero-based pages."""
    if not value.strip():
        raise FileProcessingError("Choose at least one page.", 422)
    selected: list[int] = []
    seen: set[int] = set()
    try:
        for token in value.split(","):
            token = token.strip()
            if "-" in token:
                start_text, end_text = token.split("-", 1)
                start, end = int(start_text), int(end_text)
                if start > end:
                    raise ValueError
                values: Iterable[int] = range(start, end + 1)
            else:
                values = (int(token),)
            for page in values:
                if page < 1 or page > page_count:
                    raise ValueError
                index = page - 1
                if index not in seen:
                    seen.add(index)
                    selected.append(index)
    except ValueError as exc:
        raise FileProcessingError(f"Page selection must use values between 1 and {page_count}.", 422) from exc
    return selected


def merge_pdfs(contents: Sequence[bytes]) -> PdfResult:
    if not 2 <= len(contents) <= settings.max_pdf_files:
        raise FileProcessingError(f"Merge requires 2 to {settings.max_pdf_files} PDFs.", 422)
    if sum(map(len, contents)) > settings.max_pdf_total_size:
        raise FileProcessingError("The combined PDFs exceed the merge size limit.", 413, ProcessingErrorCode.FILE_TOO_LARGE)
    writer = PdfWriter()
    page_count = 0
    for content in contents:
        reader = _reader(content)
        page_count += len(reader.pages)
        if page_count > settings.max_pdf_pages:
            raise FileProcessingError("The merged PDF would exceed the page-count limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
        for page in reader.pages:
            writer.add_page(page)
    return PdfResult(_write(writer), page_count)


def select_pdf_pages(content: bytes, page_order: Sequence[int]) -> PdfResult:
    reader = _reader(content)
    if not page_order:
        raise FileProcessingError("The output must contain at least one page.", 422)
    if len(page_order) > settings.max_pdf_pages or any(index < 0 or index >= len(reader.pages) for index in page_order):
        raise FileProcessingError("The page order contains an invalid page.", 422)
    writer = PdfWriter()
    for index in page_order:
        writer.add_page(reader.pages[index])
    return PdfResult(_write(writer), len(page_order))


def extract_pdf_pages(content: bytes, selection: str) -> PdfResult:
    reader = _reader(content)
    return select_pdf_pages(content, parse_page_selection(selection, len(reader.pages)))


def reorder_pdf_pages(content: bytes, order: str) -> PdfResult:
    reader = _reader(content)
    try:
        indexes = [int(value.strip()) - 1 for value in order.split(",")]
    except ValueError as exc:
        raise FileProcessingError("Order must be a comma-separated list of page numbers.", 422) from exc
    if sorted(indexes) != list(range(len(reader.pages))):
        raise FileProcessingError("Page order must include every page exactly once.", 422)
    return select_pdf_pages(content, indexes)


def delete_pdf_pages(content: bytes, selection: str) -> PdfResult:
    reader = _reader(content)
    deleted = set(parse_page_selection(selection, len(reader.pages)))
    remaining = [index for index in range(len(reader.pages)) if index not in deleted]
    if not remaining:
        raise FileProcessingError("Deleting every page is not allowed.", 422)
    return select_pdf_pages(content, remaining)


def split_pdf_pages(content: bytes) -> PdfResult:
    reader = _reader(content)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, page in enumerate(reader.pages, start=1):
            writer = PdfWriter()
            writer.add_page(page)
            archive.writestr(f"page-{index:04d}.pdf", _write(writer))
    result = output.getvalue()
    if len(result) > settings.max_pdf_output_size:
        raise FileProcessingError("The generated archive exceeds the output size limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
    return PdfResult(result, len(reader.pages), ".zip", "application/zip")


def images_to_pdf(contents: Sequence[bytes]) -> PdfResult:
    if not 1 <= len(contents) <= settings.max_pdf_files:
        raise FileProcessingError(f"Choose 1 to {settings.max_pdf_files} images.", 422)
    if sum(map(len, contents)) > settings.max_pdf_total_size:
        raise FileProcessingError("The combined images exceed the size limit.", 413, ProcessingErrorCode.FILE_TOO_LARGE)
    images: list[Image.Image] = []
    total_pixels = 0
    try:
        for content in contents:
            with Image.open(io.BytesIO(content)) as source:
                if getattr(source, "is_animated", False):
                    raise FileProcessingError("Animated images cannot be added to a PDF.", 422, ProcessingErrorCode.UNSUPPORTED_FEATURE)
                if source.width * source.height > settings.max_pixels:
                    raise FileProcessingError("An image exceeds the pixel limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
                total_pixels += source.width * source.height
                if total_pixels > settings.max_pdf_generated_pixels:
                    raise FileProcessingError("The combined images exceed the pixel limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
                images.append(ImageOps.exif_transpose(source).convert("RGB"))
        output = io.BytesIO()
        images[0].save(output, format="PDF", save_all=True, append_images=images[1:], resolution=96)
        result = output.getvalue()
        if len(result) > settings.max_pdf_output_size:
            raise FileProcessingError("The generated PDF exceeds the output size limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
        return PdfResult(result, len(images))
    except FileProcessingError:
        raise
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise FileProcessingError("One of the files is not a supported image.") from exc
    finally:
        for image in images:
            image.close()


def pdf_to_images(content: bytes, *, output_format: str = "png", dpi: int = 144, selection: str | None = None) -> PdfResult:
    if output_format.lower() not in {"png", "jpeg", "jpg", "webp"}:
        raise FileProcessingError("PDF pages can be exported as PNG, JPEG, or WebP.", 422, ProcessingErrorCode.UNSUPPORTED_FORMAT)
    if not 36 <= dpi <= settings.max_pdf_raster_dpi:
        raise FileProcessingError(f"DPI must be between 36 and {settings.max_pdf_raster_dpi}.", 422)
    _reader(content)
    document: fitz.Document | None = None
    try:
        document = fitz.open(stream=content, filetype="pdf")
        indexes = parse_page_selection(selection, document.page_count) if selection else list(range(document.page_count))
        total_pixels = 0
        output = io.BytesIO()
        extension = "jpg" if output_format.lower() in {"jpg", "jpeg"} else output_format.lower()
        pil_format = "JPEG" if extension == "jpg" else extension.upper()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for number, index in enumerate(indexes, start=1):
                page = document.load_page(index)
                scale = dpi / 72
                expected_pixels = math.ceil(page.rect.width * scale) * math.ceil(page.rect.height * scale)
                if total_pixels + expected_pixels > settings.max_pdf_generated_pixels:
                    raise FileProcessingError("Generated images would exceed the pixel limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
                pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=pil_format != "JPEG")
                total_pixels += pixmap.width * pixmap.height
                if total_pixels > settings.max_pdf_generated_pixels:
                    raise FileProcessingError("Generated images would exceed the pixel limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
                mode = "RGBA" if pixmap.alpha else "RGB"
                image = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
                encoded = io.BytesIO()
                image.save(encoded, format=pil_format, quality=90, optimize=True)
                image.close()
                archive.writestr(f"page-{number:04d}.{extension}", encoded.getvalue())
        result = output.getvalue()
        if len(result) > settings.max_pdf_output_size:
            raise FileProcessingError("The generated image archive exceeds the output size limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
        return PdfResult(result, len(indexes), ".zip", "application/zip")
    except FileProcessingError:
        raise
    except Exception as exc:
        raise FileProcessingError("The PDF pages could not be rendered.", 500, ProcessingErrorCode.CONVERSION_FAILED) from exc
    finally:
        if document is not None:
            document.close()


def inspect_pdf_metadata(content: bytes) -> dict[str, object]:
    reader = _reader(content)
    metadata = reader.metadata or {}
    return {
        "title": metadata.get("/Title"), "author": metadata.get("/Author"),
        "subject": metadata.get("/Subject"), "keywords": metadata.get("/Keywords"),
        "creator": metadata.get("/Creator"), "producer": metadata.get("/Producer"),
        "creation_date": str(metadata.get("/CreationDate") or "") or None,
        "modification_date": str(metadata.get("/ModDate") or "") or None,
        "page_count": len(reader.pages), "pdf_version": reader.pdf_header, "encrypted": False,
    }


def remove_pdf_metadata(content: bytes) -> PdfResult:
    reader = _reader(content)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({})
    writer.xmp_metadata = None
    return PdfResult(_write(writer), len(reader.pages))


def optimize_pdf(content: bytes) -> PdfResult:
    """Perform a lossless structural rewrite; images are not downsampled."""
    reader = _reader(content)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)
    return PdfResult(_write(writer), len(reader.pages))
