from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database.vectorstore import vector_store
from services.ocr_service import ingest_ocr_document


def ingest_document(file_path: str, ext: str):

    # PDF (with OCR fallback)
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        if not any(doc.page_content.strip() for doc in documents):
            ingest_ocr_document(file_path)
            return

    # Text & code files
    elif ext in [".txt", ".py", ".js", ".md", ".json"]:
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()

    # Word (.docx only)
    elif ext == ".docx":
        try:
            loader = UnstructuredWordDocumentLoader(file_path)
            documents = loader.load()
        except Exception as e:
            print("❌ DOCX parsing failed, using OCR:", e)
            ingest_ocr_document(file_path)
            return

    # Legacy Word (.doc)
    elif ext == ".doc":
        ingest_ocr_document(file_path)
        return

    # PPT
    elif ext == ".pptx":
        try:
            loader = UnstructuredPowerPointLoader(file_path)
            documents = loader.load()
        except Exception as e:
            print("❌ PPT parsing failed:", e)
            return

    # Excel
    elif ext in [".xls", ".xlsx"]:
        try:
            loader = UnstructuredExcelLoader(file_path)
            documents = loader.load()
        except Exception as e:
            print("❌ Excel parsing failed:", e)
            return

    else:
        raise ValueError("Unsupported file type")

    if not documents:
        return

    # Normalize metadata
    for doc in documents:
        doc.metadata["source"] = "document"
        doc.metadata["file_type"] = ext

   
    #  Chunk using LangChain
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)

    #  Store in vector DB
    vector_store.add_documents(chunks)
