"""Short-lived, in-memory request and processing resource limits.

Limits are intentionally per process. They provide a safe baseline for the
single-instance deployment and can later be replaced with a shared store when
multiple workers or replicas need one aggregate limit.
"""

from __future__ import annotations

import asyncio
import math
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import AsyncIterator, Callable

from config import settings


class LimitExceeded(RuntimeError):
    def __init__(self, message: str, retry_after: int) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class InMemoryRateLimiter:
    """Fixed-window-equivalent sliding limiter with bounded, expiring state."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        window_seconds: float = 60.0,
        max_keys: int = 10_000,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.enabled = enabled
        self.window_seconds = window_seconds
        self.max_keys = max_keys
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, limit: int) -> None:
        if not self.enabled:
            return
        if limit <= 0:
            raise LimitExceeded("Request processing is temporarily unavailable.", 60)

        now = self._clock()
        cutoff = now - self.window_seconds
        with self._lock:
            if key not in self._events and len(self._events) >= self.max_keys:
                stale = [
                    event_key
                    for event_key, timestamps in self._events.items()
                    if not timestamps or timestamps[-1] <= cutoff
                ]
                for event_key in stale:
                    self._events.pop(event_key, None)
                if len(self._events) >= self.max_keys:
                    namespace = "heavy:mcp" if key.startswith("heavy:mcp:") else (
                        "heavy:http" if key.startswith("heavy:http:") else "general"
                    )
                    key = f"{namespace}:overflow"

            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, math.ceil(self.window_seconds - (now - events[0])))
                raise LimitExceeded(
                    "Too many requests. Please wait briefly and try again.",
                    retry_after,
                )
            events.append(now)

            # Opportunistically discard inactive keys so identifiers are not
            # retained longer than the rate-limit window.
            if len(self._events) > 1024:
                stale = [
                    event_key
                    for event_key, timestamps in self._events.items()
                    if not timestamps or timestamps[-1] <= cutoff
                ]
                for event_key in stale:
                    self._events.pop(event_key, None)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


class ProcessingCapacity:
    """Reject heavy jobs immediately when per-client or process capacity is full."""

    def __init__(
        self,
        *,
        enabled: bool = True,
        per_client_limit: int = 2,
        global_limit: int = 4,
    ) -> None:
        self.enabled = enabled
        self.per_client_limit = per_client_limit
        self.global_limit = global_limit
        self._active_by_client: dict[str, int] = defaultdict(int)
        self._active_global = 0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def slot(self, client_id: str) -> AsyncIterator[None]:
        acquired = False
        if self.enabled:
            async with self._lock:
                if (
                    self._active_global >= self.global_limit
                    or self._active_by_client[client_id] >= self.per_client_limit
                ):
                    raise LimitExceeded(
                        "The processing service is busy. Please try again shortly.",
                        2,
                    )
                self._active_global += 1
                self._active_by_client[client_id] += 1
                acquired = True

        try:
            yield
        finally:
            if acquired:
                async with self._lock:
                    self._active_global -= 1
                    remaining = self._active_by_client[client_id] - 1
                    if remaining > 0:
                        self._active_by_client[client_id] = remaining
                    else:
                        self._active_by_client.pop(client_id, None)


request_limiter = InMemoryRateLimiter(enabled=settings.rate_limit_enabled)
processing_capacity = ProcessingCapacity(
    enabled=settings.rate_limit_enabled,
    per_client_limit=settings.max_concurrent_heavy_jobs_per_ip,
    global_limit=settings.max_concurrent_heavy_jobs_global,
)


def check_general_rate(client_id: str) -> None:
    request_limiter.check(
        f"general:{client_id}",
        settings.rate_limit_requests_per_minute,
    )


@asynccontextmanager
async def heavy_processing_slot(
    client_id: str,
) -> AsyncIterator[None]:
    check_general_rate(client_id)
    request_limiter.check(
        f"heavy:http:{client_id}",
        settings.rate_limit_heavy_jobs_per_minute,
    )
    async with processing_capacity.slot(client_id):
        yield
