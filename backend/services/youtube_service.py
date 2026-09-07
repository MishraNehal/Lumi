# from utils.youtube_transcript import extract_video_id, fetch_transcript_yt_dlp
# from langchain_core.documents import Document
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from database.vectorstore import vector_store


# def ingest_youtube(url):
#     url = str(url)
#     print("▶️ YouTube ingestion started")
#     text = fetch_transcript_yt_dlp(url)

#     if not text or not text.strip():
#         return False

#     documents = [
#         Document(
#             page_content=text,
#             metadata={"source": "youtube", "url": url}
#         )
#     ]
#     print("✅ Transcript length:", len(text))

#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=1000,
#         chunk_overlap=200
#     )

#     chunks = splitter.split_documents(documents)
#     get_vector_store(user_id).add_documents(chunks)
#     print(f"✅ YouTube chunks stored: {len(chunks)}")

#     return True


from backend.utils.youtube_transcript import fetch_transcript, extract_video_id
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.database.vectorstore import get_vector_store


def clean_transcript_text(text: str) -> str:
    """Remove YouTube-specific filler words that hurt retrieval quality."""
    fillers = [
        "subscribe", "like this video", "hit the bell",
        "guys", "welcome back", "channel", "smash that",
        "today we will", "in this video", "don't forget to",
    ]
    lowered = text.lower()
    for filler in fillers:
        lowered = lowered.replace(filler, "")
    # Return original case but with fillers removed (lowered only used for matching)
    for filler in fillers:
        text = text.replace(filler, "").replace(filler.capitalize(), "")
    return text.strip()


def ingest_youtube(url: str, user_id: int) -> dict:
    """
    Full YouTube ingestion pipeline.
    Returns a result dict with status, message, and chunk count.
    """
    url = str(url).strip()
    print(f"▶️  YouTube ingestion started: {url}")

    # Validate URL first
    video_id = extract_video_id(url)
    if not video_id:
        return {
            "success": False,
            "message": "Invalid YouTube URL. Use formats like: https://youtube.com/watch?v=ID or https://youtu.be/ID",
            "chunks": 0,
        }

    # Fetch transcript
    text = fetch_transcript(url)
    if not text or not text.strip():
        return {
            "success": False,
            "message": "No captions/subtitles available for this video. Try a video with English captions.",
            "chunks": 0,
        }

    # Clean filler words
    text = clean_transcript_text(text)

    # Create LangChain document
    documents = [
        Document(
            page_content=text,
            metadata={
                "source": "youtube",
                "url": url,
                "video_id": video_id,
                "filename": f"youtube_{video_id}",
            },
        )
    ]

    # Chunk with larger size for video content (more context = better)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(documents)

    if not chunks:
        return {
            "success": False,
            "message": "Transcript was too short to process.",
            "chunks": 0,
        }

    # Store in vector DB
    get_vector_store(user_id).add_documents(chunks)
    print(f"✅ YouTube ingestion complete: {len(chunks)} chunks stored")

    return {
        "success": True,
        "message": f"YouTube video ingested successfully.",
        "chunks": len(chunks),
        "video_id": video_id,
        "transcript_length": len(text),
    }