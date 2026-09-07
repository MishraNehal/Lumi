# from langchain_community.document_loaders import WebBaseLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from database.vectorstore import vector_store


# def ingest_web(url: str):
#     loader = WebBaseLoader(url)
#     documents = loader.load()

#     if not documents:
#         return

#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=50
#     )

#     chunks = splitter.split_documents(documents)

#     # normalize metadata
#     for doc in chunks:
#         doc.metadata["source"] = "web"
#         doc.metadata["url"] = url

#     get_vector_store(user_id).add_documents(chunks)

from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.database.vectorstore import get_vector_store


def ingest_web(url: str, user_id: int) -> dict:
    """
    Scrape a web page, chunk, embed and store in vector DB.
    Returns dict with chunk count.
    """
    try:
        loader = WebBaseLoader(url)
        documents = loader.load()
    except Exception as e:
        raise ValueError(f"Could not load URL: {str(e)}")

    if not documents:
        raise ValueError("No content found at the provided URL.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)

    # Normalize metadata
    for doc in chunks:
        doc.metadata["source"] = "web"
        doc.metadata["url"] = url
        doc.metadata["filename"] = url  # used for source label in UI

    get_vector_store(user_id).add_documents(chunks)
    print(f"✅ Web page ingested: {url} → {len(chunks)} chunks")

    return {"chunks": len(chunks)}