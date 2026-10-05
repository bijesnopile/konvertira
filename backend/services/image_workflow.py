"""Shared orchestration for processing and temporarily storing images."""

from backend.models.files import ProcessedFile, StoredFile
from backend.processors.image import remove_image_metadata
from backend.services.storage import TemporaryStorage
from backend.utils.mime import get_extension


def clean_and_store(image_bytes: bytes, storage: TemporaryStorage) -> tuple[ProcessedFile, StoredFile]:
    storage.cleanup()
    processed = remove_image_metadata(image_bytes)
    stored = storage.save(processed.content, get_extension(processed.image_format))
    return processed, stored
