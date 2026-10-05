"""Safe output filename helpers."""

import re

_UNSAFE_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def clean_filename(filename: str | None, fallback: str = "image") -> str:
    if not filename:
        return fallback

    basename = filename.strip().replace("\\", "/").rsplit("/", 1)[-1]
    cleaned = _UNSAFE_FILENAME_CHARS.sub("_", basename).strip(" .")
    return cleaned or fallback


def cleaned_output_filename(filename: str | None) -> str:
    return f"clean_{clean_filename(filename)}"


def converted_output_filename(filename: str | None, extension: str) -> str:
    cleaned = clean_filename(filename)
    stem = cleaned.rsplit(".", 1)[0] if "." in cleaned else cleaned
    return f"{stem}.{extension.lstrip('.').lower()}"
