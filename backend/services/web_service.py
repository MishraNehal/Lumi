from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database.vectorstore import vector_store


def ingest_web(url: str):
    loader = WebBaseLoader(url)
    documents = loader.load()

    if not documents:
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    chunks = splitter.split_documents(documents)

    # normalize metadata
    for doc in chunks:
        doc.metadata["source"] = "web"
        doc.metadata["url"] = url

    vector_store.add_documents(chunks)
