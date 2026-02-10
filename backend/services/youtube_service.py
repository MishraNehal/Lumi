from utils.youtube_transcript import extract_video_id, fetch_transcript_yt_dlp
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from database.vectorstore import vector_store


def ingest_youtube(url):
    url = str(url)
    print("▶️ YouTube ingestion started")
    text = fetch_transcript_yt_dlp(url)

    if not text or not text.strip():
        return False

    documents = [
        Document(
            page_content=text,
            metadata={"source": "youtube", "url": url}
        )
    ]
    print("✅ Transcript length:", len(text))

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = splitter.split_documents(documents)
    vector_store.add_documents(chunks)
    print(f"✅ YouTube chunks stored: {len(chunks)}")

    return True
