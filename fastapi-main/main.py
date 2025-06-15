from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import uvicorn
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 15 * 1024 * 1024
ALLOWED_EXTENSIONS = {".wav"}
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}")


@app.post("/upload/")
async def upload_audio_file(file: UploadFile = File(...)):
    validate_file(file)

    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    return JSONResponse(
        status_code=200,
        content={
            "message": "File uploaded successfully",
            "filename": file.filename,
            "file_size": len(file_content)
        }
    )


@app.get("/download/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='audio/wav'
    )


@app.get("/stream/{filename}")
async def get_file(filename: str):
    """Download/stream the actual file"""
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='audio/wav',
        headers={
            "Accept-Ranges": "bytes",
            "Content-Type": "audio/wav",
            "Cache-Control": "no-cache"
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
