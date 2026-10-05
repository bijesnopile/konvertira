"""HTTP request schemas."""

from pydantic import BaseModel, Field


class OpenAIFileRef(BaseModel):
    """Expanded OpenAI file reference supplied to GPT Actions at runtime."""

    name: str
    id: str
    mime_type: str
    download_link: str


class ActionRequest(BaseModel):
    openaiFileIdRefs: list[OpenAIFileRef] = Field(..., min_length=1, max_length=1)
