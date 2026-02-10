import os
from utils.ocr_engine import ocr_image, ocr_pdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database.vectorstore import vector_store



def ingest_ocr_document(file_path: str):
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    #  OCR based on file type
    if ext in [".png", ".jpg", ".jpeg"]:
        text = ocr_image(file_path)

    elif ext == ".pdf":
        text = ocr_pdf(file_path)

    else:
        raise ValueError("Unsupported OCR file type")

    if not text.strip():
        return

    # 2️ Convert to LangChain Document
    documents = [
        Document(
            page_content=text,
            metadata={"source": "ocr"}
        )
    ]

    # 3️ Chunk using LangChain
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)

    # 4️ Store in Vector DB
    vector_store.add_documents(chunks)
