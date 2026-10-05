"""Backward-compatible MCP ASGI entry point.

Deployments using ``uvicorn mcp_server:app`` continue to work.
"""

from konvertira_mcp.server import app, mcp
from backend.utils.mime import ALLOWED_IMAGE_MIME_TYPES as ALLOWED_MIME_TYPES
from config import settings
from konvertira_mcp.models.files import OpenAIFile, ProcessedImage
from konvertira_mcp.tools.image_metadata import mcp_storage, remove_image_metadata

PUBLIC_BASE_URL = settings.mcp_public_base_url
RESULT_TTL_SECONDS = settings.result_ttl_seconds
STORAGE_DIR = settings.mcp_storage_dir


def cleanup_old_files() -> None:
    mcp_storage.cleanup()


__all__ = [
    "ALLOWED_MIME_TYPES",
    "OpenAIFile",
    "ProcessedImage",
    "PUBLIC_BASE_URL",
    "RESULT_TTL_SECONDS",
    "STORAGE_DIR",
    "app",
    "cleanup_old_files",
    "mcp",
    "remove_image_metadata",
]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("mcp_server:app", host="0.0.0.0", port=settings.mcp_port)
