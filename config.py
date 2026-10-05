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


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
    max_temp_storage_bytes: int = field(
        default_factory=lambda: int(os.getenv("MAX_TEMP_STORAGE_BYTES", str(1024 * 1024 * 1024)))
    )
    result_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("RESULT_TTL_SECONDS", str(15 * 60)))
    )
    rate_limit_enabled: bool = field(
        default_factory=lambda: _bool("RATE_LIMIT_ENABLED", True)
    )
    rate_limit_requests_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "30"))
    )
    rate_limit_heavy_jobs_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_HEAVY_JOBS_PER_MINUTE", "5"))
    )
    max_concurrent_heavy_jobs_per_ip: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_HEAVY_JOBS_PER_IP", "2"))
    )
    max_concurrent_heavy_jobs_global: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_HEAVY_JOBS_GLOBAL", "4"))
    )
    trusted_proxy_ips: tuple[str, ...] = field(
        default_factory=lambda: _csv("TRUSTED_PROXY_IPS", "127.0.0.1/32,::1/128")
    )
    mcp_rate_limit_enabled: bool = field(
        default_factory=lambda: _bool("MCP_RATE_LIMIT_ENABLED", True)
    )
    mcp_rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("MCP_RATE_LIMIT_PER_MINUTE", "30"))
    )
    mcp_heavy_jobs_per_minute: int = field(
        default_factory=lambda: int(os.getenv("MCP_HEAVY_JOBS_PER_MINUTE", "10"))
    )
    mcp_max_global_jobs: int = field(
        default_factory=lambda: int(os.getenv("MCP_MAX_GLOBAL_JOBS", "4"))
    )
    mcp_job_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("MCP_JOB_TIMEOUT_SECONDS", "60"))
    )
    mcp_max_temp_storage_mb: int = field(
        default_factory=lambda: int(os.getenv("MCP_MAX_TEMP_STORAGE_MB", "512"))
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

    @property
    def mcp_max_temp_storage_bytes(self) -> int:
        return self.mcp_max_temp_storage_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
