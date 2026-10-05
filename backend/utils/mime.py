"""Supported image format and MIME mappings."""

from typing import Final

ALLOWED_IMAGE_FORMATS: Final[frozenset[str]] = frozenset({"JPEG", "PNG", "WEBP"})
ALLOWED_IMAGE_MIME_TYPES: Final[frozenset[str]] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)

FORMAT_TO_MIME: Final[dict[str, str]] = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}

FORMAT_TO_EXTENSION: Final[dict[str, str]] = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
}

EXTENSION_TO_MIME: Final[dict[str, str]] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def get_content_type(image_format: str) -> str:
    return FORMAT_TO_MIME.get(image_format.upper(), "application/octet-stream")


def get_extension(image_format: str) -> str:
    try:
        return FORMAT_TO_EXTENSION[image_format.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported image format: {image_format}") from exc


def content_type_for_path(path_suffix: str) -> str:
    return EXTENSION_TO_MIME.get(path_suffix.lower(), "application/octet-stream")
