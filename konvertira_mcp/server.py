"""MCP server creation and HTTP transport application."""

import asyncio
from contextlib import asynccontextmanager, suppress
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from backend.utils.mime import content_type_for_path
from backend.services.resource_limits import McpRateLimitError, mcp_resource_limits
from backend.services.security import enforce_general_rate
from backend.services.storage import cleanup_periodically
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
    cleanup_task = asyncio.create_task(cleanup_periodically(mcp_storage))
    try:
        async with mcp.session_manager.run():
            yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


def create_app() -> FastAPI:
    application = FastAPI(
        title="Image Privacy Protector MCP",
        version="1.0.0",
        description="MCP server for removing embedded metadata from uploaded images.",
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def protect_mcp_processing(request: Request, call_next):
        if request.method != "OPTIONS" and request.url.path.startswith("/mcp"):
            try:
                mcp_resource_limits.check_request()
            except McpRateLimitError as exc:
                return JSONResponse(
                    status_code=429,
                    content={"detail": str(exc)},
                    headers={"Retry-After": str(exc.retry_after)},
                )
        return await call_next(request)

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
    async def download_result(token: str, request: Request) -> FileResponse:
        enforce_general_rate(request)
        mcp_storage.cleanup()
        file_path = mcp_storage.resolve(token)
        if file_path is None:
            raise HTTPException(status_code=404, detail="File is no longer available.")
        return FileResponse(
            path=file_path,
            media_type=content_type_for_path(file_path.suffix),
            filename=f"konvertira-cleaned{file_path.suffix}",
            headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
        )

    return application


app = create_app()
