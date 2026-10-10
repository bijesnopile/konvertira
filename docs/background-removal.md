# Server image background removal

`POST /images/remove-background` accepts multipart `file` and optional
`output_format=png|webp` (default PNG). The matching MCP tool is
`remove_image_background(file: OpenAIFile, output_format: png|webp = png)`.
Both return a new transparent image using automated local segmentation.
The web UI lives alongside the advanced server image converter on `/convert`.
Selecting a file does not upload it; the explicit upload action does.

Supported inputs are static JPEG, PNG, WebP, HEIC/HEIF, AVIF and GIF, derived
from registry `removeBackground` server operation modes. Animated inputs are
rejected. Outputs are PNG or lossless WebP with alpha; original alpha is
multiplied by the mask. Orientation is applied and source metadata is discarded.
Complex hair, fur, shadows, glass, translucent objects and visually similar
foreground/background areas may need manual refinement. This does not guarantee
anonymity or remove visible sensitive information.

## Engine, provenance and licenses

The engine is ONNX Runtime CPU with the small general-purpose U²-NetP model
from Xuebin Qin and collaborators' U²-Net project. It uses a 320×320 inference
input and restores the mask to the original oriented dimensions. This compact
model favors a small VPS; it is not a professional matting model.

- ONNX Runtime: MIT, https://github.com/microsoft/onnxruntime/blob/main/LICENSE
- NumPy: BSD-3-Clause with bundled component notices (in the installed package).
- U²-Net project/model distribution: Apache-2.0,
  https://github.com/xuebinqin/U-2-Net/blob/master/LICENSE
  and https://github.com/xuebinqin/U-2-Net#usage-for-salient-object-detection
- ONNX weights are the fixed U²-NetP export distributed by rembg:
  https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx
  (rembg's code is MIT; rembg is not a runtime dependency).

The model is an ONNX conversion of the Apache-licensed upstream small model;
no different model terms are declared by that upstream distribution. Retain
the bundled Apache license and this attribution when redistributing the image.
No BRIA or noncommercial model is included.

Artifact: 4,574,861 bytes (~4.36 MiB), SHA-256
`309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8`.
The setup script pins both URL and hash. Requests cannot choose models, URLs
or paths. Model integrity is checked before session initialization.

## Deployment

The backend/MCP Docker image installs CPU-only ONNX Runtime/NumPy and downloads
and verifies the model at build time into `/opt/konvertira-models`.
The model and license stay in the image across container recreation; no cache
volume or new public port is needed. Build requires network access; processing
requires none. Health endpoints remain independent of model initialization.
Rebuild backend and MCP images before deploying this feature.

The model directory stays root-owned with mode `0555`; model, license and
attribution files have mode `0444`. The preparation script sets the verified
model to `0444` before atomic publication and repairs the mode on cached models.
After `USER konvertira`, the shared Dockerfile checks actual read/traverse access
and absence of write access. Both backend and MCP builds fail if this regresses.
The preparation script remains an operator/build step only.

After rebuilding and recreating both services, run these smoke checks as their
default runtime user (do not pass `--user root`):

```sh
docker compose build backend mcp
docker compose up -d --force-recreate backend mcp
docker compose exec -T backend python scripts/check_background_model_permissions.py
docker compose exec -T mcp python scripts/check_background_model_permissions.py
docker compose exec -T backend python -c "from backend.processors.background_removal import _get_session; print(_get_session().get_providers())"
docker compose exec -T mcp python -c "from backend.processors.background_removal import _get_session; print(_get_session().get_providers())"
docker compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read())"
docker compose exec -T mcp python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=2).read())"
```

For non-Docker development, run `python scripts/prepare_background_model.py`
from the repository root. Default directory is `models/` (ignored by Git).
Set `BACKGROUND_MODEL_DIR` to a trusted operator-owned directory when needed;
run the preparation script with that same environment. Missing/corrupt model
returns a clear 503, never an automatic request-time download.

Settings:

- `BACKGROUND_MAX_PIXELS=12000000`: additional decoded-pixel ceiling, always
  capped by existing `MAX_PIXELS`.
- `BACKGROUND_THREADS=1`: ONNX intra-op CPU threads, clamped to 1–4.
- `BACKGROUND_TIMEOUT_SECONDS=60`: web operation timeout.
- MCP uses existing `MCP_JOB_TIMEOUT_SECONDS`, quotas, slots and temporary
  storage/TTL. Timed-out jobs retain their slots until the work actually ends.
- One inference per process is allowed; competing background inference gets
  a busy error rather than an unbounded queue. Existing global job gates remain.

Web output is returned directly like image conversion; uploads are in memory,
not retained on disk. MCP output uses existing token storage and TTL cleanup.
On web timeout the task retains its heavy-job slot until completion; the result
is discarded. The worker thread cannot be killed safely during inference.

Budget roughly 100–200 MiB additional installed image space for dependencies
and model (platform dependent; Docker measurement required). Runtime tensor
buffers/session plus decoded images may require hundreds of MiB per process.
Large 12 MP images create several RGBA/alpha buffers; budget at least 512 MiB
additional headroom per active operation and measure RSS on representative
files. Backend and MCP each retain their own session. Use one worker per service,
keep one inference thread on small VPSs, and lower the pixel ceiling if needed.
CPU latency depends on processor/image dimensions; no GPU/CUDA is required.

## Validation

Ordinary tests stub only segmentation, exercising the real bounded image decoder,
orientation, alpha combination, encoder, API and MCP storage/guards. They download
no model. To run the optional real CPU smoke test after preparation:
`BACKGROUND_INTEGRATION=1 python -m pytest tests/backend/test_background_removal.py`.
