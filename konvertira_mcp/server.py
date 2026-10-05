"""MCP server creation and HTTP transport application."""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from backend.utils.mime import content_type_for_path
from config import settings
from konvertira_mcp.tools.image_metadata import mcp_storage, remove_image_metadata

mcp = MCPServer(
    name="Image Privacy Protector",
    version="1.0.0",
    instructions=(
        "Use remove_image_metadata when the user asks to remove embedded metadata "
        "from exactly one uploaded JPEG, PNG, or WEBP image."
    ),
)

mcp.tool(
    name="remove_image_metadata",
    title="Remove image metadata",
    description=(
        "Removes embedded metadata such as EXIF, GPS, camera, date, and related "
        "metadata from exactly one uploaded JPEG, PNG, or WEBP image. The original "
        "image is not modified."
    ),
    annotations=ToolAnnotations(
        read_only_hint=False,
        destructive_hint=False,
        open_world_hint=False,
        idempotent_hint=True,
    ),
    meta={
        "openai/fileParams": ["file"],
        "openai/toolInvocation/invoking": "Removing image metadata...",
        "openai/toolInvocation/invoked": "Image cleaned",
    },
    structured_output=True,
)(remove_image_metadata)

mcp_http_app = mcp.streamable_http_app(
    streamable_http_path="/",
    json_response=True,
    stateless_http=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=list(settings.mcp_allowed_hosts),
        allowed_origins=list(settings.mcp_allowed_origins),
    ),
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    mcp_storage.cleanup()
    async with mcp.session_manager.run():
        yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="Image Privacy Protector MCP",
        version="1.0.0",
        description="MCP server for removing embedded metadata from uploaded images.",
        lifespan=lifespan,
    )
    application.mount("/mcp", mcp_http_app)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "Image Privacy Protector MCP"}

    @application.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": "Image Privacy Protector MCP",
            "version": "1.0.0",
            "mcp_endpoint": "/mcp",
            "status": "running",
        }

    @application.get("/privacy")
    async def privacy() -> dict[str, str]:
        return {
            "service": "Image Privacy Protector",
            "privacy": (
                "Uploaded images are processed temporarily for the purpose of removing "
                "embedded metadata. Processed files are automatically removed after a "
                "limited period."
            ),
        }

    @application.get("/download/{token}")
    async def download_result(token: str) -> FileResponse:
        mcp_storage.cleanup()
        file_path = mcp_storage.resolve(token)
        if file_path is None:
            raise HTTPException(status_code=404, detail="File is no longer available.")
        return FileResponse(
            path=file_path,
            media_type=content_type_for_path(file_path.suffix),
            filename=file_path.name,
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )

    return application


app = create_app()
