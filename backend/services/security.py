"""HTTP authentication and shared security dependencies."""

import secrets

from fastapi import Depends, HTTPException, UploadFile
from fastapi.security import APIKeyHeader

from config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(x_api_key: str | None = Depends(api_key_header)) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
    if not settings.api_key:
        raise HTTPException(status_code=503, detail="API authentication is not configured.")
    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="Invalid API key.")


async def read_upload_limited(upload: UploadFile, limit: int | None = None) -> bytes:
    """Read at most the configured limit plus one byte from an upload."""

    size_limit = limit or settings.max_image_size
    content = await upload.read(size_limit + 1)
    if len(content) > size_limit:
        limit_mb = size_limit // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"The image is larger than the {limit_mb} MB limit.",
        )
    return content
