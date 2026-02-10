import os
import shutil
from fastapi import APIRouter, UploadFile, File
from services.document_service import ingest_document
from schemas.document import DocumentUploadResponse

router = APIRouter(prefix="/ingest/document")

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=DocumentUploadResponse)
def upload_document(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    _, ext = os.path.splitext(file.filename)
    ingest_document(file_path, ext.lower())

    return DocumentUploadResponse(message="Document ingested successfully")
