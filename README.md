# Konvertira

Server-side image background removal is available in the web image tools and MCP.
It creates transparent PNG/WebP using local automated segmentation and temporary
processing. Complex edges may need refinement; it does not guarantee anonymity
or remove visible sensitive information. See [deployment and model requirements](docs/background-removal.md).

Konvertira is an independently operated, privacy-focused file conversion and metadata-cleaning project. It has three applications sharing the same processors and declarative format registry:

- `frontend/` — React, TypeScript, Vite, and Tailwind CSS.
- `backend/` — FastAPI routes plus reusable processors and services.
- `konvertira_mcp/` — MCP tools for ChatGPT, backed by the same server processors.

`main.py` and `mcp_server.py` are stable compatibility entry points. The MCP package is named `konvertira_mcp` so it does not shadow the official `mcp` Python package.

## Processing modes

JPG/JPEG, PNG, and static WebP conversion, resize, compression, batch conversion, and metadata-clean re-encoding run in the browser. Those local workflows do not call the API and never fall back to an upload.

HEIC/HEIF, AVIF, static GIF, PDF, document, spreadsheet, presentation, unified metadata, and every MCP workflow are explicitly server-side. Server files are bounded, processed only for the selected operation, and any downloadable result stored by MCP or legacy API routes expires after `RESULT_TTL_SECONDS` (15 minutes by default).

Metadata removal creates a new file. It is not redaction, malware sanitization, proof of anonymity, or removal of visible personal information.

## Implemented formats and conversion matrix

`format_registry.json` is the canonical source for format IDs, extensions, MIME aliases, capabilities, constraints, execution modes, and conversion edges. `backend/formats.py` and `frontend/src/formats/registry.ts` both read it.

| Category | Inputs | Implemented outputs/operations | Mode |
|---|---|---|---|
| Images | JPEG, PNG, static WebP | JPEG, PNG, WebP; resize/compress; metadata-clean copy | Local and server |
| Advanced images | HEIC/HEIF | JPEG, PNG, WebP | Server |
| Advanced images | AVIF | JPEG, PNG, WebP | Server |
| Advanced images | static GIF | JPEG, PNG, WebP | Server |
| AVIF encoding | JPEG, PNG, static WebP | AVIF | Server |
| PDF | PDF and supported images | Merge, extract, split, reorder, delete pages, PDF-to-images, images-to-PDF, inspect/remove metadata, structural optimization | Server |
| Documents | DOCX | TXT, PDF, ODT | Server |
| Documents | DOC | DOCX, PDF | Server |
| Documents | ODT | DOCX, PDF | Server |
| Documents | RTF | DOCX, PDF | Server |
| Text | TXT | DOCX, PDF | Server |
| Text | Markdown | HTML, DOCX, PDF | Server |
| Documents | HTML | TXT | Server |
| Spreadsheets | XLSX | CSV, ODS, PDF | Server |
| Spreadsheets | XLS | CSV, XLSX, PDF | Server |
| Spreadsheets | ODS | CSV, XLSX, PDF | Server |
| Spreadsheets | CSV (UTF-8) | XLSX, ODS | Server |
| Presentations | PPTX | PDF, ODP | Server |
| Presentations | PPT | PPTX, PDF | Server |
| Presentations | ODP | PPTX, PDF | Server |

Animated images and encrypted PDFs are rejected. A workbook with multiple sheets becomes a ZIP containing one safely named CSV per sheet. CSV cannot preserve styles, charts, workbook structure, or formulas as formulas. Office conversions may change fonts, layout, formulas, charts, macros, embedded objects, links, animations, and transitions. Legacy DOC/XLS/PPT reliability depends on the installed LibreOffice version and fonts.

Metadata inspection is implemented for supported images, PDF, DOCX/XLSX/PPTX, and ODT/ODS/ODP. Metadata removal is implemented for JPEG/PNG/WebP, PDF, and those OOXML/ODF packages. Office inspection covers common package properties, not every embedded object, comment, macro, external link, or hidden identifier.

## Architecture

```text
React local tool ── browser Canvas only

FastAPI route ─┐
MCP tool ──────┼─ resource guard ─ processor/service ─ response or TTL storage
               └─ shared format registry and validation
```

Processors do not know about HTTP or MCP schemas. Routers and tools validate declared filenames/MIME types, enforce resource guards, and dispatch to the same processing layer. Extensions and MIME claims remain untrusted; Pillow, pypdf/PyMuPDF, python-docx/openpyxl, LibreOffice, and guarded package parsing verify actual content as applicable.

## Setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-dev.txt
Copy-Item .env.example .env
uvicorn main:app --reload --port 8000
```

In another terminal:

```powershell
uvicorn mcp_server:app --reload --port 8001
Set-Location frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Python dependencies are pinned in `requirements.txt`. Pillow/pillow-heif handle image codecs; pypdf and PyMuPDF handle PDF structure/rasterization; python-docx, Markdown, Beautiful Soup, and openpyxl cover direct bounded conversions; defusedxml protects metadata XML parsing. LibreOffice Writer, Calc, Impress, and DejaVu fonts are installed only in the backend image for conversions that require an external engine.

Never put secrets in `VITE_*` variables because Vite embeds them into the public bundle. `.env.example` contains placeholders only; `.env*`, keys, virtual environments, build output, temporary results, and backups are excluded from Docker build context.

## HTTP API

Public server-processing routes:

- `GET /health`
- `POST /images/convert`
- `POST /images/remove-metadata`
- `POST /pdf/{merge|extract|split|reorder|delete-pages|images-to-pdf|to-images|inspect-metadata|remove-metadata|optimize}`
- `POST /documents/convert`
- `POST /office/convert`
- `POST /metadata/{inspect|remove}`

Legacy API-key-protected compatibility routes remain `POST /remove-metadata/action` and `POST /remove-metadata/upload`, with `GET /download/{token}` for their temporary results.

## MCP

The streamable HTTP endpoint is `/mcp`. Tools are:

- `remove_image_metadata` (backward-compatible original tool)
- `convert_image`
- `inspect_file_metadata`
- `remove_file_metadata`
- `merge_pdfs`
- `extract_pdf_pages`
- `convert_pdf_to_images`
- `convert_images_to_pdf`
- `convert_document`
- `convert_spreadsheet`
- `convert_presentation`

MCP accepts typed OpenAI file references only. Downloads require HTTPS, revalidate every redirect, accept only configured OpenAI host suffixes, stream to a size limit, and use timeouts. It does not expose arbitrary URLs, paths, commands, or command-line options. The hostname allowlist substantially limits SSRF; DNS resolution is not pinned for the full connection lifetime, so production egress rules remain recommended defense in depth.

## Resource and security controls

Limits are centralized in `config.py` and documented in `.env.example`: input/output bytes, pixels, target-size attempts, PDF files/pages/DPI/generated pixels, document output, archive entries/uncompressed bytes, subprocess timeout, per-client/general/heavy quotas, global concurrency, temporary-storage capacity, and TTL.

HTTP and MCP heavy jobs reject immediately when capacity is full; they do not maintain an unbounded queue. Defaults allow two global heavy jobs, suitable as a conservative starting point for a small VPS. MCP adds an overall 60-second job timeout and retains its slot while non-cancellable thread work finishes. LibreOffice has its own 60-second subprocess timeout and an isolated randomized profile/workspace. Run one backend worker and one MCP worker while using in-memory limiters; multiple workers or replicas require a shared limiter or equivalent reverse-proxy enforcement.

Archive metadata handling validates entry count, total expanded bytes, encrypted/traversal entries, and expected OOXML/ODF package markers without extracting files. Multi-output ZIP names are generated by Konvertira. Download tokens are random and validated, results expire, storage capacity is bounded, and responses use `no-store` and `nosniff`.

The frontend nginx configuration keeps a strict CSP without `unsafe-inline` or `unsafe-eval`, plus frame, referrer, permissions, COOP, CORP, and MIME-sniffing protections. Configure HSTS at Caddy after all covered domains are HTTPS-ready.

## Docker and production

```powershell
docker compose config --quiet
docker compose build
docker compose up -d
```

Frontend, backend, and MCP ports bind to host loopback in Compose so Caddy can be the public entry point for `konvertira.com`, `api.konvertira.com`, and `mcp.konvertira.com`. Containers use non-root users where applicable, `no-new-privileges`, dropped backend/MCP capabilities, internal networking, health checks, and no Docker socket or host filesystem mount. Keep one Uvicorn worker per backend/MCP service. Temporary result volumes contain user data and must not be backed up.

Set `VITE_API_BASE_URL=https://api.konvertira.com` during the production frontend build. Restrict direct origin access, set exact `TRUSTED_PROXY_IPS`, cap request bodies/timeouts at Caddy, redact `/download/*` tokens from proxy logs, and add coarse edge rate limits. The application revalidates forwarded client addresses only from configured trusted proxy peers.

## Verification

```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m compileall -q main.py mcp_server.py config.py backend konvertira_mcp
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m pip_audit -r requirements.txt
.\venv\Scripts\python.exe -m pip_audit -r requirements-dev.txt

Set-Location frontend
npm run typecheck
npm test
npm run build
npm audit
```

The public pages are `/`, `/convert`, `/pdf-tools`, `/metadata`, `/privacy`, `/terms`, `/support`, and `/about`. `frontend/public/robots.txt` and `frontend/public/sitemap.xml` cover the public site routes.
