"""Central environment-backed configuration for Konvertira."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()


def _csv(name: str, default: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in os.getenv(name, default).split(",") if item.strip())


def _path(name: str, default: Path) -> Path:
    return Path(os.getenv(name, str(default))).expanduser().resolve()


def _mcp_hosts() -> tuple[str, ...]:
    configured = _csv("MCP_ALLOWED_HOSTS", "")
    if configured:
        return configured
    public_url = os.getenv("MCP_PUBLIC_BASE_URL") or os.getenv(
        "PUBLIC_BASE_URL", "http://localhost:8001"
    )
    netloc = urlparse(public_url).netloc
    return (netloc,) if netloc else ()


@dataclass(frozen=True, slots=True)
class Settings:
    """Application settings loaded once from environment variables."""

    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Image Privacy Protector"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "3.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    public_base_url: str = field(
        default_factory=lambda: os.getenv(
            "PUBLIC_BASE_URL", "http://localhost:8000"
        ).rstrip("/")
    )
    mcp_public_base_url: str = field(
        default_factory=lambda: os.getenv(
            "MCP_PUBLIC_BASE_URL",
            os.getenv("PUBLIC_BASE_URL", "http://localhost:8001"),
        ).rstrip("/")
    )
    mcp_port: int = field(default_factory=lambda: int(os.getenv("MCP_PORT", "8001")))
    api_key: str | None = field(default_factory=lambda: os.getenv("API_KEY") or None)
    max_image_size: int = field(
        default_factory=lambda: int(os.getenv("MAX_IMAGE_SIZE", str(20 * 1024 * 1024)))
    )
    max_pixels: int = field(default_factory=lambda: int(os.getenv("MAX_PIXELS", "100000000")))
    result_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("RESULT_TTL_SECONDS", str(15 * 60)))
    )
    storage_dir: Path = field(
        default_factory=lambda: _path(
            "STORAGE_DIR", Path(tempfile.gettempdir()) / "image-privacy-protector"
        )
    )
    mcp_storage_dir: Path = field(
        default_factory=lambda: _path(
            "MCP_STORAGE_DIR", Path(tempfile.gettempdir()) / "image-privacy-protector-results"
        )
    )
    allowed_download_hosts: tuple[str, ...] = field(
        default_factory=lambda: _csv(
            "ALLOWED_DOWNLOAD_HOSTS", "openai.com,oaiusercontent.com"
        )
    )
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: _csv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://localhost:8080,https://konvertira.com",
        )
    )
    mcp_allowed_hosts: tuple[str, ...] = field(
        default_factory=_mcp_hosts
    )
    mcp_allowed_origins: tuple[str, ...] = field(
        default_factory=lambda: _csv(
            "MCP_ALLOWED_ORIGINS", "https://chatgpt.com,https://www.chatgpt.com"
        )
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
