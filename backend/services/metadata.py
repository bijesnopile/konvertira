"""Normalized metadata inspection/removal dispatch for supported file families."""

from __future__ import annotations

import io
import zipfile
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath

from defusedxml import ElementTree
from PIL import ExifTags

from backend.formats import normalize_format
from backend.models.files import FileProcessingError, ProcessingErrorCode
from backend.processors.image import inspect_image_metadata, remove_image_metadata
from backend.processors.pdf import inspect_pdf_metadata, remove_pdf_metadata
from config import settings

OOXML_FORMATS = {"docx", "xlsx", "pptx"}
ODF_FORMATS = {"odt", "ods", "odp"}
OOXML_REQUIRED_PARTS = {
    "docx": "word/document.xml",
    "xlsx": "xl/workbook.xml",
    "pptx": "ppt/presentation.xml",
}
ODF_MIME_TYPES = {
    "odt": "application/vnd.oasis.opendocument.text",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "odp": "application/vnd.oasis.opendocument.presentation",
}


@dataclass(frozen=True, slots=True)
class MetadataField:
    category: str
    key: str
    label: str
    value: str
    source: str
    sensitive: bool
    removable: bool


@dataclass(frozen=True, slots=True)
class MetadataInspectionResult:
    format_id: str
    fields: tuple[MetadataField, ...]
    warning: str

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format_id,
            "fields": [asdict(field) for field in self.fields],
            "warning": self.warning,
        }


@dataclass(frozen=True, slots=True)
class MetadataRemovalResult:
    content: bytes
    format_id: str
    extension: str
    content_type: str
    removed_fields: int
    warning: str


def _category(key: str) -> tuple[str, bool]:
    lowered = key.lower()
    if any(word in lowered for word in ("gps", "latitude", "longitude", "location")):
        return "Location/GPS", True
    if any(word in lowered for word in ("author", "creator", "lastmodifiedby", "company", "manager", "owner")):
        return "Author/identity", True
    if any(word in lowered for word in ("date", "time", "created", "modified")):
        return "Dates/timestamps", True
    if any(word in lowered for word in ("camera", "model", "make", "lens", "device")):
        return "Camera/device", True
    if any(word in lowered for word in ("producer", "application", "software", "version")):
        return "Software/application", True
    if any(word in lowered for word in ("title", "subject", "keyword", "description", "copyright")):
        return "Document properties", False
    return "Other", False


def _field(key: str, value: object, source: str, *, removable: bool = True) -> MetadataField:
    category, sensitive = _category(key)
    safe_value = str(value).replace("\x00", "�")[:10000]
    label = key.rsplit("}", 1)[-1].replace("_", " ").strip() or "Unknown"
    return MetadataField(category, key, label, safe_value, source, sensitive, removable)


def _validate_archive(content: bytes) -> zipfile.ZipFile:
    if len(content) > settings.max_document_size:
        raise FileProcessingError("The document exceeds the size limit.", 413, ProcessingErrorCode.FILE_TOO_LARGE)
    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
        infos = archive.infolist()
    except (zipfile.BadZipFile, OSError) as exc:
        raise FileProcessingError("The document package is corrupt or unsupported.") from exc
    if len(infos) > settings.max_archive_entries:
        archive.close()
        raise FileProcessingError("The document package contains too many entries.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
    total = 0
    for info in infos:
        path = PurePosixPath(info.filename.replace("\\", "/"))
        if path.is_absolute() or ".." in path.parts or info.flag_bits & 1:
            archive.close()
            raise FileProcessingError("The document package contains an unsafe entry.")
        total += info.file_size
        if total > settings.max_archive_uncompressed_bytes:
            archive.close()
            raise FileProcessingError("The document package expands beyond the safety limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
    return archive


def _xml_fields(archive: zipfile.ZipFile, names: tuple[str, ...], source: str) -> list[MetadataField]:
    fields: list[MetadataField] = []
    for name in names:
        try:
            content = archive.read(name)
        except KeyError:
            continue
        if len(content) > 2 * 1024 * 1024:
            raise FileProcessingError("A metadata section exceeds the safety limit.", 413)
        try:
            root = ElementTree.fromstring(content)
        except ElementTree.ParseError as exc:
            raise FileProcessingError("The document metadata is malformed.") from exc
        for element in root.iter():
            text = (element.text or "").strip()
            if text:
                fields.append(_field(element.tag, text, source))
            for key, value in element.attrib.items():
                if value:
                    fields.append(_field(f"{element.tag}@{key}", value, source))
    return fields


def _inspect_package(content: bytes, format_id: str) -> tuple[MetadataField, ...]:
    archive = _validate_archive(content)
    try:
        _verify_package_format(archive, format_id)
        if format_id in OOXML_FORMATS:
            names = ("docProps/core.xml", "docProps/app.xml", "docProps/custom.xml")
            return tuple(_xml_fields(archive, names, "OOXML package properties"))
        return tuple(_xml_fields(archive, ("meta.xml",), "ODF package metadata"))
    finally:
        archive.close()


def _verify_package_format(archive: zipfile.ZipFile, format_id: str) -> None:
    names = set(archive.namelist())
    if format_id in OOXML_FORMATS:
        required = OOXML_REQUIRED_PARTS[format_id]
        if "[Content_Types].xml" not in names or required not in names:
            raise FileProcessingError(f"The file is not a valid {format_id.upper()} package.")
        return
    expected = ODF_MIME_TYPES[format_id]
    try:
        actual = archive.read("mimetype").decode("ascii").strip()
    except (KeyError, UnicodeDecodeError) as exc:
        raise FileProcessingError(f"The file is not a valid {format_id.upper()} package.") from exc
    if actual != expected:
        raise FileProcessingError(f"The file is not a valid {format_id.upper()} package.")


def inspect_file_metadata(content: bytes, format_id: str) -> MetadataInspectionResult:
    definition = normalize_format(format_id)
    if definition is None or not definition.capabilities.inspect_metadata:
        raise FileProcessingError("Metadata inspection is not supported for this format.", 422, ProcessingErrorCode.UNSUPPORTED_FEATURE)
    if definition.category.value == "image":
        raw = inspect_image_metadata(content)
        fields = tuple(_field(key, value, "Image EXIF", removable=definition.capabilities.remove_metadata) for key, value in raw["metadata"].items())
        warning = "Image inspection covers metadata exposed by the installed image decoder; it does not prove that no other identifying data exists."
    elif definition.id == "pdf":
        raw = inspect_pdf_metadata(content)
        fields = tuple(_field(key, value, "PDF document information") for key, value in raw.items() if value not in (None, "", False))
        warning = "PDF inspection does not detect every embedded identifier, annotation, hidden layer, or visible personal detail."
    elif definition.id in OOXML_FORMATS | ODF_FORMATS:
        fields = _inspect_package(content, definition.id)
        warning = "Office package inspection covers common package properties, not every embedded object, macro, comment, or external link."
    else:
        raise FileProcessingError("Metadata inspection is not supported for this format.", 422, ProcessingErrorCode.UNSUPPORTED_FEATURE)
    return MetadataInspectionResult(definition.id, fields, warning)


_OOXML_EMPTY = {
    "docProps/core.xml": b'<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"/>',
    "docProps/app.xml": b'<?xml version="1.0" encoding="UTF-8"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"/>',
    "docProps/custom.xml": b'<?xml version="1.0" encoding="UTF-8"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"/>',
}
_ODF_EMPTY = b'<?xml version="1.0" encoding="UTF-8"?><office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"><office:meta/></office:document-meta>'


def _remove_package_metadata(content: bytes, format_id: str) -> bytes:
    archive = _validate_archive(content)
    output = io.BytesIO()
    try:
        _verify_package_format(archive, format_id)
        with zipfile.ZipFile(output, "w") as cleaned:
            for info in archive.infolist():
                replacement = _OOXML_EMPTY.get(info.filename) if format_id in OOXML_FORMATS else (_ODF_EMPTY if info.filename == "meta.xml" else None)
                data = replacement if replacement is not None else archive.read(info)
                cleaned.writestr(info, data)
    finally:
        archive.close()
    result = output.getvalue()
    if len(result) > settings.max_document_output_size:
        raise FileProcessingError("The cleaned document exceeds the output size limit.", 413, ProcessingErrorCode.DECODED_CONTENT_TOO_LARGE)
    return result


def remove_file_metadata(content: bytes, format_id: str) -> MetadataRemovalResult:
    definition = normalize_format(format_id)
    if definition is None or not definition.capabilities.remove_metadata:
        raise FileProcessingError("Metadata removal is not supported for this format.", 422, ProcessingErrorCode.UNSUPPORTED_FEATURE)
    before = inspect_file_metadata(content, definition.id)
    if definition.category.value == "image":
        processed = remove_image_metadata(content)
        result = processed.content
    elif definition.id == "pdf":
        result = remove_pdf_metadata(content).content
    elif definition.id in OOXML_FORMATS | ODF_FORMATS:
        result = _remove_package_metadata(content, definition.id)
    else:
        raise FileProcessingError("Metadata removal is not supported for this format.", 422, ProcessingErrorCode.UNSUPPORTED_FEATURE)
    after = inspect_file_metadata(result, definition.id)
    return MetadataRemovalResult(
        result,
        definition.id,
        definition.preferred_extension,
        definition.preferred_mime_type,
        max(0, len(before.fields) - len(after.fields)),
        "Supported metadata fields were removed from a new copy. This is not a guarantee of anonymity, redaction, or malware sanitization.",
    )
