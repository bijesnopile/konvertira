from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image
import io
import base64

app = FastAPI(title="Metadata Remover API")

# Definiramo strukturu onoga što primamo (tekst slike i ime)
class ImageRequest(BaseModel):
    image_base64: str
    filename: str = "image.jpg"

# Definiramo strukturu onoga što vraćamo
class ImageResponse(BaseModel):
    image_base64: str
    filename: str

@app.post("/remove-metadata/", response_model=ImageResponse)
async def remove_metadata_endpoint(request: ImageRequest):
    try:
        # 1. Pretvaranje teksta (Base64) natrag u pravu sliku
        image_bytes = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        
        # 2. Uklanjanje metapodataka (izvlače se samo pikseli)
        data = list(image.getdata())
        clean_image = Image.new(image.mode, image.size)
        clean_image.putdata(data)
        
        # 3. Spremanje čiste slike u memoriju
        output = io.BytesIO()
        clean_image.save(output, format=image.format or "JPEG")
        
        # 4. Kodiranje čiste slike natrag u Base64 tekst za povratak
        clean_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
        
        return {"image_base64": clean_base64, "filename": f"clean_{request.filename}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))