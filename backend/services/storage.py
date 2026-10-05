"""Temporary result storage with token-based retrieval and TTL cleanup."""

from __future__ import annotations

import re
import secrets
import time
from pathlib import Path

from backend.models.files import StorageError, StoredFile
from config import settings

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,128}$")


class TemporaryStorage:
    def __init__(self, directory: Path, ttl_seconds: int) -> None:
        self.directory = directory
        self.ttl_seconds = ttl_seconds
        self.directory.mkdir(parents=True, exist_ok=True)

    def cleanup(self, *, now: float | None = None) -> int:
        """Delete expired regular files and return the deletion count."""

        deleted = 0
        current_time = time.time() if now is None else now
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
        token = secrets.token_urlsafe(32)
        normalized_extension = f".{extension.lstrip('.').lower()}"
        path = self.directory / f"{token}{normalized_extension}"
        try:
            path.write_bytes(content)
        except OSError as exc:
            raise StorageError(f"Could not save processed image: {exc}") from exc
        return StoredFile(token=token, path=path)

    def resolve(self, token: str) -> Path | None:
        if not _SAFE_TOKEN.fullmatch(token):
            return None
        try:
            matches = tuple(self.directory.glob(f"{token}.*"))
        except OSError:
            return None
        return next((path for path in matches if path.is_file()), None)


api_storage = TemporaryStorage(settings.storage_dir, settings.result_ttl_seconds)
