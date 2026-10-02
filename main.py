import io
import os
import secrets
import tempfile
import time
from pathlib import Path
from typing import Final
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from PIL import Image, UnidentifiedImageError


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIG
# ============================================================

APP_TITLE: Final[str] = "Image Privacy Protector"
APP_VERSION: Final[str] = "3.0.0"

MAX_IMAGE_SIZE: Final[int] = 20 * 1024 * 1024
MAX_PIXELS: Final[int] = 100_000_000

RESULT_TTL_SECONDS: Final[int] = 15 * 60

ALLOWED_FORMATS: Final[set[str]] = {
    "JPEG",
    "PNG",
    "WEBP",
}

ALLOWED_MIME_TYPES: Final[set[str]] = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

# OpenAI temporary uploaded-file URLs currently use this host.
ALLOWED_DOWNLOAD_HOST: Final[str] = "files.oaiusercontent.com"


# ============================================================
# API KEY
# ============================================================

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError(
        "API_KEY nije postavljen. "
        "Postavi API_KEY u Render Environment Variables."
    )


# ============================================================
# STORAGE
# ============================================================

STORAGE_DIR = Path(
    tempfile.gettempdir()
) / "image-privacy-protector"

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=(
        "Removes embedded metadata from JPEG, PNG and WEBP images."
    ),
)


# ============================================================
# AUTHENTICATION
# ============================================================

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


async def verify_api_key(
    x_api_key: str | None = Depends(api_key_header),
) -> None:
    """
    Validates the X-API-Key header.
    """

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Nedostaje X-API-Key header.",
        )

    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Neispravan API ključ.",
        )


# ============================================================
# MODELS
# ============================================================

class OpenAIFileRef(BaseModel):
    """
    Runtime object supplied by GPT Actions.

    openaiFileIdRefs is documented as an array of strings in
    the OpenAPI schema, but the runtime expands each item into
    an object containing these fields.
    """

    name: str
    id: str
    mime_type: str
    download_link: str


class ActionRequest(BaseModel):
    """
    Request received from the GPT Action.
    """

    openaiFileIdRefs: list[OpenAIFileRef] = Field(
        ...,
        min_length=1,
        max_length=1,
    )


class ActionResponse(BaseModel):
    """
    Result returned to the GPT Action.
    """

    success: bool
    filename: str
    content_type: str
    download_url: str
    message: str


# ============================================================
# HELPERS
# ============================================================

def get_content_type(image_format: str) -> str:
    return {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }.get(
        image_format,
        "application/octet-stream",
    )


def clean_filename(filename: str | None) -> str:
    if not filename:
        return "image"

    filename = os.path.basename(
        filename.strip()
    )

    return filename or "image"


def remove_metadata(
    image_bytes: bytes,
) -> tuple[bytes, str]:
    """
    Opens an image, copies only pixel data into a new image,
    then re-encodes it without the original metadata.
    """

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Slika je prazna.",
        )

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                "Slika je prevelika. "
                "Maksimalna veličina je 20 MB."
            ),
        )

    # --------------------------------------------------------
    # OPEN
    # --------------------------------------------------------

    try:
        source = Image.open(
            io.BytesIO(image_bytes)
        )

        source.load()

    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="Datoteka nije valjana slika.",
        )

    except OSError:
        raise HTTPException(
            status_code=400,
            detail=(
                "Slika je oštećena ili se ne može pročitati."
            ),
        )

    image_format = (
        source.format or ""
    ).upper()

    if image_format not in ALLOWED_FORMATS:
        raise HTTPException(
            status_code=415,
            detail=(
                "Podržani formati su JPEG, PNG i WEBP."
            ),
        )

    # --------------------------------------------------------
    # RESOLUTION
    # --------------------------------------------------------

    width, height = source.size

    if width <= 0 or height <= 0:
        raise HTTPException(
            status_code=400,
            detail="Slika ima neispravne dimenzije.",
        )

    if width * height > MAX_PIXELS:
        raise HTTPException(
            status_code=413,
            detail=(
                "Rezolucija slike je prevelika. "
                "Maksimalno je 100 megapiksela."
            ),
        )

    # --------------------------------------------------------
    # COPY PIXELS ONLY
    # --------------------------------------------------------

    clean_image = Image.new(
        source.mode,
        source.size,
    )

    clean_image.putdata(
        list(source.getdata())
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output = io.BytesIO()

    if image_format == "JPEG":

        if clean_image.mode not in ("RGB", "L"):
            clean_image = clean_image.convert("RGB")

        clean_image.save(
            output,
            format="JPEG",
            quality=100,
            subsampling=0,
            optimize=True,
            progressive=True,
        )

    elif image_format == "PNG":

        clean_image.save(
            output,
            format="PNG",
            optimize=True,
        )

    elif image_format == "WEBP":

        if clean_image.mode not in ("RGB", "RGBA"):
            clean_image = clean_image.convert("RGBA")

        clean_image.save(
            output,
            format="WEBP",
            quality=100,
            method=6,
        )

    result = output.getvalue()

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Nije moguće generirati očišćenu sliku.",
        )

    return result, image_format


def cleanup_old_files() -> None:
    """
    Deletes temporary results older than RESULT_TTL_SECONDS.
    """

    now = time.time()

    for path in STORAGE_DIR.iterdir():

        if not path.is_file():
            continue

        try:
            age = now - path.stat().st_mtime

            if age > RESULT_TTL_SECONDS:
                path.unlink(missing_ok=True)

        except OSError:
            pass


async def download_openai_file(
    download_link: str,
) -> bytes:
    """
    Preuzima privremeni OpenAI file URL.

    Dopušta samo HTTPS URL-ove na OpenAI domenama.
    Redirecti su dopušteni, ali se nakon redirecta ponovno
    provjerava konačni hostname.
    """

    parsed = urlparse(download_link)

    if parsed.scheme != "https":
        raise HTTPException(
            status_code=400,
            detail="Download URL mora koristiti HTTPS.",
        )

    initial_host = (parsed.hostname or "").lower()

    def is_allowed_openai_host(host: str) -> bool:
        host = host.lower().rstrip(".")

        return (
            host == "openai.com"
            or host.endswith(".openai.com")
            or host == "oaiusercontent.com"
            or host.endswith(".oaiusercontent.com")
        )

    if not is_allowed_openai_host(initial_host):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Nedozvoljeni download host: {initial_host}"
            ),
        )

    timeout = httpx.Timeout(
        connect=10.0,
        read=60.0,
        write=10.0,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        ) as client:

            response = await client.get(
                download_link
            )

    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ne mogu preuzeti uploadanu datoteku: {exc}"
            ),
        )

    final_host = (
        response.url.host or ""
    ).lower()

    if not is_allowed_openai_host(final_host):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Download URL se preusmjerio na "
                f"nedozvoljeni host: {final_host}"
            ),
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=(
                "OpenAI download link nije vratio "
                f"valjan odgovor ({response.status_code})."
            ),
        )

    if len(response.content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Uploadana slika je veća od 20 MB.",
        )

    return response.content


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
async def root():
    return {
        "service": APP_TITLE,
        "version": APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
    }


# ============================================================
# GPT ACTION ENDPOINT
# ============================================================

@app.post(
    "/remove-metadata/action",
    response_model=ActionResponse,
)
async def remove_metadata_action(
    request: ActionRequest,
    _: None = Depends(verify_api_key),
):
    """
    GPT Actions endpoint.

    Receives:
        openaiFileIdRefs

    Downloads the user's uploaded image directly from the
    temporary OpenAI file URL, removes metadata, stores the
    result temporarily, and returns a downloadable URL.
    """

    cleanup_old_files()

    if not request.openaiFileIdRefs:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nijedna datoteka nije proslijeđena u "
                "openaiFileIdRefs."
            ),
        )

    file_ref = request.openaiFileIdRefs[0]

    if file_ref.mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                "Podržani formati su JPEG, PNG i WEBP."
            ),
        )

    # --------------------------------------------------------
    # DOWNLOAD FROM OPENAI
    # --------------------------------------------------------

    image_bytes = await download_openai_file(
        file_ref.download_link
    )

    # --------------------------------------------------------
    # REMOVE METADATA
    # --------------------------------------------------------

    clean_bytes, image_format = remove_metadata(
        image_bytes
    )

    # --------------------------------------------------------
    # STORE TEMPORARILY
    # --------------------------------------------------------

    token = secrets.token_urlsafe(32)

    extension = {
        "JPEG": ".jpg",
        "PNG": ".png",
        "WEBP": ".webp",
    }[image_format]

    file_path = STORAGE_DIR / (
        f"{token}{extension}"
    )

    try:
        file_path.write_bytes(
            clean_bytes
        )
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Nije moguće spremiti obrađenu sliku: {exc}"
            ),
        )

    # --------------------------------------------------------
    # PUBLIC DOWNLOAD URL
    # --------------------------------------------------------

    public_url = (
        f"https://metadata-remover-ompw.onrender.com"
        f"/download/{token}"
    )

    original_name = clean_filename(
        file_ref.name
    )

    clean_name = (
        f"clean_{original_name}"
    )

    return ActionResponse(
        success=True,
        filename=clean_name,
        content_type=get_content_type(
            image_format
        ),
        download_url=public_url,
        message=(
            "Metadata su uklonjeni. "
            "Otvori download_url za preuzimanje "
            "očišćene slike."
        ),
    )


# ============================================================
# DOWNLOAD RESULT
# ============================================================

@app.get("/download/{token}")
async def download_result(
    token: str,
):
    """
    Serves a processed image temporarily.
    """

    cleanup_old_files()

    if not token or len(token) < 20:
        raise HTTPException(
            status_code=404,
            detail="Datoteka nije pronađena.",
        )

    matches = list(
        STORAGE_DIR.glob(
            f"{token}.*"
        )
    )

    if not matches:
        raise HTTPException(
            status_code=404,
            detail=(
                "Datoteka više nije dostupna. "
                "Generiraj novu očišćenu sliku."
            ),
        )

    file_path = matches[0]

    # Determine MIME type from extension.
    content_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(
        file_path.suffix.lower(),
        "application/octet-stream",
    )

    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=f"clean_{file_path.stem}{file_path.suffix}",
        headers={
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


# ============================================================
# OPTIONAL MANUAL UPLOAD ENDPOINT
# ============================================================

@app.post("/remove-metadata/upload")
async def manual_upload(
    file: bytes,
    _: None = Depends(verify_api_key),
):
    """
    Ostavljen za ručne API testove.

    GPT Action NE koristi ovaj endpoint.
    """

    clean_bytes, image_format = remove_metadata(
        file
    )

    return Response(
        content=clean_bytes,
        media_type=get_content_type(
            image_format
        ),
        headers={
            "Cache-Control": "no-store",
        },
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            "8000",
        )
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
    )