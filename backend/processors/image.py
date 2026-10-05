"""Pure image transformation functions shared by HTTP and MCP entry points."""

from __future__ import annotations

import io
import warnings
from typing import Any

from PIL import Image, UnidentifiedImageError

from backend.models.files import FileProcessingError, ProcessedFile
from backend.utils.mime import ALLOWED_IMAGE_FORMATS
from backend.utils.validation import validate_file_size
from config import settings


def _open_image(image_bytes: bytes, max_image_size: int, max_pixels: int) -> Image.Image:
    validate_file_size(image_bytes, max_image_size)

    source: Image.Image | None = None
    try:
        # Pillow may warn at a library-level threshold. Konvertira applies its
        # own configurable limit before decoding pixel buffers.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            source = Image.open(io.BytesIO(image_bytes))

        image_format = (source.format or "").upper()
        if image_format not in ALLOWED_IMAGE_FORMATS:
            raise FileProcessingError(
                "Supported formats are JPEG, PNG and WEBP.", status_code=415
            )

        width, height = source.size
        if width <= 0 or height <= 0:
            raise FileProcessingError("The image has invalid dimensions.")
        if width * height > max_pixels:
            raise FileProcessingError(
                f"The image resolution exceeds the {max_pixels:,} pixel limit.",
                status_code=413,
            )

        # Decode only after the inexpensive header-based format and dimension
        # checks, preventing compressed image bombs from allocating first.
        source.load()
    except FileProcessingError:
        if source is not None:
            source.close()
        raise
    except UnidentifiedImageError as exc:
        if source is not None:
            source.close()
        raise FileProcessingError("The file is not a valid image.") from exc
    except (OSError, Image.DecompressionBombError) as exc:
        if source is not None:
            source.close()
        raise FileProcessingError("The image is damaged or cannot be read.") from exc

    return source


def _pixels_only(source: Image.Image) -> Image.Image:
    """Copy pixel data without carrying source metadata into the output."""

    clean_image = Image.new(source.mode, source.size)
    clean_image.putdata(source.get_flattened_data())
    return clean_image


def remove_image_metadata(
    image_bytes: bytes,
    *,
    max_image_size: int | None = None,
    max_pixels: int | None = None,
) -> ProcessedFile:
    """Re-encode a supported image using only its pixel data."""

    source = _open_image(
        image_bytes,
        max_image_size or settings.max_image_size,
        max_pixels or settings.max_pixels,
    )
    image_format = (source.format or "").upper()

    try:
        clean_image = _pixels_only(source)
    finally:
        source.close()

    output = io.BytesIO()
    try:
        if image_format == "JPEG":
            if clean_image.mode not in ("RGB", "L"):
                clean_image = clean_image.convert("RGB")
            clean_image.save(
                output,
                format="JPEG",
                quality=100,
                subsampling=0,
                optimize=True,
                progressive=True,
            )
        elif image_format == "PNG":
            clean_image.save(output, format="PNG", optimize=True)
        elif image_format == "WEBP":
            if clean_image.mode not in ("RGB", "RGBA"):
                clean_image = clean_image.convert("RGBA")
            clean_image.save(output, format="WEBP", quality=100, method=6)
    except OSError as exc:
        raise FileProcessingError("The cleaned image could not be generated.", 500) from exc
    finally:
        clean_image.close()

    result = output.getvalue()
    if not result:
        raise FileProcessingError("The cleaned image could not be generated.", 500)
    return ProcessedFile(content=result, image_format=image_format)


def convert_image(
    image_bytes: bytes,
    output_format: str,
    *,
    quality: int = 90,
    max_image_size: int | None = None,
    max_pixels: int | None = None,
) -> ProcessedFile:
    """Convert a supported image to JPEG, PNG, or WEBP without source metadata."""

    normalized_format = "JPEG" if output_format.upper() in {"JPG", "JPEG"} else output_format.upper()
    if normalized_format not in ALLOWED_IMAGE_FORMATS:
        raise FileProcessingError("Output format must be JPG, PNG or WEBP.", 422)
    if not 1 <= quality <= 100:
        raise FileProcessingError("Quality must be between 1 and 100.", 422)

    source = _open_image(
        image_bytes,
        max_image_size or settings.max_image_size,
        max_pixels or settings.max_pixels,
    )
    try:
        converted = _pixels_only(source)
    finally:
        source.close()

    output = io.BytesIO()
    try:
        if normalized_format == "JPEG":
            if converted.mode not in ("RGB", "L"):
                background = Image.new("RGB", converted.size, "white")
                if "A" in converted.getbands():
                    background.paste(converted, mask=converted.getchannel("A"))
                    converted.close()
                    converted = background
                else:
                    converted = converted.convert("RGB")
            converted.save(output, format="JPEG", quality=quality, optimize=True)
        elif normalized_format == "PNG":
            converted.save(output, format="PNG", optimize=True)
        else:
            converted.save(output, format="WEBP", quality=quality, method=6)
    except OSError as exc:
        raise FileProcessingError("The converted image could not be generated.", 500) from exc
    finally:
        converted.close()

    result = output.getvalue()
    if not result:
        raise FileProcessingError("The converted image could not be generated.", 500)
    return ProcessedFile(content=result, image_format=normalized_format)


def inspect_image_metadata(
    image_bytes: bytes,
    *,
    max_image_size: int | None = None,
    max_pixels: int | None = None,
) -> dict[str, Any]:
    """Return basic format details and metadata without modifying the image."""

    source = _open_image(
        image_bytes,
        max_image_size or settings.max_image_size,
        max_pixels or settings.max_pixels,
    )
    try:
        exif = source.getexif()
        return {
            "format": (source.format or "").upper(),
            "width": source.width,
            "height": source.height,
            "mode": source.mode,
            "metadata": {str(key): str(value) for key, value in exif.items()},
        }
    finally:
        source.close()
