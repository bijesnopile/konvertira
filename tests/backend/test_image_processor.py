import io

import pytest
from PIL import Image

from backend.models.files import FileProcessingError
from backend.processors.image import convert_image, remove_image_metadata
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


def test_conversion_changes_format() -> None:
    result = convert_image(make_image("PNG"), "jpg", quality=85)
    assert result.image_format == "JPEG"
    with Image.open(io.BytesIO(result.content)) as converted:
        assert converted.format == "JPEG"
