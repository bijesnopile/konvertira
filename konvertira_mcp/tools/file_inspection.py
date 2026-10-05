"""Reusable inspection operation reserved for a future registered MCP tool."""

from typing import Any

from backend.processors.image import inspect_image_metadata


def inspect_uploaded_image(content: bytes) -> dict[str, Any]:
    return inspect_image_metadata(content)
