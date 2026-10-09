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
from konvertira_mcp.tools.workflows import (
    convert_document,
    convert_image,
    convert_images_to_pdf,
    convert_pdf_to_images,
    convert_presentation,
    convert_spreadsheet,
    extract_pdf_file_pages,
    inspect_file_metadata,
    merge_pdf_files,
    remove_file_metadata,
)

mcp = MCPServer(
    name="Konvertira",
    version="1.0.0",
    instructions=(
        "Use Konvertira tools only for supported file conversion, PDF page workflows, "
        "and metadata inspection/removal. All MCP file processing is temporary server processing."
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

_COPY_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=False,
    open_world_hint=False,
    idempotent_hint=True,
)
_INSPECT_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    open_world_hint=False,
    idempotent_hint=True,
)


def _register_tool(name, title, description, function, *, inspect=False, file_params=("file",)):
    mcp.tool(
        name=name,
        title=title,
        description=description,
        annotations=_INSPECT_ANNOTATIONS if inspect else _COPY_ANNOTATIONS,
        meta={"openai/fileParams": list(file_params)},
        structured_output=True,
    )(function)


_register_tool("convert_image", "Convert an image", "Convert one supported static image to JPEG, PNG, WebP, or AVIF with optional bounded resize settings. Animated images are rejected.", convert_image)
_register_tool("inspect_file_metadata", "Inspect file metadata", "Inspect supported image, PDF, OOXML, or ODF metadata. Results do not prove anonymity or absence of hidden content.", inspect_file_metadata, inspect=True)
_register_tool("remove_file_metadata", "Remove supported file metadata", "Create a new supported image, PDF, OOXML, or ODF copy with metadata fields Konvertira knows how to remove.", remove_file_metadata)
_register_tool("merge_pdfs", "Merge PDFs", "Merge 2 to 10 uploaded, unencrypted PDFs in the supplied order.", merge_pdf_files, file_params=("files",))
_register_tool("extract_pdf_pages", "Extract PDF pages", "Extract a validated page selection such as 1-3,5 from one unencrypted PDF.", extract_pdf_file_pages)
_register_tool("convert_pdf_to_images", "Convert PDF pages to images", "Render bounded pages from one unencrypted PDF into a ZIP of PNG, JPEG, or WebP images. Rasterization is lossy.", convert_pdf_to_images)
_register_tool("convert_images_to_pdf", "Convert images to PDF", "Create one PDF from 1 to 10 supported static images in the supplied order.", convert_images_to_pdf, file_params=("files",))
_register_tool("convert_document", "Convert a document", "Convert one supported DOCX, DOC, ODT, RTF, TXT, Markdown, or HTML document using the explicit safe conversion matrix.", convert_document)
_register_tool("convert_spreadsheet", "Convert a spreadsheet", "Convert one XLSX, XLS, ODS, or CSV file. Multi-sheet CSV output is packaged safely.", convert_spreadsheet)
_register_tool("convert_presentation", "Convert a presentation", "Convert one PPTX, PPT, or ODP presentation to a supported presentation format or PDF.", convert_presentation)

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
        title="Konvertira MCP",
        version="1.0.0",
        description="MCP server for supported Konvertira conversion, PDF, and metadata workflows.",
        lifespan=lifespan,
    )

    @application.middleware("http")
    async def protect_mcp_processing(request: Request, call_next):
        if request.method != "OPTIONS" and request.url.path.startswith("/mcp"):
            try:
                mcp_resource_limits.check_request()
            except McpRateLimitError as exc:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": str(exc)},
                    headers={"Retry-After": str(exc.retry_after)},
                )
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["Referrer-Policy"] = "no-referrer"
                return response
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    application.mount("/mcp", mcp_http_app)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "Konvertira MCP"}

    @application.get("/")
    async def root() -> dict[str, str]:
        return {
            "service": "Konvertira MCP",
            "version": "1.0.0",
            "mcp_endpoint": "/mcp",
            "status": "running",
        }

    @application.get("/privacy")
    async def privacy() -> dict[str, str]:
        return {
            "service": "Konvertira",
            "privacy": (
                "Uploaded files are processed temporarily for the selected conversion, PDF, "
                "or metadata workflow. Results are automatically removed after a limited period."
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
