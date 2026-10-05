"""Shared test fixtures."""

import io

import pytest
from PIL import Image


@pytest.fixture
def jpeg_with_metadata() -> bytes:
    image = Image.new("RGB", (8, 8), "#2c5b3b")
    exif = Image.Exif()
    exif[0x010E] = "private description"
    output = io.BytesIO()
    image.save(output, format="JPEG", exif=exif)
    image.close()
    return output.getvalue()


def make_image(image_format: str) -> bytes:
    image = Image.new("RGBA" if image_format in {"PNG", "WEBP"} else "RGB", (4, 3), "red")
    output = io.BytesIO()
    image.save(output, format=image_format)
    image.close()
    return output.getvalue()
