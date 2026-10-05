"""Image metadata-removal API routes, including legacy contracts."""

import asyncio

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import Response

from backend.models.files import FileProcessingError, StorageError
from backend.processors.image import remove_image_metadata
from backend.schemas.requests import ActionRequest
from backend.schemas.responses import ActionResponse
from backend.services.downloads import DownloadError, download_openai_file
from backend.services.image_workflow import clean_and_store
from backend.services.security import (
    heavy_request_guard,
    read_request_body_limited,
    read_upload_limited,
    verify_api_key,
)
from backend.services.storage import api_storage
from backend.utils.filenames import clean_filename, cleaned_output_filename
from backend.utils.mime import ALLOWED_IMAGE_MIME_TYPES, get_content_type
from config import settings

router = APIRouter()


def _raise_http(error: Exception) -> None:
    status_code = getattr(error, "status_code", 500)
    raise HTTPException(status_code=status_code, detail=str(error)) from error


@router.post("/remove-metadata/action", response_model=ActionResponse)
async def remove_metadata_action(
    payload: ActionRequest,
    http_request: Request,
    _: None = Depends(verify_api_key),
) -> ActionResponse:
    """Legacy GPT Actions endpoint; its path and response schema are unchanged."""

    file_ref = payload.openaiFileIdRefs[0]
    if file_ref.mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Supported formats are JPEG, PNG and WEBP.")

    try:
        async with heavy_request_guard(http_request):
            image_bytes = await download_openai_file(file_ref.download_link)
            processed, stored = await asyncio.to_thread(
                clean_and_store,
                image_bytes,
                api_storage,
            )
    except (DownloadError, FileProcessingError, StorageError) as exc:
        _raise_http(exc)
        raise AssertionError("unreachable")

    return ActionResponse(
        success=True,
        filename=cleaned_output_filename(file_ref.name),
        content_type=get_content_type(processed.image_format),
        download_url=f"{settings.public_base_url}/download/{stored.token}",
        message=(
            "Metadata were removed. Open download_url to download the cleaned image."
        ),
    )


@router.post("/remove-metadata/upload")
async def manual_upload(
    request: Request,
    file: bytes | None = Query(default=None),
    _: None = Depends(verify_api_key),
) -> Response:
    """Legacy raw-byte endpoint; accepts the historical query form and request body."""

    try:
        async with heavy_request_guard(request):
            image_bytes = (
                file
                if file is not None
                else await read_request_body_limited(request)
            )
            processed = await asyncio.to_thread(remove_image_metadata, image_bytes)
    except FileProcessingError as exc:
        _raise_http(exc)
        raise AssertionError("unreachable")
    return Response(
        content=processed.content,
        media_type=get_content_type(processed.image_format),
        headers={"Cache-Control": "no-store"},
    )


@router.post("/images/remove-metadata")
async def remove_metadata_upload(
    request: Request,
    file: UploadFile = File(...),
) -> Response:
    """Public multipart endpoint used by the Konvertira website."""

    if file.content_type and file.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=415, detail="Supported formats are JPEG, PNG and WEBP.")
    try:
        async with heavy_request_guard(request):
            image_bytes = await read_upload_limited(file)
            processed = await asyncio.to_thread(remove_image_metadata, image_bytes)
    except FileProcessingError as exc:
        _raise_http(exc)
        raise AssertionError("unreachable")

    filename = cleaned_output_filename(clean_filename(file.filename))
    return Response(
        content=processed.content,
        media_type=get_content_type(processed.image_format),
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
