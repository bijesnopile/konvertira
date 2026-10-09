"""Explicit, server-backed PDF toolkit routes."""

import asyncio
from collections.abc import Callable, Sequence

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from backend.models.files import FileProcessingError
from backend.processors.pdf import (
    PdfResult,
    delete_pdf_pages,
    extract_pdf_pages,
    images_to_pdf,
    inspect_pdf_metadata,
    merge_pdfs,
    optimize_pdf,
    pdf_to_images,
    reorder_pdf_pages,
    remove_pdf_metadata,
    split_pdf_pages,
)
from backend.services.security import heavy_request_guard, read_upload_limited
from config import settings

router = APIRouter(prefix="/pdf", tags=["PDF"])


def _validate_pdf_upload(file: UploadFile) -> None:
    if file.content_type and file.content_type.lower() != "application/pdf":
        raise FileProcessingError("The uploaded file must be a PDF.", 415)


async def _read_pdf(file: UploadFile) -> bytes:
    _validate_pdf_upload(file)
    return await read_upload_limited(file, settings.max_pdf_size)


async def _read_many(files: Sequence[UploadFile], *, per_file_limit: int | None = None) -> list[bytes]:
    if len(files) > settings.max_pdf_files:
        raise FileProcessingError(f"At most {settings.max_pdf_files} files are allowed.", 422)
    contents: list[bytes] = []
    total = 0
    for file in files:
        content = await read_upload_limited(file, per_file_limit or settings.max_pdf_size)
        total += len(content)
        if total > settings.max_pdf_total_size:
            raise FileProcessingError("The combined uploads exceed the size limit.", 413)
        contents.append(content)
    return contents


def _response(result: PdfResult, filename: str) -> Response:
    return Response(
        result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Konvertira-Page-Count": str(result.page_count),
        },
    )


async def _single_job(request: Request, file: UploadFile, operation: Callable[..., PdfResult], *args, **kwargs) -> PdfResult:
    try:
        async with heavy_request_guard(request):
            content = await _read_pdf(file)
            return await asyncio.to_thread(operation, content, *args, **kwargs)
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc


@router.post("/merge")
async def merge(request: Request, files: list[UploadFile] = File(...)) -> Response:
    try:
        async with heavy_request_guard(request):
            for file in files:
                _validate_pdf_upload(file)
            contents = await _read_many(files)
            result = await asyncio.to_thread(merge_pdfs, contents)
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    return _response(result, "merged.pdf")


@router.post("/extract")
async def extract(request: Request, file: UploadFile = File(...), pages: str = Form(...)) -> Response:
    return _response(await _single_job(request, file, extract_pdf_pages, pages), "extracted.pdf")


@router.post("/split")
async def split(request: Request, file: UploadFile = File(...)) -> Response:
    return _response(await _single_job(request, file, split_pdf_pages), "split-pages.zip")


@router.post("/reorder")
async def reorder(request: Request, file: UploadFile = File(...), order: str = Form(...)) -> Response:
    return _response(await _single_job(request, file, reorder_pdf_pages, order), "reordered.pdf")


@router.post("/delete-pages")
async def delete_pages(request: Request, file: UploadFile = File(...), pages: str = Form(...)) -> Response:
    return _response(await _single_job(request, file, delete_pdf_pages, pages), "pages-deleted.pdf")


@router.post("/images-to-pdf")
async def create_from_images(request: Request, files: list[UploadFile] = File(...)) -> Response:
    try:
        async with heavy_request_guard(request):
            contents = await _read_many(files, per_file_limit=settings.max_image_size)
            result = await asyncio.to_thread(images_to_pdf, contents)
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    return _response(result, "images.pdf")


@router.post("/to-images")
async def to_images(request: Request, file: UploadFile = File(...), format: str = Form("png"), dpi: int = Form(144), pages: str | None = Form(None)) -> Response:
    result = await _single_job(request, file, pdf_to_images, output_format=format, dpi=dpi, selection=pages)
    return _response(result, "pdf-images.zip")


@router.post("/inspect-metadata")
async def inspect_metadata(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    try:
        async with heavy_request_guard(request):
            content = await _read_pdf(file)
            result = await asyncio.to_thread(inspect_pdf_metadata, content)
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    return JSONResponse({**result, "warning": "Metadata inspection cannot prove the absence of hidden content or identifiers."}, headers={"Cache-Control": "no-store"})


@router.post("/remove-metadata")
async def remove_metadata(request: Request, file: UploadFile = File(...)) -> Response:
    result = await _single_job(request, file, remove_pdf_metadata)
    return _response(result, "metadata-removed.pdf")


@router.post("/optimize")
async def optimize(request: Request, file: UploadFile = File(...)) -> Response:
    result = await _single_job(request, file, optimize_pdf)
    response = _response(result, "optimized.pdf")
    response.headers["X-Konvertira-Optimization"] = "lossless-structural"
    return response
