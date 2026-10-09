"""Service information, health, and compatibility privacy endpoints."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from config import settings

router = APIRouter()


@router.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_policy() -> str:
    """Retain the legacy API-hosted privacy page for existing integrations."""

    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Privacy Policy - Konvertira</title>
<style>body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.6;color:#222}h1,h2{color:#111}.updated{color:#666}</style>
</head><body><h1>Privacy Policy</h1><p class="updated">Last updated: October 9, 2026</p>
<h2>1. What this service does</h2><p>Konvertira provides file conversion, PDF, and supported metadata workflows. The public website identifies local and server processing before a file is processed.</p>
<h2>2. Server processing</h2><p>When a user explicitly starts a server-backed workflow, the file is processed only for the requested operation. ChatGPT/MCP workflows retrieve files only from configured HTTPS OpenAI download hosts.</p>
<h2>3. Temporary storage</h2><p>Downloadable results may be stored temporarily and are removed after a configured limited period, which is approximately 15 minutes by default.</p>
<h2>4. Limits of metadata removal</h2><p>Metadata removal creates a new copy but does not guarantee anonymity, redaction of visible content, removal of every identifier, or malware sanitization.</p>
<h2>5. Contact</h2><p>For privacy questions, contact: <strong>legal@konvertira.com</strong></p>
</body></html>"""
