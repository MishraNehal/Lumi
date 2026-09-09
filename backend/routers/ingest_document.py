# import os
# import shutil
# from fastapi import APIRouter, UploadFile, File
# from services.document_service import ingest_document
# from schemas.document import DocumentUploadResponse

# router = APIRouter(prefix="/ingest/document")

# UPLOAD_DIR = "uploaded_docs"
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# @router.post("", response_model=DocumentUploadResponse)
# def upload_document(file: UploadFile = File(...)):
#     file_path = os.path.join(UPLOAD_DIR, file.filename)

#     with open(file_path, "wb") as f:
#         shutil.copyfileobj(file.file, f)

#     _, ext = os.path.splitext(file.filename)
#     ingest_document(file_path, ext.lower())

#     return DocumentUploadResponse(message="Document ingested successfully")


import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from backend.services.document_service import ingest_document
from fastapi import Depends
from backend.auth.dependencies import get_current_user
from backend.database.models import User

router = APIRouter(prefix="/ingest/document")

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc", ".pptx", ".xlsx", ".xls", ".py", ".js", ".md"}


@router.post("")
def upload_documents(files: List[UploadFile] = File(...), current_user: User = Depends(get_current_user)):
    """
    Upload and ingest one or multiple documents.
    Supports: PDF, TXT, DOCX, PPTX, XLSX, and more.
    """
    results = []

    for file in files:
        _, ext = os.path.splitext(file.filename)
        ext = ext.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            results.append({
                "filename": file.filename,
                "status": "skipped",
                "message": f"Unsupported file type '{ext}'. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
                "chunks": 0,
            })
            continue

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        try:
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Failed to save file: {str(e)}",
                "chunks": 0,
            })
            continue

        try:
            chunk_count = ingest_document(file_path, ext, current_user.id)
            results.append({
                "filename": file.filename,
                "status": "success",
                "message": "Ingested successfully",
                "chunks": chunk_count if chunk_count else 0,
            })
        except ValueError as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e),
                "chunks": 0,
            })
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": f"Ingestion failed: {str(e)}",
                "chunks": 0,
            })

    total_success = sum(1 for r in results if r["status"] == "success")
    total_chunks = sum(r["chunks"] for r in results)

    return {
        "message": f"{total_success}/{len(files)} file(s) ingested successfully.",
        "total_chunks": total_chunks,
        "results": results,
    }