import os
import shutil
from fastapi import APIRouter, UploadFile, File
from backend.services.ocr_service import ingest_ocr_document
from fastapi import Depends
from backend.auth.dependencies import get_current_user
from backend.database.models import User

router = APIRouter(prefix="/ingest/ocr")

UPLOAD_DIR = "uploaded_ocr"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("")
def upload_ocr_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    ingest_ocr_document(file_path, current_user.id)

    return {"message": "OCR document ingested successfully"}
