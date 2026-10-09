"""Spreadsheet and presentation conversion endpoint."""

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from backend.formats import format_from_filename, format_from_mime
from backend.models.files import FileProcessingError
from backend.processors.office import convert_office
from backend.services.security import heavy_request_guard, read_upload_limited
from backend.utils.filenames import clean_filename
from config import settings

router = APIRouter(prefix="/office", tags=["Spreadsheets and presentations"])


@router.post("/convert")
async def convert_office_upload(
    request: Request,
    file: UploadFile = File(...),
    output_format: str = Form(...),
    delimiter: str | None = Form(None),
) -> Response:
    filename_format = format_from_filename(file.filename)
    mime_format = format_from_mime(file.content_type)
    source = filename_format or mime_format
    if source is None or not source.supports_mode("server"):
        raise HTTPException(415, "The input office format is unsupported.")
    if filename_format and mime_format and filename_format.id != mime_format.id:
        raise HTTPException(415, "The filename extension and MIME type do not match.")
    try:
        async with heavy_request_guard(request):
            content = await read_upload_limited(file, settings.max_document_size)
            result = await asyncio.to_thread(
                convert_office, content, source.id, output_format, delimiter=delimiter
            )
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    cleaned = clean_filename(file.filename, "file")
    stem = cleaned.rsplit(".", 1)[0]
    return Response(
        result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{stem}{result.extension}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Konvertira-Fidelity-Warning": result.warning,
        },
    )
