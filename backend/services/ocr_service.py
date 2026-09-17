
import os
from backend.utils.ocr_engine import ocr_image, ocr_pdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.database.vectorstore import get_vector_store


def ingest_ocr_document(file_path: str, user_id: int) -> int:
    """
    Run OCR on image or PDF and store in vector DB.
    Returns the number of chunks stored.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    filename = os.path.basename(file_path)

    if ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]:
        text = ocr_image(file_path)
    elif ext == ".pdf":
        text = ocr_pdf(file_path)
    else:
        raise ValueError(f"Unsupported OCR file type: {ext}")

    if not text or not text.strip():
        raise ValueError("OCR extracted no readable text from this file.")

    documents = [
        Document(
            page_content=text,
            metadata={
                "source": "ocr",
                "filename": filename,
                "file_type": ext,
            },
        )
    ]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("OCR text was too short to process.")

    get_vector_store(user_id).add_documents(chunks)
    print(f"✅ OCR ingested: {filename} → {len(chunks)} chunks")
    return len(chunks)