import asyncio

import pytest
from fastapi import Request

from backend.services.rate_limit import InMemoryRateLimiter, LimitExceeded, ProcessingCapacity
from backend.services.security import get_client_identifier, read_request_body_limited


def _request(peer: str, headers: dict[str, str] | None = None, body: bytes = b"") -> Request:
    sent = False

    async def receive():
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [
            (name.lower().encode("ascii"), value.encode("ascii"))
            for name, value in (headers or {}).items()
        ],
        "client": (peer, 12345),
        "server": ("testserver", 443),
    }
    return Request(scope, receive)


def test_repeated_requests_are_rejected_with_retry_after() -> None:
    now = [100.0]
    limiter = InMemoryRateLimiter(window_seconds=60, clock=lambda: now[0])

    limiter.check("client", 2)
    limiter.check("client", 2)
    with pytest.raises(LimitExceeded) as error:
        limiter.check("client", 2)

    assert error.value.retry_after == 60
    now[0] = 161.0
    limiter.check("client", 2)


def test_disabled_rate_limiter_does_not_reject() -> None:
    limiter = InMemoryRateLimiter(enabled=False)
    for _ in range(100):
        limiter.check("client", 1)


def test_concurrent_processing_capacity_is_bounded() -> None:
    async def scenario() -> None:
        capacity = ProcessingCapacity(per_client_limit=1, global_limit=1)
        entered = asyncio.Event()
        release = asyncio.Event()

        async def hold_slot() -> None:
            async with capacity.slot("198.51.100.10"):
                entered.set()
                await release.wait()

        first = asyncio.create_task(hold_slot())
        await entered.wait()
        with pytest.raises(LimitExceeded):
            async with capacity.slot("198.51.100.10"):
                pass
        with pytest.raises(LimitExceeded):
            async with capacity.slot("198.51.100.11"):
                pass
        release.set()
        await first

    asyncio.run(scenario())


def test_spoofed_forwarding_header_is_ignored_from_untrusted_peer() -> None:
    request = _request("203.0.113.10", {"X-Forwarded-For": "198.51.100.20"})
    assert get_client_identifier(request, ("127.0.0.1/32",)) == "203.0.113.10"


def test_forwarding_header_is_used_from_trusted_peer() -> None:
    request = _request("127.0.0.1", {"CF-Connecting-IP": "198.51.100.20"})
    assert get_client_identifier(request, ("127.0.0.1/32",)) == "198.51.100.20"


def test_raw_request_body_is_rejected_before_unbounded_buffering() -> None:
    request = _request("203.0.113.10", body=b"12345")
    with pytest.raises(Exception) as error:
        asyncio.run(read_request_body_limited(request, limit=4))
    assert getattr(error.value, "status_code", None) == 413
