"""MCP image metadata tool implemented with shared backend services."""

import asyncio

from backend.models.files import FileProcessingError, StorageError
from backend.formats import declared_format
from backend.services.downloads import DownloadError, download_openai_file
from backend.services.image_workflow import clean_and_store
from backend.services.resource_limits import McpResourceError, mcp_resource_limits
from backend.services.storage import TemporaryStorage
from backend.utils.filenames import cleaned_output_filename
from backend.utils.mime import get_content_type
from backend.utils.validation import validate_image_mime_type
from config import settings
from konvertira_mcp.models.files import OpenAIFile, ProcessedImage

mcp_storage = TemporaryStorage(
    settings.mcp_storage_dir,
    settings.result_ttl_seconds,
    settings.mcp_max_temp_storage_bytes,
)


class McpToolUserError(RuntimeError):
    """A safe processing error that can be shown to the MCP caller."""


async def remove_image_metadata(file: OpenAIFile) -> ProcessedImage:
    """Remove embedded metadata from one ChatGPT-uploaded image."""

    async def process() -> ProcessedImage:
        try:
            hints = declared_format(file.file_name, file.mime_type)
            definition = hints.candidate
            if not hints.is_consistent or definition is None or "server" not in definition.modes_for("removeMetadata"):
                raise McpToolUserError("The file must be a JPEG, PNG, or static WebP image with matching type information.")
            validate_image_mime_type(file.mime_type)
            image_bytes = await download_openai_file(str(file.download_url))
            processed, stored = await asyncio.to_thread(
                clean_and_store,
                image_bytes,
                mcp_storage,
            )
        except (DownloadError, FileProcessingError) as exc:
            raise McpToolUserError(str(exc)) from exc
        except StorageError as exc:
            raise McpToolUserError(str(exc)) from exc

        return ProcessedImage(
            success=True,
            filename=cleaned_output_filename(file.file_name, processed.image_format),
            content_type=get_content_type(processed.image_format),
            download_url=f"{settings.mcp_public_base_url}/download/{stored.token}",
            message=(
                "The image was processed successfully. Embedded metadata was removed "
                "from the processed copy."
            ),
        )

    try:
        return await mcp_resource_limits.run_heavy_job(
            "remove_image_metadata",
            process,
        )
    except McpResourceError as exc:
        raise ValueError(str(exc)) from None
    except McpToolUserError as exc:
        raise ValueError(str(exc)) from None
    except Exception:
        raise RuntimeError(
            "Konvertira could not process this image. Please try again."
        ) from None
