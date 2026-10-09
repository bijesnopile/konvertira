import io

import pytest
from PIL import Image
from PIL.PngImagePlugin import PngImageFile

from backend.models.files import FileProcessingError
from backend.processors.image import (
    calculate_resize_dimensions,
    convert_image,
    remove_image_metadata,
)
from tests.conftest import make_image


def test_remove_image_metadata_removes_exif(jpeg_with_metadata: bytes) -> None:
    result = remove_image_metadata(jpeg_with_metadata)

    with Image.open(io.BytesIO(result.content)) as cleaned:
        assert result.image_format == "JPEG"
        assert len(cleaned.getexif()) == 0


@pytest.mark.parametrize("image_format", ["JPEG", "PNG", "WEBP"])
def test_supported_image_formats(image_format: str) -> None:
    result = remove_image_metadata(make_image(image_format))
    assert result.image_format == image_format
    assert result.content


def test_unsupported_image_format() -> None:
    with pytest.raises(FileProcessingError) as error:
        remove_image_metadata(make_image("BMP"))
    assert error.value.status_code == 415


def test_max_file_size_validation() -> None:
    with pytest.raises(FileProcessingError) as error:
        remove_image_metadata(b"too large", max_image_size=4)
    assert error.value.status_code == 413


def test_max_resolution_validation() -> None:
    with pytest.raises(FileProcessingError) as error:
        remove_image_metadata(make_image("PNG"), max_pixels=5)
    assert error.value.status_code == 413


def test_max_resolution_is_checked_before_pixel_decode(monkeypatch) -> None:
    def fail_if_loaded(_: PngImageFile):
        pytest.fail("pixel data was decoded before the dimension limit")

    monkeypatch.setattr(PngImageFile, "load", fail_if_loaded)
    with pytest.raises(FileProcessingError) as error:
        remove_image_metadata(make_image("PNG"), max_pixels=5)
    assert error.value.status_code == 413


def test_conversion_changes_format() -> None:
    result = convert_image(make_image("PNG"), "jpg", quality=85)
    assert result.image_format == "JPEG"
    with Image.open(io.BytesIO(result.content)) as converted:
        assert converted.format == "JPEG"


def test_resize_preserves_aspect_ratio_and_does_not_upscale() -> None:
    assert calculate_resize_dimensions(1200, 800, width=600) == (600, 400)
    assert calculate_resize_dimensions(1200, 800, height=200) == (300, 200)
    assert calculate_resize_dimensions(1200, 800, width=2400) == (1200, 800)
    assert calculate_resize_dimensions(
        1200, 800, width=2400, allow_upscale=True
    ) == (2400, 1600)


def test_resize_and_transparency_to_jpeg_use_selected_background() -> None:
    image = Image.new("RGBA", (8, 4), (255, 0, 0, 0))
    source = io.BytesIO()
    image.save(source, format="PNG")
    result = convert_image(
        source.getvalue(),
        "jpeg",
        width=4,
        background_color="#ffffff",
    )
    assert (result.width, result.height) == (4, 2)
    with Image.open(io.BytesIO(result.content)) as converted:
        red, green, blue = converted.convert("RGB").getpixel((0, 0))
        assert red > 240 and green > 240 and blue > 240


def test_avif_and_static_gif_conversion_paths() -> None:
    avif = convert_image(make_image("PNG"), "avif", quality=70)
    with Image.open(io.BytesIO(avif.content)) as converted:
        assert converted.format == "AVIF"

    gif = Image.new("P", (4, 3))
    gif_bytes = io.BytesIO()
    gif.save(gif_bytes, format="GIF")
    png = convert_image(gif_bytes.getvalue(), "png")
    with Image.open(io.BytesIO(png.content)) as converted:
        assert converted.format == "PNG"

    heif_image = Image.new("RGB", (4, 3), "green")
    heif_bytes = io.BytesIO()
    heif_image.save(heif_bytes, format="HEIF")
    jpeg = convert_image(heif_bytes.getvalue(), "jpeg")
    with Image.open(io.BytesIO(jpeg.content)) as converted:
        assert converted.format == "JPEG"


def test_animated_gif_is_rejected_instead_of_flattened() -> None:
    first = Image.new("RGB", (3, 3), "red")
    second = Image.new("RGB", (3, 3), "blue")
    content = io.BytesIO()
    first.save(content, format="GIF", save_all=True, append_images=[second], duration=100)
    with pytest.raises(FileProcessingError, match="Animated images") as error:
        convert_image(content.getvalue(), "png")
    assert error.value.code.value == "unsupported_feature"


def test_target_size_search_is_bounded() -> None:
    result = convert_image(
        make_image("PNG"),
        "jpeg",
        target_size_bytes=1024,
        target_size_attempts=3,
    )
    assert 1 <= result.encoding_attempts <= 3


def test_target_size_rejects_lossless_output() -> None:
    with pytest.raises(FileProcessingError, match="Target size"):
        convert_image(make_image("PNG"), "png", target_size_bytes=1024)
