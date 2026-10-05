"""Constrained remote-file downloads for OpenAI/ChatGPT file references."""

from __future__ import annotations

from urllib.parse import urljoin, urlparse

import httpx

from config import settings


class DownloadError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def is_allowed_download_host(host: str, allowed_hosts: tuple[str, ...] | None = None) -> bool:
    normalized = host.lower().rstrip(".")
    return any(
        normalized == allowed.lower().rstrip(".")
        or normalized.endswith(f".{allowed.lower().rstrip('.')}")
        for allowed in (allowed_hosts or settings.allowed_download_hosts)
    )


def validate_download_url(url: str, allowed_hosts: tuple[str, ...] | None = None) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise DownloadError("Download URL must use HTTPS.")
    host = (parsed.hostname or "").lower()
    if not is_allowed_download_host(host, allowed_hosts):
        raise DownloadError(f"Disallowed download host: {host or '[missing]'}")


async def download_openai_file(
    download_link: str,
    *,
    max_size: int | None = None,
    allowed_hosts: tuple[str, ...] | None = None,
) -> bytes:
    """Download a file while validating every redirect before following it."""

    size_limit = max_size or settings.max_image_size
    hosts = allowed_hosts or settings.allowed_download_hosts
    current_url = download_link
    timeout = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            for _ in range(6):
                validate_download_url(current_url, hosts)
                async with client.stream("GET", current_url) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise DownloadError("Download redirect did not include a location.", 502)
                        current_url = urljoin(current_url, location)
                        continue
                    if response.status_code != 200:
                        raise DownloadError(
                            f"OpenAI download link returned status {response.status_code}.", 502
                        )

                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > size_limit:
                        raise DownloadError("Uploaded image exceeds the size limit.", 413)

                    chunks: list[bytes] = []
                    received = 0
                    async for chunk in response.aiter_bytes():
                        received += len(chunk)
                        if received > size_limit:
                            raise DownloadError("Uploaded image exceeds the size limit.", 413)
                        chunks.append(chunk)
                    return b"".join(chunks)
            raise DownloadError("Download URL redirected too many times.", 502)
    except DownloadError:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise DownloadError(f"Could not download uploaded file: {exc}", 502) from exc
