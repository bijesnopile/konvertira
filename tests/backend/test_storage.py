import os
import stat

import pytest

from backend.models.files import StorageCapacityError, StorageError
from backend.services.storage import TemporaryStorage


def test_storage_cleanup_removes_only_expired_files(tmp_path) -> None:
    storage = TemporaryStorage(tmp_path, ttl_seconds=60)
    expired = storage.save(b"old", ".jpg")
    current = storage.save(b"new", ".png")
    os.utime(expired.path, (100, 100))
    os.utime(current.path, (190, 190))

    assert storage.cleanup(now=200) == 1
    assert not expired.path.exists()
    assert current.path.exists()


def test_storage_rejects_unsafe_token(tmp_path) -> None:
    storage = TemporaryStorage(tmp_path, ttl_seconds=60)
    assert storage.resolve("../../private") is None


def test_storage_enforces_total_capacity(tmp_path) -> None:
    storage = TemporaryStorage(tmp_path, ttl_seconds=60, max_bytes=5)
    storage.save(b"123", ".jpg")
    with pytest.raises(StorageCapacityError):
        storage.save(b"456", ".png")


def test_storage_rejects_unsafe_extension(tmp_path) -> None:
    storage = TemporaryStorage(tmp_path, ttl_seconds=60)
    with pytest.raises(StorageError):
        storage.save(b"image", "../../html")


@pytest.mark.skipif(os.name == "nt", reason="Windows does not expose POSIX mode bits")
def test_storage_uses_private_file_permissions(tmp_path) -> None:
    storage = TemporaryStorage(tmp_path, ttl_seconds=60)
    stored = storage.save(b"image", ".jpg")
    assert stat.S_IMODE(stored.path.stat().st_mode) & 0o077 == 0
