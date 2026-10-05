"""HTTP response schemas."""

from pydantic import BaseModel


class ActionResponse(BaseModel):
    success: bool
    filename: str
    content_type: str
    download_url: str
    message: str
