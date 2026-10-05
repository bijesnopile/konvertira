"""Konvertira FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.compat import cleanup_old_files, download_openai_file, remove_metadata
from backend.routers import conversion, downloads, health, metadata
from backend.schemas import ActionRequest, ActionResponse, OpenAIFileRef
from backend.services.security import api_key_header, verify_api_key
from backend.services.storage import api_storage
from backend.utils.filenames import clean_filename
from backend.utils.mime import (
    ALLOWED_IMAGE_FORMATS as ALLOWED_FORMATS,
    ALLOWED_IMAGE_MIME_TYPES as ALLOWED_MIME_TYPES,
    get_content_type,
)
from config import settings

# Compatibility exports retained for integrations that imported these from main.py.
APP_TITLE = settings.app_name
APP_VERSION = settings.app_version
MAX_IMAGE_SIZE = settings.max_image_size
MAX_PIXELS = settings.max_pixels
RESULT_TTL_SECONDS = settings.result_ttl_seconds
STORAGE_DIR = settings.storage_dir
API_KEY = settings.api_key
ALLOWED_DOWNLOAD_HOST = "files.oaiusercontent.com"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    api_storage.cleanup()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Removes metadata from and converts JPEG, PNG, and WEBP images.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "X-API-Key"],
        expose_headers=["Content-Disposition"],
    )
    application.include_router(health.router)
    application.include_router(metadata.router)
    application.include_router(conversion.router)
    application.include_router(downloads.router)
    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=settings.port)
