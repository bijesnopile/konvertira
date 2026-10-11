"""Temporary result storage with token-based retrieval and TTL cleanup."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import secrets
import stat
import threading
import time
from pathlib import Path

from backend.models.files import StorageCapacityError, StorageError, StoredFile
from config import settings

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,128}$")
_SAFE_EXTENSION = re.compile(r"^[a-z0-9]{1,10}$")
logger = logging.getLogger("konvertira.storage")


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
        self.directory = self.directory.absolute()
        self._directory_identity = self._identity(self.directory.lstat())[:2]
        self._last_now = time.time()
        self._last_monotonic = time.monotonic()
        self._last_diagnostic = {}
        self._clock_lock = threading.Lock()

    def _diagnostic(self, reason):
        now = time.monotonic()
        if now - self._last_diagnostic.get(reason, float("-inf")) >= 10:
            self._last_diagnostic[reason] = now
            logger.warning("storage_operation_failed reason=%s", reason)

    @staticmethod
    def _identity(info):
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)

    def _now(self):
        # A backwards wall-clock adjustment cannot extend access in this process.
        with self._clock_lock:
            monotonic = time.monotonic()
            self._last_now = max(self._last_now + max(0, monotonic - self._last_monotonic), time.time())
            self._last_monotonic = monotonic
            return self._last_now

    def _safe_directory(self):
        info = self.directory.lstat()
        if (not stat.S_ISDIR(info.st_mode) or self.directory.is_symlink()
                or getattr(info, "st_file_attributes", 0) & 0x400
                or self._identity(info)[:2] != self._directory_identity
                or self.directory.resolve() != self.directory):
            raise OSError("Unsafe storage directory")

    def _open(self, name):
        """Open a single regular entry, pinning the directory on POSIX."""
        self._safe_directory()
        path = self.directory / name
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or getattr(before, "st_file_attributes", 0) & 0x400:
            raise OSError("Unsafe storage entry")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
        directory_fd = None
        descriptor = None
        try:
            if os.open in os.supports_dir_fd:
                directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                if self._identity(os.fstat(directory_fd))[:2] != self._directory_identity:
                    raise OSError("Changed storage directory")
                descriptor = os.open(name, flags, dir_fd=directory_fd)
            else:
                descriptor = os.open(path, flags)
            opened = os.fstat(descriptor)
            self._safe_directory()
            if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                    or self._identity(before) != self._identity(opened)
                    or self._identity(path.lstat()) != self._identity(opened)):
                raise OSError("Changed storage entry")
            result = os.fdopen(descriptor, "rb")
            descriptor = None
            return result
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if directory_fd is not None:
                os.close(directory_fd)

    def _remove(self, path):
        directory_fd = None
        try:
            self._safe_directory()
            # Never follow an entry or delete outside the configured directory.
            if path.parent == self.directory and stat.S_ISREG(path.lstat().st_mode):
                if os.unlink in os.supports_dir_fd:
                    directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                    if self._identity(os.fstat(directory_fd))[:2] != self._directory_identity:
                        raise OSError("Changed storage directory")
                    try:
                        os.unlink(path.name, dir_fd=directory_fd)
                    except FileNotFoundError:
                        return False
                else:
                    path.unlink(missing_ok=True)
                return True
        except FileNotFoundError:
            return False
        except OSError:
            self._diagnostic("cleanup-filesystem")
        finally:
            if directory_fd is not None:
                os.close(directory_fd)
        return False

    def _create(self, name):
        self._safe_directory()
        directory_fd = None
        descriptor = None
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
            if os.open in os.supports_dir_fd:
                directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                if self._identity(os.fstat(directory_fd))[:2] != self._directory_identity:
                    raise OSError("Changed storage directory")
                descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
            else:
                descriptor = os.open(self.directory / name, flags, 0o600)
            self._safe_directory()
            result = descriptor
            descriptor = None
            return result
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if directory_fd is not None:
                os.close(directory_fd)

    def cleanup(self, *, now: float | None = None) -> int:
        """Delete expired regular files and return the deletion count."""

        deleted = 0
        current_time = self._now() if now is None else now
        with self._write_lock:
            try:
                self._safe_directory()
                paths = tuple(self.directory.iterdir())
            except OSError:
                self._diagnostic("cleanup-directory")
                return deleted

            for path in paths:
                info = None
                try:
                    info = path.lstat()
                    if not stat.S_ISREG(info.st_mode):
                        continue
                    metadata_match = re.fullmatch(r"\.([A-Za-z0-9_-]{20,128})\.json", path.name)
                    if not metadata_match and not re.fullmatch(r"[A-Za-z0-9_-]{20,128}\.[a-z0-9]{1,10}", path.name):
                        continue
                    if metadata_match:
                        with self._open(path.name) as metadata:
                            if os.fstat(metadata.fileno()).st_size > 1024:
                                raise ValueError("Oversized record")
                            record = json.loads(metadata.read(1025))
                        token = metadata_match[1]
                        name = record["name"]
                        if (re.fullmatch(re.escape(token) + r"\.[a-z0-9]{1,10}", name)
                                and all(type(record[k]) in (int, float) and math.isfinite(record[k]) for k in ("expires", "created"))
                                and current_time >= min(record["expires"], record["created"] + self.ttl_seconds)):
                            deleted += int(self._remove(self.directory / name))
                            deleted += int(self._remove(path))
                            continue
                    # Hidden metadata is also bounded by the store TTL. Deleting
                    # it denies access even when deleting the result fails.
                    if info is not None and current_time - info.st_mtime >= self.ttl_seconds:
                        deleted += int(self._remove(path))
                except (OSError, ValueError, KeyError, TypeError):
                    self._diagnostic("cleanup-entry")
                    # Malformed metadata has no serving authority; still recover
                    # old orphan storage without following symlinks.
                    if info is not None and current_time - info.st_mtime >= self.ttl_seconds:
                        deleted += int(self._remove(path))
                    continue
        return deleted

    def save(self, content: bytes, extension: str) -> StoredFile:
        suffix = extension.lstrip(".").lower()
        if not _SAFE_EXTENSION.fullmatch(suffix):
            raise StorageError("Could not save the processed image.")

        with self._write_lock:
            try:
                self._safe_directory()
                current_size = sum(
                    path.lstat().st_size
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
                metadata = self.directory / f".{token}.json"
                if metadata.exists() or metadata.is_symlink():
                    continue
                output_created = False
                metadata_created = False
                try:
                    descriptor = self._create(path.name)
                    output_created = True
                    with os.fdopen(descriptor, "wb") as output:
                        output.write(content)
                    created = self._now()
                    record = {"name": path.name, "created": created,
                              "expires": created + self.ttl_seconds,
                              "identity": self._identity(path.lstat())}
                    payload = json.dumps(record).encode("ascii")
                    if current_size + len(content) + len(payload) > self.max_bytes:
                        self._remove(path)
                        raise StorageCapacityError()
                    descriptor = self._create(metadata.name)
                    metadata_created = True
                    with os.fdopen(descriptor, "wb") as output:
                        output.write(payload)
                    return StoredFile(token=token, path=path)
                except FileExistsError:
                    if output_created:
                        self._remove(path)
                    continue
                except OSError as exc:
                    if output_created:
                        self._remove(path)
                    if metadata_created:
                        self._remove(metadata)
                    raise StorageError("Could not save the processed image.") from exc

        raise StorageError("Could not allocate a temporary result name.")

    def resolve(self, token: str) -> Path | None:
        opened = self.open_result(token)
        if opened is None:
            return None
        file, path = opened
        file.close()
        return path

    def open_result(self, token: str):
        """Fail closed; return a validated descriptor, never a deferred path open.

        Legacy entries without expiry metadata are intentionally unavailable.
        Download callers must use this method again at the actual response boundary.
        """
        if not _SAFE_TOKEN.fullmatch(token):
            return None
        file = None
        try:
            with self._write_lock:
                with self._open(f".{token}.json") as metadata:
                    if os.fstat(metadata.fileno()).st_size > 1024:
                        return None
                    record = json.loads(metadata.read(1025))
                name = record["name"]
                if not re.fullmatch(re.escape(token) + r"\.[a-z0-9]{1,10}", name):
                    return None
                created, expires = record["created"], record["expires"]
                if not all(type(value) in (int, float) and math.isfinite(value) for value in (created, expires)) or expires < created:
                    return None
                now = self._now()
                if now < created or now >= min(expires, created + self.ttl_seconds):
                    self._remove(self.directory / f".{token}.json")
                    self._remove(self.directory / name)
                    return None
                file = self._open(name)
                if list(self._identity(os.fstat(file.fileno()))) != record["identity"]:
                    file.close()
                    return None
                # Opening/stat may take time. Recheck before permitting delivery.
                if self._now() >= min(expires, created + self.ttl_seconds):
                    file.close()
                    return None
                file.expires_at = min(expires, created + self.ttl_seconds)
                return file, self.directory / name
        except FileNotFoundError:
            if file is not None:
                file.close()
            return None
        except (OSError, ValueError, KeyError, TypeError):
            if file is not None:
                file.close()
            self._diagnostic("resolution")
            return None


async def cleanup_periodically(storage: TemporaryStorage) -> None:
    """Remove expired results on a bounded schedule while a service is running."""

    interval = min(max(storage.ttl_seconds / 2, 30), 300)
    while True:
        await asyncio.sleep(interval)
        try:
            await asyncio.to_thread(storage.cleanup)
        except OSError:
            storage._diagnostic("cleanup-worker")


api_storage = TemporaryStorage(
    settings.storage_dir,
    settings.result_ttl_seconds,
    settings.max_temp_storage_bytes,
)
