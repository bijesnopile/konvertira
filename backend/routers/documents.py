"""Server-backed document conversion endpoint."""

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from backend.formats import format_from_filename, format_from_mime
from backend.models.files import FileProcessingError
from backend.processors.document import convert_document
from backend.services.security import heavy_request_guard, read_upload_limited
from backend.utils.filenames import converted_output_filename
from config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/convert")
async def convert_document_upload(
    request: Request,
    file: UploadFile = File(...),
    output_format: str = Form(...),
) -> Response:
    filename_format = format_from_filename(file.filename)
    mime_format = format_from_mime(file.content_type)
    source = filename_format or mime_format
    if source is None or not source.supports_mode("server"):
        raise HTTPException(415, "The input document format is not supported.")
    if filename_format and mime_format and filename_format.id != mime_format.id:
        raise HTTPException(415, "The filename extension and declared MIME type do not match.")
    try:
        async with heavy_request_guard(request):
            content = await read_upload_limited(file, settings.max_document_size)
            result = await asyncio.to_thread(convert_document, content, source.id, output_format)
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    filename = converted_output_filename(file.filename, result.extension)
    return Response(
        result.content,
        media_type=result.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-Konvertira-Fidelity-Warning": result.fidelity_warning or "",
        },
    )
