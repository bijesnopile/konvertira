from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from PIL import Image
import io

app = FastAPI(title="Metadata Remover API")

@app.post("/remove-metadata/")
async def remove_metadata_endpoint(file: UploadFile = File(...)):
    # 1. Čitanje poslane datoteke u memoriju
    image_bytes = await file.read()
    
    # 2. Otvaranje slike iz memorije pomoću Pillow biblioteke
    image = Image.open(io.BytesIO(image_bytes))
    
    # 3. Izvlačenje isključivo slikovnih piksela (svi EXIF metapodaci se ovime ignoriraju)
    data = list(image.getdata())
    
    # 4. Kreiranje potpuno nove, "čiste" slike s istim modom (RGB/RGBA) i dimenzijama
    clean_image = Image.new(image.mode, image.size)
    clean_image.putdata(data)
    
    # 5. Priprema čiste slike za slanje natrag (spremanje u memoriju umjesto na disk)
    output = io.BytesIO()
    # Zadržava originalni format, a ako ga ne može prepoznati sprema kao JPEG
    clean_image.save(output, format=image.format or "JPEG")
    output.seek(0)
    
    # 6. Slanje datoteke natrag s izričitom uputom za preuzimanje
    headers = {'Content-Disposition': f'attachment; filename="clean_{file.filename}"'}
    return StreamingResponse(output, media_type=file.content_type, headers=headers)