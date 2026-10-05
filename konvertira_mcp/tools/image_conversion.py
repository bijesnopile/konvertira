"""Reusable conversion operation reserved for a future registered MCP tool."""

from backend.models.files import ProcessedFile
from backend.processors.image import convert_image


def convert_uploaded_image(content: bytes, output_format: str, quality: int = 90) -> ProcessedFile:
    return convert_image(content, output_format, quality=quality)
