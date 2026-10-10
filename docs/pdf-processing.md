# PDF processing, renderer migration and notices

Files changed/added **by this migration**, separately from the preceding uncommitted
legal-page task:

- `README.md`
- `requirements.txt`
- `backend/Dockerfile`
- `backend/processors/pdf.py`
- `scripts/collect_pdf_notices.py`
- `tests/backend/test_pdf_processor.py`
- `tests/backend/test_pdf_api.py`
- `tests/backend/test_pdf_notices.py`
- `tests/mcp/test_workflows.py`
- `docs/legal-review-checklist.md`
- `docs/pdf-processing.md`
- `docs/licenses/pdf/pypdf.txt`
- `docs/licenses/pdf/pypdfium2-BSD-3-Clause.txt`
- `docs/licenses/pdf/pypdfium2-Apache-2.0.txt`
- `docs/licenses/pdf/PDFium-BSD.txt` (full upstream file, including Apache text)
- `docs/licenses/pdf/pdfium-binaries-MIT.txt`

Current legal-page draft contents, project licence, model notices, Caddy, Nginx,
registry, Compose and MCP public schemas were not modified by this migration.

## Runtime and compatibility

`pypdf==6.20.0` (existing) handles merge, selection/extraction, split, reorder,
delete, metadata inspection/removal and lossless **structural** optimisation.
`pypdfium2==5.14.0` now renders PDF pages using PDFium 156.0.8076.0. Pillow
continues encoding PNG/JPEG/WebP and creating PDFs from supported static images.
No route, MCP tool/annotation/schema, format registry or transport configuration
changed. Encrypted PDFs remain rejected by the existing strict pypdf validator
before native rendering. Original bytes remain unchanged.

Rendering uses `dpi / 72`, multiplied by the page's `/UserUnit` because PDFium
does not expose that factor in its page sizing API. Crop boxes and intrinsic
rotation come from native page sizing; selected pages preserve expression order
and deduplication. ZIP output retains sequential generated `page-0001.*` names,
not original page numbers. PNG/WebP render onto transparent RGBA; JPEG renders
RGB onto white. Annotations/form appearances are enabled. The wrapper's page,
bitmap and document resources are explicitly closed, including error paths; PIL
views are encoded/closed before their potentially shared native buffer is freed.

PDFium is not thread-safe, even for separate documents. A process-wide nonblocking
mutex surrounds **all** native calls and object lifetimes in the shared processor.
A competing render receives a retryable 429 busy error, not an unbounded queue.
Backend and MCP processes retain their separate existing gates, limits and MCP
timeout behaviour. Native rendering cannot safely be killed in a worker thread;
this task does not invent a universal HTTP render timeout or per-job sandbox.

All selected page dimensions are checked before any bitmap allocation, followed
by an actual rendered-pixel check. Existing PDF byte/page/DPI/generated-pixel limits
are preserved. Image encoder and ZIP buffers now enforce the output ceiling on
each write, including central-directory writes, rather than only after finishing
an arbitrarily large archive. At most the configured page count is emitted and
only one native page/bitmap and image encoder are live at a time. PDF parsers and
native rendering still have memory/CPU costs; defaults must suit the deployment.

## Expected rendering differences

The former engine and PDFium need not produce identical antialiasing, colour
management, font substitution, transparency edge pixels or encoded bytes. Tests
check physical dimensions, crop/rotation/UserUnit, order, content colours, alpha,
formats and reasonable fidelity rather than byte equality. Review complex fonts,
forms, annotations and representative user documents before production rollout.
Neither renderer supplies a forensic or archival-authenticity guarantee. Structural
operations were not rewritten; optimisation does not downsample images or guarantee
a smaller file. Metadata cleaning retains its existing limited scope, not universal
redaction or removal of every identifier.

## Dependency and licence evidence

The root `LICENSE` remains `All rights reserved`. No service registration, payment
or commercial renderer licence is required by this implementation. This is a
distribution review, not a formal legal opinion or a product-wide licence audit.

- **pypdf 6.20.0:** BSD-3-Clause, verified from the installed distribution's
  licence and [upstream licence](https://github.com/py-pdf/pypdf/blob/6.20.0/LICENSE).
  Existing dependency; no new optional extras were installed.
- **pypdfium2 5.14.0:** Apache-2.0 OR BSD-3-Clause for wrapper code. The BSD option
  is applicable for this integration; both upstream texts are retained. Its
  documentation/examples use CC-BY-4.0, not the runtime code licence. No upstream
  example code or documentation was copied into the renderer implementation.
  [Upstream release licensing](https://github.com/pypdfium2-team/pypdfium2/tree/5.14.0/LICENSES)
  and [distribution explanation](https://pypi.org/project/pypdfium2/5.14.0/).
- **PDFium native binary:** BSD-style notice plus the additional Apache text
  included in the distributed licence; retain the entire file, not only its first
  BSD paragraph. [Upstream PDFium licence](https://pdfium.googlesource.com/pdfium/+/refs/heads/main/LICENSE).
- **pdfium-binaries packaging:** MIT notice retained. Native dependencies have
  separate obligations; the main wrapper licence does not replace those.
- The Linux x86-64 wheel's actual `BUILD_LICENSES` contains notices for Abseil,
  AGG 2.3, fast_float, FreeType, ICU, lcms, libjpeg-turbo/IJG, OpenJPEG, libpng,
  LLVM libc, pdfium-binaries, PDFium, simdutf and zlib. These include Apache/MIT,
  BSD/ISC-style, FreeType, IJG and zlib/libpng terms rather than a new AGPL renderer.
  The bundled FreeType notice is the permissive FreeType Project licence; this
  product uses FreeType through PDFium and preserves that credit/disclaimer.
  ICU and font/codec notices must remain intact even where their text is long.
  No extra font download or system rendering executable was introduced.
- The pinned wheel metadata declares no Python `Requires-Dist` dependencies.
  Native dependencies are bundled or linked, **not** absent. ELF `DT_NEEDED`
  inspection of the downloaded Linux x86-64 wheel found `libpthread.so.0`,
  `libm.so.6`, `libgcc_s.so.1`, `libc.so.6` and `ld-linux-x86-64.so.2`.
  **Important:** libgcc is not simply permissively licensed: its GCC Runtime
  Library Exception provides additional permissions to GPL-covered runtime code,
  subject to its conditions. This does not mean Konvertira's own licence changes.
  [Official exception](https://www.gnu.org/licenses/gcc-exception-3.1.en.html) and
  [FSF explanation](https://www.gnu.org/licenses/gcc-exception-3.1-faq.en.html).
  The Debian build also copies the actual `libgcc-s1` copyright/exception notice
  and GPL-3 text, failing if missing. Verify eligible-build provenance and relevant
  linked-runtime obligations before redistribution; no claim that the entire
  Docker image is free of GPL/LGPL components is made. Existing LibreOffice/OS
  packages already have their independent obligations. Different architectures
  or wheel builds require their own linkage review.

Repository `docs/licenses/pdf/` retains pypdf, wrapper Apache/BSD, PDFium's complete
notice and pdfium-binaries MIT texts from the actual installed distributions.
Package-installed source copyright/SPDX headers and dist-info licence directories
remain in the images. The build-only `scripts/collect_pdf_notices.py` additionally
copies **all** installed pypdf/pypdfium2 licence files, including platform-specific
native notices, unchanged to `/usr/share/konvertira/pdf-notices`, with version and
SHA-256 manifest. Missing licence files or PDFium native notices fail the build.
This shared Dockerfile is used for both backend and MCP. No request-time licence
collection/download occurs. Model/U²-NetP licence and attribution are unchanged.

The actual downloaded Linux wheel was
`pypdfium2-5.14.0-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`, SHA-256
`11f281613fa22313d9c7ab89947665e84eccf8ebe40e1198a84a88352305648d`.
It has a Python-independent `py3` ABI and a glibc 2.17 baseline, compatible in
distribution tags with the Dockerfile's Python 3.13 Debian image. Download/notice
inspection is **not** execution of this Linux binary. Windows x64 native execution
was tested locally; Docker/Linux runtime checks remain outstanding.

## Removed-reference inventory

Initial whole-repository search (including hidden source/config files, excluding
Git internals, installed environments, generated bundles and binary archives):

| Previous location | Occurrences/action |
| --- | --- |
| `requirements.txt:13` | Removed `pymupdf==1.28.2`, replaced with pinned pypdfium2. |
| `backend/processors/pdf.py:11` | Removed `import pymupdf as fitz`. |
| `backend/processors/pdf.py:202` | Removed `fitz.Document` type/lifecycle. |
| `backend/processors/pdf.py:204` | Removed `fitz.open(stream=..., filetype=...)`. |
| `backend/processors/pdf.py:217` | Replaced `get_pixmap` and `fitz.Matrix`; related pixmap/sample code also removed. |
| `README.md:65,87` | Replaced two current-architecture references with pypdf/PDFium. |
| `docs/legal-review-checklist.md:178` | Replaced former current-dependency blocker with migration evidence and remaining notice review. |
| `docs/legal-review-checklist.md:227–228` | Kept two publisher links, explicitly marked historical. |

No other original references were found in tests, scripts, Docker, Compose or the
format registry. New negative dependency tests and this migration history mention
the removed library intentionally. A whole-tree search still finds these historical
or regression-only mentions, not a runtime import. Old virtual-environment bytecode
is not a dependency; fresh images install only updated requirements. The local
PyMuPDF package was uninstalled; both `pymupdf` and `fitz` import discovery are absent.
Previously published images can still contain it and need replacement after review.

## Local checks and recommended production smoke tests

Run from the repository root:

```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m pytest tests/backend/test_pdf_processor.py tests/backend/test_pdf_notices.py tests/backend/test_pdf_api.py tests/mcp -q
.\venv\Scripts\python.exe -m compileall -q main.py mcp_server.py config.py backend konvertira_mcp scripts
.\venv\Scripts\python.exe -m pip check
docker compose config --quiet
git diff --check
```

Test PDFs contain real vector colours, transparent regions, multiple sizes/pages
and image-derived content. Tests cover formats/DPI/ranges/order, crop/rotation/
UserUnit, encrypted/corrupt input, size/page/pixel/output ceilings, early preflight,
native cleanup after errors, busy gate, structural operations/optimisation/metadata,
API responses, MCP registration/file schemas, safe names, expiry and notices.

Local results: full pytest **160 passed, 3 skipped** (opt-in real background model,
missing local LibreOffice, Windows POSIX permissions). Six warnings are from the
existing pypdf structural-optimisation deprecated keyword arguments; behaviour was
not changed to silence them. Targeted processor/notices tests: **32 passed**;
targeted PDF/API/MCP suite: **72 passed**, including merge/image API and mocked
Debian runtime-notice collection checks that do not require Docker.
`compileall`, `pip check`, Compose configuration, frontend **44 tests** and
TypeScript passed. Docker daemon was unavailable, so no image build, Linux native
execution or deployed health check was performed. Actual vector/text render PNGs
were inspected locally with the PDF skill; no deliverable user PDF was authored.

After local review, on a host with Docker available (do not treat these as already
executed or permission to deploy):

```sh
docker compose build backend mcp
docker compose run --rm --no-deps backend python -c "import importlib.util, importlib.metadata as m, pypdfium2 as p; assert importlib.util.find_spec('pymupdf') is None; assert importlib.util.find_spec('fitz') is None; print(m.version('pypdf'), m.version('pypdfium2'), p.PDFIUM_INFO)"
docker compose run --rm --no-deps backend python -c "import json; print(json.load(open('/usr/share/konvertira/pdf-notices/manifest.json')))"
docker compose run --rm --no-deps backend sh -c 'ldd /usr/local/lib/python3.13/site-packages/pypdfium2_raw/libpdfium.so'
```

Confirm the linkage has no missing libraries and retain any applicable linked
runtime notices. Then, only when deployment is separately authorised, rebuild/
recreate both services and perform runtime checks:

```sh
docker compose exec -T backend python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).read())"
docker compose exec -T mcp python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=2).read())"
curl -fsS -F file=@smoke.pdf -F format=png -F dpi=72 -F pages=2,1 https://api.konvertira.com/pdf/to-images -o smoke-png.zip
curl -fsS -F file=@smoke.pdf -F format=jpeg -F dpi=144 https://api.konvertira.com/pdf/to-images -o smoke-jpeg.zip
curl -fsS -F file=@smoke.pdf -F format=webp -F dpi=144 https://api.konvertira.com/pdf/to-images -o smoke-webp.zip
```

Use a known nonsensitive multipage PDF. Check names, dimensions, order, text,
annotation/form appearances, transparency and colour in all archives. Through
ChatGPT, call the unchanged `convert_pdf_to_images` tool with the same test file,
download the ZIP, inspect it and verify the result expires. Check encrypted files
are rejected and quotas still work. No Caddy/CDN/domain challenge, Nginx legal route
or MCP transport change is part of this migration.
