# Konvertira

Konvertira is a privacy-first image conversion and metadata-removal service. The repository contains three independently deployable applications that share one image-processing core:

- `frontend/` — React, TypeScript, Vite, and Tailwind CSS application.
- `backend/` — FastAPI routes, processors, services, schemas, and utilities.
- `konvertira_mcp/` — MCP server and tools built on the same backend services.

The MCP package is named `konvertira_mcp` instead of `mcp` because the official MCP Python SDK already owns the top-level `mcp` package name. Using the requested name would shadow the SDK and prevent the server from importing.

The web frontend processes JPG/JPEG, PNG, and static WEBP images locally with browser canvas APIs. Image conversion and metadata stripping do not upload those files or call the backend. Backend image support remains available for MCP and future explicitly server-side workflows.

## Architecture

```text
HTTP router / MCP tool
        ↓
shared workflow and services
        ↓
pure image processor
        ↓
temporary token storage
```

`main.py` and `mcp_server.py` are compatibility entry points only. Existing deployments using `uvicorn main:app` or `uvicorn mcp_server:app` remain supported.

## Configuration

Copy `.env.example` to `.env` and replace the placeholder API key:

```powershell
Copy-Item .env.example .env
```

Never place secrets in `VITE_*` variables; Vite embeds them into the public browser bundle. Backend and MCP settings are centralized in `config.py`.

## Backend

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

Important endpoints:

- `GET /health`
- `POST /images/remove-metadata` — public multipart website endpoint
- `POST /images/convert` — public multipart website endpoint
- `POST /remove-metadata/action` — API-key-protected legacy GPT Action endpoint
- `POST /remove-metadata/upload` — API-key-protected legacy raw upload endpoint
- `GET /download/{token}` — temporary legacy result download

## MCP server

```powershell
.\venv\Scripts\Activate.ps1
uvicorn mcp_server:app --reload --port 8001
```

The streamable HTTP endpoint remains `/mcp`. The registered `remove_image_metadata` tool downloads only allowlisted HTTPS OpenAI hosts, uses the shared image processor, and stores results temporarily.

## Frontend

```powershell
Set-Location frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Production checks:

```powershell
npm run typecheck
npm test
npm run build
```

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m compileall -q main.py mcp_server.py config.py backend konvertira_mcp
.\venv\Scripts\python.exe -m pip_audit -r requirements.txt
.\venv\Scripts\python.exe -m pip_audit -r requirements-dev.txt
```

The suite covers metadata removal, supported and unsupported formats, file-size and resolution limits, conversion, filename cleaning, storage cleanup, download-host validation, FastAPI startup/routes, and MCP tool behavior.

## Docker

```powershell
docker build -f backend/Dockerfile -t konvertira-backend .
docker build --build-arg VITE_API_BASE_URL=https://api.konvertira.com -t konvertira-frontend ./frontend
docker compose up --build -d
docker compose ps
```

The development Compose file publishes backend and MCP ports only on the host loopback interface, not on external interfaces. The services also share an internal Docker network, ready for a future Caddy reverse proxy at `api.konvertira.com` and `mcp.konvertira.com`. Set `VITE_API_BASE_URL=https://api.konvertira.com` for the production build.

## Temporary data

Processed files use configurable temporary directories and are deleted after `RESULT_TTL_SECONDS`. `MAX_TEMP_STORAGE_BYTES` rejects new stored results with `503` if a temporary directory reaches its configured capacity. Compose mounts separate backend and MCP result volumes. These volumes contain short-lived user files and must not be included in backups. No database, authentication system, payments, analytics, or permanent file store is included.

## Request and resource protection

Browser-based JPG, PNG, and static WEBP operations do not call the server, so they are not rate limited. The regular HTTP API uses per-peer short-lived limits configured with:

- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_REQUESTS_PER_MINUTE`
- `RATE_LIMIT_HEAVY_JOBS_PER_MINUTE`
- `MAX_CONCURRENT_HEAVY_JOBS_PER_IP`
- `MAX_CONCURRENT_HEAVY_JOBS_GLOBAL`

The MCP/ChatGPT path deliberately uses global limits instead of guessing an end-user identity from OpenAI or proxy IPs:

- `MCP_RATE_LIMIT_ENABLED=true`
- `MCP_RATE_LIMIT_PER_MINUTE=30`
- `MCP_HEAVY_JOBS_PER_MINUTE=10`
- `MCP_MAX_GLOBAL_JOBS=4`
- `MCP_JOB_TIMEOUT_SECONDS=60`
- `MCP_MAX_TEMP_STORAGE_MB=512`

The MCP transport checks its global request quota before dispatch. Each expensive tool then checks the stricter global heavy-job quota and immediately acquires a global processing slot before MIME validation, remote download, decode, transformation, or storage. Saturated work is rejected rather than queued. An overall timeout returns a safe tool error; if non-cancellable thread work is still finishing, its slot remains reserved until that work actually ends.

Limit excess returns HTTP `429` with `Retry-After` where the HTTP layer supports it. `/health` is intentionally excluded. Limits and concurrent-job counts are per MCP application process, so run one MCP worker on the current small VPS. Multi-worker or multi-replica deployments need a shared limiter or equivalent global enforcement at the reverse proxy. Disabling `MCP_RATE_LIMIT_ENABLED` is intended for local development and does not disable concurrency, timeout, size, pixel, or storage safeguards.

Client IP detection uses the socket peer by default. `CF-Connecting-IP`, `X-Real-IP`, and `X-Forwarded-For` are accepted only when the immediate peer matches `TRUSTED_PROXY_IPS`. In production, set this to the exact Caddy or container-network peer IP/CIDR, prevent direct public access to backend ports, and configure Caddy to trust forwarding headers only from Cloudflare's current published proxy ranges. Do not use an unrestricted private-network range merely for convenience.

Cloudflare or another edge provider should add coarse per-path request limits for `/images/*`, `/mcp`, and `/download/*`, cap request body size, and block direct origin access. Edge protection complements the application limiter; it does not replace file-size, pixel, concurrency, or storage limits.

For `mcp.konvertira.com`, optional Cloudflare/Caddy hardening should allow only required HTTP methods, apply a conservative MCP request-body cap, set upstream connection/read timeouts, and restrict direct origin traffic to the trusted proxy path. Treat Cloudflare/OpenAI source IPs as infrastructure addresses rather than reliable end-user identities; avoid aggressive per-IP rules that could group many legitimate ChatGPT calls together. Keep application-wide limits enabled even when edge rules are available.

For a small VPS, begin with one MCP application worker, `MCP_MAX_GLOBAL_JOBS=2` to `4`, a 60-second timeout, and the existing 20 MB / 100 MP input limits. At the container layer, a reasonable initial envelope is 1–2 GB RAM, 1–2 CPUs, and a PID limit around 128, adjusted from observed peak memory before production traffic. These container limits are documented rather than forced because the repository does not know the VPS's total capacity.

## Security deployment notes

- Production CORS should contain only the deployed frontend origin; the example also contains localhost entries for development.
- The frontend nginx CSP allows the production API and `http://localhost:8000`. If the API origin changes, update `connect-src` in `frontend/nginx.conf` and rebuild.
- Terminate HTTPS at the public reverse proxy. Enable HSTS there only after every covered subdomain is HTTPS-ready.
- Backend container access logs are disabled because temporary download tokens appear in URL paths. Ensure reverse-proxy logs also redact or omit `/download/*` tokens.
- Use `docker compose config --quiet` for validation in shared terminals or CI logs. The non-quiet form expands `env_file` values and can print secrets.
- Keep `API_KEY` server-side. Every `VITE_*` value is public in the browser bundle.
- The in-process limiter is intentionally fail-closed for overload (rejecting new heavy work) and stores identifiers only for a short rolling window.
