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
<title>Privacy Policy - Image Privacy Protector</title>
<style>body{font-family:Arial,sans-serif;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.6;color:#222}h1,h2{color:#111}.updated{color:#666}</style>
</head><body><h1>Privacy Policy</h1><p class="updated">Last updated: October 2, 2026</p>
<h2>1. What this service does</h2><p>Image Privacy Protector processes uploaded images to remove embedded metadata such as EXIF, GPS/location information, camera information, date and time metadata, and related embedded metadata.</p>
<h2>2. Images</h2><p>Images uploaded to the service are processed only for the purpose of removing embedded metadata.</p><p>Processed images are stored temporarily so that the user can download the cleaned image.</p>
<h2>3. Temporary storage</h2><p>Processed files are automatically removed after a limited period and are not intended to be permanently stored.</p>
<h2>4. Personal information</h2><p>The service is designed to process image files and does not intentionally collect personal information beyond what is technically necessary to operate the service.</p>
<h2>5. Third-party services</h2><p>The service may receive uploaded files through OpenAI's file-processing infrastructure when used through a ChatGPT Action.</p>
<h2>6. Security</h2><p>HTTPS should be used for communication with the service. Legacy API access is protected using an API key.</p>
<h2>7. Contact</h2><p>For privacy questions, contact: <strong>matejtokic85@gmail.com</strong></p>
</body></html>"""
