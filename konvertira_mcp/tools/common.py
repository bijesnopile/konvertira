"""Shared MCP download, result, and safe-error orchestration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from backend.formats import declared_format, normalize_format
from backend.models.files import FileProcessingError, StorageError
from backend.services.downloads import DownloadError, download_openai_file
from backend.services.resource_limits import McpResourceError, mcp_resource_limits
from backend.utils.filenames import clean_filename
from config import settings
from konvertira_mcp.models.files import OpenAIFile, ProcessedResult
from konvertira_mcp.tools.image_metadata import mcp_storage

T = TypeVar("T")


class McpWorkflowError(RuntimeError):
    pass


def input_format(file: OpenAIFile):
    hints = declared_format(file.file_name, file.mime_type)
    if not hints.is_consistent:
        raise McpWorkflowError("The filename extension and MIME type do not match.")
    definition = hints.candidate
    if definition is None or not definition.supports_mode("server"):
        raise McpWorkflowError("The uploaded file format is unsupported.")
    return definition


async def download_input(file: OpenAIFile, max_size: int) -> bytes:
    input_format(file)
    return await download_openai_file(str(file.download_url), max_size=max_size)


def stored_result(content: bytes, extension: str, original_name: str | None, message: str) -> ProcessedResult:
    definition = normalize_format(extension)
    suffix = definition.preferred_extension if definition else extension
    content_type = definition.preferred_mime_type if definition else "application/zip"
    stored = mcp_storage.save(content, suffix)
    cleaned = clean_filename(original_name, "konvertira-result")
    stem = cleaned.rsplit(".", 1)[0]
    return ProcessedResult(
        success=True,
        filename=f"{stem}{suffix}",
        content_type=content_type,
        download_url=f"{settings.mcp_public_base_url}/download/{stored.token}",
        message=message,
    )


async def run_heavy(tool_name: str, operation: Callable[[], Awaitable[T]]) -> T:
    try:
        return await mcp_resource_limits.run_heavy_job(tool_name, operation)
    except McpResourceError as exc:
        raise ValueError(str(exc)) from None
    except (McpWorkflowError, DownloadError, FileProcessingError, StorageError) as exc:
        raise ValueError(str(exc)) from None
    except Exception:
        raise RuntimeError("Konvertira could not complete this file operation. Please try again.") from None
