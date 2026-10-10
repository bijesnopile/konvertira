"""MCP file input and structured output models."""

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, WithJsonSchema


class OpenAIFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    download_url: HttpUrl
    file_id: str
    mime_type: Annotated[
        str | None,
        WithJsonSchema({"type": "string"}),
    ] = Field(default_factory=lambda: None)
    file_name: Annotated[
        str | None,
        WithJsonSchema({"type": "string"}),
    ] = Field(default_factory=lambda: None)


class ProcessedImage(BaseModel):
    success: bool
    filename: str
    content_type: str
    download_url: HttpUrl
    message: str


class ProcessedResult(ProcessedImage):
    pass


class MetadataResult(BaseModel):
    format: str
    fields: list[dict[str, object]]
    warning: str


class ImageOutputFormat(StrEnum):
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    AVIF = "avif"


class PdfImageOutputFormat(StrEnum):
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"


class DocumentOutputFormat(StrEnum):
    TXT = "txt"
    HTML = "html"
    DOCX = "docx"
    ODT = "odt"
    PDF = "pdf"


class SpreadsheetOutputFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    ODS = "ods"
    PDF = "pdf"


class PresentationOutputFormat(StrEnum):
    PPTX = "pptx"
    ODP = "odp"
    PDF = "pdf"
