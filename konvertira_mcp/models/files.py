"""MCP file input and structured output models."""

from pydantic import BaseModel, ConfigDict, HttpUrl


class OpenAIFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    download_url: HttpUrl
    file_id: str
    mime_type: str | None = None
    file_name: str | None = None


class ProcessedImage(BaseModel):
    success: bool
    filename: str
    content_type: str
    download_url: HttpUrl
    message: str
