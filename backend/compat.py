"""Compatibility adapters for functions historically imported from ``main``."""

from fastapi import HTTPException

from backend.models.files import FileProcessingError
from backend.processors.image import remove_image_metadata
from backend.services.downloads import DownloadError, download_openai_file as _download
from backend.services.storage import api_storage


def remove_metadata(image_bytes: bytes) -> tuple[bytes, str]:
    try:
        result = remove_image_metadata(image_bytes)
    except FileProcessingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return result.content, result.image_format


def cleanup_old_files() -> None:
    api_storage.cleanup()


async def download_openai_file(download_link: str) -> bytes:
    try:
        return await _download(download_link)
    except DownloadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
