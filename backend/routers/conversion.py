"""Image conversion routes."""

import asyncio

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from backend.models.files import FileProcessingError
from backend.processors.image import convert_image
from backend.services.security import heavy_request_guard, read_upload_limited
from backend.utils.filenames import converted_output_filename
from backend.utils.mime import get_content_type, get_extension
from backend.utils.validation import validate_image_mime_type

router = APIRouter()


@router.post("/images/convert")
async def convert_image_upload(
    request: Request,
    file: UploadFile = File(...),
    format: str = Form(...),
    quality: int = Form(90),
    width: int | None = Form(None),
    height: int | None = Form(None),
    scale_percent: float | None = Form(None),
    preserve_aspect_ratio: bool = Form(True),
    allow_upscale: bool = Form(False),
    progressive: bool = Form(True),
    lossless: bool = Form(False),
    target_size_bytes: int | None = Form(None),
    background_color: str = Form("#ffffff"),
) -> Response:
    try:
        validate_image_mime_type(file.content_type)
        async with heavy_request_guard(request):
            image_bytes = await read_upload_limited(file)
            processed = await asyncio.to_thread(
                convert_image,
                image_bytes,
                format,
                quality=quality,
                width=width,
                height=height,
                scale_percent=scale_percent,
                preserve_aspect_ratio=preserve_aspect_ratio,
                allow_upscale=allow_upscale,
                progressive=progressive,
                lossless=lossless,
                target_size_bytes=target_size_bytes,
                background_color=background_color,
            )
    except FileProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    extension = get_extension(processed.image_format)
    filename = converted_output_filename(file.filename, extension)
    return Response(
        content=processed.content,
        media_type=get_content_type(processed.image_format),
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
            "X-Konvertira-Width": str(processed.width or ""),
            "X-Konvertira-Height": str(processed.height or ""),
            "X-Konvertira-Encoding-Attempts": str(processed.encoding_attempts),
        },
    )
