from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from PIL import Image
import io
import base64

app = FastAPI(title="Metadata Remover API")

# Tvoj tajni ključ (slobodno ga promijeni u nešto drugo)
TAJNI_KLJUC = "moja-super-tajna-lozinka-123"
api_key_scheme = APIKeyHeader(name="X-API-Key")

def provjeri_kljuc(api_key: str = Depends(api_key_scheme)):
    if api_key != TAJNI_KLJUC:
        raise HTTPException(status_code=401, detail="Pristup odbijen. Neispravan API ključ.")
    return api_key

class ImageRequest(BaseModel):
    image_base64: str
    filename: str = "image.jpg"

class ImageResponse(BaseModel):
    image_base64: str
    filename: str

# Funkcija sada prvo zahtijeva provjeru ključa (Depends) prije izvršavanja
@app.post("/remove-metadata/", response_model=ImageResponse)
async def remove_metadata_endpoint(request: ImageRequest, kljuc: str = Depends(provjeri_kljuc)):
    try:
        image_bytes = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        data = list(image.getdata())
        clean_image = Image.new(image.mode, image.size)
        clean_image.putdata(data)
        
        output = io.BytesIO()
        clean_image.save(output, format=image.format or "JPEG")
        
        clean_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
        
        return {"image_base64": clean_base64, "filename": f"clean_{request.filename}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))