"""Internal file-processing models and exceptions."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProcessedFile:
    content: bytes
    image_format: str


@dataclass(frozen=True, slots=True)
class StoredFile:
    token: str
    path: Path


class FileProcessingError(ValueError):
    """Expected validation or image-processing failure."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class StorageError(RuntimeError):
    """Temporary result storage could not complete an operation."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.status_code = status_code


class StorageCapacityError(StorageError):
    """Temporary storage is full enough that new results must be rejected."""

    def __init__(self) -> None:
        super().__init__(
            "Temporary result storage is currently full. Please try again later.",
            status_code=503,
        )
