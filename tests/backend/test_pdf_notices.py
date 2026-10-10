import hashlib
import importlib.util
from importlib.metadata import distribution
from pathlib import Path
import pytest
import scripts.collect_pdf_notices as collector

from scripts.collect_pdf_notices import collect_notices


def test_pdf_dependencies_and_native_notices(tmp_path) -> None:
    assert importlib.util.find_spec("pymupdf") is None
    assert importlib.util.find_spec("fitz") is None
    assert distribution("pypdfium2").version == "5.14.0"
    assert distribution("pypdf").version == "6.20.0"
    manifest = collect_notices(tmp_path)
    for package, info in manifest.items():
        for relative, expected_hash in info["files"].items():
            assert hashlib.sha256((tmp_path / package / relative).read_bytes()).hexdigest() == expected_hash
    assert any("freetype.txt" in path for path in manifest["pypdfium2"]["files"])
    requirements = Path("requirements.txt").read_text()
    assert "pymupdf" not in requirements.lower()
    assert "pypdfium2==5.14.0" in requirements


def test_debian_runtime_notices_are_required_and_copied(monkeypatch, tmp_path) -> None:
    copyright = tmp_path / "copyright"
    gpl = tmp_path / "GPL-3"
    copyright.write_bytes(b"Test runtime copyright and exception notice")
    gpl.write_bytes(b"Test GPL notice")

    def fixture_path(*parts):
        if parts == ("/usr/share/doc/libgcc-s1/copyright",):
            return copyright
        if parts == ("/usr/share/common-licenses/GPL-3",):
            return gpl
        return Path(*parts)

    monkeypatch.setattr(collector, "Path", fixture_path)
    output = tmp_path / "output"
    manifest = collector.collect_notices(output, debian_runtime=True)
    assert (output / "system/libgcc-s1-copyright").read_bytes() == copyright.read_bytes()
    assert (output / "system/GPL-3").read_bytes() == gpl.read_bytes()
    assert len(manifest["system"]["files"]) == 2
    gpl.unlink()
    with pytest.raises(RuntimeError, match="runtime notice missing"):
        collector.collect_notices(output, debian_runtime=True)
