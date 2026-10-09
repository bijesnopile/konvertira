"""Normalize internal failures into small, user-safe processing errors."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from backend.models.files import (
    FileProcessingError,
    ProcessingErrorCode,
    StorageCapacityError,
)


@dataclass(frozen=True, slots=True)
class NormalizedProcessingError:
    code: ProcessingErrorCode
    message: str
    status_code: int


def normalize_processing_error(error: Exception) -> NormalizedProcessingError:
    """Return a safe error contract without paths, stack traces, or tool details."""

    if isinstance(error, FileProcessingError):
        return NormalizedProcessingError(error.code, str(error), error.status_code)
    if isinstance(error, StorageCapacityError):
        return NormalizedProcessingError(error.code, str(error), error.status_code)
    if isinstance(error, (TimeoutError, asyncio.TimeoutError)):
        return NormalizedProcessingError(
            ProcessingErrorCode.PROCESSING_TIMEOUT,
            "Processing did not finish within the allowed time.",
            504,
        )
    return NormalizedProcessingError(
        ProcessingErrorCode.CONVERSION_FAILED,
        "The file could not be processed.",
        500,
    )
