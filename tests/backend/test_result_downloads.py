import asyncio
import os
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.services import storage as storage_module
from backend.services.storage import TemporaryStorage, cleanup_periodically
from backend.services.result_downloads import ResultDownloadResponse
from backend.routers import downloads
from backend.utils.mime import content_type_for_path
import konvertira_mcp.server as server
import main


@pytest.fixture
def clock(monkeypatch):
    value = [1000.0]
    monkeypatch.setattr(storage_module.time, "time", lambda: value[0])
    monkeypatch.setattr(storage_module.time, "monotonic", lambda: value[0])
    return value


@pytest.fixture(params=["backend", "mcp"])
def delivery(request, monkeypatch, tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60)
    if request.param == "backend":
        monkeypatch.setattr(downloads, "api_storage", storage)
        monkeypatch.setattr(downloads, "enforce_general_rate", lambda request: None)
        app = main.create_app()
    else:
        monkeypatch.setattr(server, "mcp_storage", storage)
        monkeypatch.setattr(server, "enforce_general_rate", lambda request: None)
        app = server.create_app()
    # No lifespan context: startup/periodic cleanup intentionally does not run.
    return storage, TestClient(app)


@pytest.mark.parametrize("extension", ["jpg", "png", "webp", "avif", "heic", "heif", "pdf", "zip", "txt", "html", "docx", "odt", "csv", "xlsx", "ods", "pptx", "odp"])
def test_output_headers_and_bytes(delivery, extension):
    storage, client = delivery
    result = storage.save(b"harmless output", extension)
    response = client.get(f"/download/{result.token}")
    assert response.status_code == 200
    assert response.content == b"harmless output"
    assert response.headers["content-type"].split(";")[0] == content_type_for_path("." + extension)
    assert response.headers["content-disposition"] == f'attachment; filename="konvertira-cleaned.{extension}"'
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_expired_download_denied_even_when_every_unlink_fails(delivery, clock, monkeypatch):
    storage, client = delivery
    result = storage.save(b"private bytes", "png")
    # Reproduces original vulnerability: cleanup cannot remove expired result.
    def denied(*args, **kwargs):
        raise PermissionError("simulated")
    monkeypatch.setattr(Path, "unlink", denied)
    monkeypatch.setattr(os, "unlink", denied)
    clock[0] = 1060
    response = client.get(f"/download/{result.token}")
    assert response.status_code == 404
    assert b"private bytes" not in response.content
    assert result.path.exists()
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert storage.resolve(result.token) is None


def test_restart_and_ttl_override(tmp_path, clock):
    original = TemporaryStorage(tmp_path, 60)
    result = original.save(b"secret", "pdf")
    clock[0] = 1020
    assert TemporaryStorage(tmp_path, 60).resolve(result.token) == result.path
    assert TemporaryStorage(tmp_path, 10).resolve(result.token) is None
    fresh = original.save(b"secret", "pdf")
    clock[0] = 1080
    # Raising current TTL cannot renew an issued token's original expiry.
    assert TemporaryStorage(tmp_path, 900).resolve(fresh.token) is None


def test_attempt_does_not_refresh_expiry(delivery, clock):
    storage, client = delivery
    result = storage.save(b"secret", "png")
    before = result.path.stat().st_mtime_ns
    clock[0] = 1059
    assert client.get(f"/download/{result.token}").status_code == 200
    assert result.path.stat().st_mtime_ns == before
    clock[0] = 1060
    assert client.get(f"/download/{result.token}").status_code == 404


@pytest.mark.parametrize("token", ["invalid", "a" * 43, "..", "../../outside", "a" * 129, "abc%2Fdef"])
def test_invalid_or_missing_token(delivery, token):
    _, client = delivery
    assert client.get(f"/download/{'%2e%2e' if token == '..' else token}").status_code == 404


def test_legacy_result_without_metadata_denied(tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60)
    token = "a" * 43
    path = tmp_path / f"{token}.png"
    path.write_bytes(b"legacy")
    assert storage.resolve(token) is None
    os.utime(path, (900, 900))
    assert storage.cleanup(now=1000) == 1


@pytest.mark.parametrize("failure", ["stat", "open", "metadata"])
def test_filesystem_errors_fail_closed(delivery, monkeypatch, failure):
    storage, client = delivery
    result = storage.save(b"private bytes", "png")
    if failure == "metadata":
        (storage.directory / f".{result.token}.json").write_bytes(b"not-json")
    else:
        def denied(*args, **kwargs):
            raise PermissionError("simulated")
        if failure == "stat":
            monkeypatch.setattr(Path, "lstat", denied)
        else:
            monkeypatch.setattr(storage, "_open", denied)
    response = client.get(f"/download/{result.token}")
    assert response.status_code == 404
    assert b"private bytes" not in response.content
    assert str(storage.directory) not in response.text


def test_symlink_and_replaced_result_denied(delivery):
    storage, client = delivery
    result = storage.save(b"original", "png")
    # Changing file contents invalidates the bound inode/size/mtime identity.
    result.path.write_bytes(b"replacement-private")
    assert client.get(f"/download/{result.token}").status_code == 404
    result.path.unlink()
    outside = storage.directory.parent / "outside-private"
    outside.write_bytes(b"outside secret")
    try:
        result.path.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation unavailable on this host")
    assert client.get(f"/download/{result.token}").status_code == 404
    assert outside.read_bytes() == b"outside secret"


def test_concurrent_cleanup_cannot_authorise_expired_result(tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"secret", "png")
    clock[0] = 1060
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(storage.resolve, result.token) for _ in range(20)]
        cleanups = [pool.submit(storage.cleanup, now=1061) for _ in range(5)]
        assert all(future.result() is None for future in futures)
        for future in cleanups:
            future.result()


async def deliver_response(response, *, on_start=None):
    messages = []
    async def receive():
        await asyncio.Event().wait()
    async def send(message):
        messages.append(message)
        if message["type"] == "http.response.start" and on_start:
            on_start()
    await response({"type": "http", "method": "GET", "asgi": {"spec_version": "2.4"}}, receive, send)
    return messages


def test_delayed_response_opens_late_and_denies_expiry_or_deletion(tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"secret", "png")
    assert storage.resolve(result.token) == result.path
    response = ResultDownloadResponse(storage, result.token, "expired")
    clock[0] = 1060
    messages = asyncio.run(deliver_response(response))
    assert messages[0]["status"] == 404
    second = storage.save(b"secret", "png")
    response = ResultDownloadResponse(storage, second.token, "expired")
    second.path.unlink()
    assert asyncio.run(deliver_response(response))[0]["status"] == 404


def test_valid_started_download_can_finish_after_expiry(tmp_path, clock, monkeypatch):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"x" * 150000, "zip")
    handles = []
    original = storage.open_result
    def capture(token):
        opened = original(token)
        if opened:
            handles.append(opened[0])
        return opened
    monkeypatch.setattr(storage, "open_result", capture)
    response = ResultDownloadResponse(storage, result.token, "expired")
    messages = asyncio.run(deliver_response(response, on_start=lambda: clock.__setitem__(0, 1060)))
    assert messages[0]["status"] == 200
    assert b"".join(m.get("body", b"") for m in messages) == b"x" * 150000
    assert handles[0].closed
    assert storage.resolve(result.token) is None


def test_substitution_after_open_cannot_change_delivered_bytes(tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"original", "png")
    def replace():
        try:
            result.path.unlink()
            result.path.write_bytes(b"replacement")
        except PermissionError:
            pass  # Windows open handle denies replacement instead.
    messages = asyncio.run(deliver_response(ResultDownloadResponse(storage, result.token, "missing"), on_start=replace))
    assert messages[0]["status"] == 200
    assert b"".join(m.get("body", b"") for m in messages) == b"original"


def test_periodic_cleanup_survives_filesystem_error(tmp_path, monkeypatch):
    storage = TemporaryStorage(tmp_path, 60)
    calls = []
    async def immediate(_):
        pass
    def cleanup():
        calls.append(1)
        if len(calls) == 1:
            raise OSError("recoverable")
        raise asyncio.CancelledError()
    monkeypatch.setattr(storage_module.asyncio, "sleep", immediate)
    monkeypatch.setattr(storage, "cleanup", cleanup)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(cleanup_periodically(storage))
    assert len(calls) == 2


def test_stat_failure_does_not_kill_cleanup(tmp_path, clock, monkeypatch):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"secret", "png")
    original = Path.lstat
    def denied(path, *args, **kwargs):
        if path == result.path:
            raise PermissionError("simulated")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "lstat", denied)
    assert storage.cleanup(now=1060) >= 0
    assert storage.resolve(result.token) is None


def test_metadata_expiry_ignores_result_mtime_refresh(tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"secret", "png")
    os.utime(result.path, (9999999999, 9999999999))
    assert storage.cleanup(now=1060) == 2
    assert not result.path.exists()


@pytest.mark.parametrize("error", ["disconnect", "read", "cancel"])
def test_descriptor_closes_on_delivery_failure(tmp_path, clock, monkeypatch, error):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"x" * 150000, "zip")
    handles = []
    original = storage.open_result
    def capture(token):
        opened = original(token)
        if opened:
            handles.append(opened[0])
        return opened
    monkeypatch.setattr(storage, "open_result", capture)
    async def run():
        async def receive():
            await asyncio.Event().wait()
        async def send(message):
            if message["type"] == "http.response.body":
                if error == "cancel":
                    raise asyncio.CancelledError()
                raise OSError("disconnected")
        if error == "read":
            # Actual file descriptor deliberately closed after open simulates
            # a read failure; response finally must still be safe/idempotent.
            def broken_capture(token):
                opened = capture(token)
                opened[0].close()
                return opened
            monkeypatch.setattr(storage, "open_result", broken_capture)
        await ResultDownloadResponse(storage, result.token, "missing")(
            {"type": "http", "method": "GET", "asgi": {"spec_version": "2.4"}}, receive, send)
    from starlette.requests import ClientDisconnect
    with pytest.raises((ValueError, ClientDisconnect, asyncio.CancelledError)):
        asyncio.run(run())
    assert handles and handles[0].closed


def test_expiry_after_descriptor_open_before_headers_denied(tmp_path, clock, monkeypatch):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"secret", "png")
    original = storage.open_result
    handles = []
    def delayed(token):
        opened = original(token)
        handles.append(opened[0])
        clock[0] = 1060
        return opened
    monkeypatch.setattr(storage, "open_result", delayed)
    messages = asyncio.run(deliver_response(ResultDownloadResponse(storage, result.token, "missing")))
    assert messages[0]["status"] == 404
    assert handles[0].closed


def test_error_headers_include_rate_limit_and_unmatched_download(delivery, monkeypatch):
    _, client = delivery
    response = client.get("/download/unmatched/path")
    assert response.status_code == 404
    assert response.headers["cache-control"] == "no-store"
    from fastapi import HTTPException
    def limited(request):
        raise HTTPException(429, "busy", headers={"Retry-After": "10"})
    monkeypatch.setattr(downloads, "enforce_general_rate", limited)
    monkeypatch.setattr(server, "enforce_general_rate", limited)
    response = client.get("/download/" + "a" * 43)
    assert response.status_code == 429
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["retry-after"] == "10"


def test_restart_with_failed_cleanup_and_diagnostics_are_private(tmp_path, clock, monkeypatch, caplog):
    original = TemporaryStorage(tmp_path, 60)
    result = original.save(b"private bytes", "png")
    clock[0] = 1060
    def denied(*args, **kwargs):
        raise PermissionError("simulated")
    monkeypatch.setattr(Path, "unlink", denied)
    monkeypatch.setattr(os, "unlink", denied)
    restarted = TemporaryStorage(tmp_path, 60)
    restarted.cleanup()
    assert restarted.resolve(result.token) is None
    assert result.path.exists()
    assert result.token not in caplog.text
    assert str(tmp_path) not in caplog.text
    assert "private bytes" not in caplog.text


def test_backwards_clock_cannot_reenable_in_process(tmp_path, clock, monkeypatch):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"secret", "png")
    clock[0] = 1060
    def denied(*args, **kwargs):
        raise PermissionError("simulated")
    monkeypatch.setattr(Path, "unlink", denied)
    monkeypatch.setattr(os, "unlink", denied)
    assert storage.resolve(result.token) is None

    clock[0] = 1040
    assert storage.resolve(result.token) is None


def test_final_header_boundary_checks_expiry_and_json_length(tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60)
    result = storage.save(b"secret", "png")
    class DelayedStart(ResultDownloadResponse):
        async def stream_response(self, send):
            clock[0] = 1060
            await super().stream_response(send)
    messages = asyncio.run(deliver_response(DelayedStart(storage, result.token, "expired result")))
    assert messages[0]["status"] == 404
    headers = dict(messages[0]["headers"])
    assert int(headers[b"content-length"]) == len(messages[1]["body"])
    assert messages[1]["body"] == b'{"detail":"expired result"}'


def test_cleanup_does_not_delete_unrelated_entries(tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60)
    unrelated = tmp_path / "operator-note.txt"
    unrelated.write_bytes(b"not a result")
    os.utime(unrelated, (900, 900))
    assert storage.cleanup(now=1060) == 0
    assert unrelated.read_bytes() == b"not a result"


@pytest.mark.parametrize("field,value", [("name", "../../outside"), ("identity", [0]), ("expires", float("nan")), ("created", "invalid")])
def test_invalid_expiration_record_fails_closed(delivery, field, value):
    storage, client = delivery
    result = storage.save(b"secret", "png")
    metadata = storage.directory / f".{result.token}.json"
    record = json.loads(metadata.read_bytes())
    record[field] = value
    metadata.write_text(json.dumps(record), encoding="ascii")
    response = client.get(f"/download/{result.token}")
    assert response.status_code == 404
    assert b"secret" not in response.content


def test_hard_link_and_directory_substitution_denied(tmp_path, clock):
    directory = tmp_path / "results"
    storage = TemporaryStorage(directory, 60)
    result = storage.save(b"secret", "png")
    alias = tmp_path / "alias"
    os.link(result.path, alias)
    assert storage.resolve(result.token) is None
    alias.unlink()
    directory.rename(tmp_path / "original-directory")
    directory.mkdir()
    assert storage.resolve(result.token) is None


def test_storage_sidecar_is_bounded_and_no_partial_result_on_capacity_failure(tmp_path, clock):
    storage = TemporaryStorage(tmp_path, 60, max_bytes=5)
    from backend.models.files import StorageCapacityError
    with pytest.raises(StorageCapacityError):
        storage.save(b"small", "png")
    assert list(tmp_path.iterdir()) == []
