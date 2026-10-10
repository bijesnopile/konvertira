"""Explicit server-only image segmentation endpoint."""
import asyncio

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response

from backend.formats import declared_format
from backend.models.files import FileProcessingError
from backend.processors.background_removal import BackgroundOutputFormat, WARNING, remove_image_background
from backend.services.security import heavy_request_guard, read_upload_limited
from backend.utils.filenames import converted_output_filename
from config import settings

router = APIRouter()
_jobs: set[asyncio.Task] = set()


def _finished(task):
    _jobs.discard(task)
    if not task.cancelled():
        task.exception()


@router.post("/images/remove-background")
async def remove_background(request: Request, file: UploadFile = File(...), output_format: BackgroundOutputFormat = Form(BackgroundOutputFormat.PNG)) -> Response:
    hints = declared_format(file.filename, file.content_type)
    definition = hints.candidate
    if not hints.is_consistent or definition is None or "server" not in definition.modes_for("removeBackground"):
        raise HTTPException(415, "Choose a supported static image with matching filename and MIME type.")

    async def operation():
        # Task owns the slot through download/decode/inference, including timeout.
        async with heavy_request_guard(request):
            content = await read_upload_limited(file)
            return await asyncio.to_thread(remove_image_background, content, output_format=output_format, expected_format=definition.id)

    task = asyncio.create_task(operation())
    _jobs.add(task)
    task.add_done_callback(_finished)
    try:
        result = await asyncio.wait_for(asyncio.shield(task), timeout=settings.background_timeout_seconds)
    except TimeoutError as exc:
        raise HTTPException(504, "Background removal exceeded the allowed processing time.") from exc
    except FileProcessingError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    extension = f".{output_format.value}"
    return Response(result.content, media_type=f"image/{output_format.value}", headers={
        "Content-Disposition": f'attachment; filename="{converted_output_filename(file.filename, extension)}"',
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "X-Konvertira-Privacy-Warning": WARNING,
    })
