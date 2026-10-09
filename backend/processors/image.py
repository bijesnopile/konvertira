"""Pure image transformation functions shared by HTTP and MCP entry points."""

from __future__ import annotations

import io
import warnings
from typing import Any

from PIL import ExifTags, Image, ImageColor, ImageOps, UnidentifiedImageError
from pillow_heif import register_heif_opener

from backend.formats import format_from_processor_name, normalize_format, require_conversion
from backend.models.files import FileProcessingError, ProcessedFile, ProcessingErrorCode
from backend.utils.validation import validate_file_size
from config import settings

register_heif_opener()


def _open_image(image_bytes: bytes, max_image_size: int, max_pixels: int) -> Image.Image:
    validate_file_size(image_bytes, max_image_size)

    source: Image.Image | None = None
    try:
        # Pillow may warn at a library-level threshold. Konvertira applies its
        # own configurable limit before decoding pixel buffers.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            source = Image.open(io.BytesIO(image_bytes))

        detected_format = format_from_processor_name(source.format)
        if detected_format is None or not detected_format.supports_mode("server"):
            raise FileProcessingError(
                "The image format is not supported for server processing.",
                status_code=415,
                code=ProcessingErrorCode.UNSUPPORTED_FORMAT,
            )
        if getattr(source, "is_animated", False) or getattr(source, "n_frames", 1) > 1:
            raise FileProcessingError(
                "Animated images are not supported by this operation.",
                status_code=422,
                code=ProcessingErrorCode.UNSUPPORTED_FEATURE,
            )

        width, height = source.size
        if width <= 0 or height <= 0:
            raise FileProcessingError("The image has invalid dimensions.")
        if width * height > max_pixels:
            raise FileProcessingError(
                f"The image resolution exceeds the {max_pixels:,} pixel limit.",
                status_code=413,
                code=ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE,
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
        raise FileProcessingError(
            "The file is not a valid image.",
            code=ProcessingErrorCode.INVALID_FILE,
        ) from exc
    except (OSError, Image.DecompressionBombError) as exc:
        if source is not None:
            source.close()
        raise FileProcessingError(
            "The image is damaged or cannot be read.",
            code=ProcessingErrorCode.INVALID_FILE,
        ) from exc

    return source


def _pixels_only(source: Image.Image) -> Image.Image:
    """Copy pixel data without carrying source metadata into the output."""

    clean_image = Image.new(source.mode, source.size)
    clean_image.putdata(source.get_flattened_data())
    return clean_image


def calculate_resize_dimensions(
    original_width: int,
    original_height: int,
    *,
    width: int | None = None,
    height: int | None = None,
    scale_percent: float | None = None,
    preserve_aspect_ratio: bool = True,
    allow_upscale: bool = False,
    max_pixels: int | None = None,
) -> tuple[int, int]:
    """Validate resize inputs and calculate bounded output dimensions."""

    if original_width <= 0 or original_height <= 0:
        raise FileProcessingError("The image has invalid dimensions.")
    if scale_percent is not None and (width is not None or height is not None):
        raise FileProcessingError(
            "Use either percentage resize or width/height, not both.",
            422,
        )
    if scale_percent is not None:
        if not 1 <= scale_percent <= 1000:
            raise FileProcessingError("Resize percentage must be between 1 and 1000.", 422)
        ratio = scale_percent / 100
        target_width = max(1, round(original_width * ratio))
        target_height = max(1, round(original_height * ratio))
    elif width is not None or height is not None:
        if width is not None and width <= 0 or height is not None and height <= 0:
            raise FileProcessingError("Resize dimensions must be positive integers.", 422)
        if preserve_aspect_ratio:
            width_ratio = width / original_width if width is not None else float("inf")
            height_ratio = height / original_height if height is not None else float("inf")
            ratio = min(width_ratio, height_ratio)
            target_width = max(1, round(original_width * ratio))
            target_height = max(1, round(original_height * ratio))
        else:
            target_width = width or original_width
            target_height = height or original_height
    else:
        target_width, target_height = original_width, original_height

    if not allow_upscale and (
        target_width > original_width or target_height > original_height
    ):
        target_width, target_height = original_width, original_height
    pixel_limit = max_pixels or settings.max_pixels
    if target_width * target_height > pixel_limit:
        raise FileProcessingError(
            f"The requested output resolution exceeds the {pixel_limit:,} pixel limit.",
            413,
            ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE,
        )
    return target_width, target_height


def _oriented_copy(source: Image.Image) -> Image.Image:
    oriented = ImageOps.exif_transpose(source)
    if oriented is source:
        return source.copy()
    return oriented


def _prepare_for_output(
    source: Image.Image,
    output_format: str,
    background_color: str,
) -> Image.Image:
    if output_format == "JPEG":
        try:
            background_rgb = ImageColor.getrgb(background_color)
        except ValueError as exc:
            raise FileProcessingError("Background color is invalid.", 422) from exc
        rgba = source.convert("RGBA")
        background = Image.new("RGB", rgba.size, background_rgb)
        background.paste(rgba, mask=rgba.getchannel("A"))
        rgba.close()
        return background
    if output_format in {"PNG", "WEBP", "AVIF"}:
        return source.convert("RGBA" if "A" in source.getbands() else "RGB")
    raise FileProcessingError(
        f"Output format {output_format} is not supported.",
        422,
        ProcessingErrorCode.UNSUPPORTED_FORMAT,
    )


def _encode_image(
    image: Image.Image,
    output_format: str,
    *,
    quality: int,
    progressive: bool,
    lossless: bool,
) -> bytes:
    output = io.BytesIO()
    save_options: dict[str, Any] = {}
    if output_format == "JPEG":
        save_options = {"quality": quality, "optimize": True, "progressive": progressive}
    elif output_format == "PNG":
        save_options = {"optimize": True, "compress_level": 9}
    elif output_format == "WEBP":
        save_options = {"quality": quality, "method": 6, "lossless": lossless}
    elif output_format == "AVIF":
        save_options = {"quality": quality, "speed": 6}
    try:
        image.save(output, format=output_format, **save_options)
    except OSError as exc:
        raise FileProcessingError(
            "The converted image could not be generated.",
            500,
            ProcessingErrorCode.CONVERSION_FAILED,
        ) from exc
    return output.getvalue()


def _encode_to_target_size(
    image: Image.Image,
    output_format: str,
    *,
    quality: int,
    target_size_bytes: int | None,
    progressive: bool,
    lossless: bool,
    max_attempts: int,
) -> tuple[bytes, int]:
    if target_size_bytes is None:
        return _encode_image(
            image,
            output_format,
            quality=quality,
            progressive=progressive,
            lossless=lossless,
        ), 1
    if output_format not in {"JPEG", "WEBP", "AVIF"} or lossless:
        raise FileProcessingError(
            "Target size is available only for lossy JPEG, WebP, and AVIF output.",
            422,
            ProcessingErrorCode.UNSUPPORTED_FEATURE,
        )
    if target_size_bytes < 1024:
        raise FileProcessingError("Target size must be at least 1 KB.", 422)

    attempts = 0
    low, high = 1, quality
    best = b""
    while low <= high and attempts < max_attempts:
        candidate_quality = (low + high) // 2
        candidate = _encode_image(
            image,
            output_format,
            quality=candidate_quality,
            progressive=progressive,
            lossless=False,
        )
        attempts += 1
        if not best or len(candidate) < len(best):
            best = candidate
        if len(candidate) <= target_size_bytes:
            best = candidate
            low = candidate_quality + 1
        else:
            high = candidate_quality - 1
    return best, attempts


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
    definition = format_from_processor_name(image_format)
    if definition is None or "server" not in definition.modes_for("removeMetadata"):
        source.close()
        raise FileProcessingError(
            f"Metadata removal is not supported for {image_format or 'this format'}.",
            422,
            ProcessingErrorCode.UNSUPPORTED_FEATURE,
        )

    try:
        clean_image = _pixels_only(source)
    finally:
        source.close()

    output = io.BytesIO()
    output_width, output_height = clean_image.size
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
        raise FileProcessingError(
            "The cleaned image could not be generated.",
            500,
            ProcessingErrorCode.CONVERSION_FAILED,
        ) from exc
    finally:
        clean_image.close()

    result = output.getvalue()
    if not result:
        raise FileProcessingError(
            "The cleaned image could not be generated.",
            500,
            ProcessingErrorCode.CONVERSION_FAILED,
        )
    if len(result) > settings.max_image_output_size:
        raise FileProcessingError("The generated image exceeds the output size limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
    return ProcessedFile(
        content=result,
        image_format=image_format,
        width=output_width,
        height=output_height,
    )


def convert_image(
    image_bytes: bytes,
    output_format: str,
    *,
    quality: int = 90,
    width: int | None = None,
    height: int | None = None,
    scale_percent: float | None = None,
    preserve_aspect_ratio: bool = True,
    allow_upscale: bool = False,
    progressive: bool = True,
    lossless: bool = False,
    target_size_bytes: int | None = None,
    background_color: str = "#ffffff",
    target_size_attempts: int | None = None,
    max_image_size: int | None = None,
    max_pixels: int | None = None,
) -> ProcessedFile:
    """Convert one static image with bounded resize and compression controls."""

    output_definition = normalize_format(output_format)
    if output_definition is None or not output_definition.supports_mode("server"):
        raise FileProcessingError(
            "The requested output format is not supported.",
            422,
            ProcessingErrorCode.UNSUPPORTED_FORMAT,
        )
    normalized_format = output_definition.processor_names[0]
    if not 1 <= quality <= 100:
        raise FileProcessingError("Quality must be between 1 and 100.", 422)
    if lossless and normalized_format != "WEBP":
        raise FileProcessingError(
            "Lossless mode is currently available only for WebP output.",
            422,
            ProcessingErrorCode.UNSUPPORTED_FEATURE,
        )

    source = _open_image(
        image_bytes,
        max_image_size or settings.max_image_size,
        max_pixels or settings.max_pixels,
    )
    source_definition = format_from_processor_name(source.format)
    if source_definition is None:
        source.close()
        raise FileProcessingError(
            "The input format is not supported.",
            415,
            ProcessingErrorCode.UNSUPPORTED_FORMAT,
        )
    require_conversion(source_definition.id, output_definition.id, "server")
    try:
        converted = _oriented_copy(source)
    finally:
        source.close()

    target_width, target_height = calculate_resize_dimensions(
        converted.width,
        converted.height,
        width=width,
        height=height,
        scale_percent=scale_percent,
        preserve_aspect_ratio=preserve_aspect_ratio,
        allow_upscale=allow_upscale,
        max_pixels=max_pixels or settings.max_pixels,
    )
    if (target_width, target_height) != converted.size:
        resized = converted.resize((target_width, target_height), Image.Resampling.LANCZOS)
        converted.close()
        converted = resized

    try:
        output_image = _prepare_for_output(converted, normalized_format, background_color)
    finally:
        converted.close()
    try:
        result, attempts = _encode_to_target_size(
            output_image,
            normalized_format,
            quality=quality,
            target_size_bytes=target_size_bytes,
            progressive=progressive,
            lossless=lossless,
            max_attempts=min(
                settings.image_target_size_attempts,
                target_size_attempts or settings.image_target_size_attempts,
            ),
        )
    finally:
        output_image.close()

    if not result:
        raise FileProcessingError(
            "The converted image could not be generated.",
            500,
            ProcessingErrorCode.CONVERSION_FAILED,
        )
    if len(result) > settings.max_image_output_size:
        raise FileProcessingError("The generated image exceeds the output size limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
    return ProcessedFile(
        content=result,
        image_format=normalized_format,
        width=target_width,
        height=target_height,
        encoding_attempts=attempts,
    )


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
        metadata = {
            ExifTags.TAGS.get(key, str(key)): str(value)
            for key, value in exif.items()
            if key != ExifTags.IFD.GPSInfo
        }
        try:
            gps = exif.get_ifd(ExifTags.IFD.GPSInfo)
        except (KeyError, TypeError, ValueError):
            gps = {}
        metadata.update(
            {
                f"GPS{ExifTags.GPSTAGS.get(key, str(key))}": str(value)
                for key, value in gps.items()
            }
        )
        return {
            "format": (source.format or "").upper(),
            "width": source.width,
            "height": source.height,
            "mode": source.mode,
            "metadata": metadata,
        }
    finally:
        source.close()
