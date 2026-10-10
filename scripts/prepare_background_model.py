"""Operator/build-only fixed model download. Never used by request processing."""
import os
import tempfile
import urllib.request
from pathlib import Path

# Deliberately independent of application imports/native codecs during image build.
import hashlib

MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
MODEL_SHA256 = "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8"


def main():
    directory = Path(os.environ.get("BACKGROUND_MODEL_DIR", "models")).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "u2netp.onnx"
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == MODEL_SHA256:
        return
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as output:
            temporary = Path(output.name)
            with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
                content = response.read(10 * 1024 * 1024 + 1)
            if len(content) > 10 * 1024 * 1024 or hashlib.sha256(content).hexdigest() != MODEL_SHA256:
                raise RuntimeError("Model checksum/size verification failed")
            output.write(content)
        temporary.replace(destination)
        print(f"Prepared {destination} ({len(content)} bytes)")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
