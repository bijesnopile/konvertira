"""Backward-compatible MIME helpers derived from the format registry."""

from typing import Final

from backend.formats import FormatCategory, format_from_extension, format_from_processor_name, implemented_formats

_SERVER_IMAGES = implemented_formats(category=FormatCategory.IMAGE, mode="server")

ALLOWED_IMAGE_FORMATS: Final[frozenset[str]] = frozenset(
    definition.processor_names[0] for definition in _SERVER_IMAGES
)
ALLOWED_IMAGE_MIME_TYPES: Final[frozenset[str]] = frozenset(
    mime_type for definition in _SERVER_IMAGES for mime_type in definition.mime_types
)

FORMAT_TO_MIME: Final[dict[str, str]] = {
    definition.processor_names[0]: definition.preferred_mime_type
    for definition in _SERVER_IMAGES
}
FORMAT_TO_EXTENSION: Final[dict[str, str]] = {
    definition.processor_names[0]: definition.preferred_extension
    for definition in _SERVER_IMAGES
}
EXTENSION_TO_MIME: Final[dict[str, str]] = {
    extension: definition.preferred_mime_type
    for definition in _SERVER_IMAGES
    for extension in definition.extensions
}


def get_content_type(image_format: str) -> str:
    definition = format_from_processor_name(image_format)
    return definition.preferred_mime_type if definition and definition.implemented else "application/octet-stream"


def get_extension(image_format: str) -> str:
    definition = format_from_processor_name(image_format)
    if definition is None or not definition.implemented:
        raise ValueError(f"Unsupported image format: {image_format}")
    return definition.preferred_extension


def content_type_for_path(path_suffix: str) -> str:
    if path_suffix.lower() == ".zip":
        return "application/zip"
    definition = format_from_extension(path_suffix)
    return definition.preferred_mime_type if definition and definition.implemented else "application/octet-stream"
