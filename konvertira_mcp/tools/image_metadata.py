"""MCP image metadata tool implemented with shared backend services."""

from backend.models.files import FileProcessingError, StorageError
from backend.services.downloads import DownloadError, download_openai_file
from backend.services.image_workflow import clean_and_store
from backend.services.storage import TemporaryStorage
from backend.utils.filenames import cleaned_output_filename
from backend.utils.mime import ALLOWED_IMAGE_MIME_TYPES, get_content_type
from config import settings
from konvertira_mcp.models.files import OpenAIFile, ProcessedImage

mcp_storage = TemporaryStorage(settings.mcp_storage_dir, settings.result_ttl_seconds)


async def remove_image_metadata(file: OpenAIFile) -> ProcessedImage:
    """Remove embedded metadata from one ChatGPT-uploaded image."""

    if file.mime_type and file.mime_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValueError("Unsupported image format. JPEG, PNG and WEBP are supported.")

    try:
        image_bytes = await download_openai_file(str(file.download_url))
        processed, stored = clean_and_store(image_bytes, mcp_storage)
    except (DownloadError, FileProcessingError) as exc:
        raise ValueError(str(exc)) from exc
    except StorageError as exc:
        raise RuntimeError(str(exc)) from exc

    return ProcessedImage(
        success=True,
        filename=cleaned_output_filename(file.file_name),
        content_type=get_content_type(processed.image_format),
        download_url=f"{settings.mcp_public_base_url}/download/{stored.token}",
        message=(
            "The image was processed successfully. Embedded metadata was removed "
            "from the processed copy."
        ),
    )
