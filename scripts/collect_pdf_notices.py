"""Build/operator-only collection of licences from installed PDF distributions.

Retain the original relative layout and contents, including native wheel notices.
This does not run on requests or download anything. Package upgrades regenerate
the notice bundle; no hand-maintained list silently drops new wheel components.
"""

from __future__ import annotations

import hashlib
import json
import sys
from importlib.metadata import distribution
from pathlib import Path, PurePosixPath


def collect_notices(output: Path, *, debian_runtime: bool = False) -> dict[str, object]:
    manifest: dict[str, object] = {}
    for name in ("pypdf", "pypdfium2"):
        package = distribution(name)
        files = [file for file in package.files or () if ".dist-info/licenses/" in str(file).replace("\\", "/")]
        if not files:
            raise RuntimeError(f"Missing distribution licence files: {name}")
        hashes = {}
        for file in files:
            relative = PurePosixPath(str(file).replace("\\", "/").split(".dist-info/licenses/", 1)[1])
            if relative.is_absolute() or ".." in relative.parts:
                raise RuntimeError("Unsafe distribution licence path")
            content = package.locate_file(file).read_bytes()
            target = output / name / Path(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            hashes[str(relative)] = hashlib.sha256(content).hexdigest()
        if name == "pypdfium2" and not any("BUILD_LICENSES/pdfium.txt" in path for path in hashes):
            raise RuntimeError("PDFium binary notices missing")
        manifest[name] = {"version": package.version, "files": hashes}
    if debian_runtime:
        # The inspected Linux wheel links libgcc_s. Keep the actual image's
        # copyright/exception information, not a guessed compiler version.
        hashes = {}
        for source in (Path("/usr/share/doc/libgcc-s1/copyright"), Path("/usr/share/common-licenses/GPL-3")):
            if not source.is_file():
                raise RuntimeError(f"Required Debian runtime notice missing: {source}")
            content = source.read_bytes()
            name = "libgcc-s1-copyright" if source.name == "copyright" else source.name
            target = output / "system" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            hashes[name] = hashlib.sha256(content).hexdigest()
        manifest["system"] = {"source": "Actual Debian image runtime notices", "files": hashes}
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    collect_notices(Path(sys.argv[1]), debian_runtime="--debian-runtime" in sys.argv[2:])
