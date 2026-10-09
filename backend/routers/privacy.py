"""Unified metadata inspection and supported-metadata removal routes."""

import asyncio

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response

from backend.formats import format_from_filename, format_from_mime
from backend.models.files import FileProcessingError
from backend.services.metadata import inspect_file_metadata, remove_file_metadata
from backend.services.security import heavy_request_guard, read_upload_limited
from backend.utils.filenames import clean_filename
from config import settings

router = APIRouter(prefix="/metadata", tags=["Metadata privacy"])


def _format(file: UploadFile):
    filename_format = format_from_filename(file.filename)
    mime_format = format_from_mime(file.content_type)
    if filename_format and mime_format and filename_format.id != mime_format.id:
        raise HTTPException(415, "The filename extension and MIME type do not match.")
    definition = filename_format or mime_format
    if definition is None:
        raise HTTPException(415, "The file format is not supported for metadata processing.")
    return definition


def _limit(definition) -> int:
    if definition.category.value == "image":
        return settings.max_image_size
    if definition.id == "pdf":
        return settings.max_pdf_size
    return settings.max_document_size


@router.post("/inspect")
async def inspect(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    definition = _format(file)
    try:
        async with heavy_request_guard(request):
            content = await read_upload_limited(file, _limit(definition))
            result = await asyncio.to_thread(inspect_file_metadata, content, definition.id)
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    return JSONResponse(result.as_dict(), headers={"Cache-Control": "no-store"})


@router.post("/remove")
async def remove(request: Request, file: UploadFile = File(...)) -> Response:
    definition = _format(file)
    try:
        async with heavy_request_guard(request):
            content = await read_upload_limited(file, _limit(definition))
            result = await asyncio.to_thread(remove_file_metadata, content, definition.id)
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    cleaned = clean_filename(file.filename, "file")
    stem = cleaned.rsplit(".", 1)[0]
    return Response(
        result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{stem}-metadata-removed{result.extension}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Konvertira-Removed-Fields": str(result.removed_fields),
            "X-Konvertira-Privacy-Warning": result.warning,
        },
    )
