"""Internal file-processing models and exceptions."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ProcessedFile:
    content: bytes
    image_format: str
    width: int | None = None
    height: int | None = None
    encoding_attempts: int = 1


@dataclass(frozen=True, slots=True)
class StoredFile:
    token: str
    path: Path


class ProcessingErrorCode(StrEnum):
    UNSUPPORTED_FORMAT = "unsupported_format"
    UNSUPPORTED_CONVERSION = "unsupported_conversion"
    INVALID_FILE = "invalid_file"
    FILE_TOO_LARGE = "file_too_large"
    DECODED_CONTENT_TOO_LARGE = "decoded_content_too_large"
    PROCESSING_TIMEOUT = "processing_timeout"
    TEMPORARY_CAPACITY_UNAVAILABLE = "temporary_capacity_unavailable"
    CONVERSION_FAILED = "conversion_failed"
    UNSUPPORTED_FEATURE = "unsupported_feature"


class FileProcessingError(ValueError):
    """Expected validation or image-processing failure."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: ProcessingErrorCode = ProcessingErrorCode.INVALID_FILE,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


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
        self.code = ProcessingErrorCode.TEMPORARY_CAPACITY_UNAVAILABLE
