# from langchain_community.document_loaders import (
#     PyPDFLoader,
#     TextLoader,
#     UnstructuredWordDocumentLoader,
#     UnstructuredPowerPointLoader,
#     UnstructuredExcelLoader
# )
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from database.vectorstore import vector_store
# from services.ocr_service import ingest_ocr_document


# def ingest_document(file_path: str, ext: str, user_id: int):

#     # PDF (with OCR fallback)
#     if ext == ".pdf":
#         loader = PyPDFLoader(file_path)
#         documents = loader.load()

#         if not any(doc.page_content.strip() for doc in documents):
#             ingest_ocr_document(file_path)
#             return

#     # Text & code files
#     elif ext in [".txt", ".py", ".js", ".md", ".json"]:
#         loader = TextLoader(file_path, encoding="utf-8")
#         documents = loader.load()

#     # Word (.docx only)
#     elif ext == ".docx":
#         try:
#             loader = UnstructuredWordDocumentLoader(file_path)
#             documents = loader.load()
#         except Exception as e:
#             print("❌ DOCX parsing failed, using OCR:", e)
#             ingest_ocr_document(file_path)
#             return

#     # Legacy Word (.doc)
#     elif ext == ".doc":
#         ingest_ocr_document(file_path)
#         return

#     # PPT
#     elif ext == ".pptx":
#         try:
#             loader = UnstructuredPowerPointLoader(file_path)
#             documents = loader.load()
#         except Exception as e:
#             print("❌ PPT parsing failed:", e)
#             return

#     # Excel
#     elif ext in [".xls", ".xlsx"]:
#         try:
#             loader = UnstructuredExcelLoader(file_path)
#             documents = loader.load()
#         except Exception as e:
#             print("❌ Excel parsing failed:", e)
#             return

#     else:
#         raise ValueError("Unsupported file type")

#     if not documents:
#         return

#     # Normalize metadata
#     for doc in documents:
#         doc.metadata["source"] = "document"
#         doc.metadata["file_type"] = ext

   
#     #  Chunk using LangChain
#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=50
#     )
#     chunks = splitter.split_documents(documents)

#     #  Store in vector DB
#     get_vector_store(user_id).add_documents(chunks)


import os
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.database.vectorstore import get_vector_store
from backend.services.ocr_service import ingest_ocr_document


def ingest_document(file_path: str, ext: str, user_id: int) -> int:
    """
    Parse, chunk, embed and store a document.
    Returns the number of chunks stored.
    """
    documents = []
    filename = os.path.basename(file_path)

    # PDF with OCR fallback
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
        try:
            documents = loader.load()
            if not any(doc.page_content.strip() for doc in documents):
                print(f"⚠️ PDF text empty, falling back to OCR: {filename}")
                return ingest_ocr_document(file_path, user_id)
        except Exception as e:
            print(f"⚠️ PDF parsing failed, falling back to OCR: {e}")
            return ingest_ocr_document(file_path, user_id)

    # Plain text and code files
    elif ext in [".txt", ".py", ".js", ".md", ".json"]:
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            documents = loader.load()
        except UnicodeDecodeError:
            loader = TextLoader(file_path, encoding="latin-1")
            documents = loader.load()

    # Word documents
    elif ext == ".docx":
        try:
            loader = UnstructuredWordDocumentLoader(file_path)
            documents = loader.load()
        except Exception as e:
            print(f"⚠️ DOCX parsing failed, trying OCR: {e}")
            return ingest_ocr_document(file_path, user_id)

    elif ext == ".doc":
        return ingest_ocr_document(file_path, user_id)

    # PowerPoint
    elif ext == ".pptx":
        try:
            loader = UnstructuredPowerPointLoader(file_path)
            documents = loader.load()
        except Exception as e:
            raise ValueError(f"Failed to parse PPTX: {str(e)}")

    # Excel
    elif ext in [".xls", ".xlsx"]:
        try:
            loader = UnstructuredExcelLoader(file_path)
            documents = loader.load()
        except Exception as e:
            raise ValueError(f"Failed to parse Excel: {str(e)}")

    else:
        raise ValueError(f"Unsupported file type: {ext}")

    if not documents:
        raise ValueError("No content could be extracted from this file.")

    # Normalize metadata — add filename for human-readable source labels
    for doc in documents:
        doc.metadata["source"] = "document"
        doc.metadata["file_type"] = ext
        doc.metadata["filename"] = filename

    # Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        raise ValueError("Document content was too short to process.")

    # Store
    get_vector_store(user_id).add_documents(chunks)
    print(f"✅ Document ingested: {filename} → {len(chunks)} chunks")
    return len(chunks)