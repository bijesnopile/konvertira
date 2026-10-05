import asyncio

import pytest

from backend.services.resource_limits import (
    McpBusyError,
    McpJobTimeoutError,
    McpRateLimitError,
    McpResourceLimits,
)
from config import Settings


def _manager(
    *,
    enabled: bool = True,
    requests: int = 3,
    heavy: int = 2,
    jobs: int = 1,
    timeout: float = 1,
) -> McpResourceLimits:
    return McpResourceLimits(
        rate_limit_enabled=enabled,
        request_limit=requests,
        heavy_limit=heavy,
        global_jobs=jobs,
        timeout_seconds=timeout,
    )


def test_request_below_global_limit_succeeds() -> None:
    manager = _manager(requests=2)
    manager.check_request()
    manager.check_request()


def test_request_above_global_limit_is_rejected() -> None:
    manager = _manager(requests=1)
    manager.check_request()
    with pytest.raises(McpRateLimitError) as error:
        manager.check_request()
    assert error.value.retry_after >= 1


def test_heavy_quota_is_stricter_than_general_quota() -> None:
    manager = _manager(requests=3, heavy=1)
    manager.check_request()
    manager.check_request()
    manager.check_heavy_job("remove_image_metadata")
    with pytest.raises(McpRateLimitError):
        manager.check_heavy_job("remove_image_metadata")


def test_global_slot_is_acquired_and_released_after_success() -> None:
    async def scenario() -> None:
        manager = _manager()

        async def operation() -> str:
            assert manager.active_jobs == 1
            return "ok"

        assert await manager.run_heavy_job("test", operation) == "ok"
        assert manager.active_jobs == 0

    asyncio.run(scenario())


def test_global_slot_is_released_after_exception() -> None:
    async def scenario() -> None:
        manager = _manager()

        async def operation() -> None:
            raise ValueError("expected test failure")

        with pytest.raises(ValueError, match="expected test failure"):
            await manager.run_heavy_job("test", operation)
        assert manager.active_jobs == 0

    asyncio.run(scenario())


def test_saturated_service_rejects_without_waiting() -> None:
    async def scenario() -> None:
        manager = _manager(jobs=1)
        started = asyncio.Event()
        finish = asyncio.Event()

        async def blocking_operation() -> None:
            started.set()
            await finish.wait()

        first = asyncio.create_task(manager.run_heavy_job("first", blocking_operation))
        await started.wait()

        invoked = False

        async def should_not_run() -> None:
            nonlocal invoked
            invoked = True

        with pytest.raises(McpBusyError):
            await asyncio.wait_for(
                manager.run_heavy_job("second", should_not_run),
                timeout=0.1,
            )
        assert invoked is False
        finish.set()
        await first
        assert manager.active_jobs == 0

    asyncio.run(scenario())


def test_timeout_returns_clean_error_and_retains_slot_until_work_finishes() -> None:
    async def scenario() -> None:
        manager = _manager(timeout=0.01)
        finish = asyncio.Event()

        async def slow_operation() -> None:
            await finish.wait()

        with pytest.raises(McpJobTimeoutError, match="allowed time"):
            await manager.run_heavy_job("slow", slow_operation)
        assert manager.active_jobs == 1

        finish.set()
        for _ in range(10):
            await asyncio.sleep(0)
            if manager.active_jobs == 0:
                break
        assert manager.active_jobs == 0

    asyncio.run(scenario())


def test_rate_limiting_can_be_disabled_without_disabling_capacity() -> None:
    manager = _manager(enabled=False, requests=1, heavy=1)
    for _ in range(10):
        manager.check_request()
        manager.check_heavy_job("test")


def test_mcp_limits_are_configurable_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("MCP_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("MCP_RATE_LIMIT_PER_MINUTE", "41")
    monkeypatch.setenv("MCP_HEAVY_JOBS_PER_MINUTE", "11")
    monkeypatch.setenv("MCP_MAX_GLOBAL_JOBS", "3")
    monkeypatch.setenv("MCP_JOB_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("MCP_MAX_TEMP_STORAGE_MB", "256")

    configured = Settings()
    assert configured.mcp_rate_limit_enabled is False
    assert configured.mcp_rate_limit_per_minute == 41
    assert configured.mcp_heavy_jobs_per_minute == 11
    assert configured.mcp_max_global_jobs == 3
    assert configured.mcp_job_timeout_seconds == 45
    assert configured.mcp_max_temp_storage_bytes == 256 * 1024 * 1024
