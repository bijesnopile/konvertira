"""Safe output filename helpers."""

import re

from backend.formats import normalize_format

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def clean_filename(filename: str | None, fallback: str = "image") -> str:
    if not filename:
        return fallback

    basename = filename.strip().replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", basename).strip(" .")
    return cleaned or fallback


def cleaned_output_filename(filename: str | None, output_format: str | None = None) -> str:
    cleaned = clean_filename(filename)
    stem, separator, source_extension = cleaned.rpartition(".")
    if not separator:
        stem = cleaned
    definition = normalize_format(output_format or source_extension)
    if definition is None or not definition.implemented:
        if output_format:
            raise ValueError(f"Unsupported output format: {output_format}")
        return f"clean_{cleaned}"
    output_extension = definition.preferred_extension
    return f"clean_{stem}{output_extension}"


def converted_output_filename(filename: str | None, extension: str) -> str:
    definition = normalize_format(extension)
    if definition is None or not definition.implemented:
        raise ValueError(f"Unsupported output extension: {extension}")
    cleaned = clean_filename(filename)
    stem = cleaned.rsplit(".", 1)[0] if "." in cleaned else cleaned
    return f"{stem}{definition.preferred_extension}"
