from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.database.vectorstore import get_vector_store


def _fallback_scrape(url: str) -> list:
    """Glue-code fallback if WebBaseLoader fails (e.g. site blocks default user-agent)."""
    import requests
    from bs4 import BeautifulSoup

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return [Document(page_content=text, metadata={})] if text.strip() else []


def ingest_web(url: str, user_id: int) -> dict:
    """
    Scrape a web page, chunk, embed and store in vector DB.
    Tries LangChain's WebBaseLoader first; falls back to a direct
    requests+BeautifulSoup scrape if that fails.
    Returns dict with chunk count.
    """
    try:
        documents = WebBaseLoader(url).load()
        if not documents or not any(d.page_content.strip() for d in documents):
            raise ValueError("WebBaseLoader returned empty content.")
    except Exception as e:
        print(f"⚠️ WebBaseLoader failed, using fallback scraper: {e}")
        try:
            documents = _fallback_scrape(url)
        except Exception as e2:
            raise ValueError(f"Could not load URL: {str(e2)}")

    if not documents:
        raise ValueError("No content found at the provided URL.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    for doc in chunks:
        doc.metadata["source"] = "web"
        doc.metadata["url"] = url
        doc.metadata["filename"] = url

    get_vector_store(user_id).add_documents(chunks)
    print(f"✅ Web page ingested: {url} → {len(chunks)} chunks")

    return {"chunks": len(chunks)}