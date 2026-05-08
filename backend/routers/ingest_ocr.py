import os
import shutil
from fastapi import APIRouter, UploadFile, File
from backend.services.ocr_service import ingest_ocr_document

router = APIRouter(prefix="/ingest/ocr")

UPLOAD_DIR = "uploaded_ocr"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("")
def upload_ocr_document(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    ingest_ocr_document(file_path)

    return {"message": "OCR document ingested successfully"}
