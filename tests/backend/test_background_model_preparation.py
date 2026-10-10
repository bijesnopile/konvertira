"""Model preparation regressions without codecs, inference, network or Docker."""
import hashlib
import io
import os
from pathlib import Path
import stat

import pytest

from scripts import prepare_background_model as prepare


@pytest.fixture
def model_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("BACKGROUND_MODEL_DIR", str(tmp_path))
    yield tmp_path
    # Windows read-only files must be made writable for test directory cleanup.
    for path in tmp_path.iterdir():
        path.chmod(0o600)


def stub_download(monkeypatch, content):
    monkeypatch.setattr(prepare.urllib.request, "urlopen", lambda *args, **kwargs: io.BytesIO(content))


def test_verified_download_is_published_read_only(monkeypatch, model_directory):
    content = b"verified test model"
    monkeypatch.setattr(prepare, "MODEL_SHA256", hashlib.sha256(content).hexdigest())
    stub_download(monkeypatch, content)
    replace = Path.replace
    modes_at_publication = []
    def record_replace(source, destination):
        modes_at_publication.append(source.stat().st_mode)
        return replace(source, destination)
    monkeypatch.setattr(Path, "replace", record_replace)
    prepare.main()
    model = model_directory / "u2netp.onnx"
    assert model.read_bytes() == content
    assert not model.stat().st_mode & stat.S_IWUSR
    assert not modes_at_publication[0] & stat.S_IWUSR
    if os.name == "posix":
        assert stat.S_IMODE(model.stat().st_mode) == 0o444
    assert list(model_directory.iterdir()) == [model]


def test_cached_verified_model_permissions_are_repaired(monkeypatch, model_directory):
    content = b"cached test model"
    monkeypatch.setattr(prepare, "MODEL_SHA256", hashlib.sha256(content).hexdigest())
    model = model_directory / "u2netp.onnx"
    model.write_bytes(content)
    model.chmod(0o600)
    def no_download(*args, **kwargs):
        pytest.fail("A verified cached model must not be downloaded again")
    monkeypatch.setattr(prepare.urllib.request, "urlopen", no_download)
    prepare.main()
    assert model.read_bytes() == content
    assert not model.stat().st_mode & stat.S_IWUSR
    if os.name == "posix":
        assert stat.S_IMODE(model.stat().st_mode) == 0o444


def test_unverified_download_is_never_published(monkeypatch, model_directory):
    stub_download(monkeypatch, b"wrong model")
    with pytest.raises(RuntimeError, match="verification failed"):
        prepare.main()
    assert list(model_directory.iterdir()) == []


def test_failed_publication_cleans_read_only_temporary_file(monkeypatch, model_directory):
    content = b"verified test model"
    monkeypatch.setattr(prepare, "MODEL_SHA256", hashlib.sha256(content).hexdigest())
    stub_download(monkeypatch, content)
    def failed_replace(*args, **kwargs):
        raise OSError("Publication failed")
    monkeypatch.setattr(Path, "replace", failed_replace)
    with pytest.raises(OSError, match="Publication failed"):
        prepare.main()
    assert list(model_directory.iterdir()) == []
