# Konvertira

Konvertira is a privacy-first image conversion and metadata-removal service. The repository contains three independently deployable applications that share one image-processing core:

- `frontend/` — React, TypeScript, Vite, and Tailwind CSS application.
- `backend/` — FastAPI routes, processors, services, schemas, and utilities.
- `konvertira_mcp/` — MCP server and tools built on the same backend services.

The MCP package is named `konvertira_mcp` instead of `mcp` because the official MCP Python SDK already owns the top-level `mcp` package name. Using the requested name would shadow the SDK and prevent the server from importing.

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
python -m pip install -r requirements.txt
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
npm run build
```

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m compileall -q main.py mcp_server.py config.py backend konvertira_mcp
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

Processed files use configurable temporary directories and are deleted after `RESULT_TTL_SECONDS`. Compose mounts separate backend and MCP result volumes. No database, authentication system, payments, analytics, or permanent file store is included.
