"""Common file validation functions."""

from backend.models.files import FileProcessingError
from backend.utils.mime import ALLOWED_IMAGE_MIME_TYPES


def validate_image_mime_type(mime_type: str | None) -> None:
    if mime_type and mime_type.lower() not in ALLOWED_IMAGE_MIME_TYPES:
        raise FileProcessingError(
            "Supported formats are JPEG, PNG and WEBP.", status_code=415
        )


def validate_file_size(content: bytes, max_size: int) -> None:
    if not content:
        raise FileProcessingError("The image is empty.", status_code=400)
    if len(content) > max_size:
        limit_mb = max_size // (1024 * 1024)
        raise FileProcessingError(
            f"The image is larger than the {limit_mb} MB limit.", status_code=413
        )
