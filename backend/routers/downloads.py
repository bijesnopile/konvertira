"""Temporary result download route."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.services.storage import api_storage
from backend.utils.mime import content_type_for_path

router = APIRouter()


@router.get("/download/{token}")
async def download_result(token: str) -> FileResponse:
    api_storage.cleanup()
    file_path = api_storage.resolve(token)
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail="File is no longer available. Generate a new cleaned image.",
        )

    return FileResponse(
        path=file_path,
        media_type=content_type_for_path(file_path.suffix),
        filename=f"clean_{file_path.stem}{file_path.suffix}",
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
