"""Canonical file-format registry shared by HTTP, processors, MCP, and the UI.

``format_registry.json`` is the source of truth. This module validates it at
import time and exposes typed, immutable lookup helpers to Python callers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping

from backend.models.files import FileProcessingError, ProcessingErrorCode

ExecutionMode = Literal["local", "server"]
Lossiness = Literal["lossless", "typically_lossy", "context_dependent"]


class FormatCategory(StrEnum):
    IMAGE = "image"
    PDF = "pdf"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    TEXT = "text"


@dataclass(frozen=True, slots=True)
class FormatCapabilities:
    inspect_metadata: bool
    remove_metadata: bool
    merge: bool
    split: bool
    quality: bool
    compression: bool
    resize: bool
    multi_file: bool


@dataclass(frozen=True, slots=True)
class FormatDefinition:
    id: str
    label: str
    category: FormatCategory
    extensions: tuple[str, ...]
    mime_types: tuple[str, ...]
    preferred_extension: str
    preferred_mime_type: str
    processor_names: tuple[str, ...]
    implemented: bool
    execution_modes: frozenset[ExecutionMode]
    operation_modes: Mapping[str, frozenset[ExecutionMode]]
    capabilities: FormatCapabilities
    lossiness: Lossiness
    constraints: tuple[str, ...]

    def supports_mode(self, mode: ExecutionMode) -> bool:
        return self.implemented and mode in self.execution_modes

    def modes_for(self, operation: str) -> frozenset[ExecutionMode]:
        return self.operation_modes.get(operation, frozenset())


@dataclass(frozen=True, slots=True)
class ConversionCapability:
    source: str
    target: str
    execution_modes: frozenset[ExecutionMode]
    lossiness: Lossiness
    constraints: tuple[str, ...]

    def supports_mode(self, mode: ExecutionMode) -> bool:
        return mode in self.execution_modes


@dataclass(frozen=True, slots=True)
class DeclaredFormat:
    """Untrusted format hints derived from a filename and/or declared MIME."""

    filename_format: FormatDefinition | None
    mime_format: FormatDefinition | None

    @property
    def is_consistent(self) -> bool:
        return (
            self.filename_format is None
            or self.mime_format is None
            or self.filename_format.id == self.mime_format.id
        )

    @property
    def candidate(self) -> FormatDefinition | None:
        if not self.is_consistent:
            return None
        return self.filename_format or self.mime_format


@dataclass(frozen=True, slots=True)
class FormatRegistry:
    formats: Mapping[str, FormatDefinition]
    conversions: Mapping[tuple[str, str], ConversionCapability]
    by_extension: Mapping[str, FormatDefinition]
    by_mime: Mapping[str, FormatDefinition]
    by_processor_name: Mapping[str, FormatDefinition]


_REGISTRY_PATH = Path(__file__).resolve().parents[1] / "format_registry.json"


def _capabilities(raw: Mapping[str, Any]) -> FormatCapabilities:
    return FormatCapabilities(
        inspect_metadata=bool(raw["inspectMetadata"]),
        remove_metadata=bool(raw["removeMetadata"]),
        merge=bool(raw["merge"]),
        split=bool(raw["split"]),
        quality=bool(raw["quality"]),
        compression=bool(raw["compression"]),
        resize=bool(raw["resize"]),
        multi_file=bool(raw["multiFile"]),
    )
def _normalized_extension(value: str) -> str:
    extension = value.strip().lower()
    if not extension:
        return extension
    return extension if extension.startswith(".") else f".{extension}"


@lru_cache(maxsize=1)
def get_format_registry() -> FormatRegistry:
    raw = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    if raw.get("schemaVersion") != 1:
        raise RuntimeError("Unsupported format registry schema version")

    formats: dict[str, FormatDefinition] = {}
    by_extension: dict[str, FormatDefinition] = {}
    by_mime: dict[str, FormatDefinition] = {}
    by_processor_name: dict[str, FormatDefinition] = {}

    for item in raw["formats"]:
        definition = FormatDefinition(
            id=item["id"].strip().lower(),
            label=item["label"],
            category=FormatCategory(item["category"]),
            extensions=tuple(_normalized_extension(value) for value in item["extensions"]),
            mime_types=tuple(value.strip().lower() for value in item["mimeTypes"]),
            preferred_extension=_normalized_extension(item["preferredExtension"]),
            preferred_mime_type=item["preferredMimeType"].strip().lower(),
            processor_names=tuple(value.strip().upper() for value in item["processorNames"]),
            implemented=bool(item["implemented"]),
            execution_modes=frozenset(item["executionModes"]),
            operation_modes=MappingProxyType(
                {
                    operation: frozenset(modes)
                    for operation, modes in item.get("operationModes", {}).items()
                }
            ),
            capabilities=_capabilities(item["capabilities"]),
            lossiness=item["lossiness"],
            constraints=tuple(item.get("constraints", ())),
        )
        if definition.id in formats:
            raise RuntimeError(f"Duplicate format id in registry: {definition.id}")
        if definition.preferred_extension not in definition.extensions:
            raise RuntimeError(f"Invalid preferred extension for {definition.id}")
        if definition.preferred_mime_type not in definition.mime_types:
            raise RuntimeError(f"Invalid preferred MIME type for {definition.id}")
        if not definition.implemented and definition.execution_modes:
            raise RuntimeError(f"Unavailable format has execution modes: {definition.id}")
        if any(
            mode not in definition.execution_modes
            for modes in definition.operation_modes.values()
            for mode in modes
        ):
            raise RuntimeError(f"Operation mode exceeds format modes: {definition.id}")
        formats[definition.id] = definition
        for extension in definition.extensions:
            if extension in by_extension:
                raise RuntimeError(f"Duplicate format extension: {extension}")
            by_extension[extension] = definition
        for mime_type in definition.mime_types:
            if mime_type in by_mime:
                raise RuntimeError(f"Duplicate format MIME type: {mime_type}")
            by_mime[mime_type] = definition
        for processor_name in definition.processor_names:
            if processor_name in by_processor_name:
                raise RuntimeError(f"Duplicate processor format name: {processor_name}")
            by_processor_name[processor_name] = definition

    conversions: dict[tuple[str, str], ConversionCapability] = {}
    for item in raw["conversions"]:
        source = item["source"].strip().lower()
        target = item["target"].strip().lower()
        if source not in formats or target not in formats:
            raise RuntimeError(f"Conversion references unknown format: {source} -> {target}")
        capability = ConversionCapability(
            source=source,
            target=target,
            execution_modes=frozenset(item["executionModes"]),
            lossiness=item["lossiness"],
            constraints=tuple(item.get("constraints", ())),
        )
        key = (source, target)
        if key in conversions:
            raise RuntimeError(f"Duplicate conversion edge: {source} -> {target}")
        if not formats[source].implemented or not formats[target].implemented:
            raise RuntimeError(f"Conversion references unavailable format: {source} -> {target}")
        if not capability.execution_modes.issubset(formats[source].modes_for("convert")):
            raise RuntimeError(f"Conversion mode is unavailable for source: {source} -> {target}")
        conversions[key] = capability

    return FormatRegistry(
        formats=MappingProxyType(formats),
        conversions=MappingProxyType(conversions),
        by_extension=MappingProxyType(by_extension),
        by_mime=MappingProxyType(by_mime),
        by_processor_name=MappingProxyType(by_processor_name),
    )


def format_from_id(value: str | None) -> FormatDefinition | None:
    if not value:
        return None
    return get_format_registry().formats.get(value.strip().lower())


def format_from_extension(value: str | None) -> FormatDefinition | None:
    if not value:
        return None
    return get_format_registry().by_extension.get(_normalized_extension(value))


def format_from_filename(filename: str | None) -> FormatDefinition | None:
    if not filename:
        return None
    basename = filename.strip().replace("\\", "/").rsplit("/", 1)[-1]
    suffix = Path(basename).suffix
    return format_from_extension(suffix)


def format_from_mime(mime_type: str | None) -> FormatDefinition | None:
    if not mime_type:
        return None
    normalized = mime_type.partition(";")[0].strip().lower()
    return get_format_registry().by_mime.get(normalized)


def format_from_processor_name(name: str | None) -> FormatDefinition | None:
    if not name:
        return None
    return get_format_registry().by_processor_name.get(name.strip().upper())


def normalize_format(value: str | None) -> FormatDefinition | None:
    """Resolve a canonical id, extension, MIME type, or processor name."""

    if not value:
        return None
    return (
        format_from_id(value)
        or format_from_extension(value)
        or format_from_mime(value)
        or format_from_processor_name(value)
    )


def declared_format(filename: str | None, mime_type: str | None) -> DeclaredFormat:
    """Return untrusted declared hints; callers must still verify file contents."""

    return DeclaredFormat(
        filename_format=format_from_filename(filename),
        mime_format=format_from_mime(mime_type),
    )


def conversion_capability(
    source: str,
    target: str,
    mode: ExecutionMode | None = None,
) -> ConversionCapability | None:
    source_format = normalize_format(source)
    target_format = normalize_format(target)
    if source_format is None or target_format is None:
        return None
    capability = get_format_registry().conversions.get((source_format.id, target_format.id))
    if capability is None or (mode is not None and not capability.supports_mode(mode)):
        return None
    return capability


def require_conversion(
    source: str,
    target: str,
    mode: ExecutionMode,
) -> ConversionCapability:
    capability = conversion_capability(source, target, mode)
    if capability is None:
        raise FileProcessingError(
            f"Conversion from {source.upper()} to {target.upper()} is not supported.",
            status_code=422,
            code=ProcessingErrorCode.UNSUPPORTED_CONVERSION,
        )
    return capability


def implemented_formats(
    *, category: FormatCategory | None = None, mode: ExecutionMode | None = None
) -> tuple[FormatDefinition, ...]:
    return tuple(
        definition
        for definition in get_format_registry().formats.values()
        if definition.implemented
        and (category is None or definition.category == category)
        and (mode is None or definition.supports_mode(mode))
    )
