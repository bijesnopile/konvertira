"""Temporary result storage with token-based retrieval and TTL cleanup."""

from __future__ import annotations

import asyncio
import re
import secrets
import threading
import time
from pathlib import Path

from backend.models.files import StorageCapacityError, StorageError, StoredFile
from config import settings

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,128}$")
_SAFE_EXTENSION = re.compile(r"^[a-z0-9]{1,10}$")


class TemporaryStorage:
    def __init__(
        self,
        directory: Path,
        ttl_seconds: int,
        max_bytes: int | None = None,
    ) -> None:
        self.directory = directory
        self.ttl_seconds = ttl_seconds
        self.max_bytes = settings.max_temp_storage_bytes if max_bytes is None else max_bytes
        self._write_lock = threading.Lock()
        self.directory.mkdir(parents=True, exist_ok=True)

    def cleanup(self, *, now: float | None = None) -> int:
        """Delete expired regular files and return the deletion count."""

        deleted = 0
        current_time = time.time() if now is None else now
        with self._write_lock:
            try:
                paths = tuple(self.directory.iterdir())
            except OSError:
                return deleted

            for path in paths:
                if not path.is_file():
                    continue
                try:
                    if current_time - path.stat().st_mtime > self.ttl_seconds:
                        path.unlink(missing_ok=True)
                        deleted += 1
                except OSError:
                    continue
        return deleted

    def save(self, content: bytes, extension: str) -> StoredFile:
        suffix = extension.lstrip(".").lower()
        if not _SAFE_EXTENSION.fullmatch(suffix):
            raise StorageError("Could not save the processed image.")

        with self._write_lock:
            try:
                current_size = sum(
                    path.stat().st_size
                    for path in self.directory.iterdir()
                    if path.is_file()
                )
            except OSError as exc:
                raise StorageError("Could not inspect temporary result storage.") from exc

            if self.max_bytes <= 0 or current_size + len(content) > self.max_bytes:
                raise StorageCapacityError()

            for _ in range(3):
                token = secrets.token_urlsafe(32)
                path = self.directory / f"{token}.{suffix}"
                try:
                    with path.open("xb") as output:
                        output.write(content)
                    path.chmod(0o600)
                    return StoredFile(token=token, path=path)
                except FileExistsError:
                    continue
                except OSError as exc:
                    path.unlink(missing_ok=True)
                    raise StorageError("Could not save the processed image.") from exc

        raise StorageError("Could not allocate a temporary result name.")

    def resolve(self, token: str) -> Path | None:
        if not _SAFE_TOKEN.fullmatch(token):
            return None
        try:
            matches = tuple(self.directory.glob(f"{token}.*"))
        except OSError:
            return None
        return next((path for path in matches if path.is_file()), None)


async def cleanup_periodically(storage: TemporaryStorage) -> None:
    """Remove expired results on a bounded schedule while a service is running."""

    interval = min(max(storage.ttl_seconds / 2, 30), 300)
    while True:
        await asyncio.sleep(interval)
        await asyncio.to_thread(storage.cleanup)


api_storage = TemporaryStorage(
    settings.storage_dir,
    settings.result_ttl_seconds,
    settings.max_temp_storage_bytes,
)
