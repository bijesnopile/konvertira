import io
import os
from typing import Final

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.security import APIKeyHeader
from PIL import Image, UnidentifiedImageError


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

APP_TITLE: Final[str] = "Metadata Remover API"
APP_VERSION: Final[str] = "2.0.0"

# Maksimalna veličina uploadane slike: 20 MB
MAX_IMAGE_SIZE: Final[int] = 20 * 1024 * 1024

# Maksimalno 100 megapiksela
MAX_PIXELS: Final[int] = 100_000_000

ALLOWED_FORMATS: Final[set[str]] = {
    "JPEG",
    "PNG",
    "WEBP",
}


# ============================================================
# API KEY
# ============================================================

API_KEY = os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError(
        "API_KEY nije postavljen. "
        "Provjeri postoji li .env datoteka."
    )


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="API za uklanjanje metadata iz slika.",
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
    Provjerava X-API-Key header.

    Očekuje:

        X-API-Key: tvoj-kljuc
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
# HELPERS
# ============================================================

def get_content_type(image_format: str) -> str:
    """
    Pretvara Pillow format u MIME type.
    """

    content_types = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }

    return content_types.get(
        image_format,
        "application/octet-stream",
    )


def clean_filename(filename: str | None) -> str:
    """
    Čisti filename da ne sadrži path.
    """

    if not filename:
        return "image"

    filename = os.path.basename(
        filename.strip()
    )

    return filename or "image"


# ============================================================
# METADATA REMOVAL
# ============================================================

def remove_metadata(
    image_bytes: bytes,
) -> tuple[bytes, str]:
    """
    Uklanja metadata iz slike.

    Podržani:
        JPEG
        PNG
        WEBP

    Vraća:
        (obrađena_slika, format)
    """

    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Slika je prazna.",
        )

    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Slika je prevelika. Maksimalno 20 MB.",
        )

    # --------------------------------------------------------
    # OPEN IMAGE
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
            detail="Slika je oštećena ili se ne može pročitati.",
        )

    # --------------------------------------------------------
    # FORMAT
    # --------------------------------------------------------

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
    # RESOLUTION CHECK
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
    # CREATE CLEAN IMAGE
    # --------------------------------------------------------

    # Nova Image instanca dobiva samo pixel podatke.
    # Originalni EXIF/XMP/IPTC/GPS metadata se ne kopiraju.
    clean_image = Image.new(
        source.mode,
        source.size,
    )

    clean_image.putdata(
        list(source.getdata())
    )

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    output = io.BytesIO()

    if image_format == "JPEG":

        # JPEG treba RGB ili L.
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

    clean_bytes = output.getvalue()

    if not clean_bytes:
        raise HTTPException(
            status_code=500,
            detail="Nije moguće generirati očišćenu sliku.",
        )

    return clean_bytes, image_format


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "service": APP_TITLE,
        "version": APP_VERSION,
        "status": "running",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
    }


# ============================================================
# IMAGE UPLOAD
# ============================================================

@app.post("/remove-metadata/upload")
async def upload_image(
    file: UploadFile = File(...),
    _: None = Depends(verify_api_key),
):
    """
    Prima sliku preko multipart/form-data.

    Auth:
        X-API-Key

    Form field:
        file

    Podržani:
        JPEG
        PNG
        WEBP
    """

    # --------------------------------------------------------
    # MIME TYPE
    # --------------------------------------------------------

    allowed_mime_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=415,
            detail=(
                "Dozvoljeni su samo JPEG, PNG i WEBP."
            ),
        )

    # --------------------------------------------------------
    # READ FILE
    # --------------------------------------------------------

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploadana datoteka je prazna.",
        )

    # --------------------------------------------------------
    # REMOVE METADATA
    # --------------------------------------------------------

    clean_bytes, image_format = remove_metadata(
        image_bytes
    )

    # --------------------------------------------------------
    # FILENAME
    # --------------------------------------------------------

    original_name = clean_filename(
        file.filename
    )

    clean_name = f"clean_{original_name}"

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return Response(
        content=clean_bytes,
        media_type=get_content_type(image_format),
        headers={
            "Content-Disposition": (
                f'attachment; filename="{clean_name}"'
            )
        },
    )


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )