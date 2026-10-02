import contextlib
import os
import secrets
import tempfile
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, HttpUrl

from main import (
    MAX_IMAGE_SIZE,
    clean_filename,
    download_openai_file,
    get_content_type,
    remove_metadata,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIG
# ============================================================

PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    "https://metadata-remover-ompw.onrender.com",
).rstrip("/")

RESULT_TTL_SECONDS = 15 * 60

STORAGE_DIR = (
    Path(tempfile.gettempdir())
    / "image-privacy-protector-results"
)

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer(
    name="Image Privacy Protector",
    version="1.0.0",
    instructions=(
        "Use remove_image_metadata when the user asks to remove "
        "embedded metadata from exactly one uploaded JPEG, PNG, "
        "or WEBP image."
    ),
)


# ============================================================
# FILE MODEL
# ============================================================

class OpenAIFile(BaseModel):
    """
    File object supplied by ChatGPT for an MCP file input.

    OpenAI requires:
        download_url
        file_id

    Optional:
        mime_type
        file_name
    """

    model_config = ConfigDict(
        extra="forbid"
    )

    download_url: HttpUrl
    file_id: str

    mime_type: str | None = None
    file_name: str | None = None


# ============================================================
# RESPONSE MODEL
# ============================================================

class ProcessedImage(BaseModel):
    success: bool
    filename: str
    content_type: str
    download_url: HttpUrl
    message: str


# ============================================================
# CLEANUP
# ============================================================

def cleanup_old_files() -> None:
    """
    Removes temporary processed images older than the TTL.
    """

    now = time.time()

    for path in STORAGE_DIR.iterdir():

        if not path.is_file():
            continue

        try:
            age = now - path.stat().st_mtime

            if age > RESULT_TTL_SECONDS:
                path.unlink(missing_ok=True)

        except OSError:
            # Cleanup failure should not break image processing.
            pass


# ============================================================
# MCP TOOL
# ============================================================

@mcp.tool(
    name="remove_image_metadata",
    title="Remove image metadata",
    description=(
        "Removes embedded metadata such as EXIF, GPS, camera, "
        "date, and related metadata from exactly one uploaded "
        "JPEG, PNG, or WEBP image. The original image is not "
        "modified."
    ),
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
        idempotent_hint=True,
    ),
    meta={
        "openai/fileParams": ["file"],
        "openai/toolInvocation/invoking": (
            "Removing image metadata..."
        ),
        "openai/toolInvocation/invoked": (
            "Image cleaned"
        ),
    },
    structured_output=True,
)
async def remove_image_metadata(
    file: OpenAIFile,
) -> ProcessedImage:
    """
    Remove metadata from one uploaded image.
    """

    cleanup_old_files()

    # --------------------------------------------------------
    # MIME TYPE
    # --------------------------------------------------------

    if (
        file.mime_type
        and file.mime_type not in ALLOWED_MIME_TYPES
    ):
        raise ValueError(
            "Unsupported image format. "
            "JPEG, PNG and WEBP are supported."
        )

    # --------------------------------------------------------
    # DOWNLOAD IMAGE FROM CHATGPT
    # --------------------------------------------------------

    image_bytes = await download_openai_file(
        str(file.download_url)
    )

    if not image_bytes:
        raise ValueError(
            "Uploaded image is empty."
        )

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise ValueError(
            "Image is larger than the 20 MB limit."
        )

    # --------------------------------------------------------
    # REMOVE METADATA
    # --------------------------------------------------------

    clean_bytes, image_format = remove_metadata(
        image_bytes
    )

    # --------------------------------------------------------
    # TEMPORARY STORAGE
    # --------------------------------------------------------

    token = secrets.token_urlsafe(32)

    extension = {
        "JPEG": ".jpg",
        "PNG": ".png",
        "WEBP": ".webp",
    }.get(image_format)

    if not extension:
        raise ValueError(
            f"Unsupported output format: {image_format}"
        )

    result_path = (
        STORAGE_DIR
        / f"{token}{extension}"
    )

    try:
        result_path.write_bytes(
            clean_bytes
        )
    except OSError as exc:
        raise RuntimeError(
            f"Could not save processed image: {exc}"
        ) from exc

    # --------------------------------------------------------
    # DOWNLOAD URL
    # --------------------------------------------------------

    download_url = (
        f"{PUBLIC_BASE_URL}"
        f"/download/{token}"
    )

    original_name = clean_filename(
        file.file_name
    )

    clean_name = (
        f"clean_{original_name}"
    )

    return ProcessedImage(
        success=True,
        filename=clean_name,
        content_type=get_content_type(
            image_format
        ),
        download_url=download_url,
        message=(
            "The image was processed successfully. "
            "Embedded metadata was removed from the "
            "processed copy."
        ),
    )


# ============================================================
# MCP HTTP APPLICATION
# ============================================================

mcp_http_app = mcp.streamable_http_app(
    streamable_http_path="/",
    json_response=True,
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[
            "metadata-remover-ompw.onrender.com",
        ],
        allowed_origins=[
            "https://chatgpt.com",
            "https://www.chatgpt.com",
        ],
    ),
)


# ============================================================
# FASTAPI LIFESPAN
# ============================================================

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Starts and stops the MCP session manager correctly.
    """

    async with mcp.session_manager.run():
        yield


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Image Privacy Protector MCP",
    version="1.0.0",
    description=(
        "MCP server for removing embedded metadata "
        "from uploaded images."
    ),
    lifespan=lifespan,
)


# ============================================================
# MCP ENDPOINT
# ============================================================

app.mount(
    "/mcp",
    mcp_http_app,
)


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Image Privacy Protector MCP",
    }


@app.get("/")
async def root():
    return {
        "service": "Image Privacy Protector MCP",
        "version": "1.0.0",
        "mcp_endpoint": "/mcp",
        "status": "running",
    }


# ============================================================
# PRIVACY POLICY
# ============================================================

@app.get("/privacy")
async def privacy():
    return {
        "service": "Image Privacy Protector",
        "privacy": (
            "Uploaded images are processed temporarily "
            "for the purpose of removing embedded metadata. "
            "Processed files are automatically removed "
            "after a limited period."
        ),
    }


# ============================================================
# DOWNLOAD RESULT
# ============================================================

@app.get("/download/{token}")
async def download_result(
    token: str,
):
    """
    Returns a processed image.

    Files are temporary and are cleaned automatically.
    """

    cleanup_old_files()

    if not token or len(token) < 20:
        raise HTTPException(
            status_code=404,
            detail="File not found.",
        )

    matches = list(
        STORAGE_DIR.glob(
            f"{token}.*"
        )
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail=(
                "File is no longer available."
            ),
        )

    file_path = matches[0]

    content_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(
        file_path.suffix.lower(),
        "application/octet-stream",
    )

    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=file_path.name,
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )