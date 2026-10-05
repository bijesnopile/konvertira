"""Global MCP quotas, processing capacity, and overall job timeouts."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from backend.services.rate_limit import InMemoryRateLimiter, LimitExceeded
from config import settings

T = TypeVar("T")

logger = logging.getLogger("konvertira.mcp.resources")


class McpResourceError(RuntimeError):
    """Expected, user-safe MCP resource-protection rejection."""


class McpRateLimitError(McpResourceError):
    def __init__(self, retry_after: int) -> None:
        super().__init__("Too many processing requests. Please wait briefly and try again.")
        self.retry_after = retry_after


class McpBusyError(McpResourceError):
    def __init__(self) -> None:
        super().__init__(
            "Konvertira is currently handling too many file-processing requests. "
            "Please try again in a moment."
        )


class McpJobTimeoutError(McpResourceError):
    def __init__(self) -> None:
        super().__init__(
            "Konvertira could not finish processing within the allowed time. "
            "Please try a smaller file."
        )


class GlobalJobCapacity:
    """Immediate, non-queuing global capacity gate."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self._active = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            if self.limit <= 0 or self._active >= self.limit:
                raise McpBusyError()
            self._active += 1

    async def release(self) -> None:
        async with self._lock:
            if self._active > 0:
                self._active -= 1

    @property
    def active(self) -> int:
        return self._active


class McpResourceLimits:
    """Reusable lifecycle controller for all expensive MCP tools."""

    def __init__(
        self,
        *,
        rate_limit_enabled: bool,
        request_limit: int,
        heavy_limit: int,
        global_jobs: int,
        timeout_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.request_limit = request_limit
        self.heavy_limit = heavy_limit
        self.timeout_seconds = timeout_seconds
        self._clock = clock
        self._last_rejection_log: dict[str, float] = {}
        self._log_lock = threading.Lock()
        self._limiter = InMemoryRateLimiter(
            enabled=rate_limit_enabled,
            window_seconds=60,
            clock=clock,
        )
        self._capacity = GlobalJobCapacity(global_jobs)

    def clear(self) -> None:
        self._limiter.clear()
        with self._log_lock:
            self._last_rejection_log.clear()

    def check_request(self) -> None:
        try:
            self._limiter.check("mcp:requests:global", self.request_limit)
        except LimitExceeded as exc:
            if self._should_log_rejection("request-rate"):
                logger.warning("mcp_request_blocked reason=rate_limit")
            raise McpRateLimitError(exc.retry_after) from None

    def check_heavy_job(self, tool_name: str) -> None:
        try:
            self._limiter.check("mcp:heavy:global", self.heavy_limit)
        except LimitExceeded as exc:
            if self._should_log_rejection(f"heavy-rate:{tool_name}"):
                logger.warning("mcp_job_blocked tool=%s reason=rate_limit", tool_name)
            raise McpRateLimitError(exc.retry_after) from None

    async def run_heavy_job(
        self,
        tool_name: str,
        operation_factory: Callable[[], Awaitable[T]],
    ) -> T:
        """Run one job without queueing and retain capacity until work really ends."""

        self.check_heavy_job(tool_name)
        try:
            await self._capacity.acquire()
        except McpBusyError:
            if self._should_log_rejection(f"busy:{tool_name}"):
                logger.warning("mcp_job_blocked tool=%s reason=busy", tool_name)
            raise

        started = time.monotonic()
        logger.info("mcp_job_started tool=%s", tool_name)
        try:
            task = asyncio.create_task(operation_factory())
        except Exception:
            await self._capacity.release()
            logger.info(
                "mcp_job_completed tool=%s outcome=failed duration_seconds=%.3f",
                tool_name,
                time.monotonic() - started,
            )
            raise
        deferred_release = False

        try:
            completed, _ = await asyncio.wait(
                {task},
                timeout=self.timeout_seconds,
            )
            if not completed:
                deferred_release = True
                task.add_done_callback(self._release_after_background_completion)
                logger.warning(
                    "mcp_job_timeout tool=%s duration_seconds=%.3f",
                    tool_name,
                    time.monotonic() - started,
                )
                raise McpJobTimeoutError()
            result = task.result()
        except asyncio.CancelledError:
            if not task.done():
                deferred_release = True
                task.add_done_callback(self._release_after_background_completion)
            raise
        except McpJobTimeoutError:
            raise
        except Exception:
            logger.info(
                "mcp_job_completed tool=%s outcome=failed duration_seconds=%.3f",
                tool_name,
                time.monotonic() - started,
            )
            raise
        else:
            logger.info(
                "mcp_job_completed tool=%s outcome=success duration_seconds=%.3f",
                tool_name,
                time.monotonic() - started,
            )
            return result
        finally:
            if not deferred_release:
                await self._capacity.release()

    def _release_after_background_completion(self, task: asyncio.Task[object]) -> None:
        if not task.cancelled():
            task.exception()
        asyncio.create_task(self._capacity.release())

    def _should_log_rejection(self, key: str) -> bool:
        """Avoid allowing a request flood to become a log-volume flood."""

        now = self._clock()
        with self._log_lock:
            previous = self._last_rejection_log.get(key, float("-inf"))
            if now - previous < 10:
                return False
            self._last_rejection_log[key] = now
            return True

    @property
    def active_jobs(self) -> int:
        return self._capacity.active

    @property
    def rate_limits_enabled(self) -> bool:
        return self._limiter.enabled

    @rate_limits_enabled.setter
    def rate_limits_enabled(self, enabled: bool) -> None:
        self._limiter.enabled = enabled


mcp_resource_limits = McpResourceLimits(
    rate_limit_enabled=settings.mcp_rate_limit_enabled,
    request_limit=settings.mcp_rate_limit_per_minute,
    heavy_limit=settings.mcp_heavy_jobs_per_minute,
    global_jobs=settings.mcp_max_global_jobs,
    timeout_seconds=settings.mcp_job_timeout_seconds,
)
