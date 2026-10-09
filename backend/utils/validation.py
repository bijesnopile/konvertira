"""Common file validation functions based on untrusted declared metadata."""

from backend.formats import FormatCategory, format_from_mime
from backend.models.files import FileProcessingError, ProcessingErrorCode


def validate_image_mime_type(mime_type: str | None) -> None:
    if not mime_type:
        return
    definition = format_from_mime(mime_type)
    if (
        definition is None
        or definition.category != FormatCategory.IMAGE
        or not definition.supports_mode("server")
    ):
        raise FileProcessingError(
            "The declared image format is not supported for server processing.",
            status_code=415,
            code=ProcessingErrorCode.UNSUPPORTED_FORMAT,
        )


def validate_file_size(content: bytes, max_size: int) -> None:
    if not content:
        raise FileProcessingError(
            "The image is empty.",
            status_code=400,
            code=ProcessingErrorCode.INVALID_FILE,
        )
    if len(content) > max_size:
        limit_mb = max_size // (1024 * 1024)
        raise FileProcessingError(
            f"The image is larger than the {limit_mb} MB limit.",
            status_code=413,
            code=ProcessingErrorCode.FILE_TOO_LARGE,
        )
