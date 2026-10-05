"""Image conversion routes."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from backend.models.files import FileProcessingError
from backend.processors.image import convert_image
from backend.services.security import read_upload_limited
from backend.utils.filenames import converted_output_filename
from backend.utils.mime import ALLOWED_IMAGE_MIME_TYPES, get_content_type

router = APIRouter()


@router.post("/images/convert")
async def convert_image_upload(
    file: UploadFile = File(...),
    format: str = Form(...),
    quality: int = Form(90),
) -> Response:
    if file.content_type and file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Supported formats are JPEG, PNG and WEBP.")

    image_bytes = await read_upload_limited(file)
    try:
        processed = convert_image(image_bytes, format, quality=quality)
    except FileProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    extension = "jpg" if processed.image_format == "JPEG" else processed.image_format.lower()
    filename = converted_output_filename(file.filename, extension)
    return Response(
        content=processed.content,
        media_type=get_content_type(processed.image_format),
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
