import os

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
