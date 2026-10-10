"""Docker build/smoke check, executed as the actual non-root runtime user."""
import os
from pathlib import Path
import stat


def main():
    if os.geteuid() == 0:
        raise RuntimeError("Model permissions must be checked as a non-root user")
    directory = Path(os.environ["BACKGROUND_MODEL_DIR"])
    if stat.S_IMODE(directory.stat().st_mode) != 0o555:
        raise RuntimeError("Model directory must have mode 0555")
    if not os.access(directory, os.R_OK | os.X_OK) or os.access(directory, os.W_OK):
        raise RuntimeError("Runtime user must traverse/read, but not write, the model directory")
    for name in ("u2netp.onnx", "LICENSE-U2NET.txt", "ATTRIBUTION.md"):
        path = directory / name
        if stat.S_IMODE(path.stat().st_mode) != 0o444 or os.access(path, os.W_OK):
            raise RuntimeError(f"Model artifact must be read-only: {name}")
        with path.open("rb") as source:
            if not source.read(1):
                raise RuntimeError(f"Model artifact is empty: {name}")
    print("Non-root runtime user can read model artifacts and cannot write them")


if __name__ == "__main__":
    main()
