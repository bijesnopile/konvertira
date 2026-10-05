"""HTTP authentication, client identity, and request safety helpers."""

from contextlib import asynccontextmanager
import ipaddress
import secrets
from typing import AsyncIterator

from fastapi import Depends, HTTPException, Request, UploadFile
from fastapi.security import APIKeyHeader

from backend.services.rate_limit import (
    LimitExceeded,
    check_general_rate,
    heavy_processing_slot,
)
from config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(x_api_key: str | None = Depends(api_key_header)) -> None:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header.")
    if not settings.api_key:
        raise HTTPException(status_code=503, detail="API authentication is not configured.")
    if not secrets.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="Invalid API key.")


async def read_upload_limited(upload: UploadFile, limit: int | None = None) -> bytes:
    """Read at most the configured limit plus one byte from an upload."""

    size_limit = limit or settings.max_image_size
    content = await upload.read(size_limit + 1)
    if len(content) > size_limit:
        limit_mb = size_limit // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"The image is larger than the {limit_mb} MB limit.",
        )
    return content


async def read_request_body_limited(request: Request, limit: int | None = None) -> bytes:
    """Read a raw request body without buffering more than the configured limit."""

    size_limit = limit or settings.max_image_size
    chunks: list[bytes] = []
    received = 0
    async for chunk in request.stream():
        received += len(chunk)
        if received > size_limit:
            limit_mb = size_limit // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=f"The image is larger than the {limit_mb} MB limit.",
            )
        chunks.append(chunk)
    return b"".join(chunks)


def _is_trusted_proxy(peer: str, trusted_proxies: tuple[str, ...]) -> bool:
    try:
        address = ipaddress.ip_address(peer)
    except ValueError:
        return False

    for configured in trusted_proxies:
        try:
            if address in ipaddress.ip_network(configured, strict=False):
                return True
        except ValueError:
            continue
    return False


def _valid_forwarded_address(value: str) -> str | None:
    candidate = value.split(",", 1)[0].strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def get_client_identifier(
    request: Request,
    trusted_proxies: tuple[str, ...] | None = None,
) -> str:
    """Return an IP identifier, trusting forwarding headers only from known peers."""

    peer = request.client.host if request.client else "unknown"
    trusted = settings.trusted_proxy_ips if trusted_proxies is None else trusted_proxies
    if not _is_trusted_proxy(peer, trusted):
        return peer

    for header in ("cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
        value = request.headers.get(header)
        if value and (forwarded := _valid_forwarded_address(value)):
            return forwarded
    return peer


def _limit_http_exception(error: LimitExceeded) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail=str(error),
        headers={"Retry-After": str(error.retry_after)},
    )


def enforce_general_rate(request: Request) -> None:
    try:
        check_general_rate(get_client_identifier(request))
    except LimitExceeded as exc:
        raise _limit_http_exception(exc) from exc


@asynccontextmanager
async def heavy_request_guard(
    request: Request,
) -> AsyncIterator[None]:
    try:
        async with heavy_processing_slot(
            get_client_identifier(request),
        ):
            yield
    except LimitExceeded as exc:
        raise _limit_http_exception(exc) from exc
